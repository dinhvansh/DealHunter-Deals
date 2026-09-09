from __future__ import annotations

import asyncio
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from dealhunter.providers.base import MarketplaceProvider, SearchHit


CSV_FIELDS = [
    "platform",
    "query",
    "shop_id",
    "item_id",
    "listing_title",
    "listing_url",
    "search_displayed_price",
    "variant_id",
    "variant_name",
    "sku_text",
    "observed_price",
    "listed_price",
    "sale_price",
    "stock_state",
    "collected_at",
    "manual_variant_name",
    "manual_price",
    "manual_status",
    "notes",
]


@dataclass(slots=True)
class ValidationRow:
    platform: str
    query: str
    shop_id: str
    item_id: str
    listing_title: str
    listing_url: str
    search_displayed_price: int | None
    variant_id: str
    variant_name: str
    sku_text: str | None
    observed_price: int
    listed_price: int | None
    sale_price: int | None
    stock_state: str | None
    collected_at: datetime

    def to_csv_dict(self) -> dict[str, str | int]:
        return {
            "platform": self.platform,
            "query": self.query,
            "shop_id": self.shop_id,
            "item_id": self.item_id,
            "listing_title": self.listing_title,
            "listing_url": self.listing_url,
            "search_displayed_price": self.search_displayed_price or "",
            "variant_id": self.variant_id,
            "variant_name": self.variant_name,
            "sku_text": self.sku_text or "",
            "observed_price": self.observed_price,
            "listed_price": self.listed_price or "",
            "sale_price": self.sale_price or "",
            "stock_state": self.stock_state or "",
            "collected_at": self.collected_at.isoformat(),
            "manual_variant_name": "",
            "manual_price": "",
            "manual_status": "",
            "notes": "",
        }


@dataclass(slots=True)
class CollectionFailure:
    item_id: str
    shop_id: str
    url: str
    error: str


@dataclass(slots=True)
class ValidationSample:
    query: str
    listing_count: int
    rows: list[ValidationRow] = field(default_factory=list)
    failures: list[CollectionFailure] = field(default_factory=list)

    @property
    def variant_count(self) -> int:
        return len(self.rows)


@dataclass(slots=True)
class ValidationReport:
    total_rows: int
    validated_rows: int
    passed: int
    failed: int
    skipped: int
    pending: int

    @property
    def accuracy(self) -> float | None:
        denominator = self.passed + self.failed
        if denominator == 0:
            return None
        return self.passed / denominator

    @property
    def gate_passed(self) -> bool:
        return self.validated_rows >= 50 and (self.accuracy or 0) >= 0.95


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "-")
    if not cleaned or cleaned == "-":
        return None
    return int(cleaned)


async def collect_live_sample(
    provider: MarketplaceProvider,
    query: str,
    listing_limit: int = 10,
    max_concurrency: int = 3,
) -> ValidationSample:
    hits = await provider.search_products(query, limit=listing_limit)
    sample = ValidationSample(query=query, listing_count=len(hits))
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def collect_one(hit: SearchHit) -> tuple[list[ValidationRow], CollectionFailure | None]:
        async with semaphore:
            try:
                detail = await provider.get_listing((hit.external_shop_id, hit.external_item_id))
            except Exception as exc:
                return [], CollectionFailure(
                    item_id=hit.external_item_id,
                    shop_id=hit.external_shop_id,
                    url=hit.url,
                    error=f"{type(exc).__name__}: {exc}",
                )

        rows = [
            ValidationRow(
                platform=detail.platform,
                query=query,
                shop_id=detail.external_shop_id,
                item_id=detail.external_item_id,
                listing_title=detail.title,
                listing_url=detail.url or hit.url,
                search_displayed_price=hit.displayed_price,
                variant_id=variant.external_variation_id,
                variant_name=variant.variation_name,
                sku_text=variant.sku_text,
                observed_price=variant.observed_price,
                listed_price=variant.listed_price,
                sale_price=variant.sale_price,
                stock_state=variant.stock_state,
                collected_at=detail.collected_at,
            )
            for variant in detail.variants
        ]
        return rows, None

    results = await asyncio.gather(*(collect_one(hit) for hit in hits))
    for rows, failure in results:
        sample.rows.extend(rows)
        if failure is not None:
            sample.failures.append(failure)
    return sample


def write_validation_csv(rows: Iterable[ValidationRow], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_dict())
    return path


def evaluate_validation_csv(
    source: str | Path,
    price_tolerance: int = 0,
) -> ValidationReport:
    path = Path(source)
    passed = failed = skipped = pending = 0
    total = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(CSV_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"validation CSV missing columns: {', '.join(sorted(missing))}")

        for row in reader:
            total += 1
            explicit = (row.get("manual_status") or "").strip().casefold()
            if explicit in {"skip", "skipped", "n/a", "na"}:
                skipped += 1
                continue
            if explicit in {"pass", "passed", "ok", "true", "1"}:
                passed += 1
                continue
            if explicit in {"fail", "failed", "false", "0"}:
                failed += 1
                continue

            expected_price = _parse_int(row.get("manual_price"))
            expected_name = (row.get("manual_variant_name") or "").strip()
            if expected_price is None and not expected_name:
                pending += 1
                continue

            price_ok = True
            name_ok = True
            if expected_price is not None:
                observed = _parse_int(row.get("observed_price"))
                price_ok = observed is not None and abs(observed - expected_price) <= price_tolerance
            if expected_name:
                name_ok = _normalize_text(row.get("variant_name") or "") == _normalize_text(expected_name)

            if price_ok and name_ok:
                passed += 1
            else:
                failed += 1

    validated = passed + failed
    return ValidationReport(
        total_rows=total,
        validated_rows=validated,
        passed=passed,
        failed=failed,
        skipped=skipped,
        pending=pending,
    )


def default_output_path(query: str) -> Path:
    slug = "-".join(query.casefold().split())[:60] or "sample"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("validation") / f"shopee-{slug}-{stamp}.csv"
