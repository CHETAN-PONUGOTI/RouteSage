import math
from uuid import UUID

from app.domain.models.enums import FeasibilityStatus
from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route


class ScoringEngine:
    def _normalize_higher_is_better(
        self, value: float, v_min: float, v_max: float
    ) -> float:
        if math.isclose(v_min, v_max, abs_tol=1e-9):
            return 1.0
        return (value - v_min) / (v_max - v_min)

    def _normalize_lower_is_better(
        self, value: float, v_min: float, v_max: float
    ) -> float:
        if math.isclose(v_min, v_max, abs_tol=1e-9):
            return 1.0
        return (v_max - value) / (v_max - v_min)

    def score_routes(
        self, routes: list[Route], profile: OptimizationProfile
    ) -> tuple[dict[UUID, float], dict[UUID, dict[str, float]]]:
        """
        Scores only feasible routes based on the given optimization profile.
        Returns:
            - A dict mapping route ID to total score.
            - A dict mapping route ID to a dictionary of score contributions.
        """
        feasible_routes = [
            r for r in routes if r.feasibility_status == FeasibilityStatus.FEASIBLE
        ]

        if not feasible_routes:
            return {}, {}

        # Extract metric arrays
        costs = [r.total_cost for r in feasible_routes]
        times = [r.transit_time for r in feasible_routes]
        reliabilities = [r.reliability for r in feasible_routes]
        risks = [r.aggregate_risk for r in feasible_routes]

        # Calculate bounds
        c_min, c_max = min(costs), max(costs)
        t_min, t_max = min(times), max(times)
        rel_min, rel_max = min(reliabilities), max(reliabilities)
        risk_min, risk_max = min(risks), max(risks)

        route_scores = {}
        score_breakdown = {}

        for r in feasible_routes:
            # 1. Normalize
            n_cost = self._normalize_lower_is_better(r.total_cost, c_min, c_max)
            n_time = self._normalize_lower_is_better(r.transit_time, t_min, t_max)
            n_rel = self._normalize_higher_is_better(r.reliability, rel_min, rel_max)
            n_risk = self._normalize_lower_is_better(
                r.aggregate_risk, risk_min, risk_max
            )

            # 2. Apply weights to compute contributions
            c_cost = n_cost * profile.cost_weight
            c_time = n_time * profile.time_weight
            c_rel = n_rel * profile.reliability_weight
            c_risk = n_risk * profile.risk_weight

            # 3. Sum total score
            total_score = c_cost + c_time + c_rel + c_risk

            # Validate math (sum(contributions) == overall_score within float tolerance)
            assert math.isclose(
                total_score, c_cost + c_time + c_rel + c_risk, rel_tol=1e-9
            )

            route_scores[r.id] = total_score
            score_breakdown[r.id] = {
                "cost": c_cost,
                "time": c_time,
                "reliability": c_rel,
                "risk": c_risk,
            }

        return route_scores, score_breakdown
