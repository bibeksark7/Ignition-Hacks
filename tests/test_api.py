from fastapi.testclient import TestClient

from pricing.api import app
from tests.test_pricing import SAMPLE_CONTRACT_A

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_list_demo_fixtures():
    r = client.get("/demo")
    assert r.status_code == 200
    assert set(r.json()["fixtures"]) == {"high_risk_wildfire_house", "low_risk_house", "moderate_flood_house"}


def test_get_demo_fixture():
    r = client.get("/demo/low_risk_house")
    assert r.status_code == 200
    body = r.json()
    assert "contract_a" in body and "contract_b" in body
    assert 0 <= body["contract_b"]["risk_score"]["overall"] <= 100


def test_get_demo_fixture_unknown_name_404s():
    r = client.get("/demo/does_not_exist")
    assert r.status_code == 404


def test_post_price_valid_contract():
    r = client.post("/price", json=SAMPLE_CONTRACT_A)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["risk_score"]["overall"] <= 100
    assert body["annual_premium"] > 0


def test_post_price_missing_required_field_returns_422():
    bad = dict(SAMPLE_CONTRACT_A)
    del bad["roof_area_m2"]
    r = client.post("/price", json=bad)
    assert r.status_code == 422


def test_post_price_out_of_range_field_returns_422():
    bad = dict(SAMPLE_CONTRACT_A, canopy_overlap_pct=150)
    r = client.post("/price", json=bad)
    assert r.status_code == 422
