import time

from app.domain.models.enums import FeasibilityStatus
from app.domain.models.optimization import OptimizationProfile, OptimizationResult
from app.domain.models.route import Route
from app.domain.models.shipment import Shipment
from app.domain.optimization.constraints import ConstraintEngine
from app.domain.optimization.pareto import ParetoAnalyzer
from app.domain.optimization.scoring import ScoringEngine


class RouteOptimizer:
    def __init__(
        self,
        constraint_engine: ConstraintEngine,
        scoring_engine: ScoringEngine,
        pareto_analyzer: ParetoAnalyzer | None = None,
    ):
        self.constraint_engine = constraint_engine
        self.scoring_engine = scoring_engine
        self.pareto_analyzer = pareto_analyzer or ParetoAnalyzer()

    def optimize(
        self, shipment: Shipment, routes: list[Route], profile: OptimizationProfile
    ) -> tuple[OptimizationResult, list[Route]]:
        start_time = time.perf_counter()

        # 1. Hard Constraint Evaluation
        evaluated_routes = self.constraint_engine.evaluate_routes(shipment, routes)

        # 2. Extract feasibility status and violations
        infeasible_route_ids = []
        constraint_results = {}
        feasible_routes = []

        for r in evaluated_routes:
            if r.feasibility_status == FeasibilityStatus.INFEASIBLE:
                infeasible_route_ids.append(r.id)
                constraint_results[r.id] = r.violated_constraints
            else:
                feasible_routes.append(r)

        # 3. Score Feasible Routes
        route_scores, score_breakdowns = self.scoring_engine.score_routes(
            feasible_routes, profile
        )

        # 4. Deterministic Ranking
        # Tie-breaker:
        # 1. Highest total score (-score)
        # 2. Lowest total cost (cost)
        # 3. Lowest transit time (time)
        # 4. Lexicographical UUID (str(id)) to guarantee reproducible determinism
        def ranking_key(r: Route) -> tuple[float, float, float, str]:
            score = route_scores.get(r.id, 0.0)
            return (-score, r.total_cost, r.transit_time, str(r.id))

        ranked_feasible = sorted(feasible_routes, key=ranking_key)
        ranked_feasible_ids = [r.id for r in ranked_feasible]

        # 5. Pareto Dominance Analysis (Analytical layer, does not affect primary recommendation)
        pareto_efficient, pareto_dominated = self.pareto_analyzer.analyze(
            feasible_routes
        )
        tradeoffs = {
            "pareto_efficient": [str(r.id) for r in pareto_efficient],
            "dominated": [str(r.id) for r in pareto_dominated],
        }

        # 6. Recommendation
        recommended_route_id = ranked_feasible_ids[0] if ranked_feasible_ids else None

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        # 7. Construct Structured Optimization Result
        result = OptimizationResult(
            shipment_id=shipment.id,
            profile=profile,
            recommended_route_id=recommended_route_id,
            feasible_routes=ranked_feasible_ids,  # Implicitly ranked best-to-worst
            infeasible_routes=infeasible_route_ids,
            route_scores=route_scores,
            score_breakdown=score_breakdowns,
            constraint_results=constraint_results,
            tradeoffs=tradeoffs,
            execution_time_ms=execution_time_ms,
        )

        return result, evaluated_routes
