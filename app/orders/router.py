from typing import Annotated
from typing import List
import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.dependencies import validate_user_access
from app.core.dependencies import get_db
from app.core.dependencies import get_redis_client
from app.orders.schemas import OrderCreate
from app.orders.schemas import OrderRead
from app.orders.schemas import OrderUpdateStatus
from app.orders.service import OrderService
from app.user.models import User as DBUser


router = APIRouter(tags=["orders"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis_client)]
CurrentUserDep = Annotated[
    DBUser, Security(get_current_active_user, scopes=["user", "admin", "staff"])
]
AuthorizedUserID = Annotated[int, Depends(validate_user_access)]


@router.post("/orders/", response_model=OrderRead)
async def create_order(
    order_in: OrderCreate,
    db: SessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> OrderRead:
    """
    Creates a new order for the current user.
    """
    order_service = OrderService(db, redis)
    return await order_service.create_order(current_user.id, order_in)


@router.get("/orders/{order_id}/", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    db: SessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> OrderRead:
    """
    Retrieves a specific order by its ID.
    Enforces ownership: Users can only see their own orders.
    """
    order_service = OrderService(db, redis)
    order = await order_service.get_order(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_admin = "admin" in current_user.scopes
    is_owner = order.user_id == current_user.id

    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")

    return order


@router.patch("/orders/{order_id}/", response_model=OrderRead)
async def update_order_status(
    order_id: uuid.UUID,
    order_in: OrderUpdateStatus,
    db: SessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> OrderRead:
    """
    Updates the status of an existing order (e.g., PENDING -> PAID).
    """
    order_service = OrderService(db, redis)

    updated_order = await order_service.update_order_status(order_id, order_in.status)

    if not updated_order:
        raise HTTPException(status_code=404, detail="Order not found")

    return updated_order


@router.get("/orders/user/{user_id}/", response_model=List[OrderRead])
async def get_orders_for_user(
    user_id: AuthorizedUserID,
    db: SessionDep,
    redis: RedisDep,
) -> List[OrderRead]:
    """
    Retrieves all orders for a specific user.
    Authorization (Admin or Owner) is handled by dependency.
    """
    order_service = OrderService(db, redis)
    return await order_service.get_user_orders(user_id)
