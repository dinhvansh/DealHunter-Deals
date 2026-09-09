import json
from pathlib import Path

from dealhunter.providers.shopee.parser import parse_listing, parse_search
from dealhunter.providers.shopee.url_parser import parse_shopee_ids

FIX = Path(__file__).parent / "fixtures"


def test_url_parser_supports_common_formats():
    assert parse_shopee_ids("https://shopee.vn/product/1001/2002") == ("1001", "2002")
    assert parse_shopee_ids("https://shopee.vn/foo-i.1001.2002") == ("1001", "2002")


def test_search_price_is_vnd_and_not_raw_scaled_integer():
    payload = json.loads((FIX / "search.json").read_text())
    hit = parse_search(payload, "https://shopee.vn", 10)[0]
    assert hit.displayed_price == 2_390_000
    assert hit.external_item_id == "2002"


def test_variant_prices_are_mapped_per_model():
    payload = json.loads((FIX / "detail.json").read_text())
    detail = parse_listing(payload, "https://shopee.vn", "1001", "2002")
    prices = {variant.variation_name: variant.observed_price for variant in detail.variants}
    assert prices == {"1TB": 2_390_000, "2TB": 3_990_000}
    assert detail.variants[0].external_variation_id == "3001"
    assert detail.variants[1].external_variation_id == "3002"
