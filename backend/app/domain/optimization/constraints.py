from pydantic import BaseModel, ConfigDict

from app.domain.models.enums import FeasibilityStatus
from app.domain.models.route import Route
from app.domain.models.shipment import Shipment


class HardConstraints(BaseModel):
    max_transit_time_days: float | None = None
    max_total_cost: float | None = None
    max_aggregate_risk: float | None = None

    model_config = ConfigDict(frozen=True)


class ConstraintEngine:
    def __init__(self, custom_constraints: HardConstraints | None = None):
        self.custom_constraints = custom_constraints or HardConstraints()

    def evaluate_route(self, shipment: Shipment, route: Route) -> Route:
        """
        Evaluates a route against the shipment's inherent constraints and any
        custom hard constraints. Returns a new Route instance with updated status.
        """
        violations: list[str] = []

        # 1. Inherent Shipment Constraint: Delivery Deadline
        time_available_days = (
            shipment.delivery_deadline - shipment.created_at
        ).total_seconds() / 86400.0
        if route.transit_time > time_available_days:
            violations.append(
                f"DELIVERY_DEADLINE_EXCEEDED: Route transit time ({route.transit_time}d) "
                f"exceeds available time ({time_available_days:.1f}d)"
            )

        # 2. Custom Max Transit Time
        if (
            self.custom_constraints.max_transit_time_days is not None
            and route.transit_time > self.custom_constraints.max_transit_time_days
        ):
            violations.append(
                f"MAX_TRANSIT_TIME_EXCEEDED: Route transit time ({route.transit_time}d) "
                f"exceeds maximum allowed ({self.custom_constraints.max_transit_time_days}d)"
            )

        # 3. Custom Max Cost
        if (
            self.custom_constraints.max_total_cost is not None
            and route.total_cost > self.custom_constraints.max_total_cost
        ):
            violations.append(
                f"MAX_COST_EXCEEDED: Route cost (${route.total_cost:.2f}) "
                f"exceeds maximum allowed (${self.custom_constraints.max_total_cost:.2f})"
            )

        # 4. Custom Max Risk
        if (
            self.custom_constraints.max_aggregate_risk is not None
            and route.aggregate_risk > self.custom_constraints.max_aggregate_risk
        ):
            violations.append(
                f"MAX_RISK_EXCEEDED: Route aggregate risk ({route.aggregate_risk:.2f}) "
                f"exceeds maximum allowed ({self.custom_constraints.max_aggregate_risk:.2f})"
            )

        status = (
            FeasibilityStatus.INFEASIBLE if violations else FeasibilityStatus.FEASIBLE
        )

        # Use model_copy to preserve immutability
        return route.model_copy(
            update={"feasibility_status": status, "violated_constraints": violations}
        )

    def evaluate_routes(self, shipment: Shipment, routes: list[Route]) -> list[Route]:
        """Evaluates a list of routes and returns a new list of updated routes."""
        return [self.evaluate_route(shipment, route) for route in routes]
