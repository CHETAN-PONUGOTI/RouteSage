from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OptimizationProfile(BaseModel):
    name: str = Field(..., min_length=1)
    cost_weight: float = Field(..., ge=0.0, le=1.0)
    time_weight: float = Field(..., ge=0.0, le=1.0)
    reliability_weight: float = Field(..., ge=0.0, le=1.0)
    risk_weight: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "OptimizationProfile":
        total = sum(
            [
                self.cost_weight,
                self.time_weight,
                self.reliability_weight,
                self.risk_weight,
            ]
        )
        if not (0.999 <= total <= 1.001):  # Handle floating point inaccuracies
            raise ValueError(
                f"Optimization weights must sum to 1.0. Current sum is {total}"
            )
        return self


class OptimizationResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    shipment_id: UUID
    profile: OptimizationProfile

    recommended_route_id: UUID | None = Field(default=None)
    feasible_routes: list[UUID] = Field(default_factory=list)
    infeasible_routes: list[UUID] = Field(default_factory=list)

    # Mapping of Route ID to overall score
    route_scores: dict[UUID, float] = Field(default_factory=dict)

    # Mapping of Route ID to breakdown contributions
    score_breakdown: dict[UUID, dict[str, float]] = Field(default_factory=dict)

    # Mapping of Route ID to constraint violation reasons
    constraint_results: dict[UUID, list[str]] = Field(default_factory=dict)

    # Trade-offs and Pareto dominance details
    tradeoffs: dict[str, str] = Field(default_factory=dict)

    execution_time_ms: float = Field(..., ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(frozen=True)
