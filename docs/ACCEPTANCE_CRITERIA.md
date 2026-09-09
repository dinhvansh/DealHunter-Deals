# Acceptance Criteria

## North-star metric: Deal Alert Precision

The project is useful only if a high percentage of surfaced deals are genuinely attractive when manually checked.

Example daily evaluation:

```text
10 alerts
8 genuinely good
1 normal
1 incorrect voucher
=> 80% precision
```

Targets:

- >= 80%: usable
- >= 90%: strong
- >= 95%: excellent

Do not scale catalog size while precision is poor.

## Phase 1 — Collector

Pass when:

- search returns stable marketplace item identity
- shops are normalized without duplication
- variations are uniquely identified
- >= 95% sampled variation prices match manual marketplace inspection
- minimum-display-price is never incorrectly assigned to a different variant
- repeated collection stores snapshots without corrupting identity

## Phase 2 — Price history

Pass when:

- snapshots are immutable
- 7/30/90d median and 30/90/180d lows match recomputation
- stale data is identified
- UI/API can show exact data timestamp

## Phase 3 — Promotion engine

Pass when:

- min spend is honored
- fixed/percent discounts calculate correctly
- max discount caps calculate correctly
- expired/not-started vouchers are rejected
- product/shop/category scope is honored
- incompatible stacking is rejected
- calculation trace explains why each voucher was applied/rejected
- manually checked test set meets accuracy target

## Phase 4 — Deal engine

Pass when:

- displayed strike-through price is not treated as historical truth
- strong historical discounts rank above fake sale labels
- low-quality/suspicious items can be penalized
- low-confidence voucher estimates are visibly penalized
- score components are inspectable

## Watchlist

Pass when:

- a specific variation can be watched
- NORMAL/HOT mode changes cadence
- target price triggers once without repeated spam
- new voucher/historical-low events can trigger alerts
- alert cooldown/deduplication works

## Verification

Pass when:

- verification only runs on authorized/manual/watchlisted candidates
- secrets are not logged
- verified price includes timestamp
- expired session and challenge conditions fail safely
- supported verification flow matches manual account checks >= 90%

## Affiliate

Pass when:

- affiliate URL generation preserves intended product destination
- `/go/{code}` records a click then redirects
- source/campaign attribution works
- conversion import is idempotent
- affiliate potential does not alter Deal Score

## UI

Pass when the user can complete these workflows on desktop and mobile:

1. search for a product
2. understand why a candidate is ranked
3. distinguish observed/estimated/verified price
4. view price history
5. add/remove watchlist
6. manually verify a tracked product
7. view opportunity deals
8. generate/share affiliate deal when available

## Final user-value test

For a 2–4 week pilot, manually classify every alert.

The system is ready to scale when:

- alert precision >= 80%
- incorrect variation mapping is rare and investigated
- promotion false positives are within acceptable threshold
- collector uptime is stable
- user actually finds multiple alerts worth purchasing or sharing
