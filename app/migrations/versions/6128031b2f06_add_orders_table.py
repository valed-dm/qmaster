"""add orders table

Revision ID: 6128031b2f06
Revises: c39431c5f796
Create Date: 2025-12-16 12:04:43.622658

"""

from typing import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "6128031b2f06"
down_revision: Union[str, None] = "c39431c5f796"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "orders",
        sa.Column(
            "id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PAID", "SHIPPED", "CANCELED", name="order_status"),
            server_default=sa.text("'PENDING'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("orders")
    order_status_enum = sa.Enum(name="order_status")
    order_status_enum.drop(op.get_bind(), checkfirst=True)
