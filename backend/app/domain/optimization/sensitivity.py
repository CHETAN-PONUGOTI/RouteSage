import math
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route
from app.domain.optimization.scoring import ScoringEngine


class SensitivityScenario(BaseModel):
    scenario_name: str
    profile: OptimizationProfile
    recommended_route_id: UUID | None

    model_config = ConfigDict(frozen=True)


class SensitivityAnalysisResult(BaseModel):
    baseline_recommended_route_id: UUID | None
    scenarios: list[SensitivityScenario]
    is_robust: bool
    stability_score: float

    model_config = ConfigDict(frozen=True)


class SensitivityAnalyzer:
    def __init__(self, scoring_engine: ScoringEngine):
        self.scoring_engine = scoring_engine

    def _perturb_weights(
        self, profile: OptimizationProfile, focus: str, delta: float
    ) -> OptimizationProfile:
        weights = {
            "cost": profile.cost_weight,
            "time": profile.time_weight,
            "reliability": profile.reliability_weight,
            "risk": profile.risk_weight,
        }

        original_focus_weight = weights[focus]
        new_focus_weight = max(0.0, min(1.0, original_focus_weight + delta))

        # Calculate exactly how much we changed the focus
        actual_delta = new_focus_weight - original_focus_weight

        # If no change was possible (e.g., trying to add to 1.0 or subtract from 0.0), return as-is
        if math.isclose(actual_delta, 0.0, abs_tol=1e-9):
            return profile

        remaining_new = 1.0 - new_focus_weight
        remaining_old = 1.0 - original_focus_weight

        if remaining_old <= 0.0:
            # Original was 1.0, so the others were 0.0. Distribute evenly.
            dist = remaining_new / 3.0
            for k in weights:
                if k != focus:
                    weights[k] = dist
        elif remaining_new <= 0.0:
            # New is 1.0, so the others must be 0.0
            for k in weights:
                if k != focus:
                    weights[k] = 0.0
        else:
            # Scale proportionally
            scale = remaining_new / remaining_old
            for k in weights:
                if k != focus:
                    weights[k] *= scale

        weights[focus] = new_focus_weight

        return OptimizationProfile(
            name=f"{profile.name} (Perturbed: {focus} {delta:+.2f})",
            cost_weight=weights["cost"],
            time_weight=weights["time"],
            reliability_weight=weights["reliability"],
            risk_weight=weights["risk"],
        )

    def analyze(
        self,
        feasible_routes: list[Route],
        baseline_profile: OptimizationProfile,
        baseline_winner_id: UUID | None,
    ) -> SensitivityAnalysisResult:
        if not feasible_routes:
            return SensitivityAnalysisResult(
                baseline_recommended_route_id=baseline_winner_id,
                scenarios=[],
                is_robust=True,
                stability_score=1.0,
            )

        scenarios = []
        objectives = ["cost", "time", "reliability", "risk"]
        deltas = [0.2, -0.2]

        for obj in objectives:
            for delta in deltas:
                perturbed_profile = self._perturb_weights(baseline_profile, obj, delta)

                # If perturbation didn't change the profile, skip it to avoid redundancy
                if perturbed_profile.name == baseline_profile.name:
                    continue

                route_scores, _ = self.scoring_engine.score_routes(
                    feasible_routes, perturbed_profile
                )

                # Rank deterministically using the exact same tie-breaking logic as the pipeline
                def ranking_key(r: Route, scores=route_scores) -> tuple:
                    score = scores.get(r.id, 0.0)
                    return (-score, r.total_cost, r.transit_time, str(r.id))

                ranked = sorted(feasible_routes, key=ranking_key)
                winner_id = ranked[0].id if ranked else None

                direction = "+" if delta > 0 else "-"
                scenarios.append(
                    SensitivityScenario(
                        scenario_name=f"{obj}_{direction}{abs(int(delta * 100))}%",
                        profile=perturbed_profile,
                        recommended_route_id=winner_id,
                    )
                )

        # Calculate stability
        if not scenarios:
            stability_score = 1.0
        else:
            matches = sum(
                1 for s in scenarios if s.recommended_route_id == baseline_winner_id
            )
            stability_score = matches / len(scenarios)

        is_robust = math.isclose(stability_score, 1.0, rel_tol=1e-9)

        return SensitivityAnalysisResult(
            baseline_recommended_route_id=baseline_winner_id,
            scenarios=scenarios,
            is_robust=is_robust,
            stability_score=stability_score,
        )
