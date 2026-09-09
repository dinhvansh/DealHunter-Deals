from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any] | None = None


TOOL_SPECS = [
    ToolSpec("search_products", "Search normalized marketplace products and variants."),
    ToolSpec("get_product", "Return a normalized product/variant with current pricing."),
    ToolSpec("compare_products", "Compare variants using deterministic DealHunter data."),
    ToolSpec("get_price_history", "Return immutable price history and derived statistics."),
    ToolSpec("get_deals", "Return ranked deals."),
    ToolSpec("get_opportunities", "Return unusually good products not explicitly requested."),
    ToolSpec("add_watchlist", "Add a variant to the user watchlist."),
    ToolSpec("update_watchlist", "Update watchlist thresholds and mode."),
    ToolSpec("remove_watchlist", "Remove a variant from the watchlist."),
    ToolSpec("verify_price", "Request account-specific verification for a watched variant."),
    ToolSpec("get_affiliate_opportunities", "Return high-quality affiliate-share candidates."),
    ToolSpec("generate_share_payload", "Create factual share copy from deterministic deal data."),
]


def tool_catalog() -> list[dict[str, str]]:
    return [{"name": tool.name, "description": tool.description} for tool in TOOL_SPECS]
