from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from typing import Any
import uuid

import sqlalchemy as sa
from sqlalchemy import JSON
from sqlalchemy import Enum
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.timestamp import TimestampMixin


if TYPE_CHECKING:
    from app.user.models import User


class OrderStatus(str, PyEnum):
    """Enumeration of possible statuses for an order.

    Attributes:
        PENDING: Order has been created but not yet paid.
        PAID: Order has been paid by the user.
        SHIPPED: Order has been shipped to the user.
        CANCELED: Order has been canceled.
    """

    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class Order(Base, TimestampMixin):
    """Represents a customer order in the database.

    Attributes:
        id (UUID): Primary key of the order.
        user_id (int): Foreign key referencing the owner user.
        items (list[dict]): List of items included in the order.
        total_price (float): Total price of all items in the order.
        status (OrderStatus): Current status of the order.
        user (User): Relationship to the owning User instance.
        created_at (datetime): Timestamp when the order was created.
        updated_at (datetime): Timestamp when the order was last updated.
    """

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", create_type=False),
        default=OrderStatus.PENDING,
        server_default="'PENDING'",
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="orders")
