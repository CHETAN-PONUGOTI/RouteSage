from uuid import UUID

from app.domain.models.explanation import (
    ExplanationEvidence,
    RouteEvidence,
    ScoreDriver,
)
from app.domain.models.optimization import OptimizationResult
from app.domain.models.route import Route


class EvidenceBuilder:
    @staticmethod
    def build(result: OptimizationResult, routes: list[Route]) -> ExplanationEvidence:
        route_map = {r.id: r for r in routes}

        # Pareto efficient route IDs are stored as UUID strings in result.tradeoffs
        pareto_efficient_id_strings = result.tradeoffs.get("pareto_efficient", [])
        pareto_efficient_ids = set()
        for s in pareto_efficient_id_strings:
            try:
                pareto_efficient_ids.add(UUID(s))
            except (ValueError, AttributeError):
                pass

        evidence_routes = []
        for route_id in result.feasible_routes + result.infeasible_routes:
            if route_id not in route_map:
                continue

            route_obj = route_map[route_id]
            is_feasible = route_id in result.feasible_routes
            is_recommended = route_id == result.recommended_route_id

            # Extract drivers from breakdown — no recalculation
            breakdown = result.score_breakdown.get(route_id, {})
            drivers = [
                ScoreDriver(objective=k, contribution=v) for k, v in breakdown.items()
            ]
            # Sort drivers by highest contribution
            drivers.sort(key=lambda d: d.contribution, reverse=True)

            # Pareto uses stable UUID matching
            is_pareto = route_id in pareto_efficient_ids

            evidence_routes.append(
                RouteEvidence(
                    route_id=route_id,
                    route_name=route_obj.route_name,
                    is_feasible=is_feasible,
                    total_score=result.route_scores.get(route_id),
                    score_drivers=drivers,
                    constraint_violations=result.constraint_results.get(route_id, []),
                    is_pareto_efficient=is_pareto,
                    is_recommended=is_recommended,
                )
            )

        return ExplanationEvidence(
            run_id=result.id,
            shipment_id=result.shipment_id,
            has_feasible_routes=len(result.feasible_routes) > 0,
            recommended_route_id=result.recommended_route_id,
            weights={
                "cost": result.profile.cost_weight,
                "time": result.profile.time_weight,
                "reliability": result.profile.reliability_weight,
                "risk": result.profile.risk_weight,
            },
            routes=evidence_routes,
        )
