import logging

from sqlalchemy.orm import Session

from dealhunter.providers.base import MarketplaceProvider, SearchHit
from dealhunter.services.persistence import MarketplaceRepository

logger = logging.getLogger(__name__)


class CollectorService:
    def __init__(self, provider: MarketplaceProvider, session: Session):
        self.provider = provider
        self.repo = MarketplaceRepository(session)

    async def discover_and_collect(
        self,
        query: str,
        limit: int = 20,
        detail_limit: int = 10,
    ) -> tuple[list[SearchHit], int]:
        hits = await self.provider.search_products(query, limit=limit)
        persisted = 0
        failures = 0
        for hit in hits[:detail_limit]:
            try:
                detail = await self.provider.get_listing(
                    (hit.external_shop_id, hit.external_item_id)
                )
                persisted += len(self.repo.persist_listing(detail, self.provider.name))
            except Exception:
                failures += 1
                logger.exception(
                    "collector_detail_failed provider=%s shop_id=%s item_id=%s",
                    self.provider.name,
                    hit.external_shop_id,
                    hit.external_item_id,
                )
        logger.info(
            "collector_search_complete provider=%s query=%r discovered=%d persisted_variants=%d failures=%d",
            self.provider.name,
            query,
            len(hits),
            persisted,
            failures,
        )
        return hits, persisted

    async def collect_listing(self, url: str) -> int:
        detail = await self.provider.get_listing(url)
        persisted = len(self.repo.persist_listing(detail, self.provider.name))
        logger.info(
            "collector_listing_complete provider=%s item_id=%s persisted_variants=%d",
            self.provider.name,
            detail.external_item_id,
            persisted,
        )
        return persisted
