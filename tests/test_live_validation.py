from __future__ import annotations

import csv
from datetime import datetime, timezone

import pytest

from dealhunter.providers.base import ListingDetail, MarketplaceProvider, SearchHit, VariantQuote
from dealhunter.services.live_validation import (
    CSV_FIELDS,
    ValidationRow,
    collect_live_sample,
    evaluate_validation_csv,
    write_validation_csv,
)


class FakeProvider(MarketplaceProvider):
    name = "fake"

    async def search_products(self, query: str, limit: int = 20) -> list[SearchHit]:
        return [
            SearchHit(
                platform="shopee",
                external_item_id="item-1",
                external_shop_id="shop-1",
                title="SSD 2TB",
                url="https://example.test/item-1",
                displayed_price=1_500_000,
            )
        ]

    async def get_listing(self, url_or_ids: str | tuple[str, str]) -> ListingDetail:
        return ListingDetail(
            platform="shopee",
            external_item_id="item-1",
            external_shop_id="shop-1",
            shop_name="Shop",
            title="SSD 2TB",
            url="https://example.test/item-1",
            category_external_id="ssd",
            variants=[
                VariantQuote("v1", "1TB", 1_500_000),
                VariantQuote("v2", "2TB", 2_500_000, listed_price=2_900_000),
            ],
            collected_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_collect_live_sample_expands_variants():
    sample = await collect_live_sample(FakeProvider(), "ssd 2tb", listing_limit=10)
    assert sample.listing_count == 1
    assert sample.variant_count == 2
    assert sample.rows[1].variant_id == "v2"
    assert sample.rows[1].observed_price == 2_500_000


def test_validation_csv_report_and_gate(tmp_path):
    path = tmp_path / "sample.csv"
    rows = []
    now = datetime(2026, 9, 9, tzinfo=timezone.utc)

    for index in range(50):
        rows.append(
            ValidationRow(
                platform="shopee",
                query="ssd",
                shop_id="shop",
                item_id=f"item-{index}",
                listing_title="SSD",
                listing_url="https://example.test",
                search_displayed_price=1_000_000,
                variant_id=f"v-{index}",
                variant_name="2TB",
                sku_text=None,
                observed_price=2_000_000,
                listed_price=None,
                sale_price=None,
                stock_state="in_stock",
                collected_at=now,
            )
        )
    write_validation_csv(rows, path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        data = list(csv.DictReader(handle))

    for index, row in enumerate(data):
        row["manual_price"] = "2000000" if index < 48 else "2100000"
        row["manual_variant_name"] = "2TB"

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)

    report = evaluate_validation_csv(path)
    assert report.validated_rows == 50
    assert report.passed == 48
    assert report.failed == 2
    assert report.accuracy == pytest.approx(0.96)
    assert report.gate_passed is True


def test_validation_report_accepts_explicit_status(tmp_path):
    path = tmp_path / "manual.csv"

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        base = {field: "" for field in CSV_FIELDS}
        base.update({"observed_price": "100", "variant_name": "A", "manual_status": "pass"})
        writer.writerow(base)
        base2 = dict(base)
        base2["manual_status"] = "skip"
        writer.writerow(base2)

    report = evaluate_validation_csv(path)
    assert report.passed == 1
    assert report.skipped == 1
    assert report.pending == 0
