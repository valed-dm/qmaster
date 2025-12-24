"""
Order-specific authorization dependencies.

This module provides dependencies for order authorization checks that require
order-specific context and services.
"""

from __future__ import annotations

from typing import Annotated
import uuid

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import _parse_user_scopes
from app.auth.dependencies import get_current_active_user
from app.core.dependencies import get_db
from app.core.dependencies import get_redis_client
from app.orders.schemas import OrderRead
from app.orders.service import OrderService
from app.user.models import User


async def validate_order_access(
    order_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis_client)],
) -> OrderRead:
    """
    Dependency that validates user has access to a specific order.

    Ensures the requesting user is either:
    1. An admin (can access any order)
    2. The owner of the order (order.user_id matches current_user.id)

    Args:
        order_id: UUID of the order to validate access for.
        current_user: The authenticated user from get_current_active_user.
        db: Database session.
        redis: Redis client.

    Returns:
        OrderRead schema if access is granted.

    Raises:
        HTTPException (404): If the order is not found.
        HTTPException (403): If the user is not authorized to access the order.
    """
    order_service = OrderService(db, redis)
    order = await order_service.get_order(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    user_scopes = _parse_user_scopes(current_user.scopes)
    is_admin = "admin" in user_scopes
    is_owner = order.user_id == current_user.id

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this order",
        )

    return order

