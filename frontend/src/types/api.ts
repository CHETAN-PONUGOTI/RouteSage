export type CargoType = "GENERAL" | "PERISHABLE" | "HAZARDOUS" | "FRAGILE";
export type ShipmentPriority = "STANDARD" | "HIGH" | "URGENT";
export type TransportMode = "SEA" | "AIR" | "RAIL" | "ROAD";
export type FeasibilityStatus = "PENDING" | "FEASIBLE" | "INFEASIBLE";
export type RiskCategory = "CONGESTION" | "GEOPOLITICAL" | "WEATHER" | "OPERATIONAL";

export interface Shipment {
  id: string;
  origin: string;
  destination: string;
  cargo_type: CargoType;
  weight: number;
  shipment_value: number;
  delivery_deadline: string;
  priority: ShipmentPriority;
  created_at: string;
  updated_at: string;
}

export interface RiskFactor {
  category: RiskCategory;
  severity: number;
  description: string;
}

export interface RouteLeg {
  sequence: number;
  origin: string;
  destination: string;
  transport_mode: TransportMode;
  duration: number;
  cost: number;
  risk_factors: RiskFactor[];
}

export interface Route {
  id: string;
  shipment_id: string;
  route_name: string;
  total_cost: number;
  transit_time: number;
  delay_probability: number;
  reliability: number;
  aggregate_risk: number;
  feasibility_status: FeasibilityStatus;
  violated_constraints: string[];
  legs: RouteLeg[];
}

export interface OptimizationProfile {
  name: string;
  cost_weight: number;
  time_weight: number;
  reliability_weight: number;
  risk_weight: number;
}

export interface OptimizationResult {
  id: string;
  shipment_id: string;
  recommended_route_id: string | null;
  feasible_routes: string[];
  infeasible_routes: string[];
  route_scores: Record<string, number>;
  score_breakdown: Record<string, Record<string, number>>;
  constraint_results: Record<string, string[]>;
  tradeoffs: Record<string, string[]>;
  sensitivity: Record<string, any> | null;
  execution_time_ms: number;
  created_at: string;
  profile: OptimizationProfile;
}
