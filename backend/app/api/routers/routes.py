from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_optimization_repository,
    get_route_repository,
    get_shipment_repository,
)
from app.api.schemas.route import RouteCreate, RouteResponse
from app.domain.optimization.constraints import ConstraintEngine
from app.domain.optimization.pareto import ParetoAnalyzer
from app.domain.optimization.pipeline import RouteOptimizer
from app.domain.optimization.scoring import ScoringEngine
from app.infrastructure.repositories import (
    OptimizationResultRepository,
    RouteRepository,
    ShipmentRepository,
)
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/api/v1/shipments", tags=["Routes"])

def get_optimization_service(
    shipment_repo: ShipmentRepository = Depends(get_shipment_repository),
    route_repo: RouteRepository = Depends(get_route_repository),
    opt_repo: OptimizationResultRepository = Depends(get_optimization_repository)
) -> OptimizationService:
    optimizer = RouteOptimizer(ConstraintEngine(), ScoringEngine(), ParetoAnalyzer())
    return OptimizationService(shipment_repo, route_repo, opt_repo, optimizer)

@router.post("/{shipment_id}/routes", response_model=list[RouteResponse], status_code=201)
def create_routes(shipment_id: UUID, data: list[RouteCreate], service: OptimizationService = Depends(get_optimization_service)):
    return service.create_routes(shipment_id, data)

@router.get("/{shipment_id}/routes", response_model=list[RouteResponse])
def get_routes(shipment_id: UUID, service: OptimizationService = Depends(get_optimization_service)):
    return service.get_routes(shipment_id)
