# Data Model

This document defines the first normalized PostgreSQL model. Names are provisional but relationships and invariants should be preserved.

## 1. Core marketplace entities

### `platforms`

```text
id
code                unique, e.g. shopee
name
enabled
created_at
updated_at
```

### `shops`

```text
id
platform_id         FK platforms
external_shop_id
name
url
is_mall
is_preferred
rating
followers_count
seller_score         nullable normalized score
raw_metadata         jsonb
last_seen_at
created_at
updated_at
```

Unique: `(platform_id, external_shop_id)`.

### `products`

Represents a marketplace listing/item, not yet a canonical cross-shop product.

```text
id
platform_id
shop_id
external_item_id
title
url
brand_text
category_text
image_url
currency
status              active/inactive/unknown
raw_metadata         jsonb
first_seen_at
last_seen_at
created_at
updated_at
```

Unique: `(platform_id, external_item_id, shop_id)` unless provider identity proves item ID globally unique.

### `product_variants`

Primary tracking unit for prices.

```text
id
product_id
external_variant_id
name
sku_code             nullable provider/shop SKU
attributes           jsonb
normalized_brand     nullable
normalized_model     nullable
normalized_capacity  nullable
status
first_seen_at
last_seen_at
created_at
updated_at
```

Unique: `(product_id, external_variant_id)`.

For products with no marketplace variation, create one synthetic default variant with a stable internal/external marker.

## 2. Price history

### `price_snapshots`

Append-only observed public pricing.

```text
id
variant_id
observed_at
source_type          official_api / affiliate / public_web / browser / manual
listed_price
sale_price
flash_price
observed_best_price  lowest directly observed public product price, nullable
currency
stock_status
stock_quantity       nullable
raw_evidence         jsonb
collector_version
created_at
```

Important: `observed_best_price` is still an observed marketplace value and MUST NOT contain calculated voucher stacking.

Recommended indexes:

```text
(variant_id, observed_at desc)
(observed_at)
```

Potential later partitioning: by month on `observed_at` once volume justifies it.

### `price_statistics`

Materialized/cache table for fast reads. Can be recomputed from snapshots.

```text
variant_id           PK/FK
sample_count
median_7d
median_30d
median_90d
low_30d
low_90d
low_180d
high_30d
last_observed_price
last_observed_at
volatility_30d
updated_at
```

This table is derived data, not the primary history source.

## 3. Promotions and vouchers

### `promotions`

Normalized promotion/voucher definition.

```text
id
platform_id
shop_id              nullable
external_promotion_id nullable
promotion_type       shop_voucher / platform_voucher / category / payment / freeship / campaign / flash
name
code                  nullable
discount_type         percentage / fixed / freeship / price_override
value                 numeric
max_discount          nullable
min_spend             nullable
currency
starts_at
ends_at
stack_group           nullable
priority              nullable
is_public
status
raw_rule_text         nullable
raw_metadata          jsonb
created_at
updated_at
```

### `promotion_rules`

Stores deterministic eligibility conditions.

```text
id
promotion_id
rule_type             category / shop / product / variant / payment / min_qty / user_segment / other
operator              eq / in / gte / lte / contains / etc.
field_name
value_json            jsonb
is_hard_rule
created_at
```

Unknown/unparsed requirements should remain explicit rather than silently converted to eligible.

### `promotion_variant_matches`

Cached matching result.

```text
promotion_id
variant_id
match_status          eligible / ineligible / unknown
reason
checked_at
```

Unique: `(promotion_id, variant_id)`.

### `promotion_evaluations`

Records one deterministic price calculation for audit/debugging.

```text
id
variant_id
evaluated_at
base_price
estimated_best_price
currency
promotion_ids         jsonb
breakdown             jsonb
eligibility_unknowns  jsonb
engine_version
created_at
```

## 4. Deal scoring

### `deal_evaluations`

```text
id
variant_id
evaluated_at
observed_price
estimated_price       nullable
historical_baseline   nullable
deal_score
confidence_score
opportunity_score
share_score           nullable
components            jsonb
warnings              jsonb
engine_version
created_at
```

`components` should preserve component-level values so ranking decisions are explainable.

Example:

```json
{
  "historical_position": 92,
  "real_discount": 88,
  "absolute_saving": 73,
  "seller_trust": 95,
  "product_quality": 84,
  "voucher_efficiency": 90,
  "risk_penalty": 5
}
```

## 5. Watchlist

### `watchlists`

```text
id
user_id
name
created_at
updated_at
```

