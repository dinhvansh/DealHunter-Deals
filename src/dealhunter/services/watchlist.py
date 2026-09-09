from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WatchMode(str, Enum):
    NORMAL = "NORMAL"
    HOT = "HOT"


@dataclass(slots=True)
class WatchRule:
    variant_id: str
    mode: WatchMode = WatchMode.NORMAL
    target_price: int | None = None
    min_deal_score: int | None = None
    verify_account: bool = False
    alert_on_price_drop: bool = True
    alert_on_new_voucher: bool = True
    alert_on_historical_low: bool = True


def should_alert(rule: WatchRule, current_price: int, deal_score: int, is_new_low: bool = False) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if rule.target_price is not None and current_price <= rule.target_price:
        reasons.append("target_price")
    if rule.min_deal_score is not None and deal_score >= rule.min_deal_score:
        reasons.append("deal_score")
    if rule.alert_on_historical_low and is_new_low:
        reasons.append("historical_low")
    return bool(reasons), reasons
