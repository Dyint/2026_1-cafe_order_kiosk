from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from cafe_order_kiosk.utils import utc_now


class OrderStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    CANCELED = "canceled"


@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    price: int
    category: str | None = None
    description: str | None = None
    is_available: bool = True


@dataclass(frozen=True)
class DiscountCoupon:
    code: str
    description: str
    discount_rate: int = 0
    discount_amount: int = 0
    minimum_order_amount: int = 0

    def __post_init__(self) -> None:
        if self.discount_rate < 0 or self.discount_rate > 100:
            raise ValueError("discount_rate must be between 0 and 100")
        if self.discount_amount < 0:
            raise ValueError("discount_amount must be greater than or equal to 0")
        if self.minimum_order_amount < 0:
            raise ValueError("minimum_order_amount must be greater than or equal to 0")
        if self.discount_rate == 0 and self.discount_amount == 0:
            raise ValueError("discount_rate or discount_amount is required")

    def calculate_discount(self, subtotal: int) -> int:
        if subtotal < self.minimum_order_amount:
            return 0

        rate_discount = subtotal * self.discount_rate // 100
        fixed_discount = self.discount_amount
        discount = max(rate_discount, fixed_discount)
        return min(discount, subtotal)


@dataclass
class OrderItem:
    menu_item_id: int
    name: str
    unit_price: int
    quantity: int
    options: list[str] = field(default_factory=list)

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Payment:
    method: str
    amount: int
    paid_at: datetime


@dataclass
class Order:
    id: int
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    created_at: datetime = field(default_factory=utc_now)
    paid_at: datetime | None = None
    canceled_at: datetime | None = None
    note: str | None = None
    payment: Payment | None = None
    coupon: DiscountCoupon | None = None

    @property
    def subtotal(self) -> int:
        return sum(item.line_total for item in self.items)

    @property
    def discount_amount(self) -> int:
        if self.coupon is None:
            return 0
        return self.coupon.calculate_discount(self.subtotal)

    @property
    def total(self) -> int:
        return self.subtotal - self.discount_amount
