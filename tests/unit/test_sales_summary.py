from cafe_order_kiosk.kiosk_store import KioskStore


def test_sales_summary_counts_only_paid_orders() -> None:
    store = KioskStore.with_default_menu()
    paid_order = store.create_order()
    open_order = store.create_order()

    store.add_item(paid_order.id, menu_item_id=1, quantity=2)
    store.add_item(open_order.id, menu_item_id=2, quantity=3)
    store.pay_order(paid_order.id, method="card", amount=7000)

    summary = store.sales_summary()

    assert summary.paid_order_count == 1
    assert summary.total_amount == 7000
    assert len(summary.items) == 1
    assert summary.items[0].name == "Americano"
    assert summary.items[0].quantity == 2
    assert summary.items[0].amount == 7000


def test_sales_summary_groups_same_menu_items() -> None:
    store = KioskStore.with_default_menu()
    first = store.create_order()
    second = store.create_order()

    store.add_item(first.id, menu_item_id=2, quantity=1)
    store.add_item(second.id, menu_item_id=2, quantity=2)
    store.pay_order(first.id, method="card", amount=4000)
    store.pay_order(second.id, method="cash", amount=8000)

    summary = store.sales_summary()

    assert summary.paid_order_count == 2
    assert summary.total_amount == 12000
    assert len(summary.items) == 1
    assert summary.items[0].menu_item_id == 2
    assert summary.items[0].quantity == 3
    assert summary.items[0].amount == 12000


def test_sales_summary_sorts_by_quantity_then_amount() -> None:
    store = KioskStore.with_default_menu()
    order = store.create_order()

    store.add_item(order.id, menu_item_id=10, quantity=1)
    store.add_item(order.id, menu_item_id=1, quantity=3)
    store.add_item(order.id, menu_item_id=2, quantity=2)
    store.pay_order(order.id, method="card", amount=23700)

    summary = store.sales_summary()

    names = [item.name for item in summary.items]
    assert names == ["Americano", "Latte", "Cheesecake"]


def test_empty_sales_summary() -> None:
    store = KioskStore.with_default_menu()

    summary = store.sales_summary()

    assert summary.paid_order_count == 0
    assert summary.total_amount == 0
    assert summary.items == ()
