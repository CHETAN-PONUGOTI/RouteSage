from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def shipment_id(client):
    now = datetime.now(timezone.utc)
    payload = {
        "origin": "A", "destination": "B", "cargo_type": "GENERAL",
        "weight": 100, "shipment_value": 100, 
        "delivery_deadline": (now + timedelta(days=1)).isoformat(),
        "priority": "STANDARD"
    }
    resp = client.post("/api/v1/shipments", json=payload)
    return resp.json()["id"]

def test_create_routes(client, shipment_id):
    routes_payload = [
        {
            "route_name": "Fast Route",
            "total_cost": 5000,
            "transit_time": 10,
            "delay_probability": 0.1,
            "reliability": 0.9,
            "aggregate_risk": 0.1,
            "legs": [
                {
                    "sequence": 1,
                    "origin": "A",
                    "destination": "B",
                    "transport_mode": "AIR",
                    "duration": 10,
                    "cost": 5000,
                    "risk_factors": []
                }
            ]
        }
    ]
    
    resp = client.post(f"/api/v1/shipments/{shipment_id}/routes", json=routes_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 1
    assert data[0]["route_name"] == "Fast Route"
    assert "id" in data[0]

def test_get_routes(client, shipment_id):
    routes_payload = [
        {
            "route_name": "Fast Route",
            "total_cost": 5000,
            "transit_time": 10,
            "delay_probability": 0.1,
            "reliability": 0.9,
            "aggregate_risk": 0.1,
            "legs": [
                {
                    "sequence": 1,
                    "origin": "A",
                    "destination": "B",
                    "transport_mode": "AIR",
                    "duration": 10,
                    "cost": 5000,
                    "risk_factors": []
                }
            ]
        }
    ]
    client.post(f"/api/v1/shipments/{shipment_id}/routes", json=routes_payload)
    
    resp = client.get(f"/api/v1/shipments/{shipment_id}/routes")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_create_routes_shipment_not_found(client):
    import uuid
    resp = client.post(f"/api/v1/shipments/{uuid.uuid4()}/routes", json=[])
    assert resp.status_code == 404
