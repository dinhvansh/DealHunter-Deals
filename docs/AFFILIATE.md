# Affiliate & Sharing

## Goal

When DealHunter finds a genuinely strong deal, the user may share it through an affiliate link and earn commission where the marketplace program permits it.

Affiliate monetization is downstream of deal quality.

## Non-negotiable rule

```text
Deal quality -> ranking -> optional affiliate/share
```

Never:

```text
high commission -> higher Deal Score
```

## Components

### Affiliate Provider

```text
AffiliateProvider
  generate_link(destination_url, campaign)
  get_product_commission(product)
  import_conversions(data)
```

Initial target: Shopee affiliate support through the user's authorized affiliate mechanism.

Future: Lazada and other programs through separate adapters.

### Redirect service

Public links should optionally use:

```text
https://<domain>/go/<code>
```

Flow:

```text
visitor click
 -> record source/campaign/time
 -> redirect to marketplace affiliate URL
```

Do not add unnecessary fingerprinting.

### Analytics

Minimum metrics:

- clicks
- orders/conversions when available
- conversion rate
- order value
- commission
- top deals
- top categories
- source/channel performance

## Affiliate opportunity

A product is an affiliate opportunity only after meeting quality thresholds.

Example:

```text
DealScore >= 90
ConfidenceScore >= 85
SellerTrust >= threshold
Affiliate available = true
```

Then compute Share Score.

## Share Score

Share Score may include affiliate potential at a limited weight, for example 10%.

Strong non-affiliate deals can still have high Deal Scores and appear in Deal Radar.

## Share content generator

Inputs must come from deterministic DealHunter fields:

- product title
- observed/estimated/verified price
- historical baseline
- deal score/confidence
- voucher notes
- seller status
- affiliate redirect URL

AI may rewrite this into:

- Telegram post
- Facebook post
- Zalo-ready message
- short caption

AI must not invent discount values or "lowest ever" claims not supported by stored history.

## Public deal pages

Potential route:

```text
/deals/<slug>
```

Page should contain:

- product
- current price type
- price history
- deal explanation
- promotion steps
- freshness timestamp
- CTA using affiliate link when available
- affiliate disclosure where required

## Conversion ingestion

Phase 1 can support manual report import if necessary.

Later provider-specific integrations can automate conversion updates when officially available to the account/program.

## Privacy

Affiliate/public pages must not expose:

- private account vouchers
- marketplace cookies/tokens
- user-specific verification session details
- personally identifiable purchase history unless explicitly designed and consented
