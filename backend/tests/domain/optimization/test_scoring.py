import math
from uuid import uuid4

from app.domain.models.enums import FeasibilityStatus, TransportMode
from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route, RouteLeg
from app.domain.optimization.scoring import ScoringEngine


def create_route(
    cost: float,
    time: float,
    rel: float,
    risk: float,
    status: FeasibilityStatus = FeasibilityStatus.FEASIBLE,
) -> Route:
    return Route(
        id=uuid4(),
        shipment_id=uuid4(),
        route_name="Test Route",
        total_cost=cost,
        transit_time=time,
        delay_probability=1.0 - rel,
        reliability=rel,
        aggregate_risk=risk,
        feasibility_status=status,
        legs=[
            RouteLeg(
                sequence=1,
                origin="A",
                destination="B",
                transport_mode=TransportMode.ROAD,
                duration=time,
                cost=cost,
            )
        ],
    )


def test_normalization_directions():
    engine = ScoringEngine()

    # Cost: lower is better
    # values: 100, 200, 300 -> min=100, max=300
    assert engine._normalize_lower_is_better(100.0, 100.0, 300.0) == 1.0
    assert engine._normalize_lower_is_better(200.0, 100.0, 300.0) == 0.5
    assert engine._normalize_lower_is_better(300.0, 100.0, 300.0) == 0.0

    # Reliability: higher is better
    # values: 0.8, 0.9, 0.95 -> min=0.8, max=0.95
    assert math.isclose(engine._normalize_higher_is_better(0.8, 0.8, 0.95), 0.0)
    assert math.isclose(engine._normalize_higher_is_better(0.95, 0.8, 0.95), 1.0)


def test_normalization_edge_cases():
    engine = ScoringEngine()

    # Max == Min
    assert engine._normalize_lower_is_better(500.0, 500.0, 500.0) == 1.0
    assert engine._normalize_higher_is_better(0.9, 0.9, 0.9) == 1.0


def test_single_candidate_route():
    r1 = create_route(1000.0, 5.0, 0.9, 0.1)

    profile = OptimizationProfile(
        name="Test",
        cost_weight=0.25,
        time_weight=0.25,
        reliability_weight=0.25,
        risk_weight=0.25,
    )

    engine = ScoringEngine()
    scores, breakdowns = engine.score_routes([r1], profile)

    # A single route implies max == min for all metrics, so all norm scores are 1.0
    assert scores[r1.id] == 1.0
    assert breakdowns[r1.id]["cost"] == 0.25
    assert breakdowns[r1.id]["time"] == 0.25


def test_infeasible_routes_ignored():
    r1 = create_route(100.0, 1.0, 0.9, 0.1, status=FeasibilityStatus.FEASIBLE)
    r2 = create_route(50.0, 0.5, 0.9, 0.1, status=FeasibilityStatus.INFEASIBLE)

    profile = OptimizationProfile(
        name="Test",
        cost_weight=1.0,
        time_weight=0.0,
        reliability_weight=0.0,
        risk_weight=0.0,
    )

    engine = ScoringEngine()
    scores, _ = engine.score_routes([r1, r2], profile)

    assert r1.id in scores
    assert r2.id not in scores
    # Since r1 is the only feasible route, it gets 1.0
    assert scores[r1.id] == 1.0


def test_hand_calculated_multi_route_scoring():
    rA = create_route(cost=1000.0, time=10.0, rel=0.9, risk=0.2)
    rB = create_route(cost=2000.0, time=5.0, rel=0.9, risk=0.1)
    rC = create_route(cost=3000.0, time=10.0, rel=0.9, risk=0.0)  # Zero risk

    profile = OptimizationProfile(
        name="Hand Calc Profile",
        cost_weight=0.4,
        time_weight=0.3,
        reliability_weight=0.2,
        risk_weight=0.1,
    )

    engine = ScoringEngine()
    scores, breakdowns = engine.score_routes([rA, rB, rC], profile)

    # Hand-calculated expectations:
    # Cost (1000, 2000, 3000). weight 0.4
    # rA cost norm = 1.0 * 0.4 = 0.4
    # rB cost norm = 0.5 * 0.4 = 0.2
    # rC cost norm = 0.0 * 0.4 = 0.0

    # Time (10, 5, 10). weight 0.3
    # rA time norm = 0.0 * 0.3 = 0.0
    # rB time norm = 1.0 * 0.3 = 0.3
    # rC time norm = 0.0 * 0.3 = 0.0

    # Rel (0.9, 0.9, 0.9). weight 0.2 -> Tied, all 1.0
    # rA, rB, rC rel = 1.0 * 0.2 = 0.2

    # Risk (0.2, 0.1, 0.0). weight 0.1
    # rA risk norm = 0.0 * 0.1 = 0.0
    # rB risk norm = 0.5 * 0.1 = 0.05
    # rC risk norm = 1.0 * 0.1 = 0.1

    # Totals:
    # rA = 0.4 + 0.0 + 0.2 + 0.0 = 0.6
    # rB = 0.2 + 0.3 + 0.2 + 0.05 = 0.75
    # rC = 0.0 + 0.0 + 0.2 + 0.1 = 0.3

    assert math.isclose(scores[rA.id], 0.6)
    assert math.isclose(scores[rB.id], 0.75)
    assert math.isclose(scores[rC.id], 0.3)

    # Check breakdown reconciliation
    for rid in [rA.id, rB.id, rC.id]:
        b = breakdowns[rid]
        assert math.isclose(
            b["cost"] + b["time"] + b["reliability"] + b["risk"], scores[rid]
        )
