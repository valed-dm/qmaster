from unittest.mock import patch

from httpx import AsyncClient


async def test_create_order_happy_path(async_client: AsyncClient, auth_token: str):
    """
    Test creating an order using the standard test user.
    """
    # 1. Setup Headers (using the fixture token which has correct scopes)
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Payload
    payload = {
        "items": [
            {"product_id": 1, "name": "Widget A", "quantity": 2, "price": 10.5},
            {"product_id": 2, "name": "Widget B", "quantity": 1, "price": 20.0},
        ],
        "total_price": 41.0,
    }

    # 3. Mock Celery
    with patch("app.orders.service.process_order.delay") as mock_celery:
        response = await async_client.post("/orders/", json=payload, headers=headers)

    # 4. Assertions
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["status"] == "PENDING"
    assert data["total_price"] == 41.0
    assert len(data["items"]) == 2
    assert "id" in data

    mock_celery.assert_called_once()


async def test_get_order_security(
    async_client: AsyncClient, user_a_token: str, user_b_token: str
):
    """
    Test that User B cannot see User A's order.
    Uses user_a_token and user_b_token fixtures from conftest.
    """
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # 1. User A creates an order
    with patch("app.orders.service.process_order.delay"):
        create_resp = await async_client.post(
            "/orders/",
            json={
                "items": [{"product_id": 1, "name": "x", "quantity": 1, "price": 10}],
                "total_price": 10,
            },
            headers=headers_a,
        )
    assert create_resp.status_code == 200
    order_id = create_resp.json()["id"]

    # 2. User A tries to read it (Should Succeed)
    resp_a = await async_client.get(f"/orders/{order_id}/", headers=headers_a)
    assert resp_a.status_code == 200
    assert resp_a.json()["id"] == order_id

    # 3. User B tries to read it (Should Fail - 403 Forbidden)
    resp_b = await async_client.get(f"/orders/{order_id}/", headers=headers_b)
    assert resp_b.status_code == 403
    assert "Not authorized" in resp_b.json()["detail"]


async def test_update_order_status(async_client: AsyncClient, auth_token: str):
    """
    Test updating status using the standard test user.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 1. Create Order
    with patch("app.orders.service.process_order.delay"):
        create_resp = await async_client.post(
            "/orders/",
            json={
                "items": [{"product_id": 1, "name": "x", "quantity": 1, "price": 10}],
                "total_price": 10,
            },
            headers=headers,
        )
    order_id = create_resp.json()["id"]

    # 2. Update Status
    update_payload = {"status": "PAID"}
    resp = await async_client.patch(
        f"/orders/{order_id}/", json=update_payload, headers=headers
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "PAID"

    # 3. Verify Read returns new status
    get_resp = await async_client.get(f"/orders/{order_id}/", headers=headers)
    assert get_resp.json()["status"] == "PAID"


async def test_get_user_orders_security(
    async_client: AsyncClient, user_a_token: str, user_b_token: str
):
    """
    Test the /orders/user/{user_id}/ endpoint security dependency.
    """
    headers_a = {"Authorization": f"Bearer {user_a_token}"}
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # 1. Get User A's ID
    me_resp = await async_client.get("/users/me", headers=headers_a)

    # --- DEBUG ASSERTION ---
    # This will show us the real error in the pytest output
    assert (
        me_resp.status_code == 200
    ), f"GET /users/me failed! Status: {me_resp.status_code}. Response: {me_resp.text}"
    # -----------------------
    print(f"DEBUG JSON: {me_resp.json()}")

    id_a = me_resp.json()["id"]

    # 2. User B tries to list User A's orders -> Expect 403
    resp = await async_client.get(f"/orders/user/{id_a}/", headers=headers_b)
    assert resp.status_code == 403
