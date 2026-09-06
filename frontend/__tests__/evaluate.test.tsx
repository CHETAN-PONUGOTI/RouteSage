import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import EvaluatePage from "../src/app/shipments/[shipmentId]/evaluate/page";
import { apiService } from "../src/services/api";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useParams: () => ({ shipmentId: "test-shipment-id" }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/shipments/test-shipment-id/evaluate"
}));

jest.mock("../src/services/api", () => ({
  apiService: {
    getShipment: jest.fn(),
    getRoutes: jest.fn(),
    runOptimization: jest.fn(),
    getOptimizationRun: jest.fn(),
    getExplanation: jest.fn(),
  }
}));

const mockShipment = {
  id: "test-shipment-id",
  origin: "New York",
  destination: "London",
  cargo_type: "GENERAL",
  weight: 1000,
  shipment_value: 50000,
  delivery_deadline: new Date().toISOString(),
  priority: "STANDARD",
};

const mockRoutes = [
  {
    id: "route-1",
    route_name: "Fast Air Route",
    total_cost: 1500,
    transit_time: 24,
    reliability: 0.95,
    aggregate_risk: 0.1,
    feasibility_status: "FEASIBLE",
    violated_constraints: [],
    legs: [{ origin: "JFK", destination: "LHR", transport_mode: "AIR", duration: 12, cost: 1500, risk_factors: [] }]
  },
  {
    id: "route-2",
    route_name: "Slow Sea Route",
    total_cost: 500,
    transit_time: 336,
    reliability: 0.85,
    aggregate_risk: 0.2,
    feasibility_status: "INFEASIBLE",
    violated_constraints: ["Transit time exceeds deadline"],
    legs: [{ origin: "NY Port", destination: "London Port", transport_mode: "SEA", duration: 336, cost: 500, risk_factors: [] }]
  }
];

