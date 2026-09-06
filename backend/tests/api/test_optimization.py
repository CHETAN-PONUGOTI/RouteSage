from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def shipment_id(client):
    now = datetime.now(timezone.utc)
    payload = {
        "origin": "A", "destination": "B", "cargo_type": "GENERAL",
        "weight": 100, "shipment_value": 100, 
        "delivery_deadline": (now + timedelta(days=20)).isoformat(), # Plenty of time
        "priority": "STANDARD"
    }
    resp = client.post("/api/v1/shipments", json=payload)
    return resp.json()["id"]

@pytest.fixture
def shipment_with_routes(client, shipment_id):
    routes_payload = [
        {
            "route_name": "Fast Route",
            "total_cost": 5000,
            "transit_time": 10,
            "delay_probability": 0.1,
            "reliability": 0.9,
            "aggregate_risk": 0.1,
            "legs": [
                {"sequence":1, "origin":"A", "destination":"B", "transport_mode":"AIR", "duration":10, "cost":5000}
            ]
        },
        {
            "route_name": "Cheap Route",
            "total_cost": 1000,
            "transit_time": 15,
            "delay_probability": 0.2,
            "reliability": 0.8,
            "aggregate_risk": 0.2,
            "legs": [
                {"sequence":1, "origin":"A", "destination":"B", "transport_mode":"SEA", "duration":15, "cost":1000}
            ]
        }
    ]
    client.post(f"/api/v1/shipments/{shipment_id}/routes", json=routes_payload)
    return shipment_id

def test_full_optimization_flow(client, shipment_with_routes):
    shipment_id = shipment_with_routes
    opt_payload = {
        "profile": {
            "name": "Cost Focus",
            "cost_weight": 0.7,
            "time_weight": 0.1,
            "reliability_weight": 0.1,
            "risk_weight": 0.1
        }
    }
    
    resp = client.post(f"/api/v1/shipments/{shipment_id}/optimize", json=opt_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["shipment_id"] == shipment_id
    assert len(data["feasible_routes"]) == 2
    assert data["recommended_route_id"] is not None
    
    # Retrieve the run
    run_id = data["id"]
    get_resp = client.get(f"/api/v1/optimization-runs/{run_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == run_id
    assert get_data["recommended_route_id"] == data["recommended_route_id"]
    assert "cost focus" in get_data["profile"]["name"].lower()

def test_optimization_no_routes(client, shipment_id):
    opt_payload = {
        "profile": {
            "name": "Cost Focus",
            "cost_weight": 0.7,
            "time_weight": 0.1,
            "reliability_weight": 0.1,
            "risk_weight": 0.1
        }
    }
    resp = client.post(f"/api/v1/shipments/{shipment_id}/optimize", json=opt_payload)
    assert resp.status_code == 400
    assert "no routes" in resp.json()["detail"].lower()

def test_optimization_all_infeasible(client):
    now = datetime.now(timezone.utc)
    # Deadline in 1 day
    payload = {
        "origin": "A", "destination": "B", "cargo_type": "GENERAL",
        "weight": 100, "shipment_value": 100, 
        "delivery_deadline": (now + timedelta(days=1)).isoformat(),
        "priority": "STANDARD"
    }
    resp = client.post("/api/v1/shipments", json=payload)
    ship_id = resp.json()["id"]
    
    # Route takes 10 days
    routes_payload = [{
        "route_name": "Too Slow",
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
    }]
    client.post(f"/api/v1/shipments/{ship_id}/routes", json=routes_payload)
    
    opt_payload = {
        "profile": {
            "name": "Cost Focus",
            "cost_weight": 0.25,
            "time_weight": 0.25,
            "reliability_weight": 0.25,
            "risk_weight": 0.25
        }
    }
    opt_resp = client.post(f"/api/v1/shipments/{ship_id}/optimize", json=opt_payload)
    assert opt_resp.status_code == 200
    data = opt_resp.json()
    
    # Expected: No recommended route, all in infeasible_routes
    assert data["recommended_route_id"] is None
    assert len(data["feasible_routes"]) == 0
    assert len(data["infeasible_routes"]) == 1
    assert len(data["constraint_results"]) == 1 # 1 route violated
