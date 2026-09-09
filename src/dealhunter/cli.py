from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dealhunter.core.config import get_settings
from dealhunter.providers.shopee import ShopeeProvider
from dealhunter.services.live_validation import (
    collect_live_sample,
    default_output_path,
    evaluate_validation_csv,
    write_validation_csv,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dealhunter", description="DealHunter operations CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sample = sub.add_parser("live-sample", help="Collect a live Shopee validation sample")
    sample.add_argument("query", nargs="?", default="ssd 2tb")
    sample.add_argument("--listings", type=int, default=10)
    sample.add_argument("--concurrency", type=int, default=3)
    sample.add_argument("--transport", choices=["http", "chrome", "playwright"], default=None)
    sample.add_argument("--output", type=Path, default=None)

    report = sub.add_parser("live-report", help="Calculate accuracy from a reviewed CSV")
    report.add_argument("csv", type=Path)
    report.add_argument("--price-tolerance", type=int, default=0)
    report.add_argument("--require-gate", action="store_true")

    return parser


async def _run_sample(args: argparse.Namespace) -> int:
    settings = get_settings()
    provider = ShopeeProvider(
        base_url=settings.shopee_base_url,
        transport_mode=args.transport or settings.shopee_transport,
        timeout=settings.shopee_timeout_seconds,
        chrome_profile_dir=settings.chrome_profile_dir,
        chrome_headless=settings.chrome_headless,
        chrome_executable_path=settings.chrome_executable_path,
    )
    try:
        sample = await collect_live_sample(
            provider,
            query=args.query,
            listing_limit=max(1, args.listings),
            max_concurrency=max(1, args.concurrency),
        )
    finally:
        await provider.aclose()

    output = args.output or default_output_path(args.query)
    write_validation_csv(sample.rows, output)

    print(f"Query: {sample.query}")
    print(f"Listings discovered: {sample.listing_count}")
    print(f"Variants exported: {sample.variant_count}")
    print(f"Listing failures: {len(sample.failures)}")
    print(f"CSV: {output}")
    if sample.failures:
        print("\nFailures:")
        for failure in sample.failures:
            print(f"- {failure.shop_id}/{failure.item_id}: {failure.error}")
    print("\nNext: open the CSV, fill manual_price/manual_variant_name or manual_status, then run:")
    print(f"  dealhunter live-report {output}")
    return 0 if sample.variant_count else 2


def _run_report(args: argparse.Namespace) -> int:
    report = evaluate_validation_csv(args.csv, price_tolerance=max(0, args.price_tolerance))
    accuracy = "n/a" if report.accuracy is None else f"{report.accuracy * 100:.2f}%"
    print(f"Rows: {report.total_rows}")
    print(f"Validated: {report.validated_rows}")
    print(f"Passed: {report.passed}")
    print(f"Failed: {report.failed}")
    print(f"Skipped: {report.skipped}")
    print(f"Pending: {report.pending}")
    print(f"Accuracy: {accuracy}")
    print(f"Phase 1 gate (>=50 validated and >=95% accuracy): {'PASS' if report.gate_passed else 'NOT YET'}")
    if args.require_gate and not report.gate_passed:
        return 2
    return 0


def main() -> int:
    args = _parser().parse_args()
    if args.command == "live-sample":
        return asyncio.run(_run_sample(args))
    if args.command == "live-report":
        return _run_report(args)
    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
