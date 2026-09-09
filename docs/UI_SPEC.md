# UI / PWA Specification

## Goal

The UI should help a user decide **what to buy now**, not overwhelm them with monitoring data.

Primary surfaces:

1. Deal Radar
2. AI Search
3. Opportunity Deals
4. Product Detail
5. Watchlist
6. Affiliate / Creator
7. Admin / System Health

Responsive web/PWA first. Native mobile app is not required initially.

## 1. Global price language

Every price must display its semantic type:

- `Observed` — current listing/SKU price seen by collector
- `Estimated` — best public price calculated from known promotions
- `Verified` — account-specific price verified at a timestamp

Never show an Estimated price as confirmed checkout price.

Every deal card should display freshness (`as_of`, `verified_at`) where relevant.

## 2. Deal Radar

Default home screen.

Card fields:

```text
Product / Variant
Seller badge / rating signal
Observed price
Estimated price
Verified price (when available)
Median 30d
Historical low
Deal Score
Confidence Score
Main reason: e.g. "23% below 30d median"
Actions: View / Watch / Verify / Share
```

Default sorting: Opportunity Score descending.

Filters:

- platform
- category
- brand
- price range
- minimum Deal Score
- minimum Confidence
- trusted seller
- historical low
- voucher available
- affiliate available

## 3. AI Search

Single natural-language entry box with optional structured refinements.

Example:

> Tìm camera hành trình 2 cam khoảng 1.5 triệu, ưu tiên 70mai hoặc DDPAI.

UI should show parsed intent as editable chips:

```text
Category: Dash cam
Budget: <= 1.5m
Camera count: 2
Brands: 70mai, DDPAI
```

Results are ranked by DealHunter data, not affiliate commission.

## 4. Opportunity Deals

Purpose:

> Show excellent deals the user was not actively looking for.

Sections:

- Hot today
- New historical lows
- Best voucher opportunities
- Trusted-brand deals

Allow category preference configuration so discovery does not become spam.

## 5. Product Detail

Sections:

### Header

- canonical product / listing / exact variant
- seller
- marketplace link
- current score and confidence

### Price summary

```text
Observed
Estimated
Verified (optional)
30d median
90d low
180d low
```

### Price history chart

- selectable 7d / 30d / 90d / 180d
- annotate meaningful promotion/verification events where useful

### Promotion breakdown

Show applied and rejected vouchers with reasons.

Example:

```text
Shop voucher       -100k    eligible
Platform voucher   -300k    eligible
Freeship             -30k    uncertain
Bank voucher        -150k    payment required
```

### Other sellers

Future/canonical product feature: compare equivalent variants from other sellers.

### Actions

- Add Watchlist
- Verify My Price
- Open Marketplace
- Share Deal

## 6. Watchlist

Table/card fields:

- product/variant
- observed/estimated/verified price
- target price
- watch mode NORMAL/HOT
- last checked
- verification enabled
- current status

Controls:

```text
Alert when:
[ ] target price reached
[ ] new historical low
[ ] price drops > X%
[ ] new voucher appears
[ ] Deal Score > X
```

Avoid repeat notifications by showing cooldown state.

## 7. Affiliate / Creator

### Affiliate Opportunities

Show only deals that already meet quality/confidence thresholds.

Fields:

- Deal Score
- Confidence
- Share Score
- affiliate availability
- optional commission information

Actions:

- Generate affiliate link
- Generate post
- Copy
- Share channel shortcut

### Earnings dashboard

When conversion data is available:

- clicks
- conversions/orders
- conversion rate
- commission
- top deals
- top categories
- source/channel performance

## 8. Public Deal Page

Potential route:

`/deals/{slug}`

Must clearly show:

- product/variant
- seller
- current price type
- historical comparison
- price freshness
- promotion instructions
- deal rationale
- buy CTA
- affiliate disclosure when applicable

Never expose private verification/session data.

## 9. Admin / System Health

Internal screen:

- collector success rate
- stale variants
- parser failures
- voucher parse failures
- verification failures
- queue depth
- recent alerts
- alert precision feedback

## 10. UX priorities

Priority order:

1. Can I trust this price?
2. Is this actually a good deal?
3. Why is it good?
4. Can I buy it now?
5. Should I watch it instead?
6. Is it worth sharing?

Charts and analytics are secondary to decision clarity.
