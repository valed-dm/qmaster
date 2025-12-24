from typing import Annotated
from typing import List
import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Security
from fastapi import status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.dependencies import require_admin
from app.auth.dependencies import validate_user_access
from app.core.dependencies import get_db
from app.core.dependencies import get_redis_client
from app.orders.dependencies import validate_order_access
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
AuthorizedOrder = Annotated[OrderRead, Depends(validate_order_access)]
AdminUser = Annotated[DBUser, Depends(require_admin)]


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
    order: AuthorizedOrder,
) -> OrderRead:
    """
    Retrieves a specific order by its ID.
    Enforces ownership: Users can only see their own orders, admins can see any order.
    Authorization is handled by the validate_order_access dependency.
    """
    return order


@router.patch("/orders/{order_id}/", response_model=OrderRead)
async def update_order_status(
    order_id: uuid.UUID,
    order_in: OrderUpdateStatus,
    db: SessionDep,
    redis: RedisDep,
    _: AdminUser,
) -> OrderRead:
    """
    Updates the status of an existing order (e.g., PENDING -> PAID).
    Enforces authorization: Only admins can update order status.
    Authorization is handled by the require_admin dependency.
    """
    order_service = OrderService(db, redis)
    updated_order = await order_service.update_order_status(order_id, order_in.status)

    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

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
