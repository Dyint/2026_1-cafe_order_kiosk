from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
CLI_PATH = ROOT / "cafe_order_kiosk" / "cli.py"
RECEIPT_PATH = ROOT / "cafe_order_kiosk" / "receipt.py"
TEST_PATH = ROOT / "tests" / "unit" / "test_receipt.py"


def require_project_root() -> None:
    required = [
        CLI_PATH,
        ROOT / "cafe_order_kiosk" / "models.py",
        ROOT / "cafe_order_kiosk" / "kiosk_store.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("프로젝트 루트 폴더에서 실행해야 합니다. 누락된 파일: " + ", ".join(missing))


def write_receipt_module() -> None:
    RECEIPT_PATH.write_text(
        '''from __future__ import annotations

from cafe_order_kiosk.models import Order, OrderStatus
from cafe_order_kiosk.utils import format_money


STATUS_TEXT = {
    OrderStatus.OPEN: "진행중",
    OrderStatus.PAID: "결제완료",
    OrderStatus.CANCELED: "취소",
}


def build_receipt(order: Order) -> str:
    lines: list[str] = [
        "========== 카페 주문 영수증 ==========",
        f"주문번호: #{order.id}",
        f"상태: {format_order_status(order.status)}",
    ]

    if order.note:
        lines.append(f"메모: {order.note}")

    lines.append("----------------------------------------")

    if not order.items:
        lines.append("주문 항목 없음")
    else:
        for idx, item in enumerate(order.items, start=1):
            options = f" [{', '.join(item.options)}]" if item.options else ""
            price = format_money(item.unit_price)
            total = format_money(item.line_total)
            lines.append(f"{idx}. {item.name}{options} x{item.quantity} @ {price}원 = {total}원")

    lines.append("----------------------------------------")
    lines.append(f"합계: {format_money(order.total)}원")

    if order.payment:
        lines.append(f"결제수단: {order.payment.method}")
        lines.append(f"결제금액: {format_money(order.payment.amount)}원")
    elif order.status is OrderStatus.CANCELED:
        lines.append("결제상태: 취소됨")
    else:
        lines.append("결제상태: 미결제")

    lines.append("========================================")
    return "\\n".join(lines)


def format_order_status(status: OrderStatus) -> str:
    return STATUS_TEXT.get(status, status.value)
''',
        encoding="utf-8",
    )


def patch_cli() -> None:
    text = CLI_PATH.read_text(encoding="utf-8")

    if "from cafe_order_kiosk.receipt import build_receipt" not in text:
        text = text.replace(
            "from cafe_order_kiosk.utils import format_money\n",
            "from cafe_order_kiosk.utils import format_money\nfrom cafe_order_kiosk.receipt import build_receipt\n",
        )

    if 'command in {"영수증", "receipt"}' not in text:
        target = '        elif command in {"결제", "pay"}:\n            handle_pay(store, state, args)\n'
        if target not in text:
            raise SystemExit("cli.py에서 결제 명령 처리 위치를 찾지 못했습니다.")
        text = text.replace(
            target,
            target + '        elif command in {"영수증", "receipt"}:\n            handle_receipt(store, state, args)\n',
            1,
        )

    if 'print("\\t영수증 [주문_id]")' not in text:
        target = '    print("\\t결제 <방법> [금액]")\n'
        if target not in text:
            raise SystemExit("cli.py에서 도움말 결제 명령 위치를 찾지 못했습니다.")
        text = text.replace(target, target + '    print("\\t영수증 [주문_id]")\n', 1)

    if "def handle_receipt(" not in text:
        handler = '''

def handle_receipt(store: KioskStore, state: CLIState, args: list[str]) -> None:
    if args:
        order_id = parse_int_arg(args[:1], "order_id")
        if order_id is None:
            return
    else:
        if state.current_order_id is None:
            print("선택된 주문이 없습니다. 먼저 '주문 생성'을 사용하거나 주문_id를 입력하세요.")
            return
        order_id = state.current_order_id

    order = store.get_order(order_id)
    if order is None:
        print("주문을 찾을 수 없습니다.")
        return

    print(build_receipt(order))
'''
        marker = "\ndef print_order(order) -> None:"
        if marker not in text:
            raise SystemExit("cli.py에서 print_order 함수 위치를 찾지 못했습니다.")
        text = text.replace(marker, handler + marker, 1)

    CLI_PATH.write_text(text, encoding="utf-8")


def write_tests() -> None:
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.write_text(
        '''from cafe_order_kiosk.kiosk_store import KioskStore
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
''',
        encoding="utf-8",
    )


def main() -> None:
    require_project_root()
    write_receipt_module()
    patch_cli()
    write_tests()
    print("영수증 출력 기능 파일을 적용했습니다.")
    print("다음 명령어로 테스트하세요: python -m pytest -q")


if __name__ == "__main__":
    main()
