import pytest

from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.models import DiscountCoupon


def test_apply_percent_coupon_updates_total() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()
    store.add_item(order.id, menu_item_id=2, quantity=2)

    store.apply_coupon(order.id, "welcome10")
    order = store.get_order(order.id)

    assert order is not None
    assert order.coupon is not None
    assert order.coupon.code == "WELCOME10"
    assert order.subtotal == 8000
    assert order.discount_amount == 800
    assert order.total == 7200


def test_apply_fixed_coupon_requires_minimum_order_amount() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()
    store.add_item(order.id, menu_item_id=1, quantity=1)

    with pytest.raises(ValueError, match="Order total does not meet coupon minimum"):
        store.apply_coupon(order.id, "CAFE1000")


def test_apply_fixed_coupon_and_pay_discounted_total() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()
    store.add_item(order.id, menu_item_id=10, quantity=2)

    store.apply_coupon(order.id, "CAFE1000")
    store.pay_order(order.id, method="card", amount=9400)
    order = store.get_order(order.id)

    assert order is not None
    assert order.subtotal == 10400
    assert order.discount_amount == 1000
    assert order.total == 9400
    assert order.payment is not None
    assert order.payment.amount == 9400


def test_remove_coupon_restores_total() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()
    store.add_item(order.id, menu_item_id=2, quantity=2)

    store.apply_coupon(order.id, "WELCOME10")
    store.remove_coupon(order.id)
    order = store.get_order(order.id)

    assert order is not None
    assert order.coupon is None
    assert order.discount_amount == 0
    assert order.total == 8000


def test_coupon_discount_is_capped_by_subtotal() -> None:
    coupon = DiscountCoupon(
        code="FREE",
        description="최대 주문금액까지만 할인",
        discount_amount=999999,
    )

    assert coupon.calculate_discount(3500) == 3500
