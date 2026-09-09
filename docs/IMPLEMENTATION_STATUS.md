# Implementation Status

Updated: 2026-09-09

## Phase 0 — Foundation

Status: **implemented**

- FastAPI service foundation
- PostgreSQL/Redis Docker Compose
- SQLAlchemy + Alembic
- CI tests and lint gate

## Phase 1 — Shopee Collector

Status: **implemented, live validation still required**

- provider abstraction and Shopee adapter
- search discovery and direct URL parsing
- exact variation/model mapping
- immutable price snapshots
- idempotent shop/listing/variant persistence

Release gate remains >=95% manually verified mapping over 50–100 live SSD variants.

## Phase 2 — Price History

Status: **implemented core**

- immutable history query
- 7/30/90-day medians
- 30/90/180-day lows

## Phase 3 — Voucher & Promotion Engine

Status: **implemented deterministic core**

- normalized voucher rules
- percent/fixed/freeship discounts
- min-spend and validity checks
- mutually-exclusive stack groups
- calculation trace + confidence

Marketplace-specific public voucher discovery still requires live adapter work.

## Phase 4 — Deal Engine

Status: **implemented core scoring**

- Deal Score
- Confidence Score
- Opportunity Score
- Share Score
- score components/explanations

Production release still requires manually labeled evaluation data and >=80% alert precision.

## Phase 5 — Web UI / PWA

Status: **UI shell implemented**

- responsive DealHunter landing/dashboard shell
- Deal Radar / Opportunities / Watchlist / Affiliate navigation placeholders

Live API wiring, auth and full product detail charts remain.

## Phase 6 — Watchlist + Alert logic

Status: **domain core implemented**

- NORMAL/HOT modes
- target price
- deal-score threshold
- historical-low event evaluation

Telegram transport, persistence and scheduler jobs remain.

## Phase 7 — Account Verification

Status: **safe interface implemented**

- AccountVerifier contract
- timestamped VerificationResult
- disabled/fail-safe verifier

Authenticated browser session adapter is intentionally not automated until an authorized account flow is configured and manually validated. No CAPTCHA bypass or auto-buy behavior is implemented.

## Phase 8 — Affiliate Engine

Status: **provider abstraction implemented**

- AffiliateProvider abstraction
- deterministic redirect-code generation
- generic query-param provider for development/testing

Real Shopee/Lazada affiliate provider credentials/API adapter, click persistence and conversion import remain environment/integration work.

## Phase 9 — Public Deals + Creator Tools

Status: **core share payload implemented**

- deterministic factual share payload from deal data
- Share Score in scoring engine

Public SEO pages and channel-specific publishing integrations remain.

## Phase 10 — AI Skill / Agent

Status: **tool contract implemented**

- full tool catalog defined per `docs/AI_SKILL.md`
- deterministic business logic remains outside AI

Runtime binding of tool handlers to API/service layer remains.

## What is intentionally not claimed complete

The codebase now contains executable foundations across all planned phases, but production completion still depends on live marketplace/provider validation and credentials for external integrations. Specifically:

- Phase 1 live Shopee 50–100 SSD validation
- public voucher/campaign live discovery
- Telegram bot token and delivery integration
- authorized account verification session flow
- real affiliate provider integration credentials and conversion source
- AI runtime/plugin deployment target

These are release gates, not hidden technical debt. The core architecture is present so each external integration can be added without redesigning the domain model.
