from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class DiscountType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"
    FREESHIP = "freeship"


@dataclass(slots=True)
class VoucherRule:
    code: str
    discount_type: DiscountType
    discount_value: int
    max_discount: int | None = None
    min_spend: int = 0
    stack_group: str | None = None
    stackable: bool | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class AppliedVoucher:
    code: str
    discount: int


@dataclass(slots=True)
class PromotionResult:
    observed_price: int
    estimated_price: int
    applied: list[AppliedVoucher]
    rejected: list[tuple[str, str]]
    confidence: float


def _active(v: VoucherRule, now: datetime) -> bool:
    if v.start_at and now < v.start_at:
        return False
    if v.end_at and now > v.end_at:
        return False
    return True


def _discount(v: VoucherRule, subtotal: int) -> int:
    if subtotal < v.min_spend:
        return 0
    if v.discount_type == DiscountType.FIXED:
        return min(v.discount_value, subtotal)
    if v.discount_type == DiscountType.PERCENT:
        amount = subtotal * v.discount_value // 100
        if v.max_discount is not None:
            amount = min(amount, v.max_discount)
        return min(amount, subtotal)
    if v.discount_type == DiscountType.FREESHIP:
        return max(0, v.discount_value)
    return 0


def optimize_promotions(price: int, vouchers: list[VoucherRule], now: datetime | None = None) -> PromotionResult:
    now = now or datetime.now(timezone.utc)
    eligible: list[VoucherRule] = []
    rejected: list[tuple[str, str]] = []
    for voucher in vouchers:
        if not _active(voucher, now):
            rejected.append((voucher.code, "inactive"))
            continue
        if price < voucher.min_spend:
            rejected.append((voucher.code, "min_spend"))
            continue
        eligible.append(voucher)

    # Deterministic greedy per stack group: choose the best discount in each mutually-exclusive group,
    # while stackable vouchers without a group can all participate.
    selected: list[VoucherRule] = []
    grouped: dict[str, list[VoucherRule]] = {}
    for voucher in eligible:
        if voucher.stack_group:
            grouped.setdefault(voucher.stack_group, []).append(voucher)
        else:
            selected.append(voucher)
    for group_vouchers in grouped.values():
        selected.append(max(group_vouchers, key=lambda v: _discount(v, price)))

    subtotal = price
    applied: list[AppliedVoucher] = []
    confidences: list[float] = []
    for voucher in sorted(selected, key=lambda v: _discount(v, subtotal), reverse=True):
        discount = _discount(voucher, subtotal)
        if discount <= 0:
            rejected.append((voucher.code, "zero_discount"))
            continue
        if voucher.discount_type != DiscountType.FREESHIP:
            subtotal = max(0, subtotal - discount)
        else:
            # Freeship is represented in estimated checkout savings, but product subtotal stays unchanged.
            subtotal = max(0, subtotal - discount)
        applied.append(AppliedVoucher(voucher.code, discount))
        confidences.append(voucher.confidence)

    confidence = min(confidences) if confidences else 1.0
    return PromotionResult(price, subtotal, applied, rejected, confidence)
