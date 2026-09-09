# Acceptance and Validation Plan

## 1. Quality philosophy

DealHunter should be judged by whether a human can trust a deal alert, not by how many pages it crawls.

The primary product metric is **Deal Alert Precision**.

## 2. Definitions

### Correct SKU

The displayed product variation matches the exact marketplace variation being priced.

### Correct observed price

The price shown as Observed was directly visible for that exact SKU/variation at the recorded timestamp.

### Correct estimated price

The calculation follows structured active promotion rules and clearly marks unknown eligibility assumptions.

### Correct verified price

The value came from a successful authenticated verification run for the relevant account/session and includes a timestamp.

### Correct deal alert

An alert is correct when:

1. SKU is correct;
2. current price evidence is fresh enough for the alert context;
3. historical comparison uses the same variation;
4. voucher assumptions are transparent;
5. opening/checking the marketplace confirms the opportunity is materially attractive;
6. no hidden affiliate ranking bias caused the alert.

## 3. Phase 1 collector validation

Create a manually verified SSD dataset of 50–100 variants.

For every row record:

```text
validation timestamp
marketplace URL
shop name/shop ID if available
item ID
variant/model ID
variant name
visible current price
stock state
expected mall/preferred state
notes
```

Run collector and compare.

Metrics:

```text
variation_identity_accuracy = correct variant mappings / checked mappings
observed_price_accuracy = correct exact prices / checked prices
listing_identity_accuracy = correct item/shop mappings / checked listings
```

Required before Phase 2/3 expansion:

- variation identity >= 95%;
- observed price >= 95%;
- no systematic cross-variation contamination;
- retry/upsert creates no duplicate external identities.

Every failure must be categorized:

```text
parser
provider data ambiguity
variation mapping
stale page/API
blocked/rate-limited
out of stock
price type confusion
unknown
```

## 4. Price-history validation

Tests:

- append multiple snapshots for one variant;
- verify time ordering;
- median 7/30/90 calculation against known fixture;
- low 30/90/180 calculation;
- empty history;
- one sample;
- outlier price;
- campaign spike;
- duplicate retry.

Invariant:

Historical statistics for a variant must never include another variation's price.

## 5. Promotion engine test matrix

Every rule type needs deterministic tests.

### Percentage discount

```text
base: 2,000,000
20%
expected: 400,000
```

### Percentage with cap

```text
base: 3,000,000
20%, max 500,000
expected discount: 500,000
```

### Fixed discount

```text
base: 2,000,000
fixed 200,000
expected: 1,800,000
```

### Minimum spend fail

```text
base: 1,400,000
voucher minimum: 1,500,000
expected: INELIGIBLE
```

### Unknown account condition

```text
targeted/account voucher
no verification context
expected: UNKNOWN, not eligible
```

### Stacking

Test:

- shop + platform allowed;
- same stack group exclusivity;
- payment restriction;
- freeship separate;
- explicit exclusion;
- expired voucher;
- future voucher;
- invalid category/product scope.

### Engine correctness target

For supported deterministic scenarios: **100% fixture correctness**.

For real manually checked marketplace cases: target **>=90%** before broad alerts.

## 6. Scoring validation

Deal Score tests must prove monotonic expectations where appropriate.

Examples:

- same product/seller, lower real price should not reduce historical/discount score;
- lower confidence must reduce OpportunityScore;
- affiliate commission change must not alter DealScore;
- seller risk penalty should reduce DealScore;
- 80% nominal MSRP discount with no historical advantage should not automatically score as excellent;
- new historical low should materially improve historical-position component.

Store engine version in expected fixtures.

## 7. Watchlist tests

Cases:

- add/remove/update watch;
- duplicate active watch prevented;
- normal vs hot scheduling priority;
- target price trigger;
- new low trigger;
- new voucher trigger;
- deal score trigger;
- unchanged state does not spam alert;
- trigger cooldown expires correctly;
- provider failure marks stale/error without fake alert.

## 8. Verification tests

### Security

- API never returns cookies/session tokens;
- DB business tables contain no raw password;
- logs redact sensitive session material;
- only configured watch/explicit action can request verification.

### Correctness

- success records final price + timestamp;
- failed run does not overwrite public price;
- stale previous verified price remains labeled stale;
- eligible/ineligible promotions recorded;
- verification timeout/failure reason recorded;
- duplicate trigger respects cooldown/idempotency.

### Behavioral boundary

Automated purchase, captcha bypass and bulk voucher claiming are not acceptance scenarios and must not be implemented as hidden side effects.

## 9. Affiliate tests

- affiliate link points to expected product/listing;
- `/go/{code}` rejects unknown/unsafe destinations;
- click attribution records source/campaign;
- redirect still works when analytics recording degrades, where safe;
- same deal evaluation has identical DealScore before and after affiliate data is present;
- ShareScore can change when affiliate availability changes;
- duplicate imported conversion does not double-count.

## 10. UI acceptance

### Deal Radar

A user can immediately distinguish:

```text
Observed
Estimated
Verified
```

No two tiers are presented as equivalent certainty.

### Product Detail

Must show:

- exact variant;
- timestamp/freshness;
- price history;
- promotion breakdown;
- Deal Score;
- Confidence;
- warnings;
- Watch action.

### Watchlist

User can see:

- target;
- watch mode;
- latest price;
- last check;
- last verification;
- current state.

### Mobile

Core deal facts remain readable without horizontal scrolling.

## 11. Deal Alert Precision study

Before scaling catalog, perform recurring human review.

Example daily review sheet:

```text
alert_id
variant
DealScore
Confidence
observed_price
estimated_price
verified_price if any
human verdict: GOOD / NORMAL / WRONG
failure reason
notes
```

Precision:

```text
GOOD alerts / reviewed alerts
```

Quality bands:

- `<70%`: stop expansion and fix data/engine;
- `70–79%`: experimental only;
- `>=80%`: useful;
- `>=90%`: strong;
- `>=95%`: excellent.

Do not improve this metric by simply suppressing difficult manual review cases; sample must represent actual alerts.

## 12. Performance acceptance — foundation

Do not prematurely optimize, but enforce basic bounds.

Foundation targets should be measured and then documented, including:

- API response latency for cached/read endpoints;
- one listing refresh duration;
- queue throughput;
- scheduler lag;
- DB query duration for 180-day history;
- redirect endpoint latency.

No hard production numbers are defined until real provider behavior is measured.

## 13. Provider resilience acceptance

Simulate or observe:

- timeout;
- HTTP/provider error;
- malformed payload;
- variation missing;
- price missing;
- rate limit;
- temporary blocking;
- schema change.

Expected behavior:

- bounded retries;
- backoff;
- observable failure;
- existing good data retained;
- no fabricated price;
- no duplicate entity creation.

## 14. Release checklist

Before merging a phase as complete:

- [ ] exit criteria in `ROADMAP.md` met;
- [ ] migrations reviewed;
- [ ] unit/integration tests green;
- [ ] manual validation sample attached/documented;
- [ ] secrets scan/log review clean;
- [ ] known limitations documented;
- [ ] scoring/promotion engine version updated if behavior changed;
- [ ] provider changes have saved fixtures/tests when possible;
- [ ] no affiliate input affects DealScore;
- [ ] observed/estimated/verified semantics remain intact.
