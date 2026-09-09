from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    limit: int = Field(default=20, ge=1, le=60)
    collect_details: int = Field(default=10, ge=0, le=20)


class ListingCollectRequest(BaseModel):
    url: str


class SearchHitOut(BaseModel):
    item_id: str
    shop_id: str
    title: str
    url: str
    displayed_price: int | None


class CollectResponse(BaseModel):
    discovered: int
    variants_persisted: int
    results: list[SearchHitOut] = Field(default_factory=list)
