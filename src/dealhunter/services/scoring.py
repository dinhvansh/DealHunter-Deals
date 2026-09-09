from __future__ import annotations

from dataclasses import dataclass

from dealhunter.services.price_history import PriceStats


@dataclass(slots=True)
class ScoreResult:
    deal_score: int
    confidence_score: int
    opportunity_score: int
    share_score: int
    components: dict[str, float]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def compute_scores(
    observed_price: int,
    estimated_price: int,
    stats: PriceStats,
    confidence: float,
    seller_trust: float = 0.8,
    product_quality: float = 0.8,
    popularity: float = 0.5,
    affiliate_available: bool = False,
) -> ScoreResult:
    baseline = stats.median_30d or stats.median_90d or observed_price
    baseline = max(1, baseline)
    effective = min(observed_price, estimated_price)

    discount_pct = max(0.0, (baseline - effective) / baseline * 100)
    historical_low_bonus = 100.0 if stats.low_180d and effective < stats.low_180d else 0.0
    absolute_saving = max(0, baseline - effective)
    absolute_saving_score = min(100.0, absolute_saving / 1_000_000 * 35.0)

    deal = _clamp(
        discount_pct * 1.8
        + historical_low_bonus * 0.2
        + absolute_saving_score * 0.15
        + seller_trust * 10
        + product_quality * 10
    )
    confidence_score = int(_clamp(confidence * 100))
    opportunity = int(_clamp(deal * confidence))
    share = _clamp(
        deal * 0.55
        + popularity * 100 * 0.2
        + seller_trust * 100 * 0.1
        + (100 if affiliate_available else 0) * 0.1
        + min(100.0, discount_pct * 2) * 0.05
    )

    return ScoreResult(
        deal_score=int(deal),
        confidence_score=confidence_score,
        opportunity_score=opportunity,
        share_score=int(share),
        components={
            "discount_pct": round(discount_pct, 2),
            "historical_low_bonus": historical_low_bonus,
            "absolute_saving_score": round(absolute_saving_score, 2),
            "seller_trust": seller_trust,
            "product_quality": product_quality,
            "popularity": popularity,
        },
    )
