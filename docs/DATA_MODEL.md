# Data Model

This model is intentionally marketplace-agnostic while preserving provider identifiers.

## Core entities

### `products`

Canonical product concept when known.

Fields:

- id UUID PK
- canonical_name
- brand
- model
- category_id
- attributes JSONB
- created_at
- updated_at

Canonicalization can be incomplete during early phases.

### `shops`

- id UUID PK
- platform
- external_shop_id
- name
- seller_type
- rating
- seller_trust_score
- metadata JSONB
- last_seen_at

Unique: `(platform, external_shop_id)`.

### `listings`

Marketplace item/listing.

- id UUID PK
- platform
- external_item_id
- shop_id FK
- canonical_product_id nullable FK
- title
- url
- category_external_id
- metadata JSONB
- first_seen_at
- last_seen_at

Unique: `(platform, external_item_id, shop_id)`.

### `product_variants`

The primary tracking unit.

- id UUID PK
- listing_id FK
- external_variation_id
- sku_text nullable
- variation_name
- attributes JSONB
- active boolean
- first_seen_at
- last_seen_at

Unique: `(listing_id, external_variation_id)`.

## Pricing

### `price_snapshots`

Immutable time series.

- id bigserial PK
- variant_id FK
- observed_price
- listed_price nullable
- sale_price nullable
- flash_price nullable
- currency default VND
- stock_state nullable
- collected_at timestamptz
- provider
- source_hash nullable
- raw_ref nullable

Indexes:

- `(variant_id, collected_at desc)`
- `(collected_at)`

Do not overwrite history.

### `price_statistics`

Optional materialized/derived cache.

- variant_id PK/FK
- current_price
- median_7d
- median_30d
- median_90d
- low_30d
- low_90d
- low_180d
- high_30d
- observations_30d
- computed_at

Source of truth remains `price_snapshots`.

## Promotions

### `vouchers`

- id UUID PK
- platform
- external_voucher_id nullable
- voucher_type: shop/platform/category/freeship/payment/campaign
- title
- discount_type: percent/fixed/freeship
- discount_value
- max_discount nullable
- min_spend nullable
- start_at
- end_at
- stack_group nullable
- stackable nullable
- confidence
- metadata JSONB
- first_seen_at
- last_seen_at

### `voucher_scopes`

Normalized eligibility scope.

- id UUID PK
- voucher_id FK
- scope_type: platform/shop/category/listing/variant/payment/user_segment
- scope_value
- include boolean

### `voucher_matches`

Cached product/variant eligibility candidate.

- voucher_id FK
- variant_id FK
- match_state: eligible/ineligible/unknown
- reason
- evaluated_at

Unique: `(voucher_id, variant_id)`.

### `promotion_evaluations`

Calculation trace for Estimated Best Price.

- id UUID PK
- variant_id FK
- observed_price
- estimated_price
- applied_vouchers JSONB
- rejected_vouchers JSONB
- confidence
- evaluated_at

## Deal scoring

### `deal_scores`

- id UUID PK
- variant_id FK
- deal_score 0..100
- confidence_score 0..100
- opportunity_score 0..100
- share_score nullable 0..100
- components JSONB
- price_snapshot_id nullable
- promotion_evaluation_id nullable
- computed_at

## Watchlist

### `watchlists`

- id UUID PK
- user_id
- variant_id FK
- mode NORMAL/HOT
- target_price nullable
- min_deal_score nullable
- verify_account boolean
- alert_on_price_drop boolean
- alert_on_new_voucher boolean
- alert_on_historical_low boolean
- enabled boolean
- created_at

Unique: `(user_id, variant_id)`.

### `watch_events`

- id UUID PK
- watchlist_id FK
- event_type
- payload JSONB
- occurred_at
- verification_requested boolean

## Account verification

### `verification_sessions`

Metadata only; secrets/session material should be stored through an encrypted secret mechanism.

- id UUID PK
- user_id
- platform
- state active/expired/error
- secret_ref
- last_verified_at
- expires_at nullable

### `verification_runs`

- id UUID PK
- watchlist_id nullable
- variant_id FK
- session_id FK
- observed_price
- estimated_price nullable
- verified_price nullable
- eligible_promotions JSONB
- ineligible_promotions JSONB
- state success/partial/failed
- failure_reason nullable
- verified_at

A Verified Account Price is always tied to a `verified_at` timestamp.

## Alerts

### `alerts`

- id UUID PK
- user_id
- variant_id FK
- alert_type
- title
- body
- channel
- payload JSONB
- created_at
- sent_at nullable
- state

## Affiliate

### `affiliate_programs`

- id UUID PK
- platform
- provider_name
- account_ref
- enabled
- metadata JSONB

### `affiliate_links`

- id UUID PK
- program_id FK
- variant_id nullable FK
- listing_id nullable FK
- destination_url
- affiliate_url
- redirect_code unique
- campaign nullable
- created_at

### `affiliate_clicks`

- id bigserial PK
- affiliate_link_id FK
- source nullable
- campaign nullable
- user_agent_hash nullable
- referrer nullable
- clicked_at

### `affiliate_conversions`

- id UUID PK
- program_id FK
- external_conversion_id
- affiliate_link_id nullable FK
- order_value nullable
- commission_value nullable
- state
- occurred_at
- imported_at

## Categories

### `categories`

- id UUID PK
- parent_id nullable FK
- name
- slug
- attributes_schema JSONB nullable

## Suggested retention

- price snapshots: long-term; key competitive asset
- raw collector payloads: short/medium retention unless needed for debugging
- verification logs: minimal required retention; redact sensitive data
- affiliate click data: retain according to privacy policy and analytics needs
