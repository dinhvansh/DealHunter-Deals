from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class VerificationResult:
    state: str
    observed_price: int
    estimated_price: int | None = None
    verified_price: int | None = None
    applied_promotions: list[dict] = field(default_factory=list)
    confidence: float = 0.0
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    failure_reason: str | None = None


class AccountVerifier:
    async def verify(self, variant_id: str) -> VerificationResult:
        raise NotImplementedError


class DisabledVerifier(AccountVerifier):
    async def verify(self, variant_id: str) -> VerificationResult:
        return VerificationResult(
            state="failed",
            observed_price=0,
            confidence=0.0,
            failure_reason="account_verification_not_configured",
        )
