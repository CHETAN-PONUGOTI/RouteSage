from app.domain.models.optimization import OptimizationProfile, OptimizationResult
from app.domain.models.route import RiskFactor, Route, RouteLeg
from app.domain.models.shipment import Shipment
from app.infrastructure.models import (
    OptimizationProfileModel,
    OptimizationRunModel,
    RiskFactorModel,
    RouteLegModel,
    RouteModel,
    ShipmentModel,
)


class DataMapper:
    @staticmethod
    def to_domain_shipment(model: ShipmentModel) -> Shipment:
        return Shipment(
            id=model.id,
            origin=model.origin,
            destination=model.destination,
            cargo_type=model.cargo_type,
            weight=model.weight,
            shipment_value=model.shipment_value,
            delivery_deadline=model.delivery_deadline,
            priority=model.priority,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_orm_shipment(domain: Shipment) -> ShipmentModel:
        return ShipmentModel(
            id=domain.id,
            origin=domain.origin,
            destination=domain.destination,
            cargo_type=domain.cargo_type,
            weight=domain.weight,
            shipment_value=domain.shipment_value,
            delivery_deadline=domain.delivery_deadline,
            priority=domain.priority,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    @staticmethod
    def to_domain_route(model: RouteModel) -> Route:
        legs = [
            RouteLeg(
                sequence=leg.sequence,
                origin=leg.origin,
                destination=leg.destination,
                transport_mode=leg.transport_mode,
                duration=leg.duration,
                cost=leg.cost,
                risk_factors=[
                    RiskFactor(
                        category=rf.category,
                        severity=rf.severity,
                        description=rf.description,
                    )
                    for rf in leg.risk_factors
                ],
            )
            for leg in model.legs
        ]

        return Route(
            id=model.id,
            shipment_id=model.shipment_id,
            route_name=model.route_name,
            total_cost=model.total_cost,
            transit_time=model.transit_time,
            delay_probability=model.delay_probability,
            reliability=model.reliability,
            aggregate_risk=model.aggregate_risk,
            feasibility_status=model.feasibility_status,
            violated_constraints=model.violated_constraints,
            legs=legs,
        )

    @staticmethod
    def to_orm_route(domain: Route) -> RouteModel:
        legs = []
        for leg in domain.legs:
            r_factors = [
                RiskFactorModel(
                    category=rf.category,
                    severity=rf.severity,
                    description=rf.description,
                )
                for rf in leg.risk_factors
            ]
            legs.append(
                RouteLegModel(
                    sequence=leg.sequence,
                    origin=leg.origin,
                    destination=leg.destination,
                    transport_mode=leg.transport_mode,
                    duration=leg.duration,
                    cost=leg.cost,
                    risk_factors=r_factors,
                )
            )

        return RouteModel(
            id=domain.id,
            shipment_id=domain.shipment_id,
            route_name=domain.route_name,
            total_cost=domain.total_cost,
            transit_time=domain.transit_time,
            delay_probability=domain.delay_probability,
            reliability=domain.reliability,
            aggregate_risk=domain.aggregate_risk,
            feasibility_status=domain.feasibility_status,
            violated_constraints=domain.violated_constraints,
            legs=legs,
        )

    @staticmethod
    def to_domain_profile(model: OptimizationProfileModel) -> OptimizationProfile:
        return OptimizationProfile(
            name=model.name,
            cost_weight=model.cost_weight,
            time_weight=model.time_weight,
            reliability_weight=model.reliability_weight,
            risk_weight=model.risk_weight,
        )

    @staticmethod
    def to_orm_profile(domain: OptimizationProfile, id_val) -> OptimizationProfileModel:
        return OptimizationProfileModel(
            id=id_val,
            name=domain.name,
            cost_weight=domain.cost_weight,
            time_weight=domain.time_weight,
            reliability_weight=domain.reliability_weight,
            risk_weight=domain.risk_weight,
        )

    @staticmethod
    def to_domain_optimization_result(
        model: OptimizationRunModel, profile: OptimizationProfile
    ) -> OptimizationResult:
        # Convert string dict keys (JSON parses to string) back to UUID
        from uuid import UUID

        def dict_str_to_uuid(d: dict) -> dict:
            return {UUID(k): v for k, v in d.items()}

        def list_str_to_uuid(l: list) -> list:
            return [UUID(s) for s in l]

        return OptimizationResult(
            id=model.id,
            shipment_id=model.shipment_id,
            profile=profile,
            recommended_route_id=model.recommended_route_id,
            feasible_routes=list_str_to_uuid(model.feasible_routes),
            infeasible_routes=list_str_to_uuid(model.infeasible_routes),
            route_scores=dict_str_to_uuid(model.route_scores),
            score_breakdown=dict_str_to_uuid(model.score_breakdown),
            constraint_results=dict_str_to_uuid(model.constraint_results),
            tradeoffs=model.tradeoffs,
            sensitivity=model.sensitivity,
            execution_time_ms=model.execution_time_ms,
            created_at=model.created_at,
        )

    @staticmethod
    def to_orm_optimization_result(
        domain: OptimizationResult, profile_id
    ) -> OptimizationRunModel:
        # UUIDs must be serialized as strings for JSON columns
        def dict_uuid_to_str(d: dict) -> dict:
            return {str(k): v for k, v in d.items()}

        def list_uuid_to_str(l: list) -> list:
            return [str(s) for s in l]

        return OptimizationRunModel(
            id=domain.id,
            shipment_id=domain.shipment_id,
            profile_id=profile_id,
            recommended_route_id=domain.recommended_route_id,
            feasible_routes=list_uuid_to_str(domain.feasible_routes),
            infeasible_routes=list_uuid_to_str(domain.infeasible_routes),
            route_scores=dict_uuid_to_str(domain.route_scores),
            score_breakdown=dict_uuid_to_str(domain.score_breakdown),
            constraint_results=dict_uuid_to_str(domain.constraint_results),
            tradeoffs=domain.tradeoffs,
            sensitivity=domain.sensitivity,
            execution_time_ms=domain.execution_time_ms,
            created_at=domain.created_at,
        )
