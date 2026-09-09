# API and UI Contracts

## 1. API design goals

The API must serve three clients without duplicating business logic:

- private web/PWA;
- AI skill/agent tools;
- background workers/notifications.

All prices are represented as integers in the smallest supported currency unit for VND (`integer` VND), never binary floating point.

All timestamps are ISO 8601 with timezone.

## 2. Product/search APIs

### `POST /api/v1/search`

Search marketplace products from structured intent.

Request:

```json
{
  "query": "ssd 2tb pcie 4.0",
  "platforms": ["shopee"],
  "budget_max": 2000000,
  "brands": ["Samsung", "WD", "Crucial"],
  "filters": {
    "mall_only": false,
    "min_seller_score": 70
  }
}
```

Response should return normalized variants and evaluation summary, not raw provider payloads.

### `GET /api/v1/products/{product_id}`

Returns listing, shop, variants and current state.

### `GET /api/v1/variants/{variant_id}`

Returns exact variation data, current observed price, estimated price, latest deal evaluation and freshness.

### `GET /api/v1/variants/{variant_id}/history`

Query params:

```text
range=30d|90d|180d|all
```

Returns timestamp/price points plus statistics.

### `POST /api/v1/variants/{variant_id}/refresh`

Private/admin/manual refresh command. Must be rate limited.

## 3. Deal APIs

### `GET /api/v1/deals`

Filters:

```text
platform
category
brand
min_deal_score
min_confidence
price_min
price_max
mall_only
affiliate_available
sort=opportunity|deal|freshness|share
```

Default sort: `opportunity`.

### `GET /api/v1/deals/{evaluation_id}`

Returns full score components, historical comparison, promotion breakdown, warnings and freshness.

## 4. Promotion APIs

### `GET /api/v1/variants/{variant_id}/promotions`

Returns active known promotions with eligibility states.

### `POST /api/v1/variants/{variant_id}/estimate`

Re-evaluates current public best price from known promotion rules.

Response:

```json
{
  "observed_price": 2390000,
  "estimated_best_price": 1990000,
  "currency": "VND",
  "breakdown": [
    {"type": "shop_voucher", "amount": 100000, "eligibility": "eligible"},
    {"type": "platform_voucher", "amount": 300000, "eligibility": "eligible"}
  ],
  "unknowns": ["shipping_destination"],
  "evaluated_at": "2026-09-09T20:01:00+07:00"
}
```

## 5. Watchlist APIs

### `GET /api/v1/watchlists`

### `POST /api/v1/watchlists`

### `POST /api/v1/watchlists/{watchlist_id}/items`

Request:

```json
{
  "variant_id": "uuid",
  "mode": "hot",
  "target_price": 1500000,
  "min_deal_score": 85,
  "verify_account": true,
  "alerts": {
    "new_low": true,
    "new_voucher": true,
    "price_drop_pct": 10
  }
}
```

### `PATCH /api/v1/watchlist-items/{id}`

### `DELETE /api/v1/watchlist-items/{id}`

### `POST /api/v1/watchlist-items/{id}/verify`

Explicit user verification request.

## 6. Verification APIs

### `GET /api/v1/verifications/{id}`

Response must expose status and timestamps.

Example:

```json
{
  "status": "success",
  "verified_final_price": 1890000,
  "currency": "VND",
  "verified_at": "2026-09-09T20:05:31+07:00",
  "applied_promotions": ["..."],
  "warnings": []
}
```

Never expose cookies/session credentials.

## 7. Affiliate APIs

### `POST /api/v1/affiliate/links`

Creates an affiliate link for an eligible product/variant.

### `GET /go/{short_code}`

Public redirect endpoint.

Requirements:

- log click metadata;
- destination must belong to an approved affiliate provider/domain;
- no arbitrary open redirects;
- fast redirect even if analytics storage partially fails.

### `GET /api/v1/affiliate/opportunities`

Returns high ShareScore deals.

### `POST /api/v1/affiliate/import-conversions`

Later/admin endpoint for supported reports/imports.

## 8. AI tool surface

The AI skill should call small deterministic tools instead of receiving database access.

Initial tool set:

```text
search_products(query, constraints)
get_product(product_id)
get_variant(variant_id)
get_price_history(variant_id, range)
get_deals(filters)
compare_variants(variant_ids)
add_to_watchlist(variant_id, settings)
remove_from_watchlist(watchlist_item_id)
verify_price(watchlist_item_id)
get_verification(verification_id)
get_affiliate_opportunities(filters)
generate_affiliate_link(variant_id, campaign)
```

