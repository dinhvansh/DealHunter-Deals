from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dealhunter.db import Base
from dealhunter.db.extended_models import AffiliateClick, AffiliateLinkRecord, WatchlistRecord
from dealhunter.db.models import Listing, ProductVariant, Shop
from dealhunter.services.affiliate import QueryParamAffiliateProvider, create_affiliate_link
from dealhunter.services.platform_store import (
    list_watch,
    record_affiliate_click,
    save_affiliate_link,
    upsert_watch,
)
from dealhunter.services.watchlist import WatchMode, WatchRule


def _seed(db: Session):
    shop = Shop(platform="shopee", external_shop_id="shop", name="Shop")
    db.add(shop); db.flush()
    listing = Listing(platform="shopee", external_item_id="item", shop_id=shop.id, title="SSD", url="https://example.com")
    db.add(listing); db.flush()
    variant = ProductVariant(listing_id=listing.id, external_variation_id="v", variation_name="2TB")
    db.add(variant); db.commit()
    return listing, variant


def test_watch_and_affiliate_store_roundtrip():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        listing, variant = _seed(db)
        row = upsert_watch(db, "local", WatchRule(str(variant.id), WatchMode.HOT, target_price=2_000_000))
        assert row.mode == "HOT"
        assert len(list_watch(db, "local")) == 1
        link = create_affiliate_link(QueryParamAffiliateProvider("aff", "x"), listing.url, "test")
        saved = save_affiliate_link(db, link, campaign="test", variant_id=variant.id, listing_id=listing.id)
        record_affiliate_click(db, saved, source="pytest")
        assert db.scalar(select(AffiliateLinkRecord)).redirect_code == link.redirect_code
        assert db.scalar(select(AffiliateClick)).source == "pytest"
        assert db.scalar(select(WatchlistRecord)).target_price == 2_000_000
