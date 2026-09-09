from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from dealhunter.db.models import PriceSnapshot


@dataclass(slots=True)
class PriceStats:
    current_price: int | None
    median_7d: int | None
    median_30d: int | None
    median_90d: int | None
    low_30d: int | None
    low_90d: int | None
    low_180d: int | None
    observations_30d: int


def _window(values: list[tuple[datetime, int]], days: int, now: datetime) -> list[int]:
    threshold = now - timedelta(days=days)
    return [price for ts, price in values if ts >= threshold]


def _median(values: list[int]) -> int | None:
    return int(median(values)) if values else None


def _min(values: list[int]) -> int | None:
    return min(values) if values else None


def get_price_history(db: Session, variant_id: str, days: int = 90) -> list[PriceSnapshot]:
    threshold = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(PriceSnapshot)
        .where(PriceSnapshot.variant_id == variant_id, PriceSnapshot.collected_at >= threshold)
        .order_by(PriceSnapshot.collected_at.asc())
    )
    return list(db.scalars(stmt).all())


def compute_price_stats(db: Session, variant_id: str, now: datetime | None = None) -> PriceStats:
    now = now or datetime.now(timezone.utc)
    threshold = now - timedelta(days=180)
    stmt = (
        select(PriceSnapshot)
        .where(PriceSnapshot.variant_id == variant_id, PriceSnapshot.collected_at >= threshold)
        .order_by(PriceSnapshot.collected_at.asc())
    )
    snapshots = list(db.scalars(stmt).all())
    values = [(s.collected_at, int(s.observed_price)) for s in snapshots]
    current = values[-1][1] if values else None

    w7 = _window(values, 7, now)
    w30 = _window(values, 30, now)
    w90 = _window(values, 90, now)
    w180 = _window(values, 180, now)

    return PriceStats(
        current_price=current,
        median_7d=_median(w7),
        median_30d=_median(w30),
        median_90d=_median(w90),
        low_30d=_min(w30),
        low_90d=_min(w90),
        low_180d=_min(w180),
        observations_30d=len(w30),
    )
