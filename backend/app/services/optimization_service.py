from uuid import UUID, uuid4

from fastapi import HTTPException

from app.api.schemas.optimization import (
    OptimizationProfileRequest,
)
from app.api.schemas.route import RouteCreate
from app.domain.models.optimization import OptimizationProfile
from app.domain.models.route import RiskFactor, Route, RouteLeg
from app.domain.optimization.pipeline import RouteOptimizer
from app.infrastructure.repositories import (
    OptimizationResultRepository,
    RouteRepository,
    ShipmentRepository,
)


class OptimizationService:
    def __init__(
        self,
        shipment_repo: ShipmentRepository,
        route_repo: RouteRepository,
        opt_repo: OptimizationResultRepository,
        optimizer: RouteOptimizer
    ):
        self.shipment_repo = shipment_repo
        self.route_repo = route_repo
        self.opt_repo = opt_repo
        self.optimizer = optimizer

    def create_routes(self, shipment_id: UUID, routes_data: list[RouteCreate]) -> list[Route]:
        shipment = self.shipment_repo.get(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        domain_routes = []
        for rd in routes_data:
            legs = []
            for ld in rd.legs:
                risk_factors = [
                    RiskFactor(category=rf.category, severity=rf.severity, description=rf.description)
                    for rf in ld.risk_factors
                ]
                legs.append(RouteLeg(
                    sequence=ld.sequence,
                    origin=ld.origin,
                    destination=ld.destination,
                    transport_mode=ld.transport_mode,
                    duration=ld.duration,
                    cost=ld.cost,
                    risk_factors=risk_factors
                ))

            try:
                domain_routes.append(Route(
                id=uuid4(),
                shipment_id=shipment_id,
                route_name=rd.route_name,
                total_cost=rd.total_cost,
                transit_time=rd.transit_time,
                delay_probability=rd.delay_probability,
                reliability=rd.reliability,
                aggregate_risk=rd.aggregate_risk,
                feasibility_status=rd.feasibility_status,
                violated_constraints=rd.violated_constraints,
                legs=legs
            ))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        self.route_repo.save_all(domain_routes)
        return domain_routes


    def update_route(self, shipment_id: UUID, route_id: UUID, data: RouteCreate) -> Route:
        route = self.route_repo.get(route_id)
        if not route or route.shipment_id != shipment_id:
            raise HTTPException(status_code=404, detail="Route not found")
        
        legs = []
        for ld in data.legs:
            risk_factors = [
                RiskFactor(category=rf.category, severity=rf.severity, description=rf.description)
                for rf in ld.risk_factors
            ]
            legs.append(RouteLeg(
                sequence=ld.sequence,
                origin=ld.origin,
                destination=ld.destination,
                transport_mode=ld.transport_mode,
                duration=ld.duration,
                cost=ld.cost,
                risk_factors=risk_factors
            ))

        try:
            updated_route = Route(
            id=route_id,
            shipment_id=shipment_id,
            route_name=data.route_name,
            total_cost=data.total_cost,
            transit_time=data.transit_time,
            delay_probability=data.delay_probability,
            reliability=data.reliability,
            aggregate_risk=data.aggregate_risk,
            feasibility_status=data.feasibility_status,
            violated_constraints=data.violated_constraints,
            legs=legs
        )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        self.route_repo.save_all([updated_route])
        return updated_route

    def delete_route(self, shipment_id: UUID, route_id: UUID) -> None:
        route = self.route_repo.get(route_id)
        if not route or route.shipment_id != shipment_id:
            raise HTTPException(status_code=404, detail="Route not found")
        self.route_repo.delete(route_id)

    def get_routes(self, shipment_id: UUID) -> list[Route]:
        shipment = self.shipment_repo.get(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return self.route_repo.get_by_shipment(shipment_id)

    def run_optimization(self, shipment_id: UUID, profile_req: OptimizationProfileRequest):
        shipment = self.shipment_repo.get(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")

        routes = self.route_repo.get_by_shipment(shipment_id)
        if not routes:
            raise HTTPException(status_code=400, detail="Shipment has no routes to optimize")

        profile = OptimizationProfile(
            name=profile_req.name,
            cost_weight=profile_req.cost_weight,
            time_weight=profile_req.time_weight,
            reliability_weight=profile_req.reliability_weight,
            risk_weight=profile_req.risk_weight
        )

        result, _ = self.optimizer.optimize(shipment, routes, profile)

        # If all routes are infeasible, result.recommended_route_id will be None.
        # This is expected and we persist and return the result.
        self.opt_repo.save(result)

        return result

    def get_optimization_result(self, run_id: UUID):
        result = self.opt_repo.get(run_id)
        if not result:
            raise HTTPException(status_code=404, detail="Optimization run not found")
        return result
