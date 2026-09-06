from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from app.domain.models.explanation import StructuredExplanation
from app.domain.models.optimization import OptimizationProfile, OptimizationResult
from app.domain.models.route import Route, RouteLeg
from app.domain.services.evidence import EvidenceBuilder
from app.domain.services.explanation import ExplanationGenerator, GroundingError
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_leg():
    return RouteLeg(
        sequence=1,
        origin="A",
        destination="B",
        transport_mode="AIR",
        duration=5,
        cost=500,
    )


def make_route(shipment_id, name="Route A", aggregate_risk=0.5, feasible=True):
    return Route(
        id=uuid4(),
        shipment_id=shipment_id,
        route_name=name,
        total_cost=1000,
        transit_time=24,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=aggregate_risk,
        legs=[make_leg()],
    )


def make_result(shipment_id, recommended_id, feasible_ids, infeasible_ids=None,
                scores=None, breakdown=None, constraints=None, tradeoffs=None):
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
        recommended_route_id=recommended_id,
        feasible_routes=feasible_ids,
        infeasible_routes=infeasible_ids or [],
        route_scores=scores or {},
        score_breakdown=breakdown or {},
        constraint_results=constraints or {},
        tradeoffs=tradeoffs or {},
        execution_time_ms=1.0,
    )


# ---------------------------------------------------------------------------
# Evidence builder tests
# ---------------------------------------------------------------------------

def test_evidence_builder_correctness():
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    r2 = make_route(sid, "Route B")

    result = make_result(
        sid,
        recommended_id=r1.id,
        feasible_ids=[r1.id],
        infeasible_ids=[r2.id],
        scores={r1.id: 0.8},
        breakdown={r1.id: {"cost": 0.4, "time": 0.4}},
        constraints={r2.id: ["Too expensive"]},
        tradeoffs={"pareto_efficient": [str(r1.id)]},
    )

    evidence = EvidenceBuilder.build(result, [r1, r2])

    assert evidence.recommended_route_id == r1.id
    assert evidence.has_feasible_routes is True
    assert len(evidence.routes) == 2

    r1_ev = next(r for r in evidence.routes if r.route_id == r1.id)
    assert r1_ev.is_recommended is True
    assert r1_ev.is_feasible is True
    assert r1_ev.is_pareto_efficient is True  # UUID-based, not name-based
    assert len(r1_ev.score_drivers) == 2

    r2_ev = next(r for r in evidence.routes if r.route_id == r2.id)
    assert r2_ev.is_recommended is False
    assert r2_ev.is_feasible is False
    assert r2_ev.is_pareto_efficient is False
    assert "Too expensive" in r2_ev.constraint_violations


def test_evidence_builder_pareto_uses_uuid_not_name():
    """Pareto matching must use UUID strings, not route names."""
    sid = uuid4()
    r1 = make_route(sid, "Pareto Route")
    r2 = make_route(sid, "Pareto Route")  # Same name, different UUID

    result = make_result(
        sid,
        recommended_id=r1.id,
        feasible_ids=[r1.id, r2.id],
        tradeoffs={"pareto_efficient": [str(r1.id)]},  # Only r1 is Pareto
    )

    evidence = EvidenceBuilder.build(result, [r1, r2])
    r1_ev = next(r for r in evidence.routes if r.route_id == r1.id)
    r2_ev = next(r for r in evidence.routes if r.route_id == r2.id)
    assert r1_ev.is_pareto_efficient is True
    assert r2_ev.is_pareto_efficient is False  # Same name, different UUID → correctly excluded


# ---------------------------------------------------------------------------
# Deterministic fallback tests
# ---------------------------------------------------------------------------

def test_deterministic_fallback_mentions_recommended_route():
    sid = uuid4()
    r1 = make_route(sid, "Fast Air")
    result = make_result(
        sid,
        recommended_id=r1.id,
        feasible_ids=[r1.id],
        breakdown={r1.id: {"cost": 0.5, "time": 0.3}},
    )
    evidence = EvidenceBuilder.build(result, [r1])
    resp = ExplanationGenerator._generate_deterministic(evidence)

    assert "Fast Air" in resp.explanation
    assert "cost" in resp.explanation
    assert resp.generated_by == "deterministic"


def test_deterministic_fallback_no_feasible():
    sid = uuid4()
    result = make_result(sid, recommended_id=None, feasible_ids=[])
    evidence = EvidenceBuilder.build(result, [])
    resp = ExplanationGenerator._generate_deterministic(evidence)

    assert "No feasible route exists" in resp.explanation
    assert resp.generated_by == "deterministic"


# ---------------------------------------------------------------------------
# Grounding validation tests
# ---------------------------------------------------------------------------

def _make_evidence_with_routes():
    sid = uuid4()
    r1 = make_route(sid, "Route Alpha")
    r2 = make_route(sid, "Route Beta")
    result = make_result(
        sid,
        recommended_id=r1.id,
        feasible_ids=[r1.id],
        infeasible_ids=[r2.id],
        constraints={r2.id: ["Weight limit exceeded"]},
    )
    return EvidenceBuilder.build(result, [r1, r2])


def test_grounding_rejects_wrong_recommended_route():
    """CASE A: LLM recommends wrong route."""
    evidence = _make_evidence_with_routes()
    bad_structured = StructuredExplanation(
        recommended_route_name="Route Beta",  # Wrong — optimizer chose Route Alpha
        reasons=["Route Beta had lower cost"],
        tradeoffs=[],
        constraint_notes=[],
    )
    with pytest.raises(GroundingError, match="optimizer selected"):
        ExplanationGenerator.validate_structured(evidence, bad_structured)


