from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dealhunter.core.config import get_settings
from dealhunter.db.session import SessionLocal
from dealhunter.providers.errors import ProviderError
from dealhunter.providers.shopee import ShopeeProvider
from dealhunter.services.collector import CollectorService
from dealhunter.services.settings_store import get_marketplace_account

from .schemas import CollectResponse, ListingCollectRequest, SearchHitOut, SearchRequest

router = APIRouter(prefix="/api/v1")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_provider(db: Session | None = None) -> ShopeeProvider:
    settings = get_settings()
    base_url = settings.shopee_base_url
    transport_mode = settings.shopee_transport
    profile_dir = settings.chrome_profile_dir
    if db is not None:
        account = get_marketplace_account(db, "shopee")
        if account is not None:
            meta = account.metadata_json or {}
            base_url = str(meta.get("base_url") or base_url)
            transport_mode = str(meta.get("transport") or transport_mode)
            profile_dir = account.profile_dir or profile_dir
    return ShopeeProvider(
        base_url=base_url,
        transport_mode=transport_mode,
        timeout=settings.shopee_timeout_seconds,
        chrome_profile_dir=profile_dir,
        chrome_headless=settings.chrome_headless,
        chrome_executable_path=settings.chrome_executable_path,
    )


@router.post("/internal/collect/search", response_model=CollectResponse)
async def collect_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    provider = build_provider(db)
    try:
        hits, persisted = await CollectorService(provider, db).discover_and_collect(
            request.query,
            request.limit,
            request.collect_details,
        )
        return CollectResponse(
            discovered=len(hits),
            variants_persisted=persisted,
            results=[
                SearchHitOut(
                    item_id=hit.external_item_id,
                    shop_id=hit.external_shop_id,
                    title=hit.title,
                    url=hit.url,
                    displayed_price=hit.displayed_price,
                )
                for hit in hits
            ],
        )
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await provider.aclose()


@router.post("/internal/collect/listing", response_model=CollectResponse)
async def collect_listing(
    request: ListingCollectRequest,
    db: Session = Depends(get_db),
):
    provider = build_provider(db)
    try:
        persisted = await CollectorService(provider, db).collect_listing(request.url)
        return CollectResponse(discovered=1, variants_persisted=persisted)
    except (ProviderError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await provider.aclose()
