# DealHunter Deals

AI-assisted deal discovery, price history, voucher optimization, watchlists, verified account pricing, and affiliate sharing.

## Product goal

DealHunter is not just a price tracker. The product answers three practical questions:

1. **I need to buy something — what should I buy now?**
2. **I do not need anything specific — is there an unusually good deal worth grabbing?**
3. **I am watching this SKU — is the current checkout price actually good for my account?**

The system combines marketplace data, SKU-level price history, public vouchers/promotions, deterministic promotion rules, deal scoring, confidence scoring, optional account verification for watched products, and affiliate sharing for strong public deals.

## Core principles

- Track **SKU/variation**, not only product URLs.
- Keep **Observed Price**, **Estimated Best Price**, and **Verified Account Price** separate.
- Deal ranking must be independent from affiliate commission.
- AI may interpret intent and explain results, but voucher arithmetic and scoring rules remain deterministic.
- Account automation is only for verification of watched/explicitly selected products. No auto-purchase, captcha bypass, abuse, or bulk account actions.
- Data collectors are provider adapters so marketplace-specific implementations can be replaced without rewriting the domain core.
- Scale only after deal-alert precision is proven on a small catalog.

## Initial stack

- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Queue/cache:** Redis
- **Workers:** Celery/RQ or lightweight worker service
- **Browser collection:** Playwright; Browserless can be supported as an execution backend
- **Notifications:** Telegram first
- **UI:** responsive web/PWA
- **AI layer:** tool/skill calling DealHunter APIs

## Main modules

```text
Marketplace Providers
        |
        v
Product Discovery -> SKU Normalization -> Price Collector -> Price History
        |                                      |
        |                                      v
        +-> Voucher/Campaign Collector -> Promotion Engine
                                               |
                                               v
                                         Deal Scoring
                                          /        \
                                         v          v
                                  Opportunity    Watchlist
                                    Discovery       |
                                                    v
                                          Account Verification
                                                    |
                                                    v
                                                Alerts
                                                    |
                                +-------------------+-------------------+
                                v                                       v
                            Web / AI                              Affiliate / Share
```

## Repository documentation

- [`docs/PRODUCT_SPEC.md`](docs/PRODUCT_SPEC.md) — scope, user flows, feature definitions and non-goals.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — target architecture, components, boundaries and execution flows.
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — initial PostgreSQL domain model and invariants.
- [`docs/DEAL_ENGINE.md`](docs/DEAL_ENGINE.md) — promotion engine, price tiers, deal/confidence/opportunity scoring.
- [`docs/API_AND_UI.md`](docs/API_AND_UI.md) — backend contracts, AI tools and UI screens.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — implementation phases, tasks and go/no-go gates.
- [`docs/ACCEPTANCE.md`](docs/ACCEPTANCE.md) — correctness tests and project success metrics.
- [`AGENTS.md`](AGENTS.md) — instructions for coding agents working in this repository.

## First implementation target

The first engineering milestone is deliberately small:

> Given a Shopee search term or product URL, collect the product, shop, item identity, every relevant variation/SKU and the correct current price for each variation, then persist normalized records and price snapshots in PostgreSQL.

Suggested validation catalog: **50–100 SSD SKUs**.

Do not start with AI, account automation, affiliate analytics, or tens of thousands of products. Prove the marketplace identity and pricing model first.

## North-star quality metric

The project is successful when **Deal Alert Precision** is high enough that users trust alerts.

- `< 70%`: not ready to scale
- `>= 80%`: useful
- `>= 90%`: strong
- `>= 95%`: excellent

A correct alert means the SKU is correctly identified, the price/promotion assumptions are transparent, and opening the marketplace confirms that the opportunity was materially better than its historical baseline.

## Status

Foundation specification in progress on `docs/foundation-spec`.
