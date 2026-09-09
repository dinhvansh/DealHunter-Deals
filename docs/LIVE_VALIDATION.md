# Live Shopee Validation Runbook

This runbook closes the Phase 1 release gate by checking DealHunter variant names and prices against the live Shopee UI.

## Goal

Validate at least 50 live variants and achieve at least 95% correct mapping:

```text
Shopee listing
  -> variant/model ID
  -> variant name
  -> observed price
```

Do not scale discovery until this gate passes.

## 1. Install and configure

```bash
cp .env.example .env
pip install -e '.[dev]'
```

Browser-backed collection uses branded **Google Chrome Stable**, controlled by Playwright with a persistent profile. It does not use Playwright's bundled Chromium.

For local/host execution, install Google Chrome Stable. If Playwright manages the branded browser installation:

```bash
playwright install --with-deps chrome
```

For Docker Compose, the supplied image installs Google Chrome Stable and persists the browser profile at `/data/chrome-profile`.

> The supplied Chrome Docker image targets amd64/x86_64 Linux hosts. Do not assume it will work on ARM64 VPS hosts.

## 2. Collect a sample

Start with 10 listings:

```bash
dealhunter live-sample "ssd 2tb" --listings 10 --transport chrome
```

Direct HTTP is still available for lightweight public collection:

```bash
dealhunter live-sample "ssd 2tb" --listings 10 --transport http
```

The legacy `--transport playwright` value is accepted for backward compatibility but maps to the Google Chrome Stable transport.

The command writes a UTF-8 CSV under `validation/` unless `--output` is supplied.

Important exported fields:

- `shop_id`
- `item_id`
- `listing_title`
- `listing_url`
- `search_displayed_price`
- `variant_id`
- `variant_name`
- `observed_price`
- `listed_price`
- `sale_price`
- `stock_state`
- `collected_at`

Manual review fields are intentionally blank:

- `manual_variant_name`
- `manual_price`
- `manual_status`
- `notes`

## 3. Review in Shopee

Open each `listing_url` and select the matching variation.

Preferred validation method:

1. copy the visible variation name into `manual_variant_name`
2. copy the visible product price into `manual_price` as an integer, e.g. `1990000`
3. add notes when the price is conditional, unavailable, or obviously campaign-specific

You may instead set `manual_status` explicitly to:

- `pass`
- `fail`
- `skip`

`skip` is appropriate when a variation is unavailable or cannot be verified reliably.

## 4. Calculate accuracy

```bash
dealhunter live-report validation/shopee-ssd-2tb-YYYYMMDDTHHMMSSZ.csv
```

Output:

```text
Rows: 63
Validated: 57
Passed: 55
Failed: 2
Skipped: 3
Pending: 3
Accuracy: 96.49%
Phase 1 gate (>=50 validated and >=95% accuracy): PASS
```

To use the command as a release gate in automation:

```bash
dealhunter live-report validation/reviewed.csv --require-gate
```

It exits non-zero when the gate has not passed.

## Price tolerance

The normal release check should use exact prices. A tolerance exists only for controlled experiments where Shopee is known to show a small dynamic difference:

```bash
dealhunter live-report validation/reviewed.csv --price-tolerance 1000
```

Do not use a wide tolerance to hide parser errors.

## Recommended sequence

### Smoke sample

- 5–10 listings
- prefer listings with multiple capacities such as 500GB / 1TB / 2TB / 4TB
- inspect every failure before expanding

### Release sample

- 50–100 variants
- mix Mall/preferred/normal sellers where practical
- include single-variation and multi-variation listings
- include at least a few discounted listings

### Pass criteria

```text
validated variants >= 50
accuracy >= 95%
```

If the gate fails, classify failures before changing scoring or scaling:

- search displayed minimum price incorrectly reused for variants
- wrong model/variation ID mapping
- price-unit scaling error
- stale/conditional campaign price
- listing parser structure changed
- blocked/challenged provider response

## Persistent Chrome profile

Set these variables when using Chrome:

```env
DEALHUNTER_CHROME_PROFILE_DIR=/data/chrome-profile
DEALHUNTER_CHROME_HEADLESS=true
DEALHUNTER_CHROME_EXECUTABLE_PATH=
```

The profile is intentionally persistent so ordinary cookies/session state can survive restarts and later support authorized account verification. Do not run multiple Chrome instances against the same profile directory at the same time.

## Safety and operating rule

This tool does not bypass CAPTCHA, marketplace access controls, or automate checkout. If a challenge is encountered, record the provider failure and stop/reduce traffic rather than bypassing the challenge.
