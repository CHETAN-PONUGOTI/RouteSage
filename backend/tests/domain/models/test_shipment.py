from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.domain.models.enums import CargoType, ShipmentPriority
from app.domain.models.shipment import Shipment


def test_shipment_valid_creation():
    shipment = Shipment(
        origin="Shanghai",
        destination="Los Angeles",
        cargo_type=CargoType.GENERAL,
        weight=1500.5,
        shipment_value=50000.0,
        delivery_deadline=datetime.now(timezone.utc),
        priority=ShipmentPriority.HIGH,
    )
    assert shipment.origin == "Shanghai"
    assert shipment.destination == "Los Angeles"
    assert shipment.weight == 1500.5
    assert shipment.priority == ShipmentPriority.HIGH
    assert shipment.id is not None
    assert shipment.created_at is not None


def test_shipment_invalid_weight():
    with pytest.raises(ValidationError):
        Shipment(
            origin="Shanghai",
            destination="Los Angeles",
            cargo_type=CargoType.GENERAL,
            weight=-5.0,  # Invalid weight
            shipment_value=50000.0,
            delivery_deadline=datetime.now(timezone.utc),
        )


def test_shipment_invalid_value():
    with pytest.raises(ValidationError):
        Shipment(
            origin="Shanghai",
            destination="Los Angeles",
            cargo_type=CargoType.GENERAL,
            weight=100.0,
            shipment_value=-10.0,  # Invalid value
            delivery_deadline=datetime.now(timezone.utc),
        )
