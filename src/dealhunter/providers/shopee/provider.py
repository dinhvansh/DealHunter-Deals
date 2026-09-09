from dealhunter.providers.base import ListingDetail, MarketplaceProvider, SearchHit
from dealhunter.providers.errors import ProviderError

from .parser import parse_listing, parse_search
from .transport import ChromeJsonTransport, HttpJsonTransport, JsonTransport
from .url_parser import parse_shopee_ids


class ShopeeProvider(MarketplaceProvider):
    name = "shopee_public_v4"

    def __init__(
        self,
        base_url: str = "https://shopee.vn",
        transport: JsonTransport | None = None,
        transport_mode: str = "http",
        timeout: float = 30.0,
        chrome_profile_dir: str = "./data/chrome-profile",
        chrome_headless: bool = True,
        chrome_executable_path: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        if transport is not None:
            self.transport = transport
        elif transport_mode in {"chrome", "playwright"}:
            self.transport = ChromeJsonTransport(
                self.base_url,
                timeout=timeout,
                profile_dir=chrome_profile_dir,
                headless=chrome_headless,
                executable_path=chrome_executable_path,
            )
        else:
            self.transport = HttpJsonTransport(timeout=timeout)

    async def search_products(self, query: str, limit: int = 20) -> list[SearchHit]:
        payload = await self.transport.get_json(
            f"{self.base_url}/api/v4/search/search_items",
            params={
                "keyword": query,
                "limit": min(max(limit, 1), 60),
                "newest": 0,
                "order": "desc",
                "page_type": "search",
            },
        )
        return parse_search(payload, self.base_url, limit)

    async def get_listing(self, url_or_ids: str | tuple[str, str]) -> ListingDetail:
        shop_id, item_id = (
            parse_shopee_ids(url_or_ids) if isinstance(url_or_ids, str) else url_or_ids
        )
        errors: list[str] = []
        endpoints = [
            (
                f"{self.base_url}/api/v4/pdp/get_pc",
                {"item_id": item_id, "shop_id": shop_id},
            ),
            (
                f"{self.base_url}/api/v4/item/get",
                {"itemid": item_id, "shopid": shop_id},
            ),
        ]
        for url, params in endpoints:
            try:
                payload = await self.transport.get_json(url, params=params)
                return parse_listing(payload, self.base_url, shop_id, item_id)
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
        raise ProviderError("All Shopee detail endpoints failed: " + " | ".join(errors))

    async def aclose(self) -> None:
        await self.transport.aclose()
