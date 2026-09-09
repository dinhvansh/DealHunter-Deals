from fastapi.testclient import TestClient

from dealhunter.main import app


def test_fresh_install_redirects_to_setup():
    client = TestClient(app, follow_redirects=False)
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/setup"


def test_setup_page_renders_first_run_wizard():
    response = TestClient(app).get("/setup")
    assert response.status_code == 200
    html = response.text
    assert "DealHunter" in html
    assert "Cài lần đầu" in html
    assert "AI Provider" in html
    assert "Kết nối Shopee" in html
