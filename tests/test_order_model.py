from datetime import datetime
from datetime import timedelta
from datetime import timezone
from time import sleep
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.models import Order
from app.orders.models import OrderStatus
from app.user.models import User


class TestOrderModel:
    """
    Test suite for the Order database model.
    """

    async def test_successful_order_creation(
        self, db_session: AsyncSession, user_a: User
    ) -> None:
        """
        Tests that an order can be created successfully with all fields populated.
        """
        items_data = [
            {"product_id": 1, "name": "Test Item", "quantity": 2, "price": 10.5},
            {"product_id": 5, "name": "Another Item", "quantity": 1, "price": 100.0},
        ]

        order = Order(
            user_id=user_a.id,
            items=items_data,
            total_price=121.0,
            status=OrderStatus.PAID,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.id is not None
        assert isinstance(order.id, uuid.UUID)
        assert order.user_id == user_a.id
        assert order.total_price == 121.0
        assert order.status == OrderStatus.PAID
        # Verify JSON storage
        assert len(order.items) == 2
        assert order.items[0]["name"] == "Test Item"

    async def test_order_defaults(self, db_session: AsyncSession, user_a: User) -> None:
        """
        Tests that default values (UUID, Status=PENDING) are applied correctly.
        """
        # We do not provide 'status' or 'id'
        order = Order(
            user_id=user_a.id,
            items=[{"id": 1, "val": "test"}],
            total_price=50.0,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        # Check Defaults
        assert order.id is not None
        assert isinstance(order.id, uuid.UUID)
        assert order.status == OrderStatus.PENDING

    # --- Constraint Tests ---

    async def test_foreign_key_constraint(self, db_session: AsyncSession) -> None:
        """
        Tests that creating an order with a non-existent user_id fails.
        """
        order = Order(
            user_id=99999,
            items=[],
            total_price=10.0,
        )
        db_session.add(order)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_cascade_delete(
        self, db_session: AsyncSession, raw_db_session: AsyncSession, user_a: User
    ) -> None:
        """
        Tests that deleting a User also deletes their Orders (CASCADE).
        """
        # 1. Create an order for User A
        order = Order(
            user_id=user_a.id,
            items=[],
            total_price=10.0,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        order_id = order.id

        # 2. Delete User A
        await db_session.delete(user_a)
        await db_session.commit()

        # 3. Verify Order is gone using raw session
        # (We use raw session to ensure no session cache interference)
        fetched_order = await raw_db_session.get(Order, order_id)
        assert fetched_order is None

    async def test_total_price_is_not_nullable(
        self, db_session: AsyncSession, user_a: User
    ) -> None:
        """
        Tests that 'total_price' cannot be None.
        """
        order = Order(
            user_id=user_a.id,
            items=[],
            total_price=None,
        )
        db_session.add(order)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    # --- TimestampMixin Tests ---

    async def test_timestamps_on_create(
        self, db_session: AsyncSession, user_a: User
    ) -> None:
        now = datetime.now(timezone.utc)
        order = Order(
            user_id=user_a.id,
            items=[],
            total_price=10.0,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        assert order.created_at is not None
        assert order.updated_at is not None
        # Check that timestamp is recent (within 5 seconds)
        assert now - order.created_at < timedelta(seconds=5)
        assert now - order.updated_at < timedelta(seconds=5)

    async def test_updated_at_on_update(
        self, db_session: AsyncSession, user_a: User
    ) -> None:
        # 1. Create Order
        order = Order(
            user_id=user_a.id,
            items=[],
            total_price=10.0,
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)

        original_created_at = order.created_at
        original_updated_at = order.updated_at

        # 2. Wait a bit to ensure timestamp difference
        sleep(1)

        # 3. Update Order
        order.status = OrderStatus.SHIPPED
        await db_session.commit()
        await db_session.refresh(order)

        # 4. Assertions
        assert order.created_at == original_created_at
        assert order.updated_at > original_updated_at
