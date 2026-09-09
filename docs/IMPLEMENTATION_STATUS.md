# Implementation Status

## Current branch

`feat/phase0-phase1-foundation`

## Implemented in this branch

### Phase 0 foundation

- FastAPI application and health endpoint
- PostgreSQL 16 and Redis 7 local Docker Compose stack
- SQLAlchemy models for shop, listing, variant and immutable price snapshots
- Alembic initial migration
- CI syntax/test/lint workflow
- environment-based configuration

### Phase 1 collector foundation

- marketplace provider abstraction
- Shopee VN provider
- keyword search discovery through structured Shopee web responses
- direct product URL parsing for common Shopee URL formats
- detail lookup with `pdp/get_pc` then `item/get` fallback
- explicit model/variation ID mapping
- VND price normalization from Shopee's scaled integer representation
- HTTP transport and optional Playwright browser-backed transport
- idempotent shop/listing/variant identities
- immutable price history snapshots per collection run
- collector operational logging
- fixture-based parser and persistence tests

## Not yet claimed complete

Phase 1 remains **in validation** until a live manual sample reaches >=95% correct variation-to-price mapping across 50–100 SSD variants.

The current code deliberately does not:

- bypass CAPTCHA or anti-abuse challenges
- require account login for public discovery
- claim voucher/checkout prices
- crawl at large marketplace scale

## Next validation task

1. boot PostgreSQL and run the migration
2. collect 5–10 SSD listings
3. compare every stored variation/model ID and observed price with the live Shopee page
4. record parser failures and challenged requests
5. only then increase to the Phase 1 target of 50–100 variants
