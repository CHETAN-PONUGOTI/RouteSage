from __future__ import annotations

from pathlib import Path

import pytest
from app.infrastructure.database import Base
from app.infrastructure.repositories import RouteRepository, ShipmentRepository
from scripts.seed_database import seed_database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()


def test_seed_database_loads_records(test_db_session):
    s_repo = ShipmentRepository(test_db_session)
    r_repo = RouteRepository(test_db_session)

    # Initial state is empty
    assert len(s_repo.list()) == 0

    # Seed using the actual synthetic dataset
    s_count, r_count = seed_database(session=test_db_session)

    assert s_count == 30
    assert r_count == 120

    # Verify records in database
    shipments = s_repo.list()
    assert len(shipments) == 30

    first_shipment = shipments[0]
    routes = r_repo.get_by_shipment(first_shipment.id)
    assert len(routes) == 4


def test_seed_database_skips_when_already_populated(test_db_session):
    # First seed
    s_count1, _ = seed_database(session=test_db_session)
    assert s_count1 == 30

    # Second seed without force should skip
    s_count2, r_count2 = seed_database(session=test_db_session, force=False)
    assert s_count2 == 0
    assert r_count2 == 0

    # Third seed with force should re-seed
    s_count3, r_count3 = seed_database(session=test_db_session, force=True)
    assert s_count3 == 30
    assert r_count3 == 120


def test_seed_database_missing_file_raises_error(test_db_session):
    with pytest.raises(FileNotFoundError):
        seed_database(
            session=test_db_session,
            dataset_path=Path("non_existent_dataset.json"),
        )
