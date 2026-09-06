from datetime import datetime, timedelta, timezone


def test_create_shipment(client):
    now = datetime.now(timezone.utc)
    payload = {
        "origin": "Shanghai",
        "destination": "Rotterdam",
        "cargo_type": "GENERAL",
        "weight": 2500.0,
        "shipment_value": 50000.0,
        "delivery_deadline": (now + timedelta(days=10)).isoformat(),
        "priority": "STANDARD"
    }
    
    response = client.post("/api/v1/shipments", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["origin"] == "Shanghai"
    assert data["cargo_type"] == "GENERAL"

def test_get_shipment(client):
    now = datetime.now(timezone.utc)
    payload = {
        "origin": "A", "destination": "B", "cargo_type": "GENERAL",
        "weight": 100, "shipment_value": 100, 
        "delivery_deadline": (now + timedelta(days=1)).isoformat(),
        "priority": "STANDARD"
    }
    create_resp = client.post("/api/v1/shipments", json=payload)
    shipment_id = create_resp.json()["id"]
    
    get_resp = client.get(f"/api/v1/shipments/{shipment_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == shipment_id

def test_get_shipment_not_found(client):
    import uuid
    response = client.get(f"/api/v1/shipments/{uuid.uuid4()}")
    assert response.status_code == 404

def test_list_shipments(client):
    now = datetime.now(timezone.utc)
    payload = {
        "origin": "A", "destination": "B", "cargo_type": "GENERAL",
        "weight": 100, "shipment_value": 100, 
        "delivery_deadline": (now + timedelta(days=1)).isoformat(),
        "priority": "STANDARD"
    }
    client.post("/api/v1/shipments", json=payload)
    client.post("/api/v1/shipments", json=payload)
    
    resp = client.get("/api/v1/shipments")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2
