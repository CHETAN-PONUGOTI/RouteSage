import { render, screen } from '@testing-library/react'
import DashboardPage from '../src/app/page'
import { AppLayout } from '../src/components/layout/app-layout'

describe('Dashboard Page', () => {
  it('renders the dashboard title', () => {
    render(<DashboardPage />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toHaveTextContent('Dashboard')
  })

  it('renders the stat cards', () => {
    render(<DashboardPage />)
    expect(screen.getByText('Total Shipments')).toBeInTheDocument()
    expect(screen.getByText('Routes Evaluated')).toBeInTheDocument()
    expect(screen.getByText('Optimization Runs')).toBeInTheDocument()
  })
})

describe('App Layout', () => {
  it('renders the header and navigation', () => {
    render(
      <AppLayout>
        <div>Content</div>
      </AppLayout>
    )
    expect(screen.getByText('Safiri Route Intelligence')).toBeInTheDocument()
    expect(screen.getByText('Content')).toBeInTheDocument()
  })
})
