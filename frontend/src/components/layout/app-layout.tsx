'use client'

import * as React from "react"
import { Route } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const pathname = usePathname() || ""

  const isDashboard = pathname === "/"
  const isShipments = pathname.startsWith("/shipments")

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col text-gray-900">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="bg-blue-600 p-1.5 rounded-md flex items-center justify-center">
                <Route className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-lg tracking-tight text-gray-900">
                Safiri Route Intelligence
              </span>
            </Link>
            
            <nav className="flex items-center gap-6 text-sm font-semibold">
              <Link 
                href="/" 
                className={`transition-colors py-1 border-b-2 ${
                  isDashboard 
                    ? "text-blue-600 border-blue-600" 
                    : "text-gray-600 hover:text-gray-900 border-transparent"
                }`}
              >
                Dashboard
              </Link>
              <Link 
                href="/shipments" 
                className={`transition-colors py-1 border-b-2 ${
                  isShipments 
                    ? "text-blue-600 border-blue-600" 
                    : "text-gray-600 hover:text-gray-900 border-transparent"
                }`}
              >
                Shipments
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              Deterministic v1.0
            </span>
            <div className="h-8 w-8 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center shadow-inner">
              <span className="text-xs font-bold text-gray-700">SA</span>
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
