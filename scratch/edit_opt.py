import re

with open('backend/app/services/optimization_service.py', 'r') as f:
    content = f.read()

additions = """
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
        self.route_repo.save_all([updated_route])
        return updated_route

    def delete_route(self, shipment_id: UUID, route_id: UUID) -> None:
        route = self.route_repo.get(route_id)
        if not route or route.shipment_id != shipment_id:
            raise HTTPException(status_code=404, detail="Route not found")
        self.route_repo.delete(route_id)
"""

content = content.replace('    def get_routes(self, shipment_id: UUID) -> list[Route]:', additions + '\n    def get_routes(self, shipment_id: UUID) -> list[Route]:')

with open('backend/app/services/optimization_service.py', 'w') as f:
    f.write(content)
