import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ShipmentsPage from '../src/app/shipments/page'
import NewShipmentPage from '../src/app/shipments/new/page'
import ShipmentDetailPage from '../src/app/shipments/[shipmentId]/page'
import { apiService } from '../src/services/api'

// Mock the API service and Next.js navigation
jest.mock('../src/services/api')
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), refresh: jest.fn() }),
  useParams: () => ({ shipmentId: '123' })
}))

describe('Shipments List Page', () => {
  it('renders loading state initially', () => {
    (apiService.getShipments as jest.Mock).mockReturnValue(new Promise(() => {}))
    render(<ShipmentsPage />)
    expect(screen.getByText(/loading shipments/i)).toBeInTheDocument()
  })

  it('renders empty state if no shipments', async () => {
    (apiService.getShipments as jest.Mock).mockResolvedValue([])
    render(<ShipmentsPage />)
    await waitFor(() => {
      expect(screen.getByText(/no shipments found/i)).toBeInTheDocument()
    })
  })

  it('renders shipments from api', async () => {
    (apiService.getShipments as jest.Mock).mockResolvedValue([
      { id: '1', origin: 'A', destination: 'B', cargo_type: 'GENERAL', weight: 100, delivery_deadline: '2025-01-01T00:00:00Z', priority: 'STANDARD' }
    ])
    render(<ShipmentsPage />)
    await waitFor(() => {
      expect(screen.getByText('A → B')).toBeInTheDocument()
    })
  })
})

describe('New Shipment Page', () => {
  it('renders the form', () => {
    render(<NewShipmentPage />)
    expect(screen.getByLabelText(/origin/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/destination/i)).toBeInTheDocument()
  })
})

describe('Shipment Detail Page', () => {
  it('renders loading state initially', () => {
    (apiService.getShipment as jest.Mock).mockReturnValue(new Promise(() => {}))
    render(<ShipmentDetailPage />)
    expect(screen.getByText(/loading shipment details/i)).toBeInTheDocument()
  })

  it('renders shipment details and route availability', async () => {
    (apiService.getShipment as jest.Mock).mockResolvedValue({
      id: '123', origin: 'Paris', destination: 'London', cargo_type: 'GENERAL', weight: 100, shipment_value: 500, delivery_deadline: '2025-01-01T00:00:00Z', priority: 'STANDARD'
    });
    (apiService.getRoutes as jest.Mock).mockResolvedValue([
      { id: 'r1', route_name: 'Fast Route', legs: [{}, {}] }
    ]);
    
    render(<ShipmentDetailPage />)
    await waitFor(() => {
      expect(screen.getByText('Paris → London')).toBeInTheDocument()
      expect(screen.getByText('Candidate Routes Available')).toBeInTheDocument()
      expect(screen.getByText('Fast Route')).toBeInTheDocument()
    })
  })
})
