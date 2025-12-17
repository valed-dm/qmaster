import json
from typing import List
from typing import Optional
import uuid

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order
from app.orders.models import OrderStatus
from app.orders.schemas import OrderCreate
from app.orders.schemas import OrderRead
from app.orders.tasks import process_order


CACHE_TTL = 300


class OrderService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis

    async def create_order(self, user_id: int, order_in: OrderCreate) -> OrderRead:
        """
        Creates an order, saves it to DB, and triggers a background task.
        """
        # 1. Create DB Object
        new_order = Order(
            user_id=user_id,
            items=[
                item.model_dump() for item in order_in.items
            ],  # Convert Pydantic items to dicts for JSON column
            total_price=order_in.total_price,
            status=OrderStatus.PENDING,
        )

        self.db.add(new_order)
        await self.db.commit()
        await self.db.refresh(new_order)

        # 2. Trigger Celery Task (Publishes to RabbitMQ)
        process_order.delay(str(new_order.id))

        # 3. Cache the new order immediately
        await self._cache_order(new_order)

        return OrderRead.model_validate(new_order)

    async def get_order(self, order_id: uuid.UUID) -> Optional[OrderRead]:
        """
        Retrieves an order with Redis caching strategy.
        Returns a Pydantic Model, not an ORM object.
        """
        # 1. Try to get from Redis
        cache_key = f"order:{order_id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return OrderRead(**data)

        # 2. If it Missed, get from DB
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            return None

        # 3. Save to Redis
        await self._cache_order(order)

        return OrderRead.model_validate(order)

    async def update_order_status(
        self, order_id: uuid.UUID, status: OrderStatus
    ) -> Optional[OrderRead]:
        """
        Updates order status in DB and invalidates cache.
        Fetches directly from DB to ensure we have a mutable ORM object.
        """
        # 1. Fetch from DB (Bypass cache to ensure we have the ORM object)
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            return None

        # 2. Update and Commit
        order.status = status
        await self.db.commit()
        await self.db.refresh(order)

        # 3. Invalidate Cache
        cache_key = f"order:{order_id}"
        await self.redis.delete(cache_key)

        return OrderRead.model_validate(order)

    async def get_user_orders(self, user_id: int) -> List[OrderRead]:
        """
        Get all orders for a specific user (Direct DB hit).
        """
        result = await self.db.execute(select(Order).where(Order.user_id == user_id))
        orders = result.scalars().all()
        return [OrderRead.model_validate(o) for o in orders]

    async def _cache_order(self, order: Order) -> None:
        """Helper to serialize and save order to Redis."""
        order_schema = OrderRead.model_validate(order)
        order_json = order_schema.model_dump_json()

        cache_key = f"order:{order.id}"
        await self.redis.set(cache_key, order_json, ex=CACHE_TTL)
