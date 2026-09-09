from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from dealhunter.ai.tools import tool_catalog
from dealhunter.api.routes import build_provider
from dealhunter.db.session import get_db
from dealhunter.services.affiliate import QueryParamAffiliateProvider, create_affiliate_link
from dealhunter.services.collector import CollectorService
from dealhunter.services.platform_store import (
    get_affiliate_link,
    latest_deals,
    list_watch,
    record_affiliate_click,
    remove_watch,
    save_affiliate_link,
    save_promotion_evaluation,
    save_score,
    upsert_watch,
)
from dealhunter.services.price_history import compute_price_stats, get_price_history
from dealhunter.services.promotions import DiscountType, VoucherRule, optimize_promotions
from dealhunter.services.scoring import compute_scores
from dealhunter.services.share import build_share_payload
from dealhunter.services.watchlist import WatchMode, WatchRule

router = APIRouter(prefix="/api/v1", tags=["dealhunter"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=20, ge=1, le=100)
    collect_details: bool = True


class PromotionRequest(BaseModel):
    observed_price: int = Field(gt=0)
    variant_id: str | None = None
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


class WatchRequest(BaseModel):
    user_id: str = "local"
    variant_id: str
    mode: WatchMode = WatchMode.NORMAL
    target_price: int | None = None
    min_deal_score: int | None = Field(default=None, ge=0, le=100)
    verify_account: bool = False
    alert_on_price_drop: bool = True
    alert_on_new_voucher: bool = True
    alert_on_historical_low: bool = True


class AffiliateRequest(BaseModel):
    destination_url: str
    campaign: str | None = None
    variant_id: str | None = None
    listing_id: str | None = None
    key: str = "aff_id"
    value: str = "demo"


class ShareRequest(BaseModel):
    product_name: str
    observed_price: int
    effective_price: int
    median_30d: int | None = None
    deal_score: int
    affiliate_url: str


@router.post("/search")
async def search_products(payload: SearchRequest, db: Session = Depends(get_db)):
    provider = build_provider()
    try:
        hits, persisted = await CollectorService(provider, db).discover_and_collect(
            payload.query,
            payload.limit,
            payload.collect_details,
        )
        return {
            "query": payload.query,
            "discovered": len(hits),
            "variants_persisted": persisted,
            "results": [
                {
                    "platform": "shopee",
                    "item_id": hit.external_item_id,
                    "shop_id": hit.external_shop_id,
                    "title": hit.title,
                    "url": hit.url,
                    "displayed_price": hit.displayed_price,
                }
                for hit in hits
            ],
        }
    finally:
        await provider.aclose()


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
        "stats": asdict(stats),
    }


@router.post("/promotions/evaluate")
def evaluate_promotions(payload: PromotionRequest, db: Session = Depends(get_db)):
    vouchers: list[VoucherRule] = []
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
    evaluation_id = None
    if payload.variant_id:
        evaluation_id = str(save_promotion_evaluation(db, payload.variant_id, result).id)
    return {
        "evaluation_id": evaluation_id,
        "price_type": "estimated",
        "amount": result.estimated_price,
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
    row = save_score(db, payload.variant_id, scores)
    return {"score_id": str(row.id), **asdict(scores)}


@router.get("/deals")
def deals(limit: int = 20, min_opportunity: int = 0, db: Session = Depends(get_db)):
    return [_score_out(row) for row in latest_deals(db, limit, min_opportunity)]


@router.get("/opportunities")
def opportunities(limit: int = 20, min_opportunity: int = 70, db: Session = Depends(get_db)):
    return [_score_out(row) for row in latest_deals(db, limit, min_opportunity)]


@router.post("/watchlist")
def add_watch(payload: WatchRequest, db: Session = Depends(get_db)):
    rule = WatchRule(
        variant_id=payload.variant_id,
        mode=payload.mode,
        target_price=payload.target_price,
        min_deal_score=payload.min_deal_score,
        verify_account=payload.verify_account,
        alert_on_price_drop=payload.alert_on_price_drop,
        alert_on_new_voucher=payload.alert_on_new_voucher,
        alert_on_historical_low=payload.alert_on_historical_low,
    )
    return _watch_out(upsert_watch(db, payload.user_id, rule))


@router.get("/watchlist")
def get_watchlist(user_id: str = "local", db: Session = Depends(get_db)):
    return [_watch_out(row) for row in list_watch(db, user_id)]


@router.delete("/watchlist/{watch_id}")
def delete_watch(watch_id: str, user_id: str = "local", db: Session = Depends(get_db)):
    if not remove_watch(db, user_id, watch_id):
        raise HTTPException(status_code=404, detail="watch not found")
    return {"deleted": True}


@router.post("/affiliate/links")
def affiliate_link(payload: AffiliateRequest, db: Session = Depends(get_db)):
    provider = QueryParamAffiliateProvider(payload.key, payload.value)
    result = create_affiliate_link(provider, payload.destination_url, payload.campaign)
    row = save_affiliate_link(
        db,
        result,
        campaign=payload.campaign,
        variant_id=payload.variant_id,
        listing_id=payload.listing_id,
    )
    return {
        "id": str(row.id),
        "destination_url": result.destination_url,
        "affiliate_url": result.affiliate_url,
        "redirect_code": result.redirect_code,
        "redirect_url": f"/api/v1/go/{result.redirect_code}",
    }


@router.get("/go/{redirect_code}")
def affiliate_redirect(
    redirect_code: str,
    request: Request,
    source: str | None = None,
    db: Session = Depends(get_db),
):
    link = get_affiliate_link(db, redirect_code)
    if link is None:
        raise HTTPException(status_code=404, detail="affiliate link not found")
    record_affiliate_click(db, link, source=source, referrer=request.headers.get("referer"))
    return RedirectResponse(link.affiliate_url, status_code=302)


@router.get("/affiliate/opportunities")
def affiliate_opportunities(limit: int = 20, db: Session = Depends(get_db)):
    return [row for row in (_score_out(item) for item in latest_deals(db, limit, 70)) if row["share_score"] >= 70]


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
    return asdict(result)


@router.post("/verification/{variant_id}")
def request_verification(variant_id: str):
    raise HTTPException(
        status_code=503,
        detail={
            "state": "not_configured",
            "variant_id": variant_id,
            "message": "Authorized account verification adapter is not configured.",
        },
    )


@router.get("/ai/tools")
def ai_tools():
    return {"tools": tool_catalog()}


def _watch_out(row):
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "variant_id": str(row.variant_id),
        "mode": row.mode,
        "target_price": row.target_price,
        "min_deal_score": row.min_deal_score,
        "verify_account": row.verify_account,
        "enabled": row.enabled,
    }


def _score_out(row):
    return {
        "id": str(row.id),
        "variant_id": str(row.variant_id),
        "deal_score": row.deal_score,
        "confidence_score": row.confidence_score,
        "opportunity_score": row.opportunity_score,
        "share_score": row.share_score or 0,
        "components": row.components,
        "computed_at": row.computed_at,
    }
