from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from app.domain.models.enums import (
    CargoType,
    ShipmentPriority,
    TransportMode,
)
from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route, RouteLeg
from app.domain.models.shipment import Shipment
from app.domain.optimization.constraints import ConstraintEngine
from app.domain.optimization.pipeline import RouteOptimizer
from app.domain.optimization.scoring import ScoringEngine


@pytest.fixture
def base_shipment():
    now = datetime.now(timezone.utc)
    return Shipment(
        id=uuid4(),
        origin="Shanghai",
        destination="LA",
        cargo_type=CargoType.GENERAL,
        weight=1000.0,
        shipment_value=10000.0,
        delivery_deadline=now + timedelta(days=20),
        priority=ShipmentPriority.STANDARD,
        created_at=now,
        updated_at=now,
    )


def make_route(shipment_id, cost, time, rel, risk):
    return Route(
        id=uuid4(),
        shipment_id=shipment_id,
        route_name="Route",
        total_cost=cost,
        transit_time=time,
        delay_probability=1.0 - rel,
        reliability=rel,
        aggregate_risk=risk,
        legs=[
            RouteLeg(
                sequence=1,
                origin="A",
                destination="B",
                transport_mode=TransportMode.SEA,
                duration=time,
                cost=cost,
            )
        ],
    )


@pytest.fixture
def optimizer():
    return RouteOptimizer(
        constraint_engine=ConstraintEngine(), scoring_engine=ScoringEngine()
    )


@pytest.fixture
def profile():
    return OptimizationProfile(
        name="Balanced",
        cost_weight=0.25,
        time_weight=0.25,
        reliability_weight=0.25,
        risk_weight=0.25,
    )


def test_pipeline_multiple_feasible(optimizer, base_shipment, profile):
    r1 = make_route(base_shipment.id, 1000, 10, 0.9, 0.1)  # Best cost
    r2 = make_route(base_shipment.id, 2000, 5, 0.9, 0.1)  # Best time
    r3 = make_route(base_shipment.id, 3000, 15, 0.5, 0.5)  # Worst everything

    result, _routes = optimizer.optimize(base_shipment, [r1, r2, r3], profile)

    assert result.recommended_route_id is not None
    assert len(result.feasible_routes) == 3
    assert len(result.infeasible_routes) == 0
    assert result.profile == profile
    assert result.feasible_routes[2] == r3.id  # Worst route is last


def test_pipeline_infeasible_excluded(base_shipment, profile):
    r1 = make_route(base_shipment.id, 1000, 10, 0.9, 0.1)
    r2 = make_route(base_shipment.id, 2000, 25, 0.9, 0.1)  # Violates 20 day deadline

    opt = RouteOptimizer(ConstraintEngine(), ScoringEngine())
    result, _routes = opt.optimize(base_shipment, [r1, r2], profile)

    assert result.recommended_route_id == r1.id
    assert result.feasible_routes == [r1.id]
    assert result.infeasible_routes == [r2.id]
    assert r2.id in result.constraint_results
    assert "DELIVERY_DEADLINE_EXCEEDED" in result.constraint_results[r2.id][0]

    # Check score breakdown
    assert r1.id in result.route_scores
    assert r2.id not in result.route_scores


def test_all_routes_infeasible(optimizer, base_shipment, profile):
    r1 = make_route(base_shipment.id, 1000, 25, 0.9, 0.1)  # Violates deadline
    r2 = make_route(base_shipment.id, 2000, 30, 0.9, 0.1)  # Violates deadline

    result, _routes = optimizer.optimize(base_shipment, [r1, r2], profile)

    assert result.recommended_route_id is None
    assert len(result.feasible_routes) == 0
    assert len(result.infeasible_routes) == 2
    assert result.route_scores == {}
    assert result.score_breakdown == {}


def test_tie_breaking(optimizer, base_shipment, profile):
    # Identical metrics meaning exact same score. Tie breaking should prioritize lower cost.
    make_route(base_shipment.id, 1000, 10, 0.9, 0.1)
    make_route(base_shipment.id, 1000, 10, 0.9, 0.1)

    # We will force tie break by cost if they had different costs but somehow same score
    # (not possible with same weights, but we can set weights to 0)
    profile_zero_cost = OptimizationProfile(
        name="Zero Cost",
        cost_weight=0.0,
        time_weight=0.5,
        reliability_weight=0.5,
        risk_weight=0.0,
    )

    # r3 and r4 have same time and reliability (so same score), but r3 is cheaper.
    # Tie breaking says cost wins.
    r3 = make_route(base_shipment.id, 500, 10, 0.9, 0.1)
    r4 = make_route(base_shipment.id, 2000, 10, 0.9, 0.1)

    result, _routes = optimizer.optimize(base_shipment, [r3, r4], profile_zero_cost)

    # They should tie in score
    assert result.route_scores[r3.id] == result.route_scores[r4.id]

    # r3 should win due to tie-breaker preferring lower cost
    assert result.recommended_route_id == r3.id
    assert result.feasible_routes == [r3.id, r4.id]


def test_deterministic_repeated_optimization(optimizer, base_shipment, profile):
    r1 = make_route(base_shipment.id, 1000, 10, 0.9, 0.1)
    r2 = make_route(base_shipment.id, 2000, 5, 0.8, 0.2)

    routes_list = [r1, r2]

    result1, _ = optimizer.optimize(base_shipment, routes_list, profile)
    result2, _ = optimizer.optimize(base_shipment, routes_list, profile)

    assert result1.recommended_route_id == result2.recommended_route_id
    assert result1.feasible_routes == result2.feasible_routes
    assert result1.route_scores == result2.route_scores
    assert result1.score_breakdown == result2.score_breakdown