def test_grounding_rejects_feasibility_contradiction():
    """CASE B: LLM claims infeasible route is feasible."""
    evidence = _make_evidence_with_routes()
    bad_structured = StructuredExplanation(
        recommended_route_name="Route Alpha",
        reasons=[],
        tradeoffs=[],
        constraint_notes=["Route Beta is feasible and can be selected as an alternative."],
    )
    with pytest.raises(GroundingError, match="infeasible route"):
        ExplanationGenerator.validate_structured(evidence, bad_structured)


def test_grounding_rejects_recommendation_when_no_feasible():
    """CASE C: LLM names a route when no feasible route exists."""
    sid = uuid4()
    result = make_result(sid, recommended_id=None, feasible_ids=[])
    evidence = EvidenceBuilder.build(result, [])

    bad_structured = StructuredExplanation(
        recommended_route_name="Route X",  # Should be empty
        reasons=["Route X had the best profile"],
        tradeoffs=[],
        constraint_notes=[],
    )
    with pytest.raises(GroundingError, match="no feasible route"):
        ExplanationGenerator.validate_structured(evidence, bad_structured)


def test_grounding_accepts_valid_structured_output():
    """Valid structured output passes grounding."""
    evidence = _make_evidence_with_routes()
    good_structured = StructuredExplanation(
        recommended_route_name="Route Alpha",
        reasons=["Route Alpha had the highest weighted score."],
        tradeoffs=["Route Beta was faster but violated weight constraints."],
        constraint_notes=["Route Beta was excluded: Weight limit exceeded."],
    )
    # Should not raise
    ExplanationGenerator.validate_structured(evidence, good_structured)


# ---------------------------------------------------------------------------
# Provider failure / fallback tests
# ---------------------------------------------------------------------------

def test_gemini_failure_falls_back_to_deterministic():
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    result = make_result(sid, recommended_id=r1.id, feasible_ids=[r1.id])
    evidence = EvidenceBuilder.build(result, [r1])

    with patch.dict("os.environ", {"ENABLE_LLM_EXPLANATION": "true", "GEMINI_API_KEY": "fake-key"}):
        with patch(
            "app.domain.services.explanation.ExplanationGenerator._generate_gemini",
            side_effect=Exception("Connection error"),
        ):
            resp = ExplanationGenerator.generate(evidence)

    assert resp.generated_by == "deterministic"
    assert "Route A" in resp.explanation


def test_gemini_timeout_falls_back_to_deterministic():
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    result = make_result(sid, recommended_id=r1.id, feasible_ids=[r1.id])
    evidence = EvidenceBuilder.build(result, [r1])

    with patch.dict("os.environ", {"ENABLE_LLM_EXPLANATION": "true", "GEMINI_API_KEY": "fake-key"}):
        with patch(
            "app.domain.services.explanation.ExplanationGenerator._generate_gemini",
            side_effect=TimeoutError("Gemini timeout"),
        ):
            resp = ExplanationGenerator.generate(evidence)

    assert resp.generated_by == "deterministic"


def test_gemini_grounding_failure_falls_back():
    """When Gemini output fails grounding, fallback is used."""
    sid = uuid4()
    r1 = make_route(sid, "Route Alpha")
    result = make_result(sid, recommended_id=r1.id, feasible_ids=[r1.id])
    evidence = EvidenceBuilder.build(result, [r1])

    bad_structured = StructuredExplanation(
        recommended_route_name="Wrong Route",
        reasons=[],
        tradeoffs=[],
        constraint_notes=[],
    )

    with patch.dict("os.environ", {"ENABLE_LLM_EXPLANATION": "true", "GEMINI_API_KEY": "fake-key"}):
        with patch(
            "app.domain.services.explanation.ExplanationGenerator._generate_gemini",
            return_value=bad_structured,
        ):
            resp = ExplanationGenerator.generate(evidence)

    assert resp.generated_by == "deterministic"


def test_missing_api_key_falls_back():
    """Missing GEMINI_API_KEY triggers deterministic fallback."""
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    result = make_result(sid, recommended_id=r1.id, feasible_ids=[r1.id])
    evidence = EvidenceBuilder.build(result, [r1])

    env = {"ENABLE_LLM_EXPLANATION": "true"}
    env.pop("GEMINI_API_KEY", None)
    with patch.dict("os.environ", env, clear=False):
        import os as _os
        original = _os.environ.pop("GEMINI_API_KEY", None)
        try:
            resp = ExplanationGenerator.generate(evidence)
        finally:
            if original:
                _os.environ["GEMINI_API_KEY"] = original

    assert resp.generated_by == "deterministic"


def test_llm_disabled_uses_deterministic():
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    result = make_result(sid, recommended_id=r1.id, feasible_ids=[r1.id])
    evidence = EvidenceBuilder.build(result, [r1])

    with patch.dict("os.environ", {"ENABLE_LLM_EXPLANATION": "false"}):
        resp = ExplanationGenerator.generate(evidence)

    assert resp.generated_by == "deterministic"


# ---------------------------------------------------------------------------
# Invariant: LLM cannot mutate OptimizationResult
# ---------------------------------------------------------------------------

def test_llm_cannot_mutate_optimization_result():
    """OptimizationResult is frozen — any mutation attempt raises an error."""
    sid = uuid4()
    r1 = make_route(sid, "Route A")
    profile = OptimizationProfile(
        name="test", cost_weight=1.0, time_weight=0.0,
        reliability_weight=0.0, risk_weight=0.0
    )
    result = OptimizationResult(
        shipment_id=sid, profile=profile,
        recommended_route_id=r1.id,
        feasible_routes=[r1.id],
        execution_time_ms=1.0,
    )
    with pytest.raises(ValidationError):
        result.recommended_route_id = uuid4()
