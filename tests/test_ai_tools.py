from dealhunter.ai.tools import tool_catalog


def test_ai_tool_catalog_contains_required_tools():
    names = {tool["name"] for tool in tool_catalog()}
    assert {"search_products", "get_deals", "add_watchlist", "verify_price", "generate_share_payload"}.issubset(names)
