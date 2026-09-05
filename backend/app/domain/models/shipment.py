from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.enums import CargoType, ShipmentPriority


class Shipment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    cargo_type: CargoType
    weight: float = Field(..., gt=0, description="Weight in kg")
    shipment_value: float = Field(..., ge=0, description="Value in USD")
    delivery_deadline: datetime
    priority: ShipmentPriority = Field(default=ShipmentPriority.STANDARD)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(frozen=True)
