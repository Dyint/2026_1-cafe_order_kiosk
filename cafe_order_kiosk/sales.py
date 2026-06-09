from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SalesMenuSummary:
    menu_item_id: int
    name: str
    quantity: int
    amount: int


@dataclass(frozen=True)
class SalesSummary:
    paid_order_count: int
    total_amount: int
    items: tuple[SalesMenuSummary, ...]
