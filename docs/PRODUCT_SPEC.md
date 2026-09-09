# Product Specification

## 1. Product definition

DealHunter is an AI-assisted shopping intelligence platform focused on marketplace deals. It combines search, price history, vouchers/promotions, deal discovery, watchlists, optional account verification and affiliate sharing.

The product must support two discovery modes and one monitoring mode:

### A. Need-based search

User expresses a buying intent in natural language, for example:

> Find a 2TB PCIe 4.0 SSD under 2,000,000 VND, prefer Samsung/WD/Crucial and trustworthy sellers.

DealHunter converts intent into structured constraints, searches providers, normalizes listings/SKUs, evaluates pricing and promotions, compares historical baselines and returns a ranked shortlist.

### B. Opportunity discovery

User does not specify a product. DealHunter scans configured categories and surfaces unusually strong opportunities such as:

- new 30/90/180-day low;
- unusually large real discount versus median;
- newly released public voucher that creates a strong effective price;
- high-quality product with a meaningful absolute saving;
- trustworthy listing that becomes unusually cheap during a campaign.

### C. Watchlist monitoring

User explicitly adds a SKU/listing to a watchlist. The system monitors public price/promotion changes and may run account-specific verification only after a trigger condition is met.

## 2. Target users

### Private user

Uses DealHunter to:

- search what to buy;
- track products;
- receive high-confidence alerts;
- verify a watched product against their account;
- discover unexpected bargains.

### Deal curator / affiliate creator

Uses DealHunter to:

- find strong shareable deals;
- generate affiliate links;
- generate factual deal summaries/captions;
- track clicks and optionally imported conversion/commission reports;
- publish public deal pages.

Affiliate value must never influence the core Deal Score.

## 3. Main product surfaces

### Deal Radar

Default landing page for ranked opportunities.

Each card should show at minimum:

- product + variation;
- shop/seller trust signals;
- observed current price;
- estimated best public price;
- historical median and low;
- Deal Score;
- Confidence Score;
- key promotion assumptions;
- actions: open, watch, verify, share when eligible.

### AI Search

Natural-language search and comparison interface.

### Product Detail

Shows:

- SKU identity;
- price history chart;
- current listing/shop state;
- observed/estimated/verified prices;
- active promotions and eligibility assumptions;
- comparable listings when canonical matching exists;
- deal rationale and warnings.

### Watchlist

Shows monitored SKUs, watch mode, thresholds, last public check, last account verification, current status and alert settings.

### Opportunity

Surfaces deals not explicitly watched, filtered by category/brand/quality/seller trust/score.

### Affiliate / Creator

Shows shareable deals, affiliate link generation, redirect tracking, content generation and analytics.

## 4. Price semantics

DealHunter MUST distinguish three price classes.

### Observed Price

A price directly observed from a marketplace source for a specific SKU/variation at a timestamp.

Examples:

- listed price;
- sale price;
- flash price visible without account-specific checkout.

### Estimated Best Price

A deterministic calculation based on public promotions known to the system.

This price is not guaranteed to be available to every account.

It must include a breakdown and confidence metadata.

### Verified Account Price

A price verified through an authenticated session for a user-selected/watchlisted product.

It must store:

- `verified_at`;
- account/session reference, never raw credentials;
- applied/eligible promotion evidence;
- final observed checkout/cart amount where available;
- verification status and failure reason.

Verified prices become stale and must never be presented without their verification timestamp.

## 5. SKU identity requirement

A product URL is not a sufficient tracking unit.

Minimum marketplace identity:

```text
platform
shop_id
item_id
variation_id / model_id
```

If a marketplace lacks one of these fields, the provider must produce an equivalent stable external identity.

Price snapshots MUST belong to a specific SKU/variation whenever variations exist.

## 6. Deal quality

A large percentage discount alone is not a deal.

Deal evaluation should consider:

- historical price position;
- real discount versus median/baseline;
- absolute monetary saving;
- public promotion efficiency;
- seller trust;
- product quality/reputation;
- popularity/liquidity where reliable;
- stock/availability;
- risk penalties;
- confidence in the estimated price.

The system should prefer a strong 30% discount on a trustworthy, useful product over a nominal 80% discount on low-quality/no-name inventory.

## 7. Affiliate rules

Affiliate support is a monetization layer, not a ranking layer.

Rules:

1. Deal Score is calculated without commission data.
2. Affiliate availability and commission may influence `ShareScore`, never `DealScore`.
3. Public deal pages must clearly represent observed/estimated/verified pricing correctly.
4. Redirect links may collect click/source/campaign metadata.
5. Conversion/commission data should come from supported provider reports/APIs/imports.
6. The system must not fabricate expected commission.

## 8. Account verification boundaries

Account verification is intentionally narrow.

Allowed product behavior:

- user explicitly adds product to watchlist;
- user explicitly requests verification;
- watchlist engine triggers verification after a meaningful public price/promotion event;
- inspect eligibility/final price where permitted by the provider flow.

Out of scope:

- auto-purchase;
- automated mass claiming of vouchers;
- captcha bypass;
- bypassing anti-bot or marketplace restrictions;
- bulk multi-account abuse;
- actions intended to manipulate marketplace systems.

## 9. Alert policy

The product should optimize for trust, not alert volume.

Possible triggers:

- target price reached;
- new 30/90/180-day low;
- real discount above threshold;
- new voucher changes estimated best price materially;
- flash/campaign price begins;
- verification confirms a materially stronger price;
- Deal Score crosses configured threshold.

Alerts must explain why the deal triggered.

## 10. Watch modes

Initial modes:

### Normal

- lower monitoring frequency;
- intended for general interest;
- public checks only unless a configured trigger requests verification.

### Hot

- higher monitoring priority;
- intended for near-term purchase intent;
- account verification can trigger when public conditions become promising.

Actual scheduler intervals must be provider-aware and configurable rather than hard-coded into product rules.

## 11. AI responsibilities

AI MAY:

- interpret buying intent;
- expand queries and synonyms;
- normalize product names/specifications;
- assist canonical product matching;
- parse difficult promotion text into a proposed structured rule for validation;
- explain why a deal is strong/weak;
- generate share captions based on factual DealHunter data.

AI MUST NOT be the source of truth for:

- voucher arithmetic;
- stacking rules;
- historical statistics;
- price thresholds;
- final Deal Score math;
- eligibility already expressible as deterministic rules.

## 12. First marketplace scope

Initial engineering target: **Shopee only**.

Initial catalog target: **SSD products** with 50–100 variations/SKUs.

Why SSD first:

- variations are easy to detect and validate;
- brands/capacity/specifications are structured enough for normalization;
- price history is meaningful;
- vouchers can materially change final price;
- manual truth checking is practical.

## 13. Non-goals for the foundation release

Do not build these before the core data model is proven:

- native mobile apps;
- full social network/community features;
- automatic checkout;
- scraping every category/platform;
- sophisticated ML price forecasting;
- cross-marketplace canonical matching at internet scale;
- complex creator monetization dashboards before link generation works.

## 14. Product success metric

Primary metric: **Deal Alert Precision**.

A deal alert is considered correct when:

- SKU is correct;
- displayed historical comparison is correct;
- promotion assumptions are visible and reasonable;
- estimated/verified semantics are not confused;
- opening the marketplace confirms a materially attractive opportunity.

Initial quality gates:

- `<70%`: no scale;
- `>=80%`: useful;
- `>=90%`: strong;
- `>=95%`: excellent.
