# Account Verification

## Purpose

Account verification answers:

> With this user's current eligible promotions, what price can this tracked product actually reach right now?

It is a final verification layer, not the marketplace discovery mechanism.

## Trigger policy

Verification is allowed for:

- an explicit user request
- a watchlisted variant with `verify_account=true`
- a strong watchlist event such as target price reached or new voucher detected

Verification should not run for thousands of catalog products.

## Flow

```text
Public observed price
       |
Public voucher evaluation
       |
Estimated best price
       |
Watch event / manual verify
       |
Authenticated user session
       |
Check applicable promotions
       |
Verified Account Price
       |
Alert with verified_at
```

## Verification output

Store:

- observed price
- estimated price
- verified price
- eligible promotions
- rejected/non-applicable promotions
- verification state
- timestamp

Verified prices are time-sensitive. UI must display `verified_at`.

## Session handling

- Never store username/password plaintext.
- Prefer a separately encrypted session/cookie secret store.
- Store only secret references in normal DB tables.
- Redact tokens/cookies from logs and traces.
- Support session expiry and re-authentication state.

## Safety / platform-respect rules

The verification system must not:

- auto-purchase products
- mass-claim vouchers
- bypass CAPTCHA/anti-abuse measures
- imitate fake user engagement
- use many accounts to evade limits

If verification encounters an interactive challenge, return `verification_required`/`challenge` instead of bypassing it.

## Verification states

Suggested:

- QUEUED
- RUNNING
- SUCCESS
- PARTIAL
- SESSION_EXPIRED
- CHALLENGE
- NOT_ELIGIBLE
- FAILED

## Performance

Do not verify on every public refresh.

Example trigger:

```text
if estimated_price <= target_price
or deal_score >= verification_threshold
or new_high_value_voucher:
    enqueue verification
```

Add cooldown to prevent repeated verification of the same unchanged condition.

## Acceptance

Before enabling automatic watchlist verification:

- session can survive normal browser restarts where supported
- no secret data appears in logs
- verified result matches manual marketplace view in >= 90% of tested eligible cases
- challenge/session-expiry states fail safely