Foundation can have a single local user but schema should remain multi-user capable.

### `watchlist_items`

```text
id
watchlist_id
variant_id
mode                  normal / hot
target_price          nullable
min_deal_score        nullable
min_confidence        nullable
verify_account        boolean
alert_new_low         boolean
alert_new_voucher     boolean
alert_price_drop_pct  nullable
is_active
last_checked_at
next_check_at
created_at
updated_at
```

Unique active watch per `(watchlist_id, variant_id)`.

### `watch_triggers`

```text
id
watchlist_item_id
trigger_type
triggered_at
fingerprint
payload               jsonb
verification_requested boolean
alert_status
created_at
```

Use `fingerprint` for deduplication/cooldown.

## 6. Account verification

### `verification_profiles`

Reference only. Never store raw account password.

```text
id
user_id
platform_id
name
session_ref           encrypted/external secret reference
status
last_validated_at
created_at
updated_at
```

### `verification_runs`

```text
id
verification_profile_id
variant_id
requested_at
started_at
completed_at
status                pending/running/success/failed/blocked
observed_base_price   nullable
verified_final_price  nullable
currency
applied_promotions    jsonb
eligible_promotions   jsonb
ineligible_promotions jsonb
shipping_amount       nullable
coins_amount          nullable
failure_code          nullable
failure_message       nullable
evidence              jsonb
worker_version
created_at
```

A verified price is only valid together with `completed_at` and status.

## 7. Alerts

### `alerts`

```text
id
user_id
variant_id
watch_trigger_id      nullable
deal_evaluation_id    nullable
channel               telegram / email / webpush / other
alert_type
fingerprint
payload               jsonb
status
sent_at
created_at
```

Unique or indexed by fingerprint to prevent spam.

## 8. Affiliate model

### `affiliate_programs`

```text
id
platform_id
name
provider_code
enabled
config_ref            secret/config reference, not credentials
created_at
updated_at
```

### `affiliate_links`

```text
id
affiliate_program_id
variant_id            nullable
product_id            nullable
source_url
destination_url
short_code            unique
campaign              nullable
metadata              jsonb
created_at
expires_at            nullable
```

### `affiliate_clicks`

```text
id
affiliate_link_id
clicked_at
source_channel        nullable
referrer              nullable
campaign              nullable
anonymous_session_id  nullable
ip_hash               nullable if needed and lawful
user_agent_summary    nullable
metadata              jsonb
```

Avoid collecting unnecessary personal data.

### `affiliate_conversions`

```text
id
affiliate_program_id
external_conversion_id
affiliate_link_id     nullable
order_reference_hash nullable
conversion_at
status
order_value           nullable
commission_value      nullable
currency
raw_metadata          jsonb
imported_at
```

Unique: `(affiliate_program_id, external_conversion_id)`.

## 9. Canonical products — later phase

Cross-shop/cross-platform matching should not block foundation development.

Later tables:

### `canonical_products`

```text
id
brand
model
normalized_name
category_id
attributes
```

### `canonical_product_variants`

```text
id
canonical_product_id
attributes
```

### `variant_canonical_matches`

```text
variant_id
canonical_variant_id
confidence
method
review_status
```

Do not auto-merge low-confidence matches.

## 10. Job and collector observability

### `collector_runs`

```text
id
platform_id
job_type
started_at
completed_at
status
query_or_scope        jsonb
items_seen
items_created
items_updated
items_failed
error_code
error_message
collector_version
trace_id
```

### `provider_health`

```text
platform_id
collector_type
status
last_success_at
last_failure_at
consecutive_failures
backoff_until
metadata
updated_at
```

## 11. Required invariants

1. A price snapshot belongs to a specific variant.
2. Observed price and calculated voucher price are stored separately.
3. Verified prices always have a timestamp and verification run.
4. Affiliate commission never modifies Deal Score.
5. Promotion rules can represent `unknown`; unknown is not automatically eligible.
6. Historical snapshots are append-only in normal operation.
7. Provider entities use stable external IDs plus platform identity.
8. All worker writes are idempotent or protected by unique keys.
9. Raw provider data may be retained for debugging, but normalized fields drive application behavior.
10. Secrets and raw account credentials never enter business tables.

## 12. Initial migration subset

Phase 1 does not need every table above. Start with:

```text
platforms
shops
products
product_variants
price_snapshots
collector_runs
```

Phase 2 adds:

```text
price_statistics
```

Phase 3 adds promotions/evaluations. Watchlist, verification and affiliate tables follow their roadmap phases.
