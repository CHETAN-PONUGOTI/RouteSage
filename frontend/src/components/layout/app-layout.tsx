import * as React from "react"
import { Package, Route, Activity, Settings } from "lucide-react"
import Link from "next/link"

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="bg-blue-600 p-1.5 rounded-md">
                <Route className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-lg tracking-tight">Safiri Route Intelligence</span>
            </div>
            
            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-500">
              <Link href="/" className="text-gray-900">Dashboard</Link>
              <Link href="/shipments" className="hover:text-gray-900 transition-colors">Shipments</Link>
              <Link href="/routes" className="hover:text-gray-900 transition-colors">Routes</Link>
              <Link href="/reports" className="hover:text-gray-900 transition-colors">Reports</Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <button className="text-gray-500 hover:text-gray-900">
              <Settings className="h-5 w-5" />
            </button>
            <div className="h-8 w-8 rounded-full bg-gray-200 border flex items-center justify-center">
              <span className="text-xs font-semibold">SA</span>
            </div>
          </div>
        </div>
      </header>
      
      <main className="flex-1 container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}
