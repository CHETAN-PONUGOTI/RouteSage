"""Deterministic evaluation of the optimization decision system
against the synthetic dataset."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from uuid import UUID

from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import Route
from app.domain.models.shipment import Shipment
from app.domain.optimization.constraints import ConstraintEngine
from app.domain.optimization.pareto import ParetoAnalyzer
from app.domain.optimization.pipeline import RouteOptimizer
from app.domain.optimization.scoring import ScoringEngine


@dataclass
class RouteDecisionMetrics:
    total_shipments: int = 0
    total_routes_evaluated: int = 0
    shipments_with_feasible_route: int = 0
    shipments_with_no_feasible_route: int = 0
    recommendation_count: int = 0
    infeasible_route_recommended_count: int = 0  # Should always be 0
    avg_recommended_cost: float = 0.0
    avg_recommended_transit_time: float = 0.0
    avg_recommended_reliability: float = 0.0
    avg_recommended_risk: float = 0.0
    pareto_winner_overlap_count: int = 0  # Recommended route also Pareto-efficient
    deterministic_repeatability: bool = True
    raw_results: list[dict] = field(default_factory=list)


class DecisionSystemEvaluator:
    """Evaluates the optimization decision system without duplicating its logic."""

    def __init__(self, profile: OptimizationProfile | None = None):
        self.optimizer = RouteOptimizer(
            ConstraintEngine(), ScoringEngine(), ParetoAnalyzer()
        )
        self.profile = profile or OptimizationProfile(
            name="Balanced",
            cost_weight=0.4,
            time_weight=0.3,
            reliability_weight=0.2,
            risk_weight=0.1,
        )

    def evaluate(
        self,
        shipments: list[Shipment],
        routes_by_shipment: dict[UUID, list[Route]],
    ) -> RouteDecisionMetrics:
        metrics = RouteDecisionMetrics(total_shipments=len(shipments))

        costs = []
        times = []
        reliabilities = []
        risks = []

        for shipment in shipments:
            routes = routes_by_shipment.get(shipment.id, [])
            metrics.total_routes_evaluated += len(routes)

            if not routes:
                continue

            result, _ = self.optimizer.optimize(shipment, routes, self.profile)

            # Deterministic repeatability check: run twice and confirm same result
            result2, _ = self.optimizer.optimize(shipment, routes, self.profile)
            if result.recommended_route_id != result2.recommended_route_id:
                metrics.deterministic_repeatability = False

            if result.feasible_routes:
                metrics.shipments_with_feasible_route += 1
            else:
                metrics.shipments_with_no_feasible_route += 1

            if result.recommended_route_id:
                metrics.recommendation_count += 1

                route_map = {r.id: r for r in routes}
                rec_route = route_map.get(result.recommended_route_id)

                if rec_route:
                    # Infeasible recommendation guard
                    if result.recommended_route_id in result.infeasible_routes:
                        metrics.infeasible_route_recommended_count += 1

                    costs.append(rec_route.total_cost)
                    times.append(rec_route.transit_time)
                    reliabilities.append(rec_route.reliability)
                    risks.append(rec_route.aggregate_risk)

                    # Pareto overlap
                    pareto_ids_str = result.tradeoffs.get("pareto_efficient", [])
                    if str(result.recommended_route_id) in pareto_ids_str:
                        metrics.pareto_winner_overlap_count += 1

            metrics.raw_results.append({
                "shipment_id": str(shipment.id),
                "feasible_count": len(result.feasible_routes),
                "infeasible_count": len(result.infeasible_routes),
                "recommended_route_id": str(result.recommended_route_id) if result.recommended_route_id else None,
                "recommended_score": result.route_scores.get(result.recommended_route_id) if result.recommended_route_id else None,
            })

        if costs:
            metrics.avg_recommended_cost = mean(costs)
        if times:
            metrics.avg_recommended_transit_time = mean(times)
        if reliabilities:
            metrics.avg_recommended_reliability = mean(reliabilities)
        if risks:
            metrics.avg_recommended_risk = mean(risks)

        return metrics
