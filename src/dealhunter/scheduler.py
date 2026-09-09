from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class RefreshPolicy:
    name: str
    interval: timedelta


NORMAL_POLICY = RefreshPolicy("NORMAL", timedelta(hours=2))
HOT_POLICY = RefreshPolicy("HOT", timedelta(minutes=45))
DISCOVERY_POLICY = RefreshPolicy("DISCOVERY", timedelta(hours=4))


def policy_for_mode(mode: str) -> RefreshPolicy:
    if mode.upper() == "HOT":
        return HOT_POLICY
    return NORMAL_POLICY
