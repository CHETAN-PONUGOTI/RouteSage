from uuid import uuid4

import pytest
from app.domain.models.enums import FeasibilityStatus, RiskCategory, TransportMode
from app.domain.models.route import RiskFactor, Route, RouteLeg
from pydantic import ValidationError


def test_route_creation_valid():
    leg1 = RouteLeg(
        sequence=1,
        origin="Port A",
        destination="Port B",
        transport_mode=TransportMode.SEA,
        duration=5.0,
        cost=1000.0,
        risk_factors=[
            RiskFactor(
                category=RiskCategory.WEATHER, severity=0.2, description="Minor storms"
            )
        ],
    )
    leg2 = RouteLeg(
        sequence=2,
        origin="Port B",
        destination="City C",
        transport_mode=TransportMode.ROAD,
        duration=2.0,
        cost=500.0,
    )

    route = Route(
        shipment_id=uuid4(),
        route_name="Standard Route",
        total_cost=1500.0,
        transit_time=7.0,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=0.15,
        legs=[leg1, leg2],
    )

    assert route.route_name == "Standard Route"
    assert len(route.legs) == 2
    assert route.feasibility_status == FeasibilityStatus.PENDING


def test_route_leg_discontinuity():
    leg1 = RouteLeg(
        sequence=1,
        origin="Port A",
        destination="Port B",
        transport_mode=TransportMode.SEA,
        duration=5.0,
        cost=1000.0,
    )
    leg2 = RouteLeg(
        sequence=2,
        origin="Port Z",  # Disconnected origin
        destination="City C",
        transport_mode=TransportMode.ROAD,
        duration=2.0,
        cost=500.0,
    )

    with pytest.raises(ValidationError, match="Route discontinuity"):
        Route(
            shipment_id=uuid4(),
            route_name="Broken Route",
            total_cost=1500.0,
            transit_time=7.0,
            delay_probability=0.1,
            reliability=0.9,
            aggregate_risk=0.15,
            legs=[leg1, leg2],
        )


def test_route_leg_bad_sequence():
    leg1 = RouteLeg(
        sequence=1,
        origin="Port A",
        destination="Port B",
        transport_mode=TransportMode.SEA,
        duration=5.0,
        cost=1000.0,
    )
    leg2 = RouteLeg(
        sequence=3,  # Should be 2
        origin="Port B",
        destination="City C",
        transport_mode=TransportMode.ROAD,
        duration=2.0,
        cost=500.0,
    )

    with pytest.raises(ValidationError, match="Leg sequences must be contiguous"):
        Route(
            shipment_id=uuid4(),
            route_name="Bad Sequence Route",
            total_cost=1500.0,
            transit_time=7.0,
            delay_probability=0.1,
            reliability=0.9,
            aggregate_risk=0.15,
            legs=[leg1, leg2],
        )


def test_route_invalid_probability():
    leg1 = RouteLeg(
        sequence=1,
        origin="A",
        destination="B",
        transport_mode=TransportMode.ROAD,
        duration=1.0,
        cost=1.0,
    )

    with pytest.raises(ValidationError):
        Route(
            shipment_id=uuid4(),
            route_name="Invalid Prob",
            total_cost=10.0,
            transit_time=1.0,
            delay_probability=1.5,  # Invalid
            reliability=0.9,
            aggregate_risk=0.1,
            legs=[leg1],
        )
