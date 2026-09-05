from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.models.optimization import OptimizationProfile, OptimizationResult


def test_optimization_profile_valid():
    profile = OptimizationProfile(
        name="Balanced",
        cost_weight=0.25,
        time_weight=0.25,
        reliability_weight=0.25,
        risk_weight=0.25,
    )
    assert profile.name == "Balanced"


def test_optimization_profile_invalid_sum():
    with pytest.raises(ValidationError, match="Optimization weights must sum to 1.0"):
        OptimizationProfile(
            name="Imbalanced",
            cost_weight=0.5,
            time_weight=0.5,
            reliability_weight=0.5,
            risk_weight=0.0,
        )


def test_optimization_result_valid():
    profile = OptimizationProfile(
        name="Cost Focus",
        cost_weight=0.7,
        time_weight=0.1,
        reliability_weight=0.1,
        risk_weight=0.1,
    )

    r_id1 = uuid4()
    r_id2 = uuid4()

    result = OptimizationResult(
        shipment_id=uuid4(),
        profile=profile,
        recommended_route_id=r_id1,
        feasible_routes=[r_id1],
        infeasible_routes=[r_id2],
        route_scores={r_id1: 0.95},
        score_breakdown={
            r_id1: {"cost": 0.5, "time": 0.15, "reliability": 0.15, "risk": 0.15}
        },
        constraint_results={r_id2: ["Too slow"]},
        tradeoffs={"insight": ["Route 1 is cheaper but slower."]},
        execution_time_ms=12.5,
    )

    assert result.recommended_route_id == r_id1
    assert result.execution_time_ms == 12.5
    assert len(result.infeasible_routes) == 1
