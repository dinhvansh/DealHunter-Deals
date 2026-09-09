# Implementation Roadmap

## Development rule

Before starting a new task:

1. fetch/check repository state
2. compare current branch and latest commits
3. report divergence/conflict before changing code
4. keep architecture/docs synchronized with major decisions

## Phase 0 — Foundation

Deliverables:

- architecture docs
- data model
- API contract
- local development skeleton
- PostgreSQL/Redis Docker setup
- FastAPI health endpoint
- migration framework

Exit criteria:

- application boots locally
- DB migration works
- CI runs formatting/tests

## Phase 1 — Shopee Product & Variant Collector

Goal:

```text
keyword or URL -> listing -> shop -> variants -> exact observed price -> DB
```

Scope:

- Shopee only
- SSD category
- 50–100 variants

Deliverables:

- Shopee provider adapter
- search discovery
- listing normalization
- variant normalization
- price snapshot persistence
- collector health logging

Exit criteria:

- >= 95% correct variant-price mapping in manual sample
- repeated jobs do not create duplicate variant identities

## Phase 2 — Price History

Deliverables:

- scheduled refresh
- price snapshot queries
- 7/30/90-day medians
- 30/90/180-day lows
- history API

Exit criteria:

- history retained correctly
- derived stats reproduce from raw snapshots

## Phase 3 — Voucher & Promotion Engine

Deliverables:

- public voucher collector
- normalized voucher rules
- eligibility matcher
- stacking/optimizer engine
- calculation trace
- Estimated Best Price

Exit criteria:

- 30–50 manually checked promotion cases
- >= 85% estimated-price correctness target for initial release
- no unsupported voucher silently treated as applicable

## Phase 4 — Deal Engine

Deliverables:

- Deal Score
- Confidence Score
- Opportunity Score
- score explanations
- deal feed APIs

Exit criteria:

- manually labeled evaluation dataset
- alert ranking precision target >= 80%

## Phase 5 — Web UI / PWA

Pages:

1. Deal Radar
2. AI/Search entry screen
3. Opportunity Deals
4. Product Detail + Price History
5. Watchlist
6. Settings
7. Collector/System Health for admin

UI requirements:

- clearly distinguish Observed / Estimated / Verified price
- freshness timestamps
- mobile-first responsive layout

## Phase 6 — Watchlist + Telegram

Deliverables:

- NORMAL/HOT watch modes
- target price
- deal-score threshold
- new voucher/historical-low triggers
- Telegram notifications
- alert deduplication/cooldown

## Phase 7 — Account Verification

Deliverables:

- encrypted verification session handling
- manual verify
- event-triggered watchlist verify
- Verified Account Price
- verification audit and freshness

Exit criteria:

- >= 90% match with manual account checks for supported flows
- challenge/session expiry fails safely

## Phase 8 — Affiliate Engine

Deliverables:

- AffiliateProvider abstraction
- Shopee provider integration
- affiliate URL generation
- `/go/{code}` tracking redirect
- click analytics
- conversion import

## Phase 9 — Public Deals + Creator Tools

Deliverables:

- public deal pages
- Share Score
- affiliate opportunities page
- AI-generated share copy
- Telegram/Facebook/Zalo share templates
- affiliate analytics dashboard

## Phase 10 — AI Skill / Agent

Tools exposed to AI:

```text
search_products
get_product
compare_products
get_price_history
get_deals
get_opportunities
add_watchlist
update_watchlist
remove_watchlist
verify_price
get_affiliate_opportunities
generate_share_payload
```

AI responsibilities:

- translate natural language to structured search
- compare products using DealHunter data
- explain rankings
- manage watchlist via APIs
- help prepare share content

## Phase 11 — Scale and additional marketplaces

Only after alert precision and operational stability are proven:

- expand categories
- 1k -> 5k -> 10k+ variants
- Lazada provider
- additional affiliate providers
- adaptive refresh scheduling
- canonical product matching across shops/platforms

## Release gates

Do not scale because crawler throughput looks good.

Scale only when:

- collector accuracy is stable
- promotion evaluation is trustworthy
- alert precision >= target
- infrastructure metrics are healthy
