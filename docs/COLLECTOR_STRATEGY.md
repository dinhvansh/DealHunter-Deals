# Collector Strategy

## Objective

Build a resilient marketplace data layer without making the entire system depend on one undocumented HTML selector or one provider.

## 1. Start with Shopee

Phase 1 scope:

- one marketplace: Shopee VN
- one category: SSD recommended
- 50–100 variants
- search by keyword and direct URL
- exact variation identity and observed price

Do not start with full marketplace coverage.

## 2. Provider abstraction

```python
class MarketplaceProvider:
    async def search_products(...): ...
    async def get_listing(...): ...
    async def get_variants(...): ...
    async def get_price(...): ...
    async def get_public_promotions(...): ...
```

Possible provider implementations can use, where permitted and practical:

- official/partner APIs
- affiliate product feeds
- public web data
- browser automation
- manual imports

Core domain code must not know how a provider acquired the data.

## 3. Browser automation

Use Playwright when browser execution is required. Browserless may be used as remote browser infrastructure.

Collector design rules:

- bounded concurrency
- per-host rate control
- retry with exponential backoff
- distinguish transient vs permanent failures
- capture adapter/parser version
- do not bypass CAPTCHA or anti-abuse controls
- do not depend on account login for broad public discovery

## 4. Search discovery vs monitoring

These are different workloads.

### Discovery

Search/category scans find candidate listings. Run less frequently.

Suggested initial cadence:

- category discovery: every 2–6 hours

### Monitoring

Known watchlist/important variants can be refreshed more often.

Suggested initial cadence:

- NORMAL watch: 1–3 hours
- HOT watch: 30–60 minutes

Cadence is configuration and should adapt to campaign periods.

## 5. Event-driven recalculation

Do not recompute everything blindly.

Events:

- new price snapshot
- new voucher
- voucher updated/expired
- campaign starts
- seller/listing state changes

These events trigger targeted promotion and scoring recalculation.

Example: a newly discovered 20% max 500k electronics voucher should match relevant catalog candidates rather than cause account verification of every item.

## 6. Variant correctness

Primary Phase 1 risk is incorrect price-to-variation mapping.

Example failure:

```text
1 TB: 1.29m
2 TB: 2.09m
4 TB: 4.99m
```

If collector associates the 1 TB minimum displayed price with the 4 TB variant, DealHunter will generate a fake 74% deal.

Every snapshot must therefore map to an explicit variation identifier.

## 7. Raw evidence

During POC, retain enough source evidence to debug parsing errors:

- source URL/item ID
- timestamp
- selected raw fields or payload hash
- optional short-retention raw payload

Avoid permanently storing unnecessary personal/account data.

## 8. Scale plan

Only scale after deal precision is proven.

Recommended sequence:

1. 50–100 variants
2. 300–500 variants
3. 1,000–5,000 variants
4. 10,000+ only after scheduler/DB/queue metrics are healthy

## 9. Health metrics

Minimum collector dashboard metrics:

- successful refresh percentage
- stale variants > threshold
- search discovery count
- average response/collection time
- parse errors by adapter version
- blocked/challenge rate
- duplicate variation rate
- price anomaly rate
