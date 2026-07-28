# python_service/schemas/order.py
from pydantic import BaseModel, Field
from typing import List


class OrderItem(BaseModel):
    name: str = Field(description="Sipariş edilen ürünün adı (örn: pizza, kola, hamburger)")
    quantity: int = Field(default=1, description="Ürünün adedi/miktarı")


class OrderSchema(BaseModel):
    items: List[OrderItem] = Field(description="Siparişteki ürünlerin listesi")