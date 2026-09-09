from __future__ import annotations

import uuid
from dataclasses import asdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from dealhunter.db.extended_models import (
    AffiliateClick,
    AffiliateLinkRecord,
    DealScoreRecord,
    PromotionEvaluation,
    VerificationRun,
    WatchlistRecord,
)
from dealhunter.services.affiliate import AffiliateLink
from dealhunter.services.promotions import PromotionResult
from dealhunter.services.scoring import ScoreResult
from dealhunter.services.watchlist import WatchRule
from dealhunter.verification.base import VerificationResult


def _uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def save_promotion_evaluation(
    db: Session,
    variant_id: str | uuid.UUID,
    result: PromotionResult,
) -> PromotionEvaluation:
    row = PromotionEvaluation(
        variant_id=_uuid(variant_id),
        observed_price=result.observed_price,
        estimated_price=result.estimated_price,
        applied_vouchers=[asdict(v) for v in result.applied],
        rejected_vouchers=[{"code": code, "reason": reason} for code, reason in result.rejected],
        confidence=result.confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_score(db: Session, variant_id: str | uuid.UUID, result: ScoreResult) -> DealScoreRecord:
    row = DealScoreRecord(
        variant_id=_uuid(variant_id),
        deal_score=result.deal_score,
        confidence_score=result.confidence_score,
        opportunity_score=result.opportunity_score,
        share_score=result.share_score,
        components=result.components,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def latest_deals(db: Session, limit: int = 20, min_opportunity: int = 0) -> list[DealScoreRecord]:
    stmt = (
        select(DealScoreRecord)
        .where(DealScoreRecord.opportunity_score >= min_opportunity)
        .order_by(DealScoreRecord.opportunity_score.desc(), DealScoreRecord.computed_at.desc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    seen: set[uuid.UUID] = set()
    unique: list[DealScoreRecord] = []
    for row in rows:
        if row.variant_id in seen:
            continue
        seen.add(row.variant_id)
        unique.append(row)
    return unique


def upsert_watch(db: Session, user_id: str, rule: WatchRule) -> WatchlistRecord:
    variant_id = _uuid(rule.variant_id)
    stmt = select(WatchlistRecord).where(
        WatchlistRecord.user_id == user_id,
        WatchlistRecord.variant_id == variant_id,
    )
    row = db.scalar(stmt)
    if row is None:
        row = WatchlistRecord(user_id=user_id, variant_id=variant_id)
        db.add(row)
    row.mode = rule.mode.value
    row.target_price = rule.target_price
    row.min_deal_score = rule.min_deal_score
    row.verify_account = rule.verify_account
    row.alert_on_price_drop = rule.alert_on_price_drop
    row.alert_on_new_voucher = rule.alert_on_new_voucher
    row.alert_on_historical_low = rule.alert_on_historical_low
    row.enabled = True
    db.commit()
    db.refresh(row)
    return row


def list_watch(db: Session, user_id: str) -> list[WatchlistRecord]:
    return list(
        db.scalars(
            select(WatchlistRecord)
            .where(WatchlistRecord.user_id == user_id, WatchlistRecord.enabled.is_(True))
            .order_by(WatchlistRecord.created_at.desc())
        ).all()
    )


def remove_watch(db: Session, user_id: str, watch_id: str | uuid.UUID) -> bool:
    result = db.execute(
        delete(WatchlistRecord).where(
            WatchlistRecord.id == _uuid(watch_id),
            WatchlistRecord.user_id == user_id,
        )
    )
    db.commit()
    return bool(result.rowcount)


def save_affiliate_link(
    db: Session,
    link: AffiliateLink,
    campaign: str | None = None,
    variant_id: str | uuid.UUID | None = None,
    listing_id: str | uuid.UUID | None = None,
) -> AffiliateLinkRecord:
    row = db.scalar(select(AffiliateLinkRecord).where(AffiliateLinkRecord.redirect_code == link.redirect_code))
    if row is None:
        row = AffiliateLinkRecord(
            variant_id=_uuid(variant_id) if variant_id else None,
            listing_id=_uuid(listing_id) if listing_id else None,
            destination_url=link.destination_url,
            affiliate_url=link.affiliate_url,
            redirect_code=link.redirect_code,
            campaign=campaign,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_affiliate_link(db: Session, code: str) -> AffiliateLinkRecord | None:
    return db.scalar(select(AffiliateLinkRecord).where(AffiliateLinkRecord.redirect_code == code))


def record_affiliate_click(
    db: Session,
    link: AffiliateLinkRecord,
    source: str | None = None,
    referrer: str | None = None,
) -> AffiliateClick:
    click = AffiliateClick(
        affiliate_link_id=link.id,
        source=source,
        campaign=link.campaign,
        referrer=referrer,
    )
    db.add(click)
    db.commit()
    db.refresh(click)
    return click


def save_verification(
    db: Session,
    variant_id: str | uuid.UUID,
    result: VerificationResult,
    user_id: str | None = None,
) -> VerificationRun:
    row = VerificationRun(
        user_id=user_id,
        variant_id=_uuid(variant_id),
        observed_price=result.observed_price,
        estimated_price=result.estimated_price,
        verified_price=result.verified_price,
        eligible_promotions=result.applied_promotions,
        ineligible_promotions=[],
        state=result.state,
        failure_reason=result.failure_reason,
        verified_at=result.verified_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
