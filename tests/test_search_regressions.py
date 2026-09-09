import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dealhunter.main import provider_error_handler
from dealhunter.providers.base import MarketplaceProvider, SearchHit
from dealhunter.providers.errors import ProviderError
from dealhunter.services.collector import CollectorService


class FailingDetailProvider(MarketplaceProvider):
    name = "counting"

    def __init__(self):
        self.detail_calls = 0

    async def search_products(self, query: str, limit: int = 20) -> list[SearchHit]:
        return [
            SearchHit(
                platform="shopee",
                external_item_id=str(index),
                external_shop_id="shop",
                title=f"item {index}",
                url=f"https://example.test/{index}",
            )
            for index in range(limit)
        ]

    async def get_listing(self, url_or_ids):
        self.detail_calls += 1
        raise ProviderError("detail unavailable")


@pytest.mark.asyncio
async def test_boolean_collect_details_uses_normal_detail_batch():
    provider = FailingDetailProvider()
    service = CollectorService(provider, None)  # repository is not reached because details fail

    hits, persisted = await service.discover_and_collect(
        "camera hanh trinh",
        limit=12,
        detail_limit=True,
    )

    assert len(hits) == 12
    assert provider.detail_calls == 10
    assert persisted == 0


@pytest.mark.asyncio
async def test_false_collect_details_skips_detail_collection():
    provider = FailingDetailProvider()
    service = CollectorService(provider, None)

    _, persisted = await service.discover_and_collect(
        "camera hanh trinh",
        limit=12,
        detail_limit=False,
    )

    assert provider.detail_calls == 0
    assert persisted == 0


def test_provider_error_is_returned_as_actionable_502():
    app = FastAPI()
    app.add_exception_handler(ProviderError, provider_error_handler)

    @app.get("/boom")
    def boom():
        raise ProviderError("Google Chrome Stable could not be launched")

    response = TestClient(app, raise_server_exceptions=False).get("/boom")

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["code"] == "provider_error"
    assert "Chrome" in detail["message"]
    assert "docker compose logs" in detail["hint"]
