from fastapi.testclient import TestClient

from dealhunter.main import app


def test_home_renders_modern_deal_radar_shell():
    response = TestClient(app).get("/")
    assert response.status_code == 200
    html = response.text
    assert "DealHunter" in html
    assert "Tìm deal ngon" in html
    assert "Deal Radar" in html
    assert "Smart Deal Discovery" in html
