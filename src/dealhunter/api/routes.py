from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dealhunter.core.config import get_settings
from dealhunter.db.session import SessionLocal
from dealhunter.providers.errors import ProviderError
from dealhunter.providers.shopee import ShopeeProvider
from dealhunter.services.collector import CollectorService

from .schemas import CollectResponse, ListingCollectRequest, SearchHitOut, SearchRequest

router = APIRouter(prefix="/api/v1")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_provider() -> ShopeeProvider:
    settings = get_settings()
    return ShopeeProvider(
        base_url=settings.shopee_base_url,
        transport_mode=settings.shopee_transport,
        timeout=settings.shopee_timeout_seconds,
    )


@router.post("/internal/collect/search", response_model=CollectResponse)
async def collect_search(
    request: SearchRequest,
    db: Session = Depends(get_db),
):
    provider = build_provider()
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
    provider = build_provider()
    try:
        persisted = await CollectorService(provider, db).collect_listing(request.url)
        return CollectResponse(discovered=1, variants_persisted=persisted)
    except (ProviderError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await provider.aclose()
