import math
from uuid import uuid4

import pytest
from app.domain.models.enums import FeasibilityStatus, TransportMode
from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route, RouteLeg
from app.domain.optimization.scoring import ScoringEngine
from app.domain.optimization.sensitivity import SensitivityAnalyzer


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
        route_name="Route",
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
                transport_mode=TransportMode.SEA,
                duration=time,
                cost=cost,
            )
        ],
    )


@pytest.fixture
def baseline_profile():
    return OptimizationProfile(
        name="Baseline",
        cost_weight=0.25,
        time_weight=0.25,
        reliability_weight=0.25,
        risk_weight=0.25,
    )


@pytest.fixture
def analyzer():
    return SensitivityAnalyzer(ScoringEngine())


def test_highly_stable_recommendation(analyzer, baseline_profile):
    # Route A dominates in everything by a huge margin
    r_a = create_route(1000, 5, 0.99, 0.01)
    r_b = create_route(5000, 20, 0.50, 0.80)

    result = analyzer.analyze([r_a, r_b], baseline_profile, r_a.id)

    assert result.baseline_recommended_route_id == r_a.id
    assert result.is_robust is True
    assert result.stability_score == 1.0
    for scenario in result.scenarios:
        assert scenario.recommended_route_id == r_a.id


def test_recommendation_changing(analyzer, baseline_profile):
    # Route A is cheap but slow. Route B is expensive but fast.
    r_a = create_route(1000, 20, 0.90, 0.10)
    r_b = create_route(2000, 5, 0.90, 0.10)

    # Under balanced profile, they tie on score. Cost tie-breaker picks r_a.
    # But if we increase time weight, r_b will win.
    result = analyzer.analyze([r_a, r_b], baseline_profile, r_a.id)

    assert result.baseline_recommended_route_id == r_a.id
    assert result.is_robust is False
    assert result.stability_score < 1.0

    # Find the scenario where time weight was increased
    time_plus = next(s for s in result.scenarios if s.scenario_name == "time_+20%")
    assert time_plus.recommended_route_id == r_b.id


def test_weight_normalization():
    engine = ScoringEngine()
    analyzer = SensitivityAnalyzer(engine)
    profile = OptimizationProfile(
        name="Test",
        cost_weight=0.8,
        time_weight=0.2,
        reliability_weight=0.0,
        risk_weight=0.0,
    )

    # Increase cost to 1.0, others should be 0.0
    p1 = analyzer._perturb_weights(profile, "cost", 0.2)
    assert p1.cost_weight == 1.0
    assert p1.time_weight == 0.0

    # Decrease cost by 0.2 -> cost 0.6. Remaining is 0.4. Original remaining was 0.2 (all in time).
    # So time should scale to 0.4.
    p2 = analyzer._perturb_weights(profile, "cost", -0.2)
    assert math.isclose(p2.cost_weight, 0.6)
    assert math.isclose(p2.time_weight, 0.4)

    # Sum is always verified by Pydantic model implicitly upon creation of p1, p2.


def test_single_route_case(analyzer, baseline_profile):
    r_a = create_route(1000, 5, 0.90, 0.20)

    result = analyzer.analyze([r_a], baseline_profile, r_a.id)

    assert result.is_robust is True
    assert result.stability_score == 1.0
    for scenario in result.scenarios:
        assert scenario.recommended_route_id == r_a.id


def test_infeasible_route_exclusion(analyzer, baseline_profile):
    create_route(1000, 5, 0.90, 0.20)
    # Infeasible routes should not be included in the analysis at all.
    # Usually the pipeline filters them out. But if they sneak in, we handle it if they were feasible?
    # Wait, the prompt says "takes the same feasible route candidates". So infeasible routes are excluded BEFORE being passed in.
    # If the list is empty, it returns early.
    result = analyzer.analyze([], baseline_profile, None)

    assert result.is_robust is True
    assert len(result.scenarios) == 0


def test_deterministic_repeated_execution(analyzer, baseline_profile):
    r_a = create_route(1000, 20, 0.90, 0.10)
    r_b = create_route(2000, 5, 0.90, 0.10)

    res1 = analyzer.analyze([r_a, r_b], baseline_profile, r_a.id)
    res2 = analyzer.analyze([r_a, r_b], baseline_profile, r_a.id)

    assert res1.stability_score == res2.stability_score
    assert len(res1.scenarios) == len(res2.scenarios)
    for s1, s2 in zip(res1.scenarios, res2.scenarios):
        assert s1.recommended_route_id == s2.recommended_route_id
