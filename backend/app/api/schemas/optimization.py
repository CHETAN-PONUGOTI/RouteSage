from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OptimizationProfileRequest(BaseModel):
    name: str = "Custom Profile"
    cost_weight: float
    time_weight: float
    reliability_weight: float
    risk_weight: float

class OptimizationRequest(BaseModel):
    profile: OptimizationProfileRequest

class OptimizationResponse(BaseModel):
    id: UUID
    shipment_id: UUID
    recommended_route_id: UUID | None
    feasible_routes: list[UUID]
    infeasible_routes: list[UUID]
    route_scores: dict[UUID, float]
    score_breakdown: dict[UUID, dict[str, float]]
    constraint_results: dict[UUID, list[str]]
    tradeoffs: dict[str, list[str]]
    sensitivity: dict[str, Any] | None
    execution_time_ms: float
    created_at: datetime
    profile: OptimizationProfileRequest

    model_config = ConfigDict(from_attributes=True)
