import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        UniqueConstraint("platform", "external_shop_id", name="uq_shop_platform_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(32))
    external_shop_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str | None] = mapped_column(String(500))
    seller_type: Mapped[str | None] = mapped_column(String(64))
    rating: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint(
            "platform",
            "external_item_id",
            "shop_id",
            name="uq_listing_platform_item_shop",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    platform: Mapped[str] = mapped_column(String(32))
    external_item_id: Mapped[str] = mapped_column(String(128))
    shop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shops.id"))
    title: Mapped[str] = mapped_column(String(1000))
    url: Mapped[str] = mapped_column(Text)
    category_external_id: Mapped[str | None] = mapped_column(String(128))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    shop: Mapped[Shop] = relationship()


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint(
            "listing_id",
            "external_variation_id",
            name="uq_variant_listing_external",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"))
    external_variation_id: Mapped[str] = mapped_column(String(128))
    sku_text: Mapped[str | None] = mapped_column(String(500))
    variation_name: Mapped[str] = mapped_column(String(1000))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    listing: Mapped[Listing] = relationship()


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        Index("ix_price_variant_collected", "variant_id", "collected_at"),
        Index("ix_price_collected", "collected_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id"))
    observed_price: Mapped[int] = mapped_column(BigInteger)
    listed_price: Mapped[int | None] = mapped_column(BigInteger)
    sale_price: Mapped[int | None] = mapped_column(BigInteger)
    flash_price: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(8), default="VND")
    stock_state: Mapped[str | None] = mapped_column(String(64))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    provider: Mapped[str] = mapped_column(String(64))
    source_hash: Mapped[str | None] = mapped_column(String(128))
    raw_ref: Mapped[str | None] = mapped_column(Text)
