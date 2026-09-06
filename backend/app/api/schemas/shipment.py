from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import CargoType, ShipmentPriority


class ShipmentCreate(BaseModel):
    origin: str
    destination: str
    cargo_type: CargoType
    weight: float
    shipment_value: float
    delivery_deadline: datetime
    priority: ShipmentPriority

class ShipmentResponse(ShipmentCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
