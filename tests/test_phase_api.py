from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from dealhunter.api.v1.routes_phase2_10 import router
from dealhunter.db import Base
from dealhunter.db.session import get_db


def _client() -> TestClient:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = Session(engine)

    def override_db():
        try:
            yield session
        finally:
            pass

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_phase_routes_boot_and_promotions_work():
    client = _client()
    response = client.post(
        "/api/v1/promotions/evaluate",
        json={
            "observed_price": 2_500_000,
            "vouchers": [
                {
                    "code": "v20",
                    "discount_type": "percent",
                    "discount_value": 20,
                    "max_discount": 500_000,
                    "min_spend": 1_500_000,
                    "stack_group": "platform",
                }
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 2_000_000


def test_ai_catalog_route():
    client = _client()
    response = client.get("/api/v1/ai/tools")
    assert response.status_code == 200
    assert any(tool["name"] == "get_deals" for tool in response.json()["tools"])
