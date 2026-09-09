from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from dealhunter.core.config import get_settings
from dealhunter.db.security_models import AdminUser, AuthSession, SetupState
from dealhunter.db.models import utcnow

SESSION_COOKIE = "dealhunter_session"


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_email(value: str) -> str:
    return value.strip().lower()


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("password must be at least 10 characters")
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = encoded.split("$", 5)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: AdminUser) -> tuple[str, AuthSession]:
    settings = get_settings()
    token = secrets.token_urlsafe(48)
    now = utcnow()
    row = AuthSession(
        user_id=user.id,
        token_hash=token_hash(token),
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=max(1, settings.session_days)),
    )
    user.last_login_at = now
    db.add(row)
    db.commit()
    db.refresh(row)
    return token, row


def get_session_user(db: Session, token: str | None) -> AdminUser | None:
    if not token:
        return None
    now = datetime.now(timezone.utc)
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    if row is None or row.revoked_at is not None or _as_utc(row.expires_at) <= now:
        return None
    user = db.get(AdminUser, row.user_id)
    if user is None or not user.active:
        return None
    row.last_seen_at = utcnow()
    db.commit()
    return user


def revoke_session(db: Session, token: str | None) -> None:
    if not token:
        return
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    if row is not None and row.revoked_at is None:
        row.revoked_at = utcnow()
        db.commit()


def setup_state(db: Session) -> SetupState | None:
    return db.get(SetupState, 1)


def setup_complete(db: Session) -> bool:
    row = setup_state(db)
    return bool(row and row.complete)


def _master_key_bytes() -> bytes:
    settings = get_settings()
    if settings.secret_key:
        raw = settings.secret_key.strip().encode("utf-8")
        try:
            decoded = base64.urlsafe_b64decode(raw)
            if len(decoded) == 32:
                return raw
        except Exception:
            pass
        return base64.urlsafe_b64encode(hashlib.sha256(raw).digest())

    key_path = Path(settings.secret_key_file)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        return key_path.read_bytes().strip()
    key = Fernet.generate_key()
    key_path.write_bytes(key + b"\n")
    try:
        key_path.chmod(0o600)
    except OSError:
        pass
    return key


def encrypt_secret(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return Fernet(_master_key_bytes()).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return Fernet(_master_key_bytes()).decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("stored secret cannot be decrypted with the configured master key") from exc


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "••••••••"
    return f"{value[:3]}••••••{value[-4:]}"
