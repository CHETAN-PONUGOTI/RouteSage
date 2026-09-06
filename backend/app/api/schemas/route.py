from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import FeasibilityStatus, RiskCategory, TransportMode


class RiskFactorCreate(BaseModel):
    category: RiskCategory
    severity: float
    description: str

class RiskFactorResponse(RiskFactorCreate):
    pass

class RouteLegCreate(BaseModel):
    sequence: int
    origin: str
    destination: str
    transport_mode: TransportMode
    duration: float
    cost: float
    risk_factors: list[RiskFactorCreate] = []

class RouteLegResponse(RouteLegCreate):
    risk_factors: list[RiskFactorResponse] = []  # type: ignore

class RouteCreate(BaseModel):
    route_name: str
    total_cost: float
    transit_time: float
    delay_probability: float
    reliability: float
    aggregate_risk: float
    feasibility_status: FeasibilityStatus = FeasibilityStatus.PENDING
    violated_constraints: list[str] = []
    legs: list[RouteLegCreate]

class RouteResponse(RouteCreate):
    id: UUID
    shipment_id: UUID
    legs: List[RouteLegResponse]  # type: ignore

    model_config = ConfigDict(from_attributes=True)
