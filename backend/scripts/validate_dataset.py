import math
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from app.domain.services.synthetic_data import import_dataset


def run_validation(file_path: str):
    print(f"Validating dataset from {file_path}")
    shipments, routes = import_dataset(file_path)

    assert len(shipments) > 0, "No shipments found"
    assert len(routes) > 0, "No routes found"

    shipment_ids = {s.id for s in shipments}

    route_counts = {s.id: 0 for s in shipments}

    for route in routes:
        assert route.shipment_id in shipment_ids, (
            f"Route {route.id} has invalid shipment_id"
        )
        route_counts[route.shipment_id] += 1

        # Verify probabilities and bounds
        assert 0.0 <= route.delay_probability <= 1.0, (
            f"Invalid delay_prob {route.delay_probability}"
        )
        assert 0.0 <= route.reliability <= 1.0, (
            f"Invalid reliability {route.reliability}"
        )
        assert 0.0 <= route.aggregate_risk <= 1.0, (
            f"Invalid aggregate_risk {route.aggregate_risk}"
        )

        # Verify leg consistency
        leg_cost = sum(leg.cost for leg in route.legs)
        leg_time = sum(leg.duration for leg in route.legs)

        assert math.isclose(leg_cost, route.total_cost, rel_tol=1e-5), (
            f"Cost mismatch: {leg_cost} != {route.total_cost}"
        )
        assert math.isclose(leg_time, route.transit_time, rel_tol=1e-5), (
            f"Time mismatch: {leg_time} != {route.transit_time}"
        )

        # Continuity is guaranteed by Pydantic Route model, but we implicitly check it by importing successfully

    for s_id, count in route_counts.items():
        assert count > 1, (
            f"Shipment {s_id} has insufficient route alternatives: {count}"
        )

    print("Validation passed successfully! Data is consistent.")


def main():
    data_dir = Path(__file__).parent.parent.parent / "data"
    dataset_file = data_dir / "synthetic_dataset.json"

    if not dataset_file.exists():
        print("Dataset not found. Please run generate_dataset.py first.")
        sys.exit(1)

    run_validation(str(dataset_file))


if __name__ == "__main__":
    main()