### AI search behavior

User:

> find me a good 2TB SSD under 2m

AI should:

1. parse intent;
2. call `search_products`;
3. if needed call comparison/history tools for top candidates;
4. explain ranking from returned factual components;
5. never invent a voucher or final price.

## 9. UI information architecture

### Private routes

```text
/
/search
/deals
/product/{id}
/watchlist
/affiliate
/settings
/admin/providers
/admin/jobs
```

### Public routes

```text
/deals/public
/d/{slug-or-id}
/go/{short_code}
```

## 10. Deal Radar UI

Primary screen.

Desktop conceptual layout:

```text
+------------------------------------------------------------------+
| DealHunter        Search...                 Watchlist   Profile   |
+------------------------------------------------------------------+
| Filters            | HOT DEALS                                      |
| Platform           |                                                |
| Category           | [Product image] Samsung 990 Pro 2TB             |
| Brand              | Mall | Seller 95 | Fresh 5m                     |
| Price              |                                                |
| Deal >= 85         | Observed        2,390,000                       |
| Confidence >= 80   | Est. best       1,990,000                       |
| Mall               | 30d median      2,850,000                       |
| Affiliate          | 180d low        2,190,000                       |
|                    |                                                |
|                    | Deal 96 | Confidence 94 | Opportunity 90        |
|                    |                                                |
|                    | [Details] [Watch] [Verify] [Share]              |
+------------------------------------------------------------------+
```

Mobile cards must keep the following above the fold:

- product/variant;
- estimated price;
- comparison versus baseline;
- Deal Score + Confidence;
- Watch/Open action.

## 11. Product Detail UI

Sections:

1. identity and seller;
2. three price tiers;
3. price history chart;
4. active promotion breakdown;
5. score explanation;
6. warnings/unknown conditions;
7. other matched listings later;
8. Watch / Verify / Share actions.

Price tier display example:

```text
Observed       2,390,000   checked 4m ago
Estimated      1,990,000   2 public vouchers, shipping unknown
Verified       1,890,000   verified for My Account at 20:05
```

Never visually present Estimated and Verified as the same certainty.

## 12. Watchlist UI

Columns/cards:

```text
Product
Current observed
Estimated
Target
Deal Score
Mode
Last check
Last verification
Status
```

Status examples:

```text
WAIT
NEAR TARGET
DEAL
VERIFYING
VERIFIED DEAL
STALE
PROVIDER ERROR
```

## 13. Opportunity UI

Filters are preference-oriented:

```text
Interested categories
Minimum product quality
Minimum seller trust
Minimum deal score
Minimum confidence
Max price
```

Default should return a small curated feed, not every discounted listing.

## 14. Affiliate/Creator UI

Sections:

### Opportunities

Strong deals with:

```text
Deal Score
Share Score
Affiliate availability
Freshness
Generate Link
Generate Post
```

### Link creator

Input product/deal -> choose provider/campaign/source -> output short DealHunter redirect.

### Analytics

Initial metrics:

```text
clicks
links
source channel
campaign
```

Later when conversion data exists:

```text
orders
conversion rate
commission
commission by deal/category/channel
```

## 15. Generated share content

AI can generate copy only from structured facts supplied by DealHunter.

Required inputs:

- exact product/variant;
- observed/estimated price;
- historical comparison;
- promotion assumptions;
- seller trust indicators;
- affiliate URL.

Generated content must not claim a verified account price for the general public unless the copy clearly labels it account-specific and still relevant.

## 16. UI state and freshness

All major prices should have visible freshness metadata.

Examples:

```text
Checked 8m ago
Voucher checked 3m ago
Verified 20:05 today
History: 126 samples
```

If data is stale, the UI should show stale status rather than hide it.

## 17. Initial frontend delivery

Foundation frontend can use any maintainable web stack chosen by implementation, but must satisfy:

- responsive/PWA capable;
- server API is source of truth;
- no marketplace scraping from the browser client;
- chart library isolated behind a component;
- no dependency on native mobile SDKs.

First UI milestone requires only:

```text
Deal Radar
Search result
Product Detail + price chart
Watchlist
```

Affiliate dashboard and public deal pages follow after the deal engine is proven.
