import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import EvaluatePage from "../src/app/shipments/[shipmentId]/evaluate/page";
import { apiService } from "../src/services/api";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  useParams: () => ({ shipmentId: "test-shipment-id" }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/shipments/test-shipment-id/evaluate"
}));

jest.mock("../src/services/api");

const mockShipment = { id: "test-shipment-id", origin: "A", destination: "B" };

describe("Phase 14 Evaluate Page UI", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("blocks evaluation and shows empty state when no routes exist", async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue(mockShipment);
    (apiService.getRoutes as jest.Mock).mockResolvedValue([]);
    
    render(<EvaluatePage />);
    
    await waitFor(() => {
      expect(screen.getByText(/No candidate routes have been added to this shipment/i)).toBeInTheDocument();
    });

    const evaluateButton = screen.queryByRole("button", { name: /Evaluate Routes/i });
    expect(evaluateButton).not.toBeInTheDocument();
    
    expect(screen.getByRole("button", { name: /\+ Add Candidate Route/i })).toBeInTheDocument();
  });
});
