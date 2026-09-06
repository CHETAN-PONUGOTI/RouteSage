import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.domain.services.evaluation import DecisionSystemEvaluator
from app.domain.services.synthetic_data import SyntheticDataGenerator

def run_evaluation():
    print("Initializing Synthetic Data Generator...")
    data_gen = SyntheticDataGenerator(seed=42)
    
    print("Generating synthetic dataset (30 shipments with ~4 routes each)...")
    shipments, all_routes = data_gen.generate_dataset()
    
    # Group routes by shipment_id
    routes_by_shipment = {}
    for r in all_routes:
        routes_by_shipment.setdefault(r.shipment_id, []).append(r)
    
    print("Evaluating Decision System...")
    evaluator = DecisionSystemEvaluator()
    metrics = evaluator.evaluate(shipments, routes_by_shipment)
    
    print("\n--- Evaluation Metrics ---")
    print(f"Total Shipments Evaluated: {metrics.total_shipments}")
    print(f"Total Routes Evaluated: {metrics.total_routes_evaluated}")
    print(f"Shipments with Feasible Route: {metrics.shipments_with_feasible_route}")
    print(f"Shipments with No Feasible Route: {metrics.shipments_with_no_feasible_route}")
    print(f"Recommendation Count: {metrics.recommendation_count}")
    print(f"Infeasible Routes Recommended (Should be 0): {metrics.infeasible_route_recommended_count}")
    print(f"Average Recommended Cost: ${metrics.avg_recommended_cost:.2f}")
    print(f"Average Recommended Transit Time: {metrics.avg_recommended_transit_time:.2f} hours")
    print(f"Average Recommended Reliability: {metrics.avg_recommended_reliability:.4f}")
    print(f"Average Recommended Risk: {metrics.avg_recommended_risk:.4f}")
    print(f"Recommendations that are also Pareto-efficient: {metrics.pareto_winner_overlap_count} / {metrics.recommendation_count}")
    print(f"Deterministic Repeatability: {'PASS' if metrics.deterministic_repeatability else 'FAIL'}")

if __name__ == "__main__":
    run_evaluation()
