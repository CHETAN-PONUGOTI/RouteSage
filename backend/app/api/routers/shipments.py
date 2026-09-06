from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_shipment_repository
from app.api.schemas.shipment import ShipmentCreate, ShipmentResponse
from app.infrastructure.repositories import ShipmentRepository
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/api/v1/shipments", tags=["Shipments"])

def get_shipment_service(repo: ShipmentRepository = Depends(get_shipment_repository)) -> ShipmentService:
    return ShipmentService(repo)

@router.post("", response_model=ShipmentResponse, status_code=201)
def create_shipment(data: ShipmentCreate, service: ShipmentService = Depends(get_shipment_service)):
    return service.create_shipment(data)

@router.get("", response_model=list[ShipmentResponse])
def list_shipments(service: ShipmentService = Depends(get_shipment_service)):
    return service.list_shipments()

@router.get("/{shipment_id}", response_model=ShipmentResponse)
def get_shipment(shipment_id: UUID, service: ShipmentService = Depends(get_shipment_service)):
    return service.get_shipment(shipment_id)
