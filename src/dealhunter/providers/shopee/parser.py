import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from dealhunter.providers.base import ListingDetail, SearchHit, VariantQuote
from dealhunter.providers.errors import ProviderParseError

PRICE_SCALE = 100_000


def _money(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value) / PRICE_SCALE))
    except (TypeError, ValueError):
        return None


def _hash_evidence(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_search(payload: dict[str, Any], base_url: str, limit: int) -> list[SearchHit]:
    hits: list[SearchHit] = []
    rows = payload.get("items") or (payload.get("data") or {}).get("items") or []
    for row in rows:
        item = row.get("item_basic") or row.get("item_card", {}).get("item") or row
        item_id = item.get("itemid") or item.get("item_id")
        shop_id = item.get("shopid") or item.get("shop_id")
        name = item.get("name") or item.get("title")
        if item_id is None or shop_id is None or not name:
            continue
        hits.append(
            SearchHit(
                platform="shopee",
                external_item_id=str(item_id),
                external_shop_id=str(shop_id),
                title=str(name),
                url=f"{base_url.rstrip('/')}/product/{shop_id}/{item_id}",
                displayed_price=_money(item.get("price")),
                metadata={
                    "rating": item.get("item_rating"),
                    "is_official_shop": item.get("is_official_shop"),
                },
            )
        )
        if len(hits) >= limit:
            break
    return hits


def parse_listing(
    payload: dict[str, Any],
    base_url: str,
    shop_id: str,
    item_id: str,
) -> ListingDetail:
    data = payload.get("data") or {}
    item = data.get("item") or data
    if not isinstance(item, dict) or not item:
        raise ProviderParseError("Shopee detail payload has no item data")
    title = item.get("name") or item.get("title")
    if not title:
        raise ProviderParseError("Shopee detail payload has no item title")

    models = item.get("models") or item.get("model_list") or []
    variants: list[VariantQuote] = []
    for model in models:
        model_id = model.get("modelid") or model.get("model_id") or model.get("id")
        if model_id is None:
            continue
        price = _money(model.get("price"))
        if price is None and isinstance(model.get("price_info"), dict):
            price = _money(model["price_info"].get("current_price"))
        if price is None:
            continue
        before = _money(model.get("price_before_discount"))
        stock = model.get("stock")
        variants.append(
            VariantQuote(
                external_variation_id=str(model_id),
                variation_name=str(model.get("name") or model.get("model_name") or model_id),
                observed_price=price,
                listed_price=before,
                sale_price=price if before and price < before else None,
                stock_state=(
                    "in_stock" if stock is None or int(stock) > 0 else "out_of_stock"
                ),
                sku_text=model.get("model_sku") or model.get("sku"),
                attributes={"stock": stock},
                source_hash=_hash_evidence(model),
            )
        )

    if not variants:
        price = _money(item.get("price") or item.get("price_min"))
        if price is None:
            raise ProviderParseError("Shopee item has neither models nor a parseable price")
        variants = [
            VariantQuote(
                external_variation_id=f"default:{item_id}",
                variation_name="Default",
                observed_price=price,
                listed_price=_money(item.get("price_before_discount")),
                stock_state="in_stock" if (item.get("stock") or 0) > 0 else "unknown",
                source_hash=_hash_evidence(item),
            )
        ]

    shop = item.get("shop_data") or data.get("shop_data") or {}
    return ListingDetail(
        platform="shopee",
        external_item_id=str(item.get("itemid") or item.get("item_id") or item_id),
        external_shop_id=str(item.get("shopid") or item.get("shop_id") or shop_id),
        shop_name=shop.get("name") or shop.get("shop_name"),
        title=str(title),
        url=f"{base_url.rstrip('/')}/product/{shop_id}/{item_id}",
        category_external_id=(
            str(item.get("catid")) if item.get("catid") is not None else None
        ),
        variants=variants,
        collected_at=datetime.now(timezone.utc),
        metadata={
            "historical_sold": item.get("historical_sold"),
            "rating": item.get("item_rating"),
        },
    )
