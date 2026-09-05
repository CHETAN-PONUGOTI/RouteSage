import math

from app.domain.models.enums import FeasibilityStatus
from app.domain.models.route import Route


class ParetoAnalyzer:
    @staticmethod
    def _dominates(a: Route, b: Route) -> bool:
        """
        Returns True if route `a` dominates route `b`.
        A dominates B if it is no worse in all objectives and strictly better in at least one.
        """
        # Tolerances for floating point comparisons
        RTOL = 1e-9
        ATOL = 1e-9

        def is_worse_lower_is_better(val_a: float, val_b: float) -> bool:
            return val_a > val_b and not math.isclose(
                val_a, val_b, rel_tol=RTOL, abs_tol=ATOL
            )

        def is_worse_higher_is_better(val_a: float, val_b: float) -> bool:
            return val_a < val_b and not math.isclose(
                val_a, val_b, rel_tol=RTOL, abs_tol=ATOL
            )

        def is_better_lower_is_better(val_a: float, val_b: float) -> bool:
            return val_a < val_b and not math.isclose(
                val_a, val_b, rel_tol=RTOL, abs_tol=ATOL
            )

        def is_better_higher_is_better(val_a: float, val_b: float) -> bool:
            return val_a > val_b and not math.isclose(
                val_a, val_b, rel_tol=RTOL, abs_tol=ATOL
            )

        # 1. No worse on all objectives
        if is_worse_lower_is_better(a.total_cost, b.total_cost):
            return False
        if is_worse_lower_is_better(a.transit_time, b.transit_time):
            return False
        if is_worse_higher_is_better(a.reliability, b.reliability):
            return False
        if is_worse_lower_is_better(a.aggregate_risk, b.aggregate_risk):
            return False

        # 2. Strictly better on at least one objective
        return bool(
            is_better_lower_is_better(a.total_cost, b.total_cost)
            or is_better_lower_is_better(a.transit_time, b.transit_time)
            or is_better_higher_is_better(a.reliability, b.reliability)
            or is_better_lower_is_better(a.aggregate_risk, b.aggregate_risk)
        )

    def analyze(self, routes: list[Route]) -> tuple[list[Route], list[Route]]:
        """
        Analyzes a list of routes and returns a tuple of (pareto_efficient_routes, dominated_routes).
        Only considers feasible routes. Infeasible routes are excluded from both sets.
        """
        feasible = [
            r for r in routes if r.feasibility_status == FeasibilityStatus.FEASIBLE
        ]

        efficient = []
        dominated = []

        # Sort to ensure deterministic output ordering
        feasible_sorted = sorted(feasible, key=lambda r: str(r.id))

        for i, candidate in enumerate(feasible_sorted):
            is_dominated = False
            for j, other in enumerate(feasible_sorted):
                if i != j and self._dominates(other, candidate):
                    is_dominated = True
                    break

            if is_dominated:
                dominated.append(candidate)
            else:
                efficient.append(candidate)

        return efficient, dominated
