from fastapi import FastAPI
from fastapi.testclient import TestClient

from dealhunter.api.v1.routes_phase2_10 import router


def test_phase_routes_boot_and_promotions_work():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
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
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.get("/api/v1/ai/tools")
    assert response.status_code == 200
    assert any(tool["name"] == "get_deals" for tool in response.json()["tools"])
