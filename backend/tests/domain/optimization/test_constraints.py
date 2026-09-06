from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from app.domain.models.enums import (
    CargoType,
    FeasibilityStatus,
    ShipmentPriority,
    TransportMode,
)
from app.domain.models.route import Route, RouteLeg
from app.domain.models.shipment import Shipment
from app.domain.optimization.constraints import ConstraintEngine, HardConstraints


@pytest.fixture
def base_shipment():
    now = datetime.now(timezone.utc)
    return Shipment(
        id=uuid4(),
        origin="Port A",
        destination="Port B",
        cargo_type=CargoType.GENERAL,
        weight=1000.0,
        shipment_value=10000.0,
        delivery_deadline=now + timedelta(days=10),  # 10 days available
        priority=ShipmentPriority.STANDARD,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def base_route(base_shipment):
    leg = RouteLeg(
        sequence=1,
        origin="Port A",
        destination="Port B",
        transport_mode=TransportMode.SEA,
        duration=8.0,
        cost=1500.0,
    )
    return Route(
        id=uuid4(),
        shipment_id=base_shipment.id,
        route_name="Test Route",
        total_cost=1500.0,
        transit_time=8.0,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=0.2,
        legs=[leg],
    )


def test_feasible_route(base_shipment, base_route):
    engine = ConstraintEngine()
    evaluated = engine.evaluate_route(base_shipment, base_route)

    assert evaluated.feasibility_status == FeasibilityStatus.FEASIBLE
    assert len(evaluated.violated_constraints) == 0


def test_delivery_deadline_exceeded(base_shipment, base_route):
    # Make route slower than available time
    slow_route = base_route.model_copy(update={"transit_time": 12.0})

    engine = ConstraintEngine()
    evaluated = engine.evaluate_route(base_shipment, slow_route)

    assert evaluated.feasibility_status == FeasibilityStatus.INFEASIBLE
    assert len(evaluated.violated_constraints) == 1
    assert "DELIVERY_DEADLINE_EXCEEDED" in evaluated.violated_constraints[0]


def test_custom_max_cost_exceeded(base_shipment, base_route):
    constraints = HardConstraints(max_total_cost=1000.0)
    engine = ConstraintEngine(custom_constraints=constraints)

    evaluated = engine.evaluate_route(base_shipment, base_route)

    assert evaluated.feasibility_status == FeasibilityStatus.INFEASIBLE
    assert len(evaluated.violated_constraints) == 1
    assert "MAX_COST_EXCEEDED" in evaluated.violated_constraints[0]


def test_custom_max_risk_exceeded(base_shipment, base_route):
    constraints = HardConstraints(max_aggregate_risk=0.1)
    engine = ConstraintEngine(custom_constraints=constraints)

    evaluated = engine.evaluate_route(base_shipment, base_route)

    assert evaluated.feasibility_status == FeasibilityStatus.INFEASIBLE
    assert len(evaluated.violated_constraints) == 1
    assert "MAX_RISK_EXCEEDED" in evaluated.violated_constraints[0]


def test_multiple_violations(base_shipment, base_route):
    # Route is too slow and too risky
    slow_route = base_route.model_copy(update={"transit_time": 15.0})
    constraints = HardConstraints(max_aggregate_risk=0.1)

    engine = ConstraintEngine(custom_constraints=constraints)
    evaluated = engine.evaluate_route(base_shipment, slow_route)

    assert evaluated.feasibility_status == FeasibilityStatus.INFEASIBLE
    assert len(evaluated.violated_constraints) == 2

    violations_text = " ".join(evaluated.violated_constraints)
    assert "DELIVERY_DEADLINE_EXCEEDED" in violations_text
    assert "MAX_RISK_EXCEEDED" in violations_text


def test_evaluate_routes_batch(base_shipment, base_route):
    fast_route = base_route.model_copy(update={"transit_time": 5.0})
    slow_route = base_route.model_copy(update={"transit_time": 15.0})

    engine = ConstraintEngine()
    results = engine.evaluate_routes(base_shipment, [fast_route, slow_route])

    assert results[0].feasibility_status == FeasibilityStatus.FEASIBLE
    assert results[1].feasibility_status == FeasibilityStatus.INFEASIBLE
