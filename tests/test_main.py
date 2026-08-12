import pytest
from fastapi.testclient import TestClient
from main import app, Base, engine, SessionLocal

# Setup a clean test database
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Workspace Bunny" in response.text

def test_info_endpoint():
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "Bunny App"
    assert "version" in data

def test_crud_flow():
    # 1. Create a record
    response = client.post("/add", data={"name": "Test User", "message": "Test Secret"})
    assert response.status_code == 200
    # FastApi RedirectResponse returns 200 via TestClient because it follows redirects automatically.

    # 2. Read the record via API
    api_resp = client.get("/api/records")
    assert api_resp.status_code == 200
    records = api_resp.json()
    assert len(records) > 0
    test_record = next(r for r in records if r["name"] == "Test User")
    assert test_record["message"] == "Test Secret"

    # 3. Delete the record
    del_resp = client.post(f"/delete/{test_record['id']}")
    assert del_resp.status_code == 200
    
    # 4. Verify deletion
    api_resp_after = client.get("/api/records")
    records_after = api_resp_after.json()
    assert not any(r["id"] == test_record['id'] for r in records_after)
