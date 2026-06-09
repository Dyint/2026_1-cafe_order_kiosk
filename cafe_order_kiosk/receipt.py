from __future__ import annotations

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
    return "\n".join(lines)


def format_order_status(status: OrderStatus) -> str:
    return STATUS_TEXT.get(status, status.value)
