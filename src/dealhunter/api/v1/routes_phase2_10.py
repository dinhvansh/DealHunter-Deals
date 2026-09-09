from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dealhunter.ai.tools import tool_catalog
from dealhunter.db.session import get_db
from dealhunter.services.affiliate import QueryParamAffiliateProvider, create_affiliate_link
from dealhunter.services.price_history import compute_price_stats, get_price_history
from dealhunter.services.promotions import DiscountType, VoucherRule, optimize_promotions
from dealhunter.services.scoring import compute_scores
from dealhunter.services.share import build_share_payload

router = APIRouter(prefix="/api/v1", tags=["dealhunter"])


class PromotionRequest(BaseModel):
    observed_price: int = Field(gt=0)
    vouchers: list[dict]


class ScoreRequest(BaseModel):
    observed_price: int = Field(gt=0)
    estimated_price: int = Field(gt=0)
    variant_id: str
    confidence: float = Field(ge=0, le=1)
    seller_trust: float = Field(default=.8, ge=0, le=1)
    product_quality: float = Field(default=.8, ge=0, le=1)
    popularity: float = Field(default=.5, ge=0, le=1)
    affiliate_available: bool = False


class AffiliateRequest(BaseModel):
    destination_url: str
    campaign: str | None = None
    key: str = "aff_id"
    value: str = "demo"


class ShareRequest(BaseModel):
    product_name: str
    observed_price: int
    effective_price: int
    median_30d: int | None = None
    deal_score: int
    affiliate_url: str


@router.get("/variants/{variant_id}/history")
def variant_history(variant_id: str, days: int = 90, db: Session = Depends(get_db)):
    history = get_price_history(db, variant_id, days=days)
    stats = compute_price_stats(db, variant_id)
    return {
        "variant_id": variant_id,
        "history": [
            {
                "price_type": "observed",
                "amount": int(row.observed_price),
                "as_of": row.collected_at,
                "confidence": 1.0,
            }
            for row in history
        ],
        "stats": stats.__dict__ if hasattr(stats, "__dict__") else {
            "current_price": stats.current_price,
            "median_7d": stats.median_7d,
            "median_30d": stats.median_30d,
            "median_90d": stats.median_90d,
            "low_30d": stats.low_30d,
            "low_90d": stats.low_90d,
            "low_180d": stats.low_180d,
            "observations_30d": stats.observations_30d,
        },
    }


@router.post("/promotions/evaluate")
def evaluate_promotions(payload: PromotionRequest):
    vouchers = []
    for raw in payload.vouchers:
        try:
            vouchers.append(
                VoucherRule(
                    code=str(raw["code"]),
                    discount_type=DiscountType(str(raw["discount_type"])),
                    discount_value=int(raw["discount_value"]),
                    max_discount=int(raw["max_discount"]) if raw.get("max_discount") is not None else None,
                    min_spend=int(raw.get("min_spend", 0)),
                    stack_group=raw.get("stack_group"),
                    stackable=raw.get("stackable"),
                    confidence=float(raw.get("confidence", 1.0)),
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail=f"invalid voucher: {exc}") from exc
    result = optimize_promotions(payload.observed_price, vouchers)
    return {
        "price_type": "estimated",
        "amount": result.estimated_price,
        "as_of": None,
        "confidence": result.confidence,
        "observed_price": result.observed_price,
        "applied": [{"code": v.code, "discount": v.discount} for v in result.applied],
        "rejected": [{"code": c, "reason": r} for c, r in result.rejected],
    }


@router.post("/deals/score")
def score_deal(payload: ScoreRequest, db: Session = Depends(get_db)):
    stats = compute_price_stats(db, payload.variant_id)
    scores = compute_scores(
        payload.observed_price,
        payload.estimated_price,
        stats,
        payload.confidence,
        seller_trust=payload.seller_trust,
        product_quality=payload.product_quality,
        popularity=payload.popularity,
        affiliate_available=payload.affiliate_available,
    )
    return {
        "deal_score": scores.deal_score,
        "confidence_score": scores.confidence_score,
        "opportunity_score": scores.opportunity_score,
        "share_score": scores.share_score,
        "components": scores.components,
    }


@router.post("/affiliate/links")
def affiliate_link(payload: AffiliateRequest):
    provider = QueryParamAffiliateProvider(payload.key, payload.value)
    result = create_affiliate_link(provider, payload.destination_url, payload.campaign)
    return {
        "destination_url": result.destination_url,
        "affiliate_url": result.affiliate_url,
        "redirect_code": result.redirect_code,
        "redirect_url": f"/api/v1/go/{result.redirect_code}",
    }


@router.post("/share/generate")
def generate_share(payload: ShareRequest):
    result = build_share_payload(
        payload.product_name,
        payload.observed_price,
        payload.effective_price,
        payload.median_30d,
        payload.deal_score,
        payload.affiliate_url,
    )
    return {"title": result.title, "body": result.body, "cta": result.cta}


@router.get("/ai/tools")
def ai_tools():
    return {"tools": tool_catalog()}
