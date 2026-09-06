from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.repositories import (
    OptimizationResultRepository,
    RouteRepository,
    ShipmentRepository,
)


def get_shipment_repository(db: Session = Depends(get_db)) -> ShipmentRepository:
    return ShipmentRepository(db)

def get_route_repository(db: Session = Depends(get_db)) -> RouteRepository:
    return RouteRepository(db)

def get_optimization_repository(db: Session = Depends(get_db)) -> OptimizationResultRepository:
    return OptimizationResultRepository(db)
