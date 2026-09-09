from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from dealhunter.db.base import Base
from dealhunter.db.models import Listing, PriceSnapshot, ProductVariant, Shop
from dealhunter.services.price_history import compute_price_stats


def test_price_stats_windows():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        shop = Shop(platform="shopee", external_shop_id="s", name="S")
        db.add(shop); db.flush()
        listing = Listing(platform="shopee", external_item_id="i", shop_id=shop.id, title="SSD", url="x")
        db.add(listing); db.flush()
        variant = ProductVariant(listing_id=listing.id, external_variation_id="v", variation_name="2TB")
        db.add(variant); db.flush()
        for days, price in [(100, 3_000_000), (20, 2_500_000), (5, 2_000_000), (0, 1_900_000)]:
            db.add(PriceSnapshot(variant_id=variant.id, observed_price=price, collected_at=now - timedelta(days=days), provider="test"))
        db.commit()
        stats = compute_price_stats(db, str(variant.id), now=now)
        assert stats.current_price == 1_900_000
        assert stats.low_30d == 1_900_000
        assert stats.median_7d == 1_950_000
        assert stats.low_180d == 1_900_000
