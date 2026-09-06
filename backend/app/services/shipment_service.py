from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.api.schemas.shipment import ShipmentCreate
from app.domain.models.shipment import Shipment
from app.infrastructure.repositories import ShipmentRepository


class ShipmentService:
    def __init__(self, repository: ShipmentRepository):
        self.repository = repository

    def create_shipment(self, data: ShipmentCreate) -> Shipment:
        now = datetime.now(timezone.utc)
        shipment = Shipment(
            id=uuid4(),
            origin=data.origin,
            destination=data.destination,
            cargo_type=data.cargo_type,
            weight=data.weight,
            shipment_value=data.shipment_value,
            delivery_deadline=data.delivery_deadline,
            priority=data.priority,
            created_at=now,
            updated_at=now
        )
        self.repository.save(shipment)
        return shipment

    def get_shipment(self, shipment_id: UUID) -> Shipment:
        shipment = self.repository.get(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return shipment

    def list_shipments(self) -> list[Shipment]:
        return self.repository.list()
