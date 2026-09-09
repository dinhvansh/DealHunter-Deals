# Deal and Promotion Engine

## 1. Purpose

The Deal Engine decides whether a current marketplace opportunity is materially better than normal, how certain DealHunter is about the price, and whether the opportunity deserves an alert or public share.

It has four outputs:

- `DealScore` — how good the deal itself is;
- `ConfidenceScore` — how trustworthy the calculated opportunity is;
- `OpportunityScore` — ranking value for user alerts/discovery;
- `ShareScore` — suitability for affiliate/content sharing.

Affiliate commission MUST NOT affect `DealScore`.

## 2. Price model

### 2.1 Observed price

Directly observed price for a SKU/variation.

Recommended selection order when multiple public values exist:

```text
flash_price
sale_price
listed_price
```

Only if the collector can prove the value is for the selected variation.

### 2.2 Estimated best public price

Calculated by the Promotion Engine from public promotions whose eligibility is known or explicitly modeled.

```text
estimated_best_price = base_price
                       - eligible discounts
                       + known required costs
```

Shipping, coins, payment discounts, category vouchers and other modifiers must be represented independently in the breakdown.

### 2.3 Verified account price

Observed during an authenticated verification run for an explicitly selected/watchlisted SKU.

Verified values never silently replace historical public snapshots. They are account-specific observations stored separately.

## 3. Promotion normalization

Every promotion should normalize into:

```text
type
start/end
min spend
fixed or percentage discount
cap
scope
stack group
payment requirement
category/shop/product restrictions
public/account-specific status
known/unknown eligibility conditions
```

Example:

```json
{
  "type": "platform_voucher",
  "discount_type": "percentage",
  "value": 20,
  "max_discount": 500000,
  "min_spend": 1500000,
  "starts_at": "2026-09-09T20:00:00+07:00",
  "ends_at": "2026-09-09T22:00:00+07:00",
  "stack_group": "platform_voucher",
  "scope": {
    "categories": ["electronics"]
  }
}
```

## 4. Eligibility states

Eligibility is tri-state:

```text
ELIGIBLE
INELIGIBLE
UNKNOWN
```

Unknown MUST NOT become eligible by default.

Examples of UNKNOWN:

- account-targeted voucher with no account verification;
- payment method eligibility not supplied;
- shipping destination unavailable;
- voucher quota remaining unknown;
- ambiguous promotion text not validated.

## 5. Discount calculation

### Fixed

```text
discount = min(fixed_value, eligible_subtotal)
```

### Percentage with cap

```text
discount = min(base * percentage, max_discount)
```

### Minimum spend

Promotion is ineligible when required subtotal does not meet threshold.

### Price override / flash

Treat as a separate candidate base price if it is observed or a deterministic provider rule.

## 6. Stacking model

Do not hard-code universal marketplace assumptions in the core.

Each provider owns a stacking policy such as:

```text
shop voucher:        max 1
platform voucher:    max 1
shipping voucher:    max 1
payment promotion:   max 1
```

The policy can include exclusions and ordering rules.

The optimizer evaluates valid combinations only.

Pseudo-flow:

```text
promotions
    |
    v
filter active window
    |
    v
evaluate eligibility
    |
    v
partition by stack group
    |
    v
generate valid combinations
    |
    v
apply provider ordering/rules
    |
    v
calculate final candidates
    |
    v
select lowest valid price
```

Combinatorial explosion must be bounded. Since groups are small, generate choices by stack group rather than arbitrary power sets.

## 7. Voucher sweet spot

Useful discovery feature:

For a percentage voucher with cap:

```text
sweet_spot_price = max_discount / percentage
```

Example:

```text
20% max 500,000
sweet spot = 2,500,000
```

This can be used by discovery workers to prioritize products around the range that extracts maximum voucher value.

Sweet spot is a discovery heuristic, not a Deal Score by itself.

## 8. Historical baselines

Recommended statistics:

- median 7d;
- median 30d;
- median 90d;
- low 30d;
- low 90d;
- low 180d;
- sample count;
- volatility.

Prefer median to simple mean because marketplace prices may contain campaign spikes or parsing outliers.

Historical comparisons must use the same variant/SKU.

## 9. Deal Score v1

Use a transparent weighted score first. Do not start with ML.

Recommended normalized components, each `0..100`:

