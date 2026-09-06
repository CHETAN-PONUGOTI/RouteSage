from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from app.api.routers.optimization import get_optimization_service
from app.domain.models.optimization import OptimizationProfile, OptimizationResult
from app.domain.models.route import Route, RouteLeg
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def make_leg():
    return RouteLeg(
        sequence=1,
        origin="A",
        destination="B",
        transport_mode="AIR",
        duration=5,
        cost=500,
    )


def make_route(shipment_id, name="Route A"):
    return Route(
        id=uuid4(),
        shipment_id=shipment_id,
        route_name=name,
        total_cost=1000,
        transit_time=24,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=0.3,
        legs=[make_leg()],
    )


def make_result(shipment_id, route_id):
    profile = OptimizationProfile(
        name="test",
        cost_weight=0.4,
        time_weight=0.3,
        reliability_weight=0.2,
        risk_weight=0.1,
    )
    return OptimizationResult(
        id=uuid4(),
        shipment_id=shipment_id,
        profile=profile,
        recommended_route_id=route_id,
        feasible_routes=[route_id],
        route_scores={route_id: 0.75},
        score_breakdown={
            route_id: {"cost": 0.3, "time": 0.2, "reliability": 0.15, "risk": 0.1}
        },
        execution_time_ms=5.0,
    )


def test_explanation_endpoint_returns_404_for_unknown_run():
    fake_run_id = str(uuid4())
    # No dependency override means it hits the real repo and gets 404 if the repo is empty
    response = client.post(f"/api/v1/optimization-runs/{fake_run_id}/explanation")
    assert response.status_code == 404


def test_explanation_endpoint_does_not_rerun_optimization():
    """The explanation endpoint must never call run_optimization."""
    sid = uuid4()
    r1 = make_route(sid)
    result = make_result(sid, r1.id)

    mock_service = MagicMock()
    mock_service.get_optimization_result.return_value = result
    mock_service.get_routes.return_value = [r1]

    app.dependency_overrides[get_optimization_service] = lambda: mock_service

    try:
        response = client.post(f"/api/v1/optimization-runs/{result.id}/explanation")
        mock_service.run_optimization.assert_not_called()
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert "generated_by" in data
        assert data["generated_by"] == "deterministic"
    finally:
        app.dependency_overrides.pop(get_optimization_service, None)


def test_explanation_endpoint_uses_persisted_result():
    """Endpoint must load from persistence, not recalculate."""
    sid = uuid4()
    r1 = make_route(sid)
    result = make_result(sid, r1.id)

    mock_service = MagicMock()
    mock_service.get_optimization_result.return_value = result
    mock_service.get_routes.return_value = [r1]

    app.dependency_overrides[get_optimization_service] = lambda: mock_service

    try:
        response = client.post(f"/api/v1/optimization-runs/{result.id}/explanation")
        mock_service.get_optimization_result.assert_called_once_with(result.id)
        assert response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_optimization_service, None)
