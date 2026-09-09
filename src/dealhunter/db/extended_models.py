import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .models import utcnow


class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    external_voucher_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    voucher_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(500))
    discount_type: Mapped[str] = mapped_column(String(32))
    discount_value: Mapped[int] = mapped_column(BigInteger)
    max_discount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    min_spend: Mapped[int] = mapped_column(BigInteger, default=0)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stack_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stackable: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PromotionEvaluation(Base):
    __tablename__ = "promotion_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    observed_price: Mapped[int] = mapped_column(BigInteger)
    estimated_price: Mapped[int] = mapped_column(BigInteger)
    applied_vouchers: Mapped[list] = mapped_column(JSON, default=list)
    rejected_vouchers: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DealScoreRecord(Base):
    __tablename__ = "deal_scores"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    deal_score: Mapped[int] = mapped_column(Integer)
    confidence_score: Mapped[int] = mapped_column(Integer)
    opportunity_score: Mapped[int] = mapped_column(Integer, index=True)
    share_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WatchlistRecord(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_id", "variant_id", name="uq_watch_user_variant"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    mode: Mapped[str] = mapped_column(String(16), default="NORMAL")
    target_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    min_deal_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verify_account: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_on_price_drop: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_on_new_voucher: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_on_historical_low: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    observed_price: Mapped[int] = mapped_column(BigInteger)
    estimated_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    verified_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    eligible_promotions: Mapped[list] = mapped_column(JSON, default=list)
    ineligible_promotions: Mapped[list] = mapped_column(JSON, default=list)
    state: Mapped[str] = mapped_column(String(24))
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AffiliateLinkRecord(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("product_variants.id"), nullable=True)
    listing_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("listings.id"), nullable=True)
    destination_url: Mapped[str] = mapped_column(Text)
    affiliate_url: Mapped[str] = mapped_column(Text)
    redirect_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    affiliate_link_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("affiliate_links.id"), index=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    campaign: Mapped[str | None] = mapped_column(String(160), nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(160), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(40), default="telegram")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    state: Mapped[str] = mapped_column(String(24), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
