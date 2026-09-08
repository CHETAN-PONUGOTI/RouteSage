import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.optimization import OptimizationResult
from app.domain.models.route import Route
from app.domain.models.shipment import Shipment
from app.infrastructure.mappers import DataMapper
from app.infrastructure.models import (
    OptimizationProfileModel,
    OptimizationRunModel,
    RouteModel,
    ShipmentModel,
)


class ShipmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, shipment: Shipment) -> None:
        model = DataMapper.to_orm_shipment(shipment)
        self.session.merge(model)
        self.session.commit()

    def get(self, shipment_id: UUID) -> Shipment | None:
        model = self.session.query(ShipmentModel).filter(ShipmentModel.id == shipment_id).first()
        if not model:
            return None
        return DataMapper.to_domain_shipment(model)

    def list(self) -> list[Shipment]:
        models = self.session.query(ShipmentModel).all()
        return [DataMapper.to_domain_shipment(m) for m in models]


class RouteRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_all(self, routes: list[Route]) -> None:
        for route in routes:
            model = DataMapper.to_orm_route(route)
            self.session.merge(model)
        self.session.commit()


    def save(self, route: Route) -> None:
        model = DataMapper.to_orm_route(route)
        self.session.merge(model)
        self.session.commit()

    def get(self, route_id: UUID) -> Route | None:
        model = self.session.query(RouteModel).filter(RouteModel.id == route_id).first()
        if not model:
            return None
        return DataMapper.to_domain_route(model)

    def delete(self, route_id: UUID) -> None:
        model = self.session.query(RouteModel).filter(RouteModel.id == route_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    def get_by_shipment(self, shipment_id: UUID) -> list[Route]:
        models = (
            self.session.query(RouteModel)
            .filter(RouteModel.shipment_id == shipment_id)
            .all()
        )
        return [DataMapper.to_domain_route(m) for m in models]


class OptimizationResultRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, result: OptimizationResult) -> None:
        # Save profile first if it doesn't exist
        # We need a stable ID for the profile based on its values to avoid duplication,
        # but for now we generate a UUID based on name and weights.
        profile_str = f"{result.profile.name}-{result.profile.cost_weight}-{result.profile.time_weight}-{result.profile.reliability_weight}-{result.profile.risk_weight}"
        profile_id = uuid.uuid5(uuid.NAMESPACE_OID, profile_str)

        profile_model = (
            self.session.query(OptimizationProfileModel)
            .filter(OptimizationProfileModel.id == profile_id)
            .first()
        )
        if not profile_model:
            profile_model = DataMapper.to_orm_profile(result.profile, profile_id)
            self.session.merge(profile_model)

        run_model = DataMapper.to_orm_optimization_result(result, profile_id)
        self.session.merge(run_model)
        self.session.commit()

    def get(self, result_id: UUID) -> OptimizationResult | None:
        run_model = (
            self.session.query(OptimizationRunModel)
            .filter(OptimizationRunModel.id == result_id)
            .first()
        )
        if not run_model:
            return None

        profile_model = self.session.query(OptimizationProfileModel).filter(OptimizationProfileModel.id == run_model.profile_id).first()
        if not profile_model:
            raise ValueError("Optimization profile not found for result")
        
        profile = DataMapper.to_domain_profile(profile_model)

        return DataMapper.to_domain_optimization_result(run_model, profile)
