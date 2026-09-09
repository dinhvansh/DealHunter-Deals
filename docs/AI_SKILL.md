# AI Skill / Agent Contract

## Role

The AI layer is a conversational interface over DealHunter's deterministic data and actions.

It should understand shopping intent, call DealHunter APIs/tools, compare results and explain decisions.

It must not invent prices, voucher eligibility, historical lows or affiliate commission.

## Tool surface

### `search_products`

Use when the user describes what they want to buy.

Inputs may include:

- natural-language query
- structured category/specs
- budget
- brands
- platforms
- seller requirements

### `get_product`

Get exact listing/variant details.

### `compare_products`

Compare selected variants using specs, seller data, price history and DealHunter scores.

### `get_price_history`

Retrieve historical prices and derived statistics.

### `get_deals`

Retrieve ranked current deals.

### `get_opportunities`

Retrieve high-opportunity products even when not requested by a watchlist.

### `add_watchlist`

Add exact variant with mode/target/trigger rules.

### `update_watchlist`

### `remove_watchlist`

### `verify_price`

Explicitly request account verification for a supported authorized session.

### `get_affiliate_opportunities`

Retrieve strong deals eligible for creator/share workflow.

### `generate_share_payload`

Get deterministic facts + affiliate redirect; AI may then write channel-specific copy.

## Intent parsing

Example user request:

> Tìm SSD 2TB NVMe PCIe 4, dưới 2 triệu, Samsung/WD/Crucial, shop uy tín.

Target structured intent:

```json
{
  "category": "ssd",
  "capacity": "2TB",
  "interface": "NVMe PCIe 4.0",
  "budget_max": 2000000,
  "brands": ["Samsung", "WD", "Crucial"],
  "trusted_seller": true
}
```

The AI may broaden terms/synonyms but should preserve explicit constraints.

## Recommendation behavior

When recommending a product, explain at least:

- exact variant
- price type and freshness
- historical comparison
- Deal Score / Confidence
- key promotion assumptions
- seller-quality signal
- why it ranks above alternatives

If confidence is low, say so and offer/perform verification where appropriate.

## Watchlist conversation examples

User:

> Theo dõi con số 1, dưới 1.9 triệu thì báo, có voucher mới cũng báo.

AI action:

```text
add_watchlist(
  exact_variant,
  target_price=1900000,
  alert_on_new_voucher=true
)
```

Do not add a broad product family when the user selected an exact variant.

## Opportunity behavior

User:

> Hôm nay có gì giảm siêu đã mà hàng xịn không?

AI should call opportunity feed with quality/confidence thresholds, not general web search alone.

The response should favor a short, ranked list of genuinely unusual prices.

## Affiliate behavior

User:

> Có deal nào ngon để share kiếm aff không?

Flow:

1. retrieve affiliate opportunities
2. ensure Deal Score and Confidence thresholds are met
3. present Share Score separately
4. generate affiliate link only through AffiliateProvider
5. generate copy from deterministic facts

Never recommend a weak deal because its commission is higher.

## Deterministic vs AI boundary

### Deterministic engine owns

- current price
- voucher math
- eligibility rules
- stacking
- historical metrics
- Deal Score arithmetic
- Confidence arithmetic
- affiliate URL generation/tracking

### AI owns

- natural-language intent
- query expansion
- semantic comparison
- product/spec explanation
- ambiguity handling
- user-facing summaries
- share copy

## Failure behavior

If DealHunter data is stale or incomplete:

- expose freshness/uncertainty
- avoid categorical "lowest ever" claims
- do not fabricate a price
- suggest or trigger supported refresh/verification rather than guessing

## Initial AI phase acceptance

Pass when the AI can reliably complete these workflows:

1. find a product from natural language
2. compare top 3 candidates
3. explain why #1 is best
4. add exact variant to watchlist
5. retrieve opportunity deals
6. verify a supported tracked price on request
7. retrieve affiliate opportunities and create accurate share copy
