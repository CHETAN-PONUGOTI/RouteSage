from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from app.domain.models.enums import (
    CargoType,
    FeasibilityStatus,
    ShipmentPriority,
    TransportMode,
)
from app.domain.models.optimization import OptimizationProfile, OptimizationResult
from app.domain.models.route import Route, RouteLeg
from app.domain.models.shipment import Shipment
from app.infrastructure.database import Base
from app.infrastructure.repositories import (
    OptimizationResultRepository,
    RouteRepository,
    ShipmentRepository,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_session():
    # Use in-memory SQLite for testing persistence
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_shipment_persistence(db_session):
    repo = ShipmentRepository(db_session)
    now = datetime.now(timezone.utc)

    shipment = Shipment(
        id=uuid4(),
        origin="Shanghai",
        destination="Rotterdam",
        cargo_type=CargoType.HAZARDOUS,
        weight=2500.0,
        shipment_value=500000.0,
        delivery_deadline=now + timedelta(days=30),
        priority=ShipmentPriority.HIGH,
        created_at=now,
        updated_at=now,
    )

    repo.save(shipment)

    fetched = repo.get(shipment.id)
    assert fetched is not None
    assert fetched.id == shipment.id
    assert fetched.origin == "Shanghai"
    assert fetched.cargo_type == CargoType.HAZARDOUS
    assert fetched.weight == 2500.0


def test_route_persistence(db_session):
    # Route depends on Shipment for FK constraint
    ship_repo = ShipmentRepository(db_session)
    now = datetime.now(timezone.utc)
    shipment_id = uuid4()

    ship = Shipment(
        id=shipment_id,
        origin="A",
        destination="B",
        cargo_type=CargoType.GENERAL,
        weight=100.0,
        shipment_value=100.0,
        delivery_deadline=now,
        priority=ShipmentPriority.STANDARD,
        created_at=now,
        updated_at=now,
    )
    ship_repo.save(ship)

    repo = RouteRepository(db_session)

    route = Route(
        id=uuid4(),
        shipment_id=shipment_id,
        route_name="Fastest",
        total_cost=5000.0,
        transit_time=12.0,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=0.2,
        feasibility_status=FeasibilityStatus.FEASIBLE,
        legs=[
            RouteLeg(
                sequence=1,
                origin="A",
                destination="B",
                transport_mode=TransportMode.AIR,
                duration=12.0,
                cost=5000.0,
            )
        ],
    )

    repo.save_all([route])

    fetched = repo.get_by_shipment(shipment_id)
    assert len(fetched) == 1
    assert fetched[0].id == route.id
    assert fetched[0].route_name == "Fastest"
    assert len(fetched[0].legs) == 1
    assert fetched[0].legs[0].transport_mode == TransportMode.AIR


def test_optimization_result_persistence(db_session):
    ship_repo = ShipmentRepository(db_session)
    route_repo = RouteRepository(db_session)
    opt_repo = OptimizationResultRepository(db_session)

    now = datetime.now(timezone.utc)
    shipment_id = uuid4()

    ship = Shipment(
        id=shipment_id,
        origin="A",
        destination="B",
        cargo_type=CargoType.GENERAL,
        weight=100.0,
        shipment_value=100.0,
        delivery_deadline=now,
        priority=ShipmentPriority.STANDARD,
        created_at=now,
        updated_at=now,
    )
    ship_repo.save(ship)

    profile = OptimizationProfile(
        name="Test",
        cost_weight=0.5,
        time_weight=0.5,
        reliability_weight=0.0,
        risk_weight=0.0,
    )

    r_id = uuid4()
    route = Route(
        id=r_id,
        shipment_id=shipment_id,
        route_name="R1",
        total_cost=10,
        transit_time=10,
        delay_probability=0.1,
        reliability=0.9,
        aggregate_risk=0.1,
        feasibility_status=FeasibilityStatus.FEASIBLE,
        legs=[
            RouteLeg(
                sequence=1,
                origin="A",
                destination="B",
                transport_mode=TransportMode.SEA,
                duration=10,
                cost=10,
            )
        ],
    )
    route_repo.save_all([route])

    result = OptimizationResult(
        id=uuid4(),
        shipment_id=shipment_id,
        profile=profile,
        recommended_route_id=r_id,
        feasible_routes=[r_id],
        infeasible_routes=[],
        route_scores={r_id: 0.99},
        score_breakdown={r_id: {"cost": 0.5}},
        constraint_results={},
        tradeoffs={"pareto_efficient": [str(r_id)]},
        sensitivity={"is_robust": True},
        execution_time_ms=50.0,
    )

    opt_repo.save(result)

    fetched = opt_repo.get(result.id)

    assert fetched is not None
    assert fetched.recommended_route_id == r_id
    assert fetched.route_scores[r_id] == 0.99
    assert fetched.tradeoffs["pareto_efficient"] == [str(r_id)]
    assert fetched.sensitivity["is_robust"] is True
    assert fetched.profile.name == "Test"
