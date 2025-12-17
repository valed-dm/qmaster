import json
from typing import List
from typing import Optional
import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order
from app.orders.models import OrderStatus
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderCreate
from app.orders.schemas import OrderRead
from app.orders.tasks import process_order


CACHE_TTL = 300  # seconds


class OrderService:
    """Handles business logic for orders, caching, and background tasks."""

    def __init__(self, db: AsyncSession, redis: Redis):
        self.repo = OrderRepository(db)
        self.redis = redis

    async def create_order(self, user_id: int, order_in: OrderCreate) -> OrderRead:
        """Create a new order, trigger Celery task, and cache in Redis."""
        new_order = Order(
            user_id=user_id,
            items=[item.model_dump() for item in order_in.items],
            total_price=order_in.total_price,
            status=OrderStatus.PENDING,
        )
        new_order = await self.repo.add(new_order)

        # Trigger background Celery task
        process_order.delay(str(new_order.id))

        await self._cache_order(new_order)

        return OrderRead.model_validate(new_order)

    async def get_order(self, order_id: uuid.UUID) -> Optional[OrderRead]:
        """Retrieve an order using Redis caching; fallback to DB if needed."""
        cache_key = f"order:{order_id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return OrderRead(**data)

        order = await self.repo.get_by_id(order_id)
        if not order:
            return None

        await self._cache_order(order)
        return OrderRead.model_validate(order)

    async def update_order_status(
        self, order_id: uuid.UUID, status: OrderStatus
    ) -> Optional[OrderRead]:
        """Update the status of an order and invalidate Redis cache."""
        order = await self.repo.get_by_id(order_id)
        if not order:
            return None

        updated_order = await self.repo.update_status(order, status)
        await self.redis.delete(f"order:{order_id}")

        return OrderRead.model_validate(updated_order)

    async def get_user_orders(self, user_id: int) -> List[OrderRead]:
        """Retrieve all orders for a user."""
        orders = await self.repo.get_by_user_id(user_id)
        return [OrderRead.model_validate(o) for o in orders]

    async def _cache_order(self, order: Order) -> None:
        """Serialize and save an order to Redis."""
        order_schema = OrderRead.model_validate(order)
        order_json = order_schema.model_dump_json()
        cache_key = f"order:{order.id}"
        await self.redis.set(cache_key, order_json, ex=CACHE_TTL)
