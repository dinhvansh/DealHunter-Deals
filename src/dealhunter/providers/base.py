from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SearchHit:
    platform: str
    external_item_id: str
    external_shop_id: str
    title: str
    url: str
    displayed_price: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class VariantQuote:
    external_variation_id: str
    variation_name: str
    observed_price: int
    listed_price: int | None = None
    sale_price: int | None = None
    flash_price: int | None = None
    stock_state: str | None = None
    sku_text: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    source_hash: str | None = None


@dataclass(slots=True)
class ListingDetail:
    platform: str
    external_item_id: str
    external_shop_id: str
    shop_name: str | None
    title: str
    url: str
    category_external_id: str | None
    variants: list[VariantQuote]
    collected_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class MarketplaceProvider(ABC):
    name: str

    @abstractmethod
    async def search_products(self, query: str, limit: int = 20) -> list[SearchHit]: ...

    @abstractmethod
    async def get_listing(self, url_or_ids: str | tuple[str, str]) -> ListingDetail: ...

    async def aclose(self) -> None:
        return None
