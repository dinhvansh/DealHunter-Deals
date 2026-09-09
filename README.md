# DealHunter Deals

AI-powered deal discovery, price history, voucher optimization, watchlist verification, and affiliate sharing platform for Vietnamese marketplaces.

## Product goal

DealHunter is not just a price tracker. It should answer two practical questions:

1. **I need to buy something — what is the best deal right now?**
2. **I do not need anything specific — is there any unusually good deal worth buying or sharing?**

The system combines marketplace discovery, SKU-level price tracking, voucher/promotion rules, historical pricing, deal scoring, watchlists, optional account verification, and affiliate sharing.

## Core principles

- Track **SKU/variation**, not only product URLs.
- Separate **Observed Price**, **Estimated Best Price**, and **Verified Account Price**.
- Deal ranking must remain independent from affiliate commission.
- Use deterministic code for pricing, voucher eligibility, stacking, scoring and history calculations.
- Use AI for natural-language search, product normalization, semantic matching, promo-text parsing and explanations.
- Account verification is only for watchlisted or explicitly verified candidates, never bulk marketplace crawling.
- Start with Shopee and one category, prove accuracy, then scale.

## Target architecture

```text
AI Skill / Web UI / Telegram
            |
            v
      DealHunter API
            |
   +--------+---------+----------------+
   |                  |                |
Product Engine   Voucher Engine   Affiliate Engine
   |                  |                |
Price History   Promotion Rules   Link/Analytics
   +--------+---------+----------------+
            |
       Deal Scoring
            |
   Watchlist / Verify
            |
          Alerts

PostgreSQL + Redis + Workers + Playwright/Browserless
```

## Documentation

- [Product & Architecture](docs/ARCHITECTURE.md)
- [Data Model](docs/DATA_MODEL.md)
- [API Contract](docs/API.md)
- [Deal Scoring](docs/DEAL_SCORING.md)
- [Collector Strategy](docs/COLLECTOR_STRATEGY.md)
- [Live Shopee Validation](docs/LIVE_VALIDATION.md)
- [UI / PWA Specification](docs/UI_SPEC.md)
- [AI Skill / Agent Contract](docs/AI_SKILL.md)
- [Account Verification](docs/ACCOUNT_VERIFICATION.md)
- [Affiliate](docs/AFFILIATE.md)
- [Implementation Roadmap](docs/ROADMAP.md)
- [Acceptance Criteria](docs/ACCEPTANCE_CRITERIA.md)

## Initial stack

- Backend: Python + FastAPI
- Database: PostgreSQL
- Queue/cache: Redis
- Browser automation: Playwright; Browserless optional
- Scheduler/workers: Celery/RQ/custom worker; final choice after collector POC
- Notifications: Telegram first
- UI: responsive web/PWA
- AI layer: tool/skill calling DealHunter API

## First implementation target

**Shopee keyword or URL → item → shop → variants → exact price per variant → PostgreSQL.**

The first milestone is successful only when SKU/variation prices are consistently correct across at least 50–100 tracked variants.

## Run the Phase 1 live validation gate

```bash
pip install -e '.[dev]'
dealhunter live-sample "ssd 2tb" --listings 10
```

Review the generated CSV against the Shopee UI, fill `manual_price` / `manual_variant_name` (or `manual_status`), then calculate accuracy:

```bash
dealhunter live-report validation/<file>.csv
```

Release gate: at least **50 manually validated variants** with **>=95% accuracy**. See [Live Shopee Validation](docs/LIVE_VALIDATION.md) for the full runbook.
