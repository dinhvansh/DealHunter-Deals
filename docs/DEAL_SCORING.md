# Deal Scoring

## Goal

DealHunter should rank genuinely attractive purchases, not simply products with large displayed discount percentages.

A 75% discount on a low-quality unknown item can rank below a 30% discount on a reliable, high-value product.

## 1. Deal Score

Range: 0–100.

Initial component proposal:

```text
DealScore =
  HistoricalPriceScore   * 0.30 +
  CurrentDiscountScore   * 0.15 +
  VoucherEfficiency      * 0.15 +
  AbsoluteSavingScore    * 0.10 +
  SellerTrustScore       * 0.10 +
  ProductQualityScore    * 0.10 +
  PopularityScore        * 0.10 -
  RiskPenalty
```

Weights are configuration, not constants embedded everywhere in code.

### HistoricalPriceScore

Compare current/estimated price against:

- median 30d
- median 90d
- low 90d
- low 180d

New historical lows should receive a meaningful bonus only when there are enough observations.

### CurrentDiscountScore

Measure discount against a trusted historical baseline, not marketplace strike-through MSRP.

### VoucherEfficiency

Measures how effectively the candidate uses the current voucher opportunity.

Example:

20% max 500k reaches full discount around 2.5m order value. Products near the effective sweet spot can receive stronger voucher-efficiency scores.

### AbsoluteSavingScore

A 30% reduction saving 1,000,000 VND is often more relevant than a 70% reduction saving 40,000 VND.

### SellerTrustScore

Inputs may include:

- Mall/preferred status
- seller rating
- seller age/history when observable
- suspicious listing signals

### ProductQualityScore

Should be based on product identity/reputation/spec quality, not affiliate commission.

### PopularityScore

Signals can include sold count, review count, rating confidence and search/category interest.

### RiskPenalty

Examples:

- suspiciously mismatched variant
- insufficient history
- promotion eligibility unclear
- seller trust low
- abnormal title/spec inconsistency

## 2. Confidence Score

Range: 0–100.

Confidence reflects evidence quality, not deal attractiveness.

Example evidence confidence:

- directly observed SKU price: very high
- parsed shop voucher: high
- public platform voucher with explicit rules: high
- freeship eligibility: medium
- payment promotion: medium
- personalized voucher inferred without account verification: low

Suggested model:

```text
Confidence = weighted evidence completeness - uncertainty penalties
```

A deal may be 98/100 attractive but only 43/100 confidence.

## 3. Opportunity Score

Used for ranking and alerts.

Initial formula:

```text
OpportunityScore = DealScore * ConfidenceFactor
```

Where `ConfidenceFactor` maps 0–100 confidence to 0–1.

A nonlinear function may later be preferable so low-confidence deals are penalized more strongly.

## 4. Share Score

Share Score is separate from purchasing quality.

Initial proposal:

```text
ShareScore =
  DealQuality        * 0.35 +
  Popularity         * 0.25 +
  WowFactor          * 0.15 +
  SellerTrust        * 0.10 +
  AffiliatePotential * 0.10 +
  Freshness          * 0.05
```

Rules:

- AffiliatePotential never feeds DealScore.
- A non-affiliate deal can still be the #1 deal.
- A high-commission weak deal must never outrank a strong deal in Deal Radar.

## 5. Historical baselines

Do not compute strong historical claims until minimum sample requirements are met.

Example defaults:

- 30d median: >= 10 observations
- 90d low: >= 20 observations
- 180d historical-low label: sufficient temporal coverage, not merely count

Store score components to make every score explainable.

Example:

```json
{
  "deal_score": 94,
  "confidence_score": 91,
  "opportunity_score": 85.5,
  "components": {
    "historical": 96,
    "voucher": 88,
    "seller": 92,
    "quality": 90,
    "risk_penalty": 3
  }
}
```

## 6. Calibration

Scores must be calibrated against manual verification.

For each alert, record outcome:

- GREAT_DEAL
- GOOD_DEAL
- NORMAL
- WRONG_PRICE
- VOUCHER_NOT_APPLICABLE
- BAD_PRODUCT_MATCH

Use these labels to tune thresholds and weights.
