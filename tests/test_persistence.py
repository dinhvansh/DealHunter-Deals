import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from dealhunter.db.base import Base
from dealhunter.db.models import PriceSnapshot, ProductVariant
from dealhunter.providers.base import ListingDetail, VariantQuote
from dealhunter.services.persistence import MarketplaceRepository


def detail():
    return ListingDetail(
        platform="shopee",
        external_item_id="item1",
        external_shop_id="shop1",
        shop_name="Mall",
        title="SSD",
        url="https://shopee.vn/product/shop1/item1",
        category_external_id="ssd",
        collected_at=datetime.now(timezone.utc),
        variants=[
            VariantQuote(
                external_variation_id="v1",
                variation_name="2TB",
                observed_price=1_990_000,
            )
        ],
        metadata={},
    )


def test_repeated_collection_keeps_variant_identity_and_appends_history():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        repo = MarketplaceRepository(session)
        first = repo.persist_listing(detail(), "test")[0]
        second = repo.persist_listing(detail(), "test")[0]
        assert isinstance(first.id, uuid.UUID)
        assert first.id == second.id
        assert len(session.scalars(select(ProductVariant)).all()) == 1
        assert len(session.scalars(select(PriceSnapshot)).all()) == 2
