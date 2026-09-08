import re

with open('backend/tests/api/test_routes.py', 'r') as f:
    content = f.read()

additions = """
def test_update_route(client, shipment_id):
    routes_payload = [{
        "route_name": "Fast Route",
        "total_cost": 5000,
        "transit_time": 10,
        "delay_probability": 0.1,
        "reliability": 0.9,
        "aggregate_risk": 0.1,
        "legs": []
    }]
    resp = client.post(f"/api/v1/shipments/{shipment_id}/routes", json=routes_payload)
    route_id = resp.json()[0]["id"]

    update_payload = {
        "route_name": "Updated Route",
        "total_cost": 6000,
        "transit_time": 12,
        "delay_probability": 0.2,
        "reliability": 0.8,
        "aggregate_risk": 0.2,
        "legs": [
            {
                "sequence": 1,
                "origin": "A",
                "destination": "B",
                "transport_mode": "AIR",
                "duration": 12,
                "cost": 6000,
                "risk_factors": []
            }
        ]
    }
    resp = client.put(f"/api/v1/shipments/{shipment_id}/routes/{route_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["route_name"] == "Updated Route"
    assert data["total_cost"] == 6000
    assert len(data["legs"]) == 1
    assert data["legs"][0]["duration"] == 12

def test_delete_route(client, shipment_id):
    routes_payload = [{
        "route_name": "To Delete",
        "total_cost": 5000,
        "transit_time": 10,
        "delay_probability": 0.1,
        "reliability": 0.9,
        "aggregate_risk": 0.1,
        "legs": []
    }]
    resp = client.post(f"/api/v1/shipments/{shipment_id}/routes", json=routes_payload)
    route_id = resp.json()[0]["id"]

    resp = client.delete(f"/api/v1/shipments/{shipment_id}/routes/{route_id}")
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/shipments/{shipment_id}/routes")
    assert len(resp.json()) == 0

def test_update_route_not_found(client, shipment_id):
    import uuid
    update_payload = {
        "route_name": "Updated Route",
        "total_cost": 6000,
        "transit_time": 12,
        "delay_probability": 0.2,
        "reliability": 0.8,
        "aggregate_risk": 0.2,
        "legs": []
    }
    resp = client.put(f"/api/v1/shipments/{shipment_id}/routes/{uuid.uuid4()}", json=update_payload)
    assert resp.status_code == 404

def test_delete_route_not_found(client, shipment_id):
    import uuid
    resp = client.delete(f"/api/v1/shipments/{shipment_id}/routes/{uuid.uuid4()}")
    assert resp.status_code == 404
"""

content += additions

with open('backend/tests/api/test_routes.py', 'w') as f:
    f.write(content)
