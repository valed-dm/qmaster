"""Users table and related models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.timestamp import TimestampMixin


if TYPE_CHECKING:
    from app.orders.models import Order


class User(Base, TimestampMixin):
    """
    User model representing the 'users' table in the database.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        email (str | None): Unique email address.
        hashed_password (str): Hashed password for the user.
        full_name (str | None): User's full name.
        disabled (bool): Flag to indicate if the user account is active.
        scopes (str): Space-separated string of authorization scopes.
        orders (list["Order"]): A list of orders associated with the user.
    """

    __tablename__ = "users"
    __table_args__ = (
        sa.Index("ix_users_username", "username", unique=True),
        sa.Index("ix_users_email", "email", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    disabled: Mapped[bool] = mapped_column(
        Boolean, server_default=sa.text("false"), nullable=False
    )
    scopes: Mapped[str] = mapped_column(
        String(255), server_default=sa.text("''"), nullable=False
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
