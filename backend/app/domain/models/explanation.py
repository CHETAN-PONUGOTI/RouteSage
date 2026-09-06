from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScoreDriver(BaseModel):
    objective: str
    contribution: float


class RouteEvidence(BaseModel):
    route_id: UUID
    route_name: str
    is_feasible: bool
    total_score: float | None = None
    score_drivers: list[ScoreDriver] = Field(default_factory=list)
    constraint_violations: list[str] = Field(default_factory=list)
    is_pareto_efficient: bool = False
    is_recommended: bool = False


class ExplanationEvidence(BaseModel):
    run_id: UUID
    shipment_id: UUID
    has_feasible_routes: bool
    recommended_route_id: UUID | None = None
    weights: dict[str, float]
    routes: list[RouteEvidence] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class StructuredExplanation(BaseModel):
    """Structured output from the LLM - validated before use."""

    recommended_route_name: str
    reasons: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    constraint_notes: list[str] = Field(default_factory=list)


class ExplanationResponse(BaseModel):
    explanation: str
    generated_by: str  # "deterministic" or "gemini"
    run_id: UUID
