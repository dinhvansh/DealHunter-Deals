from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SharePayload:
    title: str
    body: str
    cta: str


def build_share_payload(
    product_name: str,
    observed_price: int,
    effective_price: int,
    median_30d: int | None,
    deal_score: int,
    affiliate_url: str,
) -> SharePayload:
    baseline = median_30d or observed_price
    pct = max(0.0, (baseline - effective_price) / max(1, baseline) * 100)
    title = f"🔥 {product_name} đang có deal tốt"
    body = (
        f"Giá hiện tại: {observed_price:,}đ\n"
        f"Giá ước tính sau ưu đãi: {effective_price:,}đ\n"
        f"Giảm thực so với mức tham chiếu: ~{pct:.1f}%\n"
        f"Deal Score: {deal_score}/100"
    )
    return SharePayload(title=title, body=body, cta=affiliate_url)
