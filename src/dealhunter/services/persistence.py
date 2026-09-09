from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from dealhunter.db.models import Listing, PriceSnapshot, ProductVariant, Shop
from dealhunter.providers.base import ListingDetail


class MarketplaceRepository:
    def __init__(self, session: Session):
        self.session = session

    def persist_listing(
        self,
        detail: ListingDetail,
        provider_name: str,
    ) -> list[ProductVariant]:
        now = detail.collected_at or datetime.now(timezone.utc)
        shop = self.session.scalar(
            select(Shop).where(
                Shop.platform == detail.platform,
                Shop.external_shop_id == detail.external_shop_id,
            )
        )
        if shop is None:
            shop = Shop(
                platform=detail.platform,
                external_shop_id=detail.external_shop_id,
                name=detail.shop_name,
                metadata_json={},
                last_seen_at=now,
            )
            self.session.add(shop)
            self.session.flush()
        else:
            shop.name = detail.shop_name or shop.name
            shop.last_seen_at = now

        listing = self.session.scalar(
            select(Listing).where(
                Listing.platform == detail.platform,
                Listing.external_item_id == detail.external_item_id,
                Listing.shop_id == shop.id,
            )
        )
        if listing is None:
            listing = Listing(
                platform=detail.platform,
                external_item_id=detail.external_item_id,
                shop_id=shop.id,
                title=detail.title,
                url=detail.url,
                category_external_id=detail.category_external_id,
                metadata_json=detail.metadata,
                first_seen_at=now,
                last_seen_at=now,
            )
            self.session.add(listing)
            self.session.flush()
        else:
            listing.title = detail.title
            listing.url = detail.url
            listing.last_seen_at = now
            listing.metadata_json = detail.metadata

        persisted: list[ProductVariant] = []
        for quote in detail.variants:
            variant = self.session.scalar(
                select(ProductVariant).where(
                    ProductVariant.listing_id == listing.id,
                    ProductVariant.external_variation_id == quote.external_variation_id,
                )
            )
            if variant is None:
                variant = ProductVariant(
                    listing_id=listing.id,
                    external_variation_id=quote.external_variation_id,
                    sku_text=quote.sku_text,
                    variation_name=quote.variation_name,
                    attributes=quote.attributes,
                    active=True,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                self.session.add(variant)
                self.session.flush()
            else:
                variant.sku_text = quote.sku_text
                variant.variation_name = quote.variation_name
                variant.attributes = quote.attributes
                variant.active = True
                variant.last_seen_at = now

            self.session.add(
                PriceSnapshot(
                    variant_id=variant.id,
                    observed_price=quote.observed_price,
                    listed_price=quote.listed_price,
                    sale_price=quote.sale_price,
                    flash_price=quote.flash_price,
                    currency="VND",
                    stock_state=quote.stock_state,
                    collected_at=now,
                    provider=provider_name,
                    source_hash=quote.source_hash,
                )
            )
            persisted.append(variant)

        self.session.commit()
        return persisted
