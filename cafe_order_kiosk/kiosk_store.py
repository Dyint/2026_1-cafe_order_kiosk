from __future__ import annotations

from collections.abc import Iterable

from cafe_order_kiosk.models import (
    DiscountCoupon,
    MenuItem,
    Order,
    OrderItem,
    OrderStatus,
    Payment,
)
from cafe_order_kiosk.utils import utc_now


DEFAULT_MENU: tuple[MenuItem, ...] = (
    MenuItem(id=1, name="Americano", price=3500, category="coffee"),
    MenuItem(id=2, name="Latte", price=4000, category="coffee"),
    MenuItem(id=3, name="Cappuccino", price=4200, category="coffee"),
    MenuItem(id=4, name="Cold Brew", price=4500, category="coffee"),
    MenuItem(id=5, name="Matcha Latte", price=4800, category="tea"),
    MenuItem(id=6, name="Chamomile Tea", price=3800, category="tea"),
    MenuItem(id=7, name="Lemonade", price=4200, category="juice"),
    MenuItem(id=8, name="Butter Croissant", price=3500, category="bakery"),
    MenuItem(id=9, name="Blueberry Muffin", price=3200, category="bakery"),
    MenuItem(id=10, name="Cheesecake", price=5200, category="dessert"),
)

DEFAULT_COUPONS: tuple[DiscountCoupon, ...] = (
    DiscountCoupon(
        code="WELCOME10",
        description="첫 방문 고객 10% 할인",
        discount_rate=10,
    ),
    DiscountCoupon(
        code="CAFE1000",
        description="10,000원 이상 주문 시 1,000원 할인",
        discount_amount=1000,
        minimum_order_amount=10000,
    ),
)


class KioskStore:
    def __init__(
        self,
        menu_items: Iterable[MenuItem] | None = None,
        coupons: Iterable[DiscountCoupon] | None = None,
    ) -> None:
        self._menu: dict[int, MenuItem] = {item.id: item for item in (menu_items or [])}
        self._coupons: dict[str, DiscountCoupon] = {
            coupon.code.upper(): coupon for coupon in (coupons or [])
        }
        self._orders: dict[int, Order] = {}
        self._next_order_id = 1

    @classmethod
    def with_default_menu(cls) -> KioskStore:
        return cls(menu_items=DEFAULT_MENU, coupons=DEFAULT_COUPONS)

    def list_menu(self, only_available: bool = True) -> list[MenuItem]:
        items: Iterable[MenuItem] = self._menu.values()
        if only_available:
            items = [item for item in items if item.is_available]
        return sorted(items, key=lambda item: item.id)

    def get_menu_item(self, menu_item_id: int) -> MenuItem | None:
        return self._menu.get(menu_item_id)

    def list_coupons(self) -> list[DiscountCoupon]:
        return sorted(self._coupons.values(), key=lambda coupon: coupon.code)

    def get_coupon(self, code: str) -> DiscountCoupon | None:
        return self._coupons.get(code.upper())

    def create_order(self, note: str | None = None) -> Order:
        order_id = self._next_order_id
        self._next_order_id += 1
        order = Order(id=order_id, note=note)
        self._orders[order_id] = order
        return order

    def list_orders(self, status: OrderStatus | None = None) -> list[Order]:
        orders: Iterable[Order] = self._orders.values()
        if status is not None:
            orders = [order for order in orders if order.status == status]
        return sorted(orders, key=lambda order: order.id)

    def get_order(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def add_item(
        self,
        order_id: int,
        menu_item_id: int,
        quantity: int,
        options: list[str] | None = None,
    ) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        menu_item = self._menu.get(menu_item_id)
        if menu_item is None:
            raise ValueError("Menu item not found")
        if not menu_item.is_available:
            raise ValueError("Menu item is not available")
        order_item = OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            unit_price=menu_item.price,
            quantity=quantity,
            options=options or [],
        )
        order.items.append(order_item)
        return order

    def remove_item(self, order_id: int, line_index: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if line_index < 1 or line_index > len(order.items):
            raise ValueError("Line item not found")
        order.items.pop(line_index - 1)
        return order

    def apply_coupon(self, order_id: int, code: str) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if not order.items:
            raise ValueError("Order has no items")

        coupon = self.get_coupon(code)
        if coupon is None:
            raise ValueError("Coupon not found")
        if order.subtotal < coupon.minimum_order_amount:
            raise ValueError("Order total does not meet coupon minimum")

        order.coupon = coupon
        return order

    def remove_coupon(self, order_id: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if order.coupon is None:
            raise ValueError("No coupon applied")

        order.coupon = None
        return order

    def cancel_order(self, order_id: int) -> Order:
        order = self._require_order(order_id)
        if order.status is OrderStatus.CANCELED:
            return order
        if order.status is OrderStatus.PAID:
            raise ValueError("Paid order cannot be canceled")
        order.status = OrderStatus.CANCELED
        order.canceled_at = utc_now()
        return order

    def pay_order(self, order_id: int, method: str, amount: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if not order.items:
            raise ValueError("Order has no items")
        if amount != order.total:
            raise ValueError("Payment amount does not match total")
        order.status = OrderStatus.PAID
        order.paid_at = utc_now()
        order.payment = Payment(method=method, amount=amount, paid_at=order.paid_at)
        return order

    def _require_order(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError("Order not found")
        return order
