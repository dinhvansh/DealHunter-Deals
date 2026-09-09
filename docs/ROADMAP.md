# Implementation Roadmap

The roadmap is intentionally ordered to prove correctness before scale.

## Phase 0 — Foundation

Goal: repository, environments and coding boundaries are ready.

Tasks:

- create Python/FastAPI backend skeleton;
- add PostgreSQL + Redis via Docker Compose;
- migration framework;
- settings/env management;
- structured logging and request/trace IDs;
- provider interface;
- test harness;
- CI for lint/test/migrations;
- `.env.example` with no secrets;
- basic health endpoints.

Exit criteria:

- `docker compose up` starts API, PostgreSQL and Redis;
- migrations run from clean DB;
- unit test suite runs in CI;
- provider interface has a fake/test provider.

## Phase 1 — Shopee product/SKU collector

Goal: prove marketplace identity and exact variation pricing.

Scope:

- Shopee only;
- SSD category;
- 50–100 SKUs/variations;
- no account login;
- no AI required.

Tasks:

1. search collector;
2. product/listing fetch;
3. shop identity;
4. variation/model extraction;
5. exact price per variation;
6. product/variant upsert;
7. append-only price snapshot;
8. collector run logging;
9. manual refresh endpoint/CLI;
10. fixture-based parser tests.

Required CLI/API behavior:

```text
search "ssd samsung 2tb"
 -> listing
 -> shop
 -> item identity
 -> every relevant variation
 -> exact current price
 -> DB persistence
```

Go/no-go gate:

- >= 95% variation identity accuracy on manually checked validation set;
- >= 95% current price accuracy;
- retries do not duplicate shops/products/variants;
- parser/provider failures are observable.

If this gate fails, do not start voucher work.

## Phase 2 — Price history and statistics

Goal: make raw collection useful for historical evaluation.

Tasks:

- scheduled refresh queue;
- dynamic due-SKU selection;
- price snapshot retention;
- 7/30/90-day median;
- 30/90/180-day low;
- sample count/freshness;
- outlier diagnostics;
- `GET /history` API;
- basic price chart UI.

Go/no-go gate:

- history chart matches stored snapshots;
- statistics reproducible from DB;
- missing/stale data represented honestly;
- scheduler does not hammer all SKUs at the same instant.

## Phase 3 — Voucher and Promotion Engine

Goal: calculate estimated best public prices deterministically.

Tasks:

- promotion collector/provider abstraction;
- normalized promotion schema;
- tri-state eligibility;
- min spend/fixed/percentage/cap rules;
- provider stacking policy;
- valid-combination optimizer;
- estimated best price breakdown;
- promotion expiration invalidation;
- engine versioning;
- test corpus of real/manual promotion scenarios.

Validation set:

Manually collect at least 30–50 real scenarios containing:

- shop voucher;
- platform voucher;
- percentage cap;
- minimum spend;
- freeship/unknown shipping;
- category restriction;
- payment restriction;
- non-stackable combination.

Go/no-go gate:

- deterministic cases calculate exactly;
- unknown conditions remain unknown;
- engine never presents an unsupported estimated price as verified;
- >= 90% correctness on supported manual scenarios before broad use.

## Phase 4 — Deal Engine and Opportunity Discovery

Goal: surface genuinely attractive deals rather than nominal discounts.

Tasks:

- DealScore v1;
- ConfidenceScore v1;
- OpportunityScore;
- component-level explanations;
- opportunity filters;
- ranking endpoint;
- discovery scheduler;
- configurable thresholds;
- initial seller/product quality inputs.

Go/no-go gate:

Run a human-reviewed sample for at least several days.

Target:

- Deal Alert Precision >= 80% before expansion;
- false positives categorized by reason;
- no score can be explained only by displayed MSRP discount.

## Phase 5 — Web/PWA core UI

Goal: use DealHunter without database/admin tools.

Screens:

- Deal Radar;
- Search;
- Product Detail;
- Price History;
- Watchlist.

Requirements:

- mobile responsive;
- visible price freshness;
- separate observed/estimated/verified UI states;
- score explanations/warnings;
- loading/error/provider health states.

Go/no-go gate:

User can complete:

```text
search -> inspect variant -> view history -> add watch -> return to radar
```

without developer tooling.

## Phase 6 — Watchlist scheduler and Telegram alerts

Goal: continuously monitor explicitly interesting products.

Tasks:

