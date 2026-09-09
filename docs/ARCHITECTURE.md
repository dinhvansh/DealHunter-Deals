# Architecture

## 1. Architectural objective

DealHunter should be a modular deal intelligence platform where marketplace-specific data collection is replaceable, while pricing, scoring, watchlist, affiliate and API behavior remain marketplace-agnostic.

The architecture must support four operating modes:

1. targeted search;
2. scheduled public discovery;
3. watchlist monitoring;
4. account verification for selected products.

## 2. Logical architecture

```text
                         +----------------------+
                         |   Web / PWA / AI     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     FastAPI API      |
                         +----------+-----------+
                                    |
              +---------------------+----------------------+
              |                     |                      |
              v                     v                      v
       Search Service        Watchlist Service       Affiliate Service
              |                     |                      |
              +---------------------+----------------------+
                                    |
                                    v
                        +-----------------------+
                        |     Domain Core       |
                        |-----------------------|
                        | Product/SKU           |
                        | Promotion Engine      |
                        | Price History         |
                        | Deal Scoring          |
                        | Confidence            |
                        | Opportunity Ranking   |
                        +-----------+-----------+
                                    |
               +--------------------+--------------------+
               |                    |                    |
               v                    v                    v
       Marketplace Adapters   Verification Adapter   Notification Adapter
               |                    |                    |
               v                    v                    v
      Public/official data     Authenticated flow       Telegram first
               |
               v
           PostgreSQL <---- Workers / Queue ----> Redis
```

## 3. Service boundaries

### API service

Responsibilities:

- REST endpoints;
- authentication/authorization for private UI;
- input validation;
- query orchestration;
- read models;
- AI tool contracts;
- watchlist commands;
- affiliate/share commands.

Must not contain marketplace scraping logic.

### Collector workers

Responsibilities:

- provider search;
- listing fetch;
- variation/SKU extraction;
- seller/shop extraction;
- public price snapshots;
- voucher/campaign extraction;
- provider-specific normalization.

Collectors emit normalized domain events/data, not raw provider HTML as the primary application model.

### Promotion engine

Responsibilities:

- validate structured promotion rules;
- determine candidate eligibility;
- enforce known stacking/exclusion rules;
- calculate deterministic discount amounts;
- produce estimated best public price and breakdown;
- state uncertainty when an eligibility condition is unknown.

### Deal engine

Responsibilities:

- historical statistics;
- current-vs-baseline comparisons;
- score components;
- risk penalties;
- confidence;
- opportunity ranking;
- trigger evaluation.

### Watchlist service

Responsibilities:

- watch settings;
- monitoring priority;
- target conditions;
- trigger state;
- verification eligibility;
- alert deduplication/cooldown.

### Verification worker

Responsibilities:

- use an authenticated session reference for user-selected products;
- verify eligible promotions/cart/checkout-visible price when supported;
- record verification result with timestamp/evidence metadata;
- never store raw account password in application tables;
- rate-limit and isolate provider/account sessions.

### Affiliate service

Responsibilities:

- provider account configuration;
- create/resolve affiliate links using supported methods;
- short redirect links;
- click tracking;
- source/campaign attribution;
- conversion report import when available;
- ShareScore inputs.

Affiliate data is prohibited from entering Deal Score.

## 4. Provider adapter contract

Marketplace-specific code should live behind an interface similar to:

```python
class MarketplaceProvider(Protocol):
    async def search(self, query, filters): ...
    async def fetch_listing(self, external_item_id): ...
    async def fetch_variations(self, external_item_id): ...
    async def fetch_public_promotions(self, listing): ...
    async def refresh_price(self, sku): ...
```

Provider implementations may use, in priority order where appropriate:

1. official APIs;
2. affiliate/provider feeds;
3. public web data;
4. browser automation;
5. manual import for unsupported data.

The domain model must not assume that browser scraping is the only source.

## 5. Collection pipeline

### Search ingestion

```text
User/Discovery Query
        |
        v
Provider Search
        |
        v
Raw candidates
        |
        v
Provider identity extraction
        |
        v
Listing + Shop upsert
        |
        v
Variation/SKU extraction
        |
        v
Current price snapshot
        |
        v
Promotion discovery
        |
        v
Deal evaluation
```

### Periodic refresh

