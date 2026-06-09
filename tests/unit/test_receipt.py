from cafe_order_kiosk.kiosk_store import KioskStore
from cafe_order_kiosk.receipt import build_receipt


def test_receipt_for_open_order() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order(note="takeout")
    store.add_item(order.id, menu_item_id=1, quantity=2, options=["ice"])

    receipt = build_receipt(order)

    assert "카페 주문 영수증" in receipt
    assert "주문번호: #1" in receipt
    assert "메모: takeout" in receipt
    assert "Americano [ice] x2" in receipt
    assert "합계: 7,000원" in receipt
    assert "결제상태: 미결제" in receipt


def test_receipt_for_paid_order() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()
    store.add_item(order.id, menu_item_id=2, quantity=1)
    store.pay_order(order.id, method="card", amount=4000)

    receipt = build_receipt(order)

    assert "상태: 결제완료" in receipt
    assert "Latte x1" in receipt
    assert "결제수단: card" in receipt
    assert "결제금액: 4,000원" in receipt


def test_receipt_for_empty_order() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    receipt = build_receipt(order)

    assert "주문 항목 없음" in receipt
    assert "합계: 0원" in receipt
