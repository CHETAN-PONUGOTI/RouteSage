from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.models.enums import FeasibilityStatus, RiskCategory, TransportMode


class RiskFactor(BaseModel):
    category: RiskCategory
    severity: float = Field(
        ..., ge=0.0, le=1.0, description="Risk severity from 0.0 to 1.0"
    )
    description: str = Field(..., min_length=1)

    model_config = ConfigDict(frozen=True)


class RouteLeg(BaseModel):
    sequence: int = Field(..., ge=0)
    origin: str = Field(..., min_length=1)
    destination: str = Field(..., min_length=1)
    transport_mode: TransportMode
    duration: float = Field(..., gt=0, description="Duration in days")
    cost: float = Field(..., ge=0, description="Cost in USD")
    risk_factors: list[RiskFactor] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class Route(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    shipment_id: UUID
    route_name: str = Field(..., min_length=1)

    # Aggregated metrics (typically populated during route construction/generation)
    total_cost: float = Field(..., ge=0)
    transit_time: float = Field(..., gt=0)
    delay_probability: float = Field(..., ge=0.0, le=1.0)
    reliability: float = Field(..., ge=0.0, le=1.0)
    aggregate_risk: float = Field(..., ge=0.0, le=1.0)

    feasibility_status: FeasibilityStatus = Field(default=FeasibilityStatus.PENDING)
    violated_constraints: list[str] = Field(default_factory=list)
    legs: list[RouteLeg] = Field(..., min_length=1)

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="after")
    def validate_leg_continuity(self) -> "Route":
        if not self.legs:
            return self

        # Ensure sequence numbers are correct and locations connect
        sorted_legs = sorted(self.legs, key=lambda x: x.sequence)

        # We can validate sequence numbers are contiguous
        for i, leg in enumerate(sorted_legs):
            if leg.sequence != i + 1:
                raise ValueError(
                    f"Leg sequences must be contiguous starting from 1. Found {leg.sequence} at index {i}."
                )

            if i > 0:
                prev_leg = sorted_legs[i - 1]
                if prev_leg.destination != leg.origin:
                    raise ValueError(
                        f"Route discontinuity: Leg {prev_leg.sequence} destination ({prev_leg.destination}) "
                        f"does not match Leg {leg.sequence} origin ({leg.origin})"
                    )
        return self
