from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_optimization_repository,
    get_route_repository,
    get_shipment_repository,
)
from app.api.schemas.optimization import OptimizationRequest, OptimizationResponse
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

router = APIRouter(tags=["Optimization"])

def get_optimization_service(
    shipment_repo: ShipmentRepository = Depends(get_shipment_repository),
    route_repo: RouteRepository = Depends(get_route_repository),
    opt_repo: OptimizationResultRepository = Depends(get_optimization_repository)
) -> OptimizationService:
    optimizer = RouteOptimizer(ConstraintEngine(), ScoringEngine(), ParetoAnalyzer())
    return OptimizationService(shipment_repo, route_repo, opt_repo, optimizer)

@router.post("/api/v1/shipments/{shipment_id}/optimize", response_model=OptimizationResponse)
def run_optimization(shipment_id: UUID, request: OptimizationRequest, service: OptimizationService = Depends(get_optimization_service)):
    return service.run_optimization(shipment_id, request.profile)

@router.get("/api/v1/optimization-runs/{run_id}", response_model=OptimizationResponse)
def get_optimization_result(run_id: UUID, service: OptimizationService = Depends(get_optimization_service)):
    return service.get_optimization_result(run_id)
