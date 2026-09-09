# AGENTS.md

Instructions for coding agents and contributors working in DealHunter.

## 1. Source of truth

Before starting any task:

1. inspect current repository HEAD;
2. inspect relevant open PRs/branches if available;
3. report divergence/conflict before making unrelated changes;
4. read the relevant files under `docs/`;
5. preserve documented invariants unless the task explicitly changes the specification.

Do not assume earlier chat context is more current than repository state.

## 2. Product invariants

These are mandatory unless a specification change is explicitly approved.

### SKU-level tracking

Track marketplace variations/SKUs, not only product URLs.

Minimum external identity concept:

```text
platform + shop/item + variant/model
```

### Price semantics

Never collapse these into one field:

```text
Observed Price
Estimated Best Price
Verified Account Price
```

- Observed = directly seen for exact SKU.
- Estimated = deterministic promotion calculation.
- Verified = authenticated account-specific verification with timestamp.

### Affiliate independence

Affiliate commission, EPC, conversion history, or share potential MUST NOT modify `DealScore`.

Affiliate data may affect `ShareScore` only.

### Deterministic core

Do not use an LLM for logic that can be expressed deterministically, including:

- voucher percentages/caps;
- stacking rules;
- min-spend eligibility;
- historical medians/lows;
- DealScore arithmetic;
- alert thresholds.

AI can interpret, classify, normalize and explain around deterministic facts.

### Unknown eligibility

Promotion eligibility supports:

```text
ELIGIBLE
INELIGIBLE
UNKNOWN
```

Never silently treat UNKNOWN as ELIGIBLE.

### Account verification boundary

Verification is only for explicit/watchlisted products and must not become auto-purchase or bulk-abuse automation.

Do not implement:

- auto checkout/purchase;
- captcha bypass;
- bulk account/voucher claiming;
- anti-bot bypass behavior;
- hidden actions not requested by the user.

## 3. Architecture rules

Marketplace-specific behavior belongs under provider adapters.

Domain/scoring/promotion code must not import Shopee-specific browser selectors directly.

Preferred dependency direction:

```text
API/UI
  -> application services
      -> domain core
          <- provider interfaces
               <- provider implementations
```

PostgreSQL is durable business storage.

Redis is not the source of truth for price history.

Workers must be retry-safe and idempotent.

## 4. Data rules

### Money

For VND use integer VND values. Do not use binary floating point for money.

### Time

Use timezone-aware timestamps. Persist UTC or a clearly standardized timezone at DB boundary; present local timezone at UI/API as needed.

### History

Price snapshots are append-only during normal operation.

Corrections require explicit repair logic/migration, not silent mutation.

### Raw provider payloads

Raw evidence may be retained for debugging but normalized domain fields drive decisions.

Never make application correctness depend on undocumented JSON fragments without provider tests.

## 5. Provider implementation rules

Preferred data-source priority when appropriate:

1. official/provider APIs;
2. affiliate feeds/APIs;
3. public web data;
4. browser automation;
5. manual import.

Do not assume scraping is the permanent interface.

Provider code should expose stable normalized operations such as:

```text
search
fetch listing
fetch variations
refresh price
fetch public promotions
```

Every learned provider parser/rule should have a saved fixture or deterministic test where possible.

## 6. Promotion engine rules

- rules are versioned;
- stacking is provider policy, not universal core behavior;
- expired/future promotions cannot apply;
- unknown requirements reduce confidence or exclude candidate combinations;
- estimated price response must expose promotion breakdown and unknown assumptions;
- optimizer must evaluate only valid combinations.

## 7. Deal scoring rules

Every score should be explainable through components.

Do not introduce opaque ML before a deterministic baseline is measured.

Any scoring change must:

1. update engine version;
2. update tests/fixtures;
3. preserve Affiliate/DealScore separation;
4. document material behavior changes.

## 8. Security rules

Never commit:

- passwords;
- cookies;
- session storage;
- API secrets;
- affiliate secret keys;
- Telegram tokens;
- database credentials.

Use environment variables/secret references.

Redact sensitive headers/session information from logs.

Verification session references must never be exposed through public API responses.

Affiliate redirect must reject unapproved arbitrary destinations to avoid open-redirect vulnerabilities.

## 9. Development sequencing

Respect phase gates in `docs/ROADMAP.md`.

Do not build later-phase complexity to hide an earlier-phase correctness issue.

Example:

If exact variation price collection is unreliable, fix Phase 1. Do not add AI matching as a workaround and continue to vouchers.

## 10. Testing requirements

At minimum:

- unit tests for domain/promotion/scoring logic;
- provider parser tests with fixtures;
- migration tests/clean DB startup;
- idempotency tests for worker retries;
- API contract tests for critical endpoints;
- manual validation dataset for provider pricing accuracy.

See `docs/ACCEPTANCE.md` for phase quality gates.

## 11. Change discipline

Prefer small PRs aligned to one roadmap task/phase.

A PR should state:

- problem;
- scope;
- architecture impact;
- migrations;
- tests;
- known limitations;
- manual verification performed.

Do not combine unrelated refactors with provider behavior changes unless necessary.

## 12. First engineering task

The first implementation objective is:

> Given a Shopee search term or product URL, identify the listing/shop, enumerate exact variations, collect exact current price for each variation and persist normalized records plus price snapshots in PostgreSQL.

Validation category: SSD, 50–100 variants.

Do not start account automation or affiliate integration before this foundation is accurate.
