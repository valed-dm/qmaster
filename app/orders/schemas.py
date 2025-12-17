from datetime import datetime
from typing import List
import uuid

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from app.orders.models import OrderStatus


class OrderItem(BaseModel):
    product_id: int
    name: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderBase(BaseModel):
    items: List[OrderItem]
    total_price: float = Field(..., gt=0)


class OrderCreate(OrderBase):
    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderRead(OrderBase):
    id: uuid.UUID
    user_id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
