# Phase 0/1 implementation notes

## What is implemented

- FastAPI service with `/health`
- PostgreSQL + Redis local stack
- Alembic core marketplace migration
- marketplace provider abstraction
- Shopee VN search adapter
- Shopee detail adapter with `pdp/get_pc` -> `item/get` fallback
- HTTP and Playwright JSON transports
- explicit variant/model identity mapping
- immutable price snapshot persistence
- internal collection endpoints
- unit tests for URL parsing, VND scaling, variant-price correctness and identity idempotency
- CI for lint + tests

## Local run

```bash
cp .env.example .env
docker compose up -d postgres redis
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn dealhunter.main:app --reload
```

If direct public HTTP is challenged, install the Playwright browser and set:

```bash
playwright install chromium
DEALHUNTER_SHOPEE_TRANSPORT=playwright
```

The browser transport does not bypass CAPTCHA or login challenges.

## First live validation

Use 5–10 SSD listings first and manually compare each Shopee model/variation price. Do not increase discovery volume until >=95% variant-price mapping is confirmed.
