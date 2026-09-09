from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from dealhunter.db.security_models import IntegrationConfig, MarketplaceAccount
from dealhunter.services.security import decrypt_secret, encrypt_secret, mask_secret


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_integration(db: Session, kind: str, name: str = "default") -> IntegrationConfig | None:
    return db.scalar(
        select(IntegrationConfig).where(
            IntegrationConfig.kind == kind,
            IntegrationConfig.name == name,
        )
    )


def upsert_integration(
    db: Session,
    *,
    kind: str,
    name: str = "default",
    provider: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
    secret: str | None = None,
    config: dict | None = None,
    enabled: bool = True,
    preserve_secret_when_blank: bool = True,
) -> IntegrationConfig:
    row = get_integration(db, kind, name)
    now = _utcnow()
    if row is None:
        row = IntegrationConfig(kind=kind, name=name, created_at=now, updated_at=now)
        db.add(row)
    row.provider = provider
    row.base_url = base_url
    row.model_name = model_name
    row.config_json = config or {}
    row.enabled = enabled
    row.updated_at = now
    if secret:
        row.secret_encrypted = encrypt_secret(secret)
    elif not preserve_secret_when_blank:
        row.secret_encrypted = None
    db.commit()
    db.refresh(row)
    return row


def reveal_integration_secret(row: IntegrationConfig | None) -> str | None:
    return decrypt_secret(row.secret_encrypted) if row else None


def safe_integration(row: IntegrationConfig | None) -> dict:
    if row is None:
        return {"configured": False}
    secret = reveal_integration_secret(row)
    return {
        "configured": True,
        "id": str(row.id),
        "kind": row.kind,
        "name": row.name,
        "provider": row.provider,
        "base_url": row.base_url,
        "model": row.model_name,
        "enabled": row.enabled,
        "secret_masked": mask_secret(secret),
        "config": row.config_json or {},
        "updated_at": row.updated_at,
    }


def get_marketplace_account(
    db: Session,
    platform: str,
    label: str = "default",
) -> MarketplaceAccount | None:
    return db.scalar(
        select(MarketplaceAccount).where(
            MarketplaceAccount.platform == platform,
            MarketplaceAccount.label == label,
        )
    )


def upsert_marketplace_account(
    db: Session,
    *,
    platform: str,
    label: str = "default",
    profile_dir: str,
    browser_login_url: str | None = None,
    state: str | None = None,
    account_hint: str | None = None,
    metadata: dict | None = None,
) -> MarketplaceAccount:
    row = get_marketplace_account(db, platform, label)
    now = _utcnow()
    if row is None:
        row = MarketplaceAccount(
            platform=platform,
            label=label,
            profile_dir=profile_dir,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    row.profile_dir = profile_dir
    row.browser_login_url = browser_login_url
    if state is not None:
        row.state = state
    if account_hint is not None:
        row.account_hint = account_hint
    if metadata is not None:
        row.metadata_json = metadata
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return row


def safe_marketplace_account(row: MarketplaceAccount | None) -> dict:
    if row is None:
        return {"configured": False, "state": "not_connected"}
    return {
        "configured": True,
        "id": str(row.id),
        "platform": row.platform,
        "label": row.label,
        "profile_dir": row.profile_dir,
        "browser_login_url": row.browser_login_url,
        "state": row.state,
        "account_hint": row.account_hint,
        "last_checked_at": row.last_checked_at,
        "updated_at": row.updated_at,
    }
