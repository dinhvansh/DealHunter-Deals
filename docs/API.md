# API Contract

Base path: `/api/v1`.

The API serves the web UI, AI skill/tool layer, Telegram integration and future clients.

## Search

### `POST /search`

Request:

```json
{
  "query": "ssd nvme 2tb pcie 4.0",
  "platforms": ["shopee"],
  "budget_max": 2000000,
  "brands": ["Samsung", "WD", "Crucial"],
  "filters": {
    "trusted_seller": true
  }
}
```

Response contains normalized variant candidates and latest scoring.

## Products

### `GET /variants/{variant_id}`

Returns listing, shop, attributes, current observed price, latest estimated price and latest score.

### `GET /variants/{variant_id}/history?days=90`

Returns time-series snapshots and derived statistics.

### `GET /variants/{variant_id}/promotions`

Returns known public promotions plus eligibility state and calculation trace.

## Deals

### `GET /deals`

Filters:

- platform
- category
- min_deal_score
- min_confidence
- max_price
- trusted_seller
- affiliate_available
- limit

Default ordering: `opportunity_score DESC`.

### `GET /opportunities`

Returns discovery candidates from configured categories. This endpoint is for "I did not ask for it, but this is unusually good" use cases.

## Watchlist

### `POST /watchlist`

```json
{
  "variant_id": "uuid",
  "mode": "HOT",
  "target_price": 1500000,
  "min_deal_score": 85,
  "verify_account": true,
  "alerts": {
    "price_drop": true,
    "new_voucher": true,
    "historical_low": true
  }
}
```

### `GET /watchlist`

### `PATCH /watchlist/{id}`

### `DELETE /watchlist/{id}`

## Verification

### `POST /verification/{variant_id}`

Manual verification request. Must use an existing authorized verification session.

Response:

```json
{
  "state": "success",
  "observed_price": 1590000,
  "estimated_price": 1290000,
  "verified_price": 1260000,
  "verified_at": "2026-09-09T14:00:00+07:00",
  "applied_promotions": [],
  "confidence": 0.98
}
```

Never return secrets/cookies/session material.

## Affiliate

### `POST /affiliate/links`

```json
{
  "variant_id": "uuid",
  "campaign": "telegram_hot_deal"
}
```

Returns DealHunter redirect URL and destination metadata.

### `GET /affiliate/opportunities`

Returns high-quality deals with Share Score and affiliate availability.

### `GET /go/{redirect_code}`

Public redirect endpoint. Records click then redirects to affiliate destination.

### `GET /affiliate/analytics`

Returns clicks, orders, conversion and commission metrics.

## Share content

### `POST /share/generate`

Input: deal/variant + target channel + tone constraints.

Output should be generated through AI layer and must use actual pricing fields from deterministic DealHunter data.

## Internal collector endpoints

Prefer queue-based internal jobs instead of public endpoints.

Conceptual jobs:

- discover_search_results
- refresh_listing
- refresh_variant_price
- refresh_public_promotions
- compute_price_statistics
- evaluate_promotions
- compute_deal_score
- evaluate_watch_events
- verify_watch_candidate

## API guarantees

Every price-bearing response should identify price type:

```json
{
  "price_type": "observed | estimated | verified",
  "amount": 1990000,
  "as_of": "timestamp",
  "confidence": 0.94
}
```

Do not expose an estimated price as checkout-confirmed.