```text
HistoricalPositionScore
RealDiscountScore
AbsoluteSavingScore
VoucherEfficiencyScore
SellerTrustScore
ProductQualityScore
PopularityScore
RiskPenalty
```

Initial formula:

```text
DealScore =
    0.25 * HistoricalPositionScore
  + 0.20 * RealDiscountScore
  + 0.15 * AbsoluteSavingScore
  + 0.10 * VoucherEfficiencyScore
  + 0.10 * SellerTrustScore
  + 0.10 * ProductQualityScore
  + 0.10 * PopularityScore
  - RiskPenalty
```

Clamp to `0..100`.

Weights are configuration/versioned constants, not magic values scattered through code.

### HistoricalPositionScore

Should strongly reward:

- current/estimated price below 30/90/180-day lows;
- price near the bottom percentile of available history.

Low sample counts reduce confidence rather than automatically producing a huge score.

### RealDiscountScore

Compare against a robust baseline such as median 30d/90d, not displayed MSRP.

```text
real_discount_pct = (baseline - candidate_price) / baseline
```

### AbsoluteSavingScore

Rewards meaningful VND savings. Use category-aware/logarithmic thresholds later so expensive items do not dominate every ranking.

### VoucherEfficiencyScore

Measures how much of a voucher's theoretical maximum is captured and how much it improves the actual final price.

### SellerTrustScore

Inputs may include:

- mall/preferred flags;
- rating;
- seller history;
- sales count when reliable;
- risk flags.

### ProductQualityScore

May initially be rule/manual/brand/category based. AI can assist classification, but persisted score inputs must be explainable.

### PopularityScore

Use only reliable signals and cap its weight. Popularity should not turn mediocre prices into "great deals".

### RiskPenalty

Examples:

- suspiciously low outlier with weak seller;
- variation mapping uncertainty;
- stale collector data;
- promotion eligibility unknown;
- too little historical data;
- stock ambiguity.

## 10. Confidence Score v1

Confidence measures evidence quality, not deal attractiveness.

Possible inputs:

```text
variation_identity_confidence
price_freshness
history_sample_confidence
promotion_eligibility_confidence
seller_data_confidence
verification_state
```

Initial conceptual formula:

```text
ConfidenceScore = weighted evidence quality - uncertainty penalties
```

Example confidence bands:

- `90–100`: high confidence;
- `75–89`: usable with minor assumptions;
- `50–74`: show warnings;
- `<50`: do not push strong "buy now" language.

## 11. Opportunity Score

Initial ranking formula:

```text
OpportunityScore = DealScore * (ConfidenceScore / 100)
```

Later add user preference/category affinity as a separate ranking modifier, without changing the underlying Deal Score.

Example:

```text
Deal 96, confidence 95 -> 91.2
Deal 99, confidence 40 -> 39.6
```

The first ranks higher despite a lower raw Deal Score.

## 12. Share Score

Share Score evaluates whether a deal is attractive to publish/share.

Suggested components:

```text
0.35 deal quality
0.25 product popularity
0.15 wow factor / real discount
0.10 seller trust
0.10 affiliate potential
0.05 freshness
```

Affiliate potential can include availability and commission only here.

Hard rule: `ShareScore` may not write back into `DealScore`.

## 13. Alert thresholds

Default configurable examples:

```text
opportunity alert:
  DealScore >= 85
  ConfidenceScore >= 75

strong alert:
  DealScore >= 90
  ConfidenceScore >= 85

verified alert:
  verified price materially beats public estimate/baseline
```

User watch thresholds override general defaults.

## 14. Staleness

Every displayed evaluation must expose freshness.

Recommended fields:

```text
price_observed_at
promotions_checked_at
deal_evaluated_at
verified_at
```

If a promotion expires, cached estimated prices must invalidate/recompute.

## 15. Explainability output

Each evaluation should produce concise reasons:

```json
{
  "positive": [
    "Estimated price is 31% below the 30-day median",
    "Estimated price is below the 180-day public low",
    "Seller trust is high"
  ],
  "warnings": [
    "Freeship eligibility is not verified for your address"
  ]
}
```

AI may turn these structured facts into natural language but may not invent additional price claims.

## 16. Engine versioning

Every promotion/deal evaluation stores an `engine_version`.

When scoring rules change, old evaluations remain interpretable and can be recomputed intentionally.

Suggested versioning:

```text
promotion-engine-v1
deal-score-v1
confidence-v1
share-score-v1
```