describe("EvaluatePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders initial state correctly with optimization controls", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);

    render(<EvaluatePage />);

    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText(/Ready to Evaluate/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Optimization Profile/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/cost weight/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/time weight/i)).toBeInTheDocument();
    
    // Evaluate button is enabled by default since weights sum to 1
    const evalBtn = screen.getByRole("button", { name: /Evaluate Routes/i });
    expect(evalBtn).not.toBeDisabled();
  });

  it("validates weight sum", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);

    render(<EvaluatePage />);
    await waitFor(() => expect(screen.queryByText(/Loading route data/i)).not.toBeInTheDocument());

    const costInput = screen.getByLabelText(/cost weight/i);
    fireEvent.change(costInput, { target: { value: "0.9" } });

    // 0.9 + 0.3 + 0.2 + 0.1 = 1.5 != 1.0
    expect(screen.getByText(/Weights must sum exactly to 1.0/i)).toBeInTheDocument();
    
    const evalBtn = screen.getByRole("button", { name: /Evaluate Routes/i });
    expect(evalBtn).toBeDisabled();
  });

  it("handles successful optimization result rendering", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);

    const mockResult = {
      id: "run-1",
      shipment_id: "test-shipment-id",
      recommended_route_id: "route-1",
      feasible_routes: ["route-1"],
      infeasible_routes: ["route-2"],
      route_scores: { "route-1": 0.88, "route-2": 0.40 },
      score_breakdown: { 
        "route-1": { cost: 0.3, time: 0.3, reliability: 0.2, risk: 0.08 } 
      },
      constraint_results: {
        "route-2": ["Transit time exceeds deadline"]
      },
      tradeoffs: {
        pareto_efficient: ["route-1", "route-2"],
        dominated: []
      },
      profile: { cost_weight: 0.4, time_weight: 0.3, reliability_weight: 0.2, risk_weight: 0.1 }
    };

    (apiService.runOptimization as jest.Mock).mockResolvedValue(mockResult);

    render(<EvaluatePage />);
    await waitFor(() => expect(screen.queryByText(/Loading route data/i)).not.toBeInTheDocument());

    const evalBtn = screen.getByRole("button", { name: /Evaluate Routes/i });
    fireEvent.click(evalBtn);

    // Wait for result
    await waitFor(() => {
      expect(screen.getAllByText(/Recommended Route/i).length).toBeGreaterThan(0);
    });

    // Recommended route details
    expect(screen.getAllByText("Fast Air Route").length).toBeGreaterThan(0);
    expect(screen.getByText(/Total Score: 88.0\/100/i)).toBeInTheDocument();

    // Table elements
    expect(screen.getAllByText("Slow Sea Route").length).toBeGreaterThan(0);
    
    // Constraint violation for infeasible route
    expect(screen.getByText("Transit time exceeds deadline")).toBeInTheDocument();

    // Pareto trade-off renders route name instead of ID
    const paretoSection = screen.getByText(/Pareto Efficient/i).parentElement?.parentElement;
    expect(paretoSection).toHaveTextContent("Fast Air Route");
  });

  it("handles no feasible route state", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);

    const mockResult = {
      id: "run-2",
      shipment_id: "test-shipment-id",
      recommended_route_id: null,
      feasible_routes: [],
      infeasible_routes: ["route-1", "route-2"],
      route_scores: {},
      score_breakdown: {},
      constraint_results: {
        "route-1": ["Too expensive"],
        "route-2": ["Too slow"]
      },
      tradeoffs: {
        pareto_efficient: [],
        dominated: []
      },
      profile: { cost_weight: 0.4, time_weight: 0.3, reliability_weight: 0.2, risk_weight: 0.1 }
    };

    (apiService.runOptimization as jest.Mock).mockResolvedValue(mockResult);

    render(<EvaluatePage />);
    await waitFor(() => expect(screen.queryByText(/Loading route data/i)).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Evaluate Routes/i }));

    await waitFor(() => {
      expect(screen.getByText(/No Feasible Route/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/All candidate routes violate one or more hard constraints/i)).toBeInTheDocument();
    expect(screen.getByText("Too expensive")).toBeInTheDocument();
    expect(screen.getByText("Too slow")).toBeInTheDocument();
  });

  it("handles optimization API error", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);
    (apiService.runOptimization as jest.Mock).mockRejectedValue(new Error("Optimization engine crashed"));

    render(<EvaluatePage />);
    await waitFor(() => expect(screen.queryByText(/Loading route data/i)).not.toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /Evaluate Routes/i }));

    await waitFor(() => {
      expect(screen.getByText("Optimization engine crashed")).toBeInTheDocument();
    });
  });

  it("handles displaying reliability, risk, and route legs (when expanded)", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);
    const mockResult = {
      id: "run-3",
      shipment_id: "test-shipment-id",
      recommended_route_id: "route-1",
      feasible_routes: ["route-1"],
      infeasible_routes: [],
      route_scores: { "route-1": 0.88 },
      score_breakdown: {},
      constraint_results: {},
      tradeoffs: { pareto_efficient: [], dominated: [] },
      profile: { cost_weight: 0.4, time_weight: 0.3, reliability_weight: 0.2, risk_weight: 0.1 }
    };
    (apiService.runOptimization as jest.Mock).mockResolvedValue(mockResult);

    (apiService.getExplanation as jest.Mock).mockResolvedValue({
      explanation: "Deterministic explanation text for Fast Air",
      generated_by: "deterministic",
      run_id: "run-3"
    });

    render(<EvaluatePage />);
    await waitFor(() => expect(screen.queryByText(/Loading route data/i)).not.toBeInTheDocument());
    
    fireEvent.click(screen.getByRole("button", { name: /Evaluate Routes/i }));
    await waitFor(() => expect(screen.getAllByText("Fast Air Route").length).toBeGreaterThan(0));

    expect(screen.getAllByText("95.0%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1.0").length).toBeGreaterThan(0);

    // Verify explanation section
    await waitFor(() => expect(screen.getByText(/Why this route\?/i)).toBeInTheDocument());
    expect(screen.getByText(/Deterministic explanation text for Fast Air/i)).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: /Toggle Route Legs/i })[0]);
    await waitFor(() => expect(screen.getByText(/Route Legs/i)).toBeInTheDocument());
    expect(screen.getByText(/JFK/i)).toBeInTheDocument();
    expect(screen.getByText(/LHR/i)).toBeInTheDocument();
    expect(screen.getByText("AIR")).toBeInTheDocument();
  });

  it("restores optimization result from runId in URL", async () => {
    // Mock runId present in URL
    const requireNavigation = require("next/navigation");
    jest.spyOn(requireNavigation, "useSearchParams").mockReturnValue(new URLSearchParams("?runId=run-4"));

    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue(mockRoutes);
    const mockOptRun = {
      id: "run-4",
      shipment_id: "test-shipment-id",
      recommended_route_id: "route-1",
      feasible_routes: ["route-1"],
      infeasible_routes: [],
      route_scores: { "route-1": 0.88 },
      score_breakdown: {},
      constraint_results: {},
      tradeoffs: { pareto_efficient: [], dominated: [] },
      profile: { cost_weight: 0.25, time_weight: 0.25, reliability_weight: 0.25, risk_weight: 0.25 }
    };
    (apiService.getOptimizationRun as jest.Mock).mockResolvedValue(mockOptRun);
    (apiService.getExplanation as jest.Mock).mockResolvedValue({
      explanation: "Persisted explanation text",
      generated_by: "deterministic",
      run_id: "run-4"
    });

    render(<EvaluatePage />);
    
    // Wait for the result to automatically render without clicking optimize
    await waitFor(() => {
      expect(screen.getAllByText("Fast Air Route").length).toBeGreaterThan(0);
    });

    expect(apiService.runOptimization).not.toHaveBeenCalled();
    expect(apiService.getOptimizationRun).toHaveBeenCalledWith("run-4");
    expect(apiService.getExplanation).toHaveBeenCalledWith("run-4");
    await waitFor(() => expect(screen.getByText(/Persisted explanation text/i)).toBeInTheDocument());
  });
});
