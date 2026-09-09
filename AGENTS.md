# DealHunter Agent Instructions

This file is the operational entry point for AI coding/deployment agents.

## Mandatory repository rule

Before every new task:

1. inspect the current branch and `main`
2. fetch the latest remote refs
3. report any new commit, divergence, conflict, dirty working tree, or unmerged PR before continuing
4. do not overwrite user changes

The repository documentation is the source of truth. Read `README.md`, `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_STATUS.md`, and the task-specific document before large changes.

## Supported production host

Preferred first deployment:

- Ubuntu 24.04 LTS
- amd64/x86_64
- 2 vCPU / 4 GB RAM minimum
- 4 vCPU / 8 GB RAM recommended for Chrome-heavy collection
- Docker + Docker Compose v2

The supplied branded Google Chrome Stable Docker images target amd64. Do not silently deploy the Chrome services on ARM.

## First installation

From a fresh host:

```bash
git clone https://github.com/dinhvansh/DealHunter-Deals.git
cd DealHunter-Deals
sudo bash scripts/bootstrap-vps.sh
```

Then open the printed `/setup` URL and create the first administrator.

Never pre-create an admin with a hard-coded/default password.

## Runtime architecture

```text
DealHunter API
├── FastAPI UI/API
├── PostgreSQL
├── Redis
├── Google Chrome Stable collector
├── persistent Chrome profile
└── optional Shopee browser-login (Xvfb + noVNC)
```

`shopee-browser-login` is optional and exists only so a human can log in to Shopee manually. DealHunter must not collect or store the user's Shopee password, OTP, CAPTCHA answer, or raw login form data.

Start the login browser only when needed:

```bash
docker compose --profile browser-login up -d shopee-browser-login
```

After the human finishes login, stop that service before the collector reuses the profile:

```bash
docker compose stop shopee-browser-login
```

Do not run two Chrome processes against the same profile simultaneously.

## Secrets

- Admin passwords: scrypt hash only.
- Integration tokens: encrypted before PostgreSQL storage.
- The encryption master key is stored separately at `/secrets/master.key` in the API-only volume when `DEALHUNTER_SECRET_KEY` is blank.
- Never print or commit `.env`, the master key, session cookies, Shopee cookies, API keys, Telegram tokens, affiliate credentials, or browser profile contents.
- UI/API responses may expose masked secrets only.

## First-run and auth behavior

Before setup is complete:

- `/health` and `/setup` are available.
- private dashboard/API routes are blocked.

After setup:

- `/login` is required.
- authenticated sessions use an HttpOnly SameSite=Strict cookie.
- set `DEALHUNTER_SESSION_COOKIE_SECURE=true` when the app is served over HTTPS.

## Database changes

Every schema change requires an Alembic migration. Validate with:

```bash
alembic upgrade head
pytest -q
```

Never edit an already-applied migration to change production history; add a new migration.

## Required validation before merge

```bash
ruff check src tests
python -m compileall -q src tests
alembic upgrade head
pytest -q
```

For Docker/deployment changes also run, where possible:

```bash
docker compose config
docker compose build api
```

## Marketplace safety

Allowed:

- public product discovery
- low-volume browser collection
- human-authorized persistent account session
- read-only account verification for watchlisted items

Do not implement CAPTCHA bypass, anti-bot evasion, credential capture, abusive request rates, auto-purchase, or voucher claiming automation.

## Production release gate

Do not scale collection simply because unit tests pass. Phase 1 live gate remains:

- at least 50 manually validated Shopee variants
- at least 95% variant/price mapping accuracy

See `docs/LIVE_VALIDATION.md`.