- watchlist CRUD;
- normal/hot priority;
- target price;
- deal/confidence threshold;
- new-low/new-voucher triggers;
- alert fingerprints/cooldown;
- Telegram bot/notification adapter;
- stale/provider-error status.

Go/no-go gate:

- no repeated alert spam for unchanged state;
- alert explains trigger and freshness;
- watched products receive higher priority without starving discovery jobs.

## Phase 7 — Account Verification

Goal: verify promising watched products against a real authenticated account session.

Only start after public collection and promotion estimation are stable.

Tasks:

- verification profile/session reference;
- isolated verification worker;
- explicit/manual verify action;
- trigger-based verify for watchlist;
- eligible/ineligible/applied promotion evidence;
- verified price + timestamp;
- bounded retry/cooldown;
- session health status;
- secret/log redaction.

Hard non-goals:

- auto purchase;
- captcha bypass;
- bulk voucher claiming;
- mass multi-account automation.

Go/no-go gate:

- verification only runs for authorized watch/explicit action;
- failed verification never overwrites valid public price data;
- credentials/cookies absent from DB logs/API responses;
- verified price always includes timestamp.

## Phase 8 — Affiliate Engine

Goal: turn strong public deals into shareable affiliate opportunities.

Tasks:

- affiliate provider abstraction;
- provider account/config reference;
- affiliate link generation;
- DealHunter short redirect;
- approved destination validation;
- click/source/campaign tracking;
- affiliate availability on deals;
- ShareScore v1.

Rules:

- commission never modifies DealScore;
- redirect cannot be an open redirect;
- analytics failures must not excessively delay redirect.

Go/no-go gate:

- generated links resolve correctly;
- source/campaign attribution works;
- DealScore stays identical with affiliate system enabled/disabled.

## Phase 9 — Public deal pages and Creator UI

Goal: share strong deals externally and create content efficiently.

Tasks:

- public deal detail page;
- deal freshness/expiry handling;
- affiliate CTA;
- creator opportunity dashboard;
- AI factual caption generation;
- Telegram/Facebook/Zalo copy formats;
- basic affiliate analytics;
- conversion import if supported.

Go/no-go gate:

- public pages clearly label Estimated versus Verified/account-specific data;
- expired/stale deal state visible;
- generated copy contains no prices not present in structured DealHunter data.

## Phase 10 — AI Skill/Agent

Goal: natural-language interface over proven backend capabilities.

Do this after APIs/data are reliable.

Tools:

```text
search_products
get_product
get_variant
get_price_history
get_deals
compare_variants
add_to_watchlist
remove_from_watchlist
verify_price
get_verification
get_affiliate_opportunities
generate_affiliate_link
```

Use cases:

- "Find me a dashcam under 1.5m."
- "Which of these three is the best deal?"
- "Watch this one and alert me if the final price is under 1.3m."
- "Any unusually good tech deals today?"
- "Which current deal is worth sharing for affiliate?"

Go/no-go gate:

AI answers are grounded in tool output and do not invent pricing/promotions.

## Phase 11 — Scale and additional marketplaces

Only after precision and provider stability are proven.

Candidate expansion:

- more Shopee categories;
- Lazada provider;
- larger catalog;
- canonical cross-shop product matching;
- user preference model;
- advanced affiliate analytics;
- additional notification channels.

Scale strategy:

```text
100 SKUs
 -> 500
 -> 1,000
 -> 5,000
 -> 10,000+
```

Each increase requires provider health and alert precision review.

## Recommended first sprint

### Sprint objective

Complete Phase 0 and the narrowest Phase 1 vertical slice.

### Tasks

1. FastAPI skeleton;
2. Docker Compose: API/Postgres/Redis;
3. Alembic migrations;
4. core tables: platform/shop/product/variant/price_snapshot/collector_run;
5. `MarketplaceProvider` interface;
6. Shopee collector proof of concept;
7. parse one search result into listings;
8. fetch one listing and all variations;
9. persist exact variation prices;
10. integration test with saved fixture;
11. CLI or API search endpoint;
12. validation spreadsheet/manual checklist for 50–100 SSD SKUs.

### Sprint definition of done

A developer can run:

```text
search: "Samsung SSD 2TB"
```

and inspect normalized DB/API output showing correct shop, item, variant identities and exact variation prices.

## Backlog discipline

Before beginning a new phase:

1. check repository HEAD and open PRs;
2. check whether previous phase exit criteria are actually met;
3. document known provider limitations;
4. do not hide technical debt behind future "AI fixing";
5. preserve deterministic tests for every marketplace rule learned.
