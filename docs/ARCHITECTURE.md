# DealHunter Architecture

## 1. Product scope

DealHunter has three main user flows.

### A. Need Search

User describes what they want in natural language, for example:

> Find a 2 TB NVMe PCIe 4.0 SSD under 2,000,000 VND, prioritize Samsung/WD/Crucial and trusted sellers.

The system parses intent, discovers marketplace listings, normalizes variants, evaluates current promotions and history, ranks candidates and explains the best options.

### B. Deal Discovery

The system periodically scans selected categories and detects unusually good opportunities even when the user has not added a product to a watchlist.

### C. Watchlist + Verification

A user explicitly tracks a SKU. Public price and promotion signals are monitored. When a strong candidate event occurs, the system may use the user's authenticated marketplace session to verify actual eligible discounts. Verification is not used for broad catalog scanning.

## 2. Logical architecture

```text
+-------------------------+
| AI Skill / Web UI / Bot |
+------------+------------+
             |
             v
+-------------------------+
|      DealHunter API     |
+-------------------------+
| Search                  |
| Product Detail          |
| Price History           |
| Deals                   |
| Watchlist               |
| Verification            |
| Affiliate/Share         |
+------------+------------+
             |
             v
+--------------------------------------------------+
| Domain Services                                   |
|                                                   |
| Product Discovery / Normalization                 |
| Price Collector                                   |
| Voucher Collector                                 |
| Promotion Optimizer                               |
| Historical Statistics                             |
| Deal/Confidence/Opportunity Scoring               |
| Watchlist Engine                                  |
| Account Verification                              |
| Affiliate Engine                                  |
| Notification Engine                               |
+-------------------+-------------------------------+
                    |
         +----------+----------+
         |                     |
         v                     v
    PostgreSQL               Redis
         ^                     ^
         |                     |
         +----------+----------+
                    |
          Workers / Scheduler
                    |
                    v
        Marketplace Adapters
       Shopee -> Lazada -> ...
```

## 3. Service boundaries

### Product Discovery

Responsibilities:

- Search products by keyword/category.
- Resolve marketplace item IDs, shops and variations.
- Normalize technical attributes and titles.
- Keep marketplace-specific identifiers intact.

Primary SKU key:

```text
platform + shop_id + item_id + variation_id
```

Never use URL alone as product identity.

### Price Collector

Stores immutable snapshots:

- listed price
- sale price
- flash price when observable
- availability/stock signal
- source and collection timestamp

Historical statistics are derived from snapshots, not overwritten in-place.

### Voucher Collector

Collects public promotion signals such as:

- shop voucher
- platform voucher
- category voucher
- freeship
- payment promotion
- campaign/flash-sale metadata

Each voucher is normalized to deterministic rule fields.

### Promotion Optimizer

Calculates the best known public combination while respecting:

- minimum spend
- percentage/fixed discounts
- discount caps
- validity window
- category/shop/product scope
- payment restrictions
- stacking rules

The engine returns a calculation trace. It must never silently invent eligibility.

### Price levels

DealHunter stores three semantically different prices:

1. **Observed Price** — directly observed listing/SKU price.
2. **Estimated Best Price** — deterministic calculation using known public promotions.
3. **Verified Account Price** — price verified with the user's authenticated session at a specific timestamp.

UI and APIs must not label estimated prices as verified checkout prices.

### Deal Scoring

Produces independent scores:

- Deal Score: how strong the purchase opportunity appears.
- Confidence Score: how reliable the supporting pricing/promotion evidence is.
- Opportunity Score: ranking score used for alerts/discovery.
- Share Score: whether a good deal is worth publishing/sharing.

Affiliate commission must never influence Deal Score.

### Watchlist Engine

Tracks user-selected variants and trigger rules.

Suggested modes:

- NORMAL: public checks every 1–3 hours.
- HOT: public checks every 30–60 minutes.

Verification runs only after relevant events such as price drops, new vouchers, campaign activation, target-price hit or manual request.

### Account Verification

Uses a previously authenticated user session to verify user-specific eligibility for a tracked product. It must not auto-purchase, mass-claim vouchers, bypass anti-bot controls or perform broad bulk verification.

### Affiliate Engine

Responsibilities:

- convert marketplace URLs to affiliate URLs through supported mechanisms
- generate DealHunter redirect links
- record clicks/source/campaign metadata
- import or receive conversion/commission data when available
- generate shareable deal payloads

Affiliate data can affect Share Score, not Deal Score.

## 4. Provider pattern

Marketplace-specific logic should sit behind adapters.

```text
MarketplaceProvider
  search_products()
  get_item()
  get_variants()
  get_price()
  get_public_promotions()

AffiliateProvider
  generate_link()
  get_product_commission()
  import_conversions()
```

Initial providers:

- ShopeeMarketplaceProvider
- ShopeeAffiliateProvider

Future:

- LazadaMarketplaceProvider
- LazadaAffiliateProvider

## 5. AI responsibilities

Good AI uses:

- parse natural-language shopping intent
- expand queries and synonyms
- normalize brand/model/spec attributes
- semantic matching of equivalent listings
- parse difficult promotion text into candidate rules
- explain why a deal is good or risky
- generate share content

Do not use AI for:

- percentage math
- voucher caps
- stacking calculations
- historical price statistics
- scoring arithmetic
- eligibility checks that can be expressed as rules

## 6. Reliability and observability

Every collector and pricing result should include:

- provider
- source identifier
- collected_at
- parser/adapter version
- success/failure state
- error classification

Required metrics:

- collector success rate
- average collection latency
- stale SKU count
- voucher parse failure rate
- verification success rate
- deal-alert precision

## 7. Security

- Never store marketplace passwords in plaintext.
- Prefer encrypted session/cookie storage if account verification is implemented.
- Keep verification secrets separate from general workers.
- Redact sensitive session data from logs.
- Use least-privilege credentials for DB/Redis/services.
- Public deal pages must never expose user-specific voucher/session information.
