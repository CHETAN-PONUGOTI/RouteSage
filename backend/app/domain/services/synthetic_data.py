import json
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5

from app.domain.models.enums import (
    CargoType,
    RiskCategory,
    ShipmentPriority,
    TransportMode,
)
from app.domain.models.route import RiskFactor, Route, RouteLeg
from app.domain.models.shipment import Shipment

NAMESPACE_SAFIRI = UUID("12345678-1234-5678-1234-567812345678")


def generate_deterministic_uuid(seed_string: str) -> UUID:
    return uuid5(NAMESPACE_SAFIRI, seed_string)


class SyntheticDataGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

        self.locations = [
            "Shanghai",
            "Singapore",
            "Rotterdam",
            "Los Angeles",
            "New York",
            "Hamburg",
            "Dubai",
            "Antwerp",
            "Shenzhen",
            "Busan",
        ]

    def generate_shipments(self, count: int = 30) -> list[Shipment]:
        shipments = []
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)

        for i in range(count):
            origin, dest = self.rng.sample(self.locations, 2)
            cargo = self.rng.choice(list(CargoType))
            priority = self.rng.choice(list(ShipmentPriority))

            # Generate reproducible values
            s_id = generate_deterministic_uuid(f"shipment_{self.seed}_{i}")
            weight = round(self.rng.uniform(100.0, 50000.0), 2)
            value = round(self.rng.uniform(5000.0, 1000000.0), 2)

            # Deadline between 7 and 45 days
            days_to_deadline = self.rng.randint(7, 45)
            deadline = now + timedelta(days=days_to_deadline)

            shipments.append(
                Shipment(
                    id=s_id,
                    origin=origin,
                    destination=dest,
                    cargo_type=cargo,
                    weight=weight,
                    shipment_value=value,
                    delivery_deadline=deadline,
                    priority=priority,
                    created_at=now,
                    updated_at=now,
                )
            )

        return shipments

    def _generate_route_alternatives(self, shipment: Shipment) -> list[Route]:
        routes = []
        base_cost = self.rng.uniform(2000.0, 10000.0)
        base_time = self.rng.uniform(10.0, 30.0)

        # We will generate 4 profiles:
        # 1. Balanced: Average cost, average time
        # 2. Cheap & Slow: Lower cost, higher time, higher delay prob
        # 3. Fast & Expensive: Higher cost, lower time, high reliability
        # 4. High Risk & Cheap: Very low cost, very high risk and delay prob

        profiles = [
            (
                "Balanced Route",
                1.0,
                1.0,
                0.8,
                0.2,
            ),  # cost_mult, time_mult, reliability, risk
            ("Economy Route", 0.7, 1.5, 0.6, 0.4),
            ("Express Route", 1.8, 0.6, 0.95, 0.1),
            ("High-Risk Low-Cost", 0.5, 1.2, 0.4, 0.8),
        ]

        for idx, (name, cost_m, time_m, base_rel, base_risk) in enumerate(profiles):
            r_id = generate_deterministic_uuid(f"route_{shipment.id}_{idx}")

            # Add some noise
            actual_cost = base_cost * cost_m * self.rng.uniform(0.9, 1.1)
            actual_time = base_time * time_m * self.rng.uniform(0.9, 1.1)
            reliability = min(1.0, max(0.0, base_rel * self.rng.uniform(0.9, 1.1)))
            aggregate_risk = min(1.0, max(0.0, base_risk * self.rng.uniform(0.9, 1.1)))
            delay_prob = 1.0 - reliability  # Inverse relationship roughly

            # Create legs
            legs = []
            num_legs = self.rng.randint(1, 3)

            leg_duration_avg = actual_time / num_legs
            leg_cost_avg = actual_cost / num_legs

            current_origin = shipment.origin

            for leg_idx in range(num_legs):
                is_last = leg_idx == num_legs - 1
                dest = (
                    shipment.destination if is_last else self.rng.choice(self.locations)
                )
                while dest == current_origin:
                    dest = self.rng.choice(self.locations)

                mode = self.rng.choice(list(TransportMode))

                # Assign risks based on overall route risk
                risk_factors = []
                if aggregate_risk > 0.3:
                    cat = self.rng.choice(list(RiskCategory))
                    risk_factors.append(
                        RiskFactor(
                            category=cat,
                            severity=round(aggregate_risk, 2),
                            description=f"Simulated {cat.value.lower()} risk",
                        )
                    )

                legs.append(
                    RouteLeg(
                        sequence=leg_idx + 1,
                        origin=current_origin,
                        destination=dest,
                        transport_mode=mode,
                        duration=round(
                            leg_duration_avg * self.rng.uniform(0.8, 1.2), 2
                        ),
                        cost=round(leg_cost_avg * self.rng.uniform(0.8, 1.2), 2),
                        risk_factors=risk_factors,
                    )
                )
                current_origin = dest

            # Recalculate totals from legs to ensure mathematical consistency
            total_leg_cost = sum(l.cost for l in legs)
            total_leg_time = sum(l.duration for l in legs)

            routes.append(
                Route(
                    id=r_id,
                    shipment_id=shipment.id,
                    route_name=name,
                    total_cost=round(total_leg_cost, 2),
                    transit_time=round(total_leg_time, 2),
                    delay_probability=round(delay_prob, 2),
                    reliability=round(reliability, 2),
                    aggregate_risk=round(aggregate_risk, 2),
                    legs=legs,
                )
            )

        return routes

    def generate_dataset(self) -> tuple[list[Shipment], list[Route]]:
        shipments = self.generate_shipments(30)
        all_routes = []
        for s in shipments:
            all_routes.extend(self._generate_route_alternatives(s))
        return shipments, all_routes


def export_dataset(shipments: list[Shipment], routes: list[Route], file_path: str):
    data = {
        "shipments": [json.loads(s.model_dump_json()) for s in shipments],
        "routes": [json.loads(r.model_dump_json()) for r in routes],
    }
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def import_dataset(file_path: str) -> tuple[list[Shipment], list[Route]]:
    with open(file_path, "r") as f:
        data = json.load(f)

    shipments = [Shipment.model_validate(s) for s in data["shipments"]]
    routes = [Route.model_validate(r) for r in data["routes"]]

    return shipments, routes
