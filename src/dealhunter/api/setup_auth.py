from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import httpx
import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from dealhunter.core.config import get_settings
from dealhunter.db.security_models import AdminUser, SetupState
from dealhunter.db.session import get_db
from dealhunter.providers.errors import ProviderError
from dealhunter.providers.shopee.transport import ChromeJsonTransport
from dealhunter.services.security import (
    SESSION_COOKIE,
    create_session,
    get_session_user,
    hash_password,
    normalize_email,
    revoke_session,
    setup_complete,
    setup_state,
    verify_password,
)
from dealhunter.services.settings_store import (
    get_integration,
    get_marketplace_account,
    reveal_integration_secret,
    safe_integration,
    safe_marketplace_account,
    upsert_integration,
    upsert_marketplace_account,
)

router = APIRouter(prefix="/api/v1", tags=["setup-auth-settings"])


class SetupRequest(BaseModel):
    admin_email: str = Field(min_length=5, max_length=320)
    admin_password: str = Field(min_length=10, max_length=200)
    display_name: str = Field(default="Administrator", min_length=2, max_length=160)
    app_url: str | None = None
    timezone: str = "Asia/Ho_Chi_Minh"
    language: str = "vi"
    ai_provider: str | None = "openai_compatible"
    ai_base_url: str | None = None
    ai_api_key: str | None = None
    ai_model: str | None = None
    browser_login_url: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class GeneralSettingsInput(BaseModel):
    app_url: str | None = None
    timezone: str = "Asia/Ho_Chi_Minh"
    language: str = "vi"


class AISettingsInput(BaseModel):
    provider: str = "openai_compatible"
    base_url: str = Field(min_length=4)
    api_key: str | None = None
    model: str | None = None
    enabled: bool = True


class TelegramSettingsInput(BaseModel):
    bot_token: str | None = None
    chat_id: str | None = None
    enabled: bool = True


class AffiliateSettingsInput(BaseModel):
    provider: str = "generic"
    api_key: str | None = None
    enabled: bool = True
    config: dict = Field(default_factory=dict)


class ShopeeSettingsInput(BaseModel):
    base_url: str = "https://shopee.vn"
    transport: str = "chrome"
    profile_dir: str | None = None
    browser_login_url: str | None = None


def _set_session_cookie(response: JSONResponse, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max(1, settings.session_days) * 86400,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )


