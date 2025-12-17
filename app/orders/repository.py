from typing import List
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order
from app.orders.models import OrderStatus


class OrderRepository:
    """Handles direct database operations for Order models."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, order: Order) -> Order:
        """Add a new order to the database and refresh it."""
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Optional[Order]:
        """Retrieve an order by its ID."""
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> List[Order]:
        """Retrieve all orders for a specific user."""
        result = await self.db.execute(select(Order).where(Order.user_id == user_id))
        return list(result.scalars().all())

    async def update_status(self, order: Order, status: OrderStatus) -> Order:
        """Update the status of an order."""
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)
        return order