```text
Scheduler
   |
   v
Due SKUs selected by priority
   |
   v
Refresh public state
   |
   +--> unchanged -> record/check cadence only
   |
   +--> changed -> snapshot -> promotion recalculation -> deal evaluation
                                               |
                                               +--> watch trigger?
                                               |       |
                                               |       v
                                               |   verification candidate
                                               |
                                               +--> opportunity threshold?
                                                       |
                                                       v
                                                     alert
```

## 6. Scheduling strategy

Scheduling must be dynamic and provider-aware.

Recommended factors:

- watch mode (`normal`, `hot`);
- current deal score;
- recent price volatility;
- active campaign window;
- voucher start/end time;
- product popularity;
- rate limits/provider health;
- last successful refresh;
- verification cooldown.

Avoid scanning all products at identical intervals.

Example initial policy, configurable only:

- normal watch: 1–3 hours;
- hot watch: 30–60 minutes;
- broad discovery: 2–6 hours;
- campaign window: temporarily higher priority.

These values are operational defaults, not domain invariants.

## 7. Data persistence

PostgreSQL is the source of truth for normalized business data.

Redis is for:

- queue transport;
- short-lived locks;
- deduplication keys;
- rate-limit buckets;
- hot cache.

Do not treat Redis as durable price history.

Price snapshots should be append-only except for explicit data repair.

## 8. Event model

Useful domain events:

```text
listing.discovered
sku.discovered
price.changed
price.new_low
promotion.discovered
promotion.changed
estimated_price.changed
watch.triggered
verification.requested
verification.completed
deal.score_changed
deal.opportunity_detected
alert.sent
affiliate.link_created
affiliate.click_recorded
```

Foundation implementation may use direct service calls first, but event names should guide boundaries so moving to a message bus later is possible.

## 9. Idempotency

Collectors and workers must be safe to retry.

Required idempotency dimensions:

- provider + external listing ID;
- provider + external SKU/variation ID;
- price snapshot timestamp bucket/source version when necessary;
- promotion external ID or normalized fingerprint;
- verification request ID;
- alert trigger fingerprint;
- affiliate redirect token.

Never create duplicate products because a worker retried.

## 10. Observability

Every collector/worker run should record:

- provider;
- job type;
- start/end time;
- success/failure;
- number discovered/updated/skipped;
- rate-limit/blocked state;
- parser/version;
- error category;
- trace/request ID.

Operational dashboard later should expose:

- provider health;
- queue depth;
- stale watched SKUs;
- verification error rate;
- alert precision samples;
- price parser failure rate.

## 11. Security boundaries

### Credentials

- secrets in environment/secret manager only;
- never commit cookies, tokens, passwords or affiliate secrets;
- authenticated browser state should be encrypted/isolated where feasible;
- logs must redact tokens/cookies.

### Account verification

- separate worker/profile from public collectors;
- low concurrency per account;
- explicit verification eligibility;
- bounded retries;
- no automated purchase.

### Public redirect service

- validate destination against configured affiliate providers;
- prevent open redirect abuse;
- use opaque short IDs;
- rate-limit suspicious traffic.

## 12. Failure behavior

DealHunter must degrade honestly.

Examples:

- price collected but voucher collector failed -> keep Observed Price, mark Estimated Price stale/unavailable;
- unknown voucher condition -> do not silently assume eligible; lower confidence or exclude from best price;
- account verification fails -> retain last verified value with stale timestamp and failure state;
- provider temporarily blocked -> back off, do not spin aggressive retries;
- historical sample too small -> score with explicit low-history confidence.

## 13. Suggested repository structure

```text
DealHunter-Deals/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── domain/
│   │   ├── services/
│   │   ├── providers/
│   │   │   └── shopee/
│   │   ├── promotion/
│   │   ├── scoring/
│   │   ├── watchlist/
│   │   ├── verification/
│   │   ├── affiliate/
│   │   └── notifications/
│   ├── migrations/
│   └── tests/
├── workers/
├── web/
├── skill/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

Exact packaging may evolve, but domain/provider separation is mandatory.

## 14. Foundation delivery rule

Do not optimize for marketplace breadth before correctness.

The first architecture milestone passes only when one provider can reliably:

1. resolve listing identity;
2. enumerate variations;
3. map exact variation prices;
4. persist snapshots idempotently;
5. refresh without duplicating domain entities;
6. expose the normalized data through an API.