def require_user(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    user = get_session_user(db, request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail={"code": "authentication_required"})
    return user


def _account_hint(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 4:
        return value[0] + "•••"
    return f"{value[:2]}•••{value[-2:]}"


@router.get("/setup/status")
def get_setup_status(db: Session = Depends(get_db)):
    row = setup_state(db)
    settings = get_settings()
    return {
        "complete": bool(row and row.complete),
        "app_url": row.app_url if row else None,
        "timezone": row.timezone if row else "Asia/Ho_Chi_Minh",
        "language": row.language if row else "vi",
        "chrome_profile_dir": settings.chrome_profile_dir,
        "browser_login_url": settings.browser_login_public_url,
    }


@router.post("/setup/complete")
def complete_setup(payload: SetupRequest, db: Session = Depends(get_db)):
    if setup_complete(db):
        raise HTTPException(status_code=409, detail="setup already completed")
    email = normalize_email(payload.admin_email)
    if "@" not in email:
        raise HTTPException(status_code=422, detail="invalid admin email")
    if db.scalar(select(AdminUser).where(AdminUser.email == email)) is not None:
        raise HTTPException(status_code=409, detail="admin already exists")

    user = AdminUser(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.admin_password),
        active=True,
    )
    db.add(user)
    state = SetupState(
        id=1,
        complete=True,
        app_url=payload.app_url.rstrip("/") if payload.app_url else None,
        timezone=payload.timezone,
        language=payload.language,
        completed_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(state)
    db.commit()
    db.refresh(user)

    settings = get_settings()
    if payload.ai_base_url:
        upsert_integration(
            db,
            kind="ai",
            provider=payload.ai_provider or "openai_compatible",
            base_url=payload.ai_base_url.rstrip("/"),
            model_name=payload.ai_model,
            secret=payload.ai_api_key,
            config={},
            enabled=True,
        )
    upsert_marketplace_account(
        db,
        platform="shopee",
        profile_dir=settings.chrome_profile_dir,
        browser_login_url=payload.browser_login_url or settings.browser_login_public_url,
        state="not_connected",
        metadata={"base_url": settings.shopee_base_url, "transport": "chrome"},
    )

    token, _ = create_session(db, user)
    response = JSONResponse(
        {
            "complete": True,
            "user": {"email": user.email, "display_name": user.display_name},
            "next": "/",
        }
    )
    _set_session_cookie(response, token)
    return response


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(AdminUser).where(AdminUser.email == normalize_email(payload.email)))
    if user is None or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")
    token, _ = create_session(db, user)
    response = JSONResponse(
        {"authenticated": True, "user": {"email": user.email, "display_name": user.display_name}}
    )
    _set_session_cookie(response, token)
    return response


@router.post("/auth/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    revoke_session(db, request.cookies.get(SESSION_COOKIE))
    response = JSONResponse({"authenticated": False})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/auth/me")
def me(user: AdminUser = Depends(require_user)):
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name}


@router.get("/settings")
def all_settings(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    state = setup_state(db)
    shopee = get_marketplace_account(db, "shopee")
    return {
        "general": {
            "app_url": state.app_url if state else None,
            "timezone": state.timezone if state else "Asia/Ho_Chi_Minh",
            "language": state.language if state else "vi",
        },
        "ai": safe_integration(get_integration(db, "ai")),
        "telegram": safe_integration(get_integration(db, "telegram")),
        "affiliate": safe_integration(get_integration(db, "affiliate")),
        "shopee": safe_marketplace_account(shopee),
    }


@router.put("/settings/general")
def save_general(
    payload: GeneralSettingsInput,
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    state = setup_state(db)
    if state is None:
        raise HTTPException(status_code=409, detail="setup not complete")
    state.app_url = payload.app_url.rstrip("/") if payload.app_url else None
    state.timezone = payload.timezone
    state.language = payload.language
    state.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"saved": True}


@router.put("/settings/ai")
def save_ai(
    payload: AISettingsInput,
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = upsert_integration(
        db,
        kind="ai",
        provider=payload.provider,
        base_url=payload.base_url.rstrip("/"),
        model_name=payload.model,
        secret=payload.api_key,
        config={},
        enabled=payload.enabled,
    )
    return safe_integration(row)


@router.post("/settings/ai/test")
async def test_ai(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = get_integration(db, "ai")
    if row is None or not row.base_url:
        raise HTTPException(status_code=409, detail="AI provider is not configured")
    token = reveal_integration_secret(row)
    provider = (row.provider or "openai_compatible").lower()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if provider == "ollama":
        url = f"{row.base_url.rstrip('/')}/api/tags"
    else:
        url = f"{row.base_url.rstrip('/')}/models"
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"AI provider returned HTTP {response.status_code}")
        return {"ok": True, "provider": provider, "model": row.model_name, "endpoint": url}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider connection failed: {exc}") from exc


@router.put("/settings/telegram")
def save_telegram(
    payload: TelegramSettingsInput,
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = upsert_integration(
        db,
        kind="telegram",
        provider="telegram",
        secret=payload.bot_token,
        config={"chat_id": payload.chat_id},
        enabled=payload.enabled,
    )
    return safe_integration(row)


@router.post("/settings/telegram/test")
async def test_telegram(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = get_integration(db, "telegram")
    token = reveal_integration_secret(row)
    if row is None or not token:
        raise HTTPException(status_code=409, detail="Telegram bot token is not configured")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
        data = response.json()
        if not response.is_success or not data.get("ok"):
            raise HTTPException(status_code=502, detail="Telegram rejected the configured bot token")
        return {"ok": True, "bot": data.get("result", {}).get("username")}
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Telegram connection failed: {exc}") from exc


@router.put("/settings/affiliate")
def save_affiliate(
    payload: AffiliateSettingsInput,
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = upsert_integration(
        db,
        kind="affiliate",
        provider=payload.provider,
        secret=payload.api_key,
        config=payload.config,
        enabled=payload.enabled,
    )
    return safe_integration(row)


@router.put("/settings/marketplaces/shopee")
def save_shopee(
    payload: ShopeeSettingsInput,
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    settings = get_settings()
    row = upsert_marketplace_account(
        db,
        platform="shopee",
        profile_dir=payload.profile_dir or settings.chrome_profile_dir,
        browser_login_url=payload.browser_login_url,
        metadata={"base_url": payload.base_url.rstrip("/"), "transport": payload.transport},
    )
    return safe_marketplace_account(row)


@router.get("/settings/marketplaces/shopee/connect")
def shopee_connect_info(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    row = get_marketplace_account(db, "shopee")
    if row is None:
        raise HTTPException(status_code=409, detail="Shopee marketplace is not configured")
    return {
        "state": row.state,
        "browser_login_url": row.browser_login_url,
        "command": "docker compose --profile browser-login up -d shopee-browser-login",
        "after_login": "Close/stop the browser-login service before testing or collecting so Chrome can reuse the same persistent profile.",
    }


@router.post("/settings/marketplaces/shopee/test")
async def test_shopee_account(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    settings = get_settings()
    row = get_marketplace_account(db, "shopee")
    if row is None:
        row = upsert_marketplace_account(
            db,
            platform="shopee",
            profile_dir=settings.chrome_profile_dir,
            browser_login_url=settings.browser_login_public_url,
            metadata={"base_url": settings.shopee_base_url, "transport": "chrome"},
        )
    meta = row.metadata_json or {}
    base_url = str(meta.get("base_url") or settings.shopee_base_url).rstrip("/")
    transport = ChromeJsonTransport(
        base_url,
        timeout=settings.shopee_timeout_seconds,
        profile_dir=row.profile_dir,
        headless=settings.chrome_headless,
        executable_path=settings.chrome_executable_path,
    )
    try:
        payload = await transport.get_json(f"{base_url}/api/v4/account/basic/get_account_info")
        data = payload.get("data") if isinstance(payload, dict) else None
        username = None
        if isinstance(data, dict):
            username = data.get("username") or data.get("user_name") or data.get("nickname")
        row.last_checked_at = datetime.now(timezone.utc)
        if username or (isinstance(data, dict) and data.get("userid")):
            row.state = "connected"
            row.account_hint = _account_hint(str(username or data.get("userid")))
            db.commit()
            return {"ok": True, "state": row.state, "account_hint": row.account_hint}
        row.state = "not_connected"
        row.account_hint = None
        db.commit()
        return {
            "ok": False,
            "state": row.state,
            "message": "Chrome profile is reachable but no logged-in Shopee account was detected.",
        }
    except ProviderError as exc:
        row.last_checked_at = datetime.now(timezone.utc)
        row.state = "error"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Shopee session test failed: {exc}") from exc
    finally:
        await transport.aclose()


@router.get("/settings/system")
async def system_status(
    db: Session = Depends(get_db),
    _user: AdminUser = Depends(require_user),
):
    settings = get_settings()
    database_ok = False
    redis_ok = False
    try:
        db.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        redis_ok = bool(await client.ping())
        await client.aclose()
    except Exception:
        redis_ok = False
    chrome_path = settings.chrome_executable_path or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    return {
        "database": {"ok": database_ok},
        "redis": {"ok": redis_ok},
        "chrome": {"ok": bool(chrome_path), "path": chrome_path},
        "chrome_profile": {"path": settings.chrome_profile_dir, "exists": Path(settings.chrome_profile_dir).exists()},
        "setup_complete": setup_complete(db),
    }
