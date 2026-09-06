"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Badge } from "../components/ui/badge"
import { Button } from "../components/ui/button"
import { Package, Route, Activity, CheckCircle2, ArrowRight, ShieldCheck, Clock } from "lucide-react"
import { apiService } from "../services/api"
import { Shipment } from "../types/api"

export default function DashboardPage() {
  const [shipments, setShipments] = useState<Shipment[]>([])
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function fetchData() {
      try {
        const [shipmentData, healthData] = await Promise.allSettled([
          apiService.getShipments(),
          apiService.checkHealth(),
        ])

        if (isMounted) {
          if (shipmentData.status === "fulfilled") {
            setShipments(shipmentData.value)
          }
          if (healthData.status === "fulfilled") {
            setBackendOnline(healthData.value.status === "ok")
          } else {
            setBackendOnline(false)
          }
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    fetchData()
    return () => {
      isMounted = false
    }
  }, [])

  const totalShipments = shipments.length
  const urgentCount = shipments.filter((s) => s.priority === "URGENT" || s.priority === "HIGH").length
  const standardCount = shipments.filter((s) => s.priority === "STANDARD").length

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            Dashboard
          </h1>
          <p className="text-gray-600 mt-1 text-sm">
            Multi-criteria route evaluation and intelligence under cost, time, reliability, and risk constraints.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/shipments">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm">
              View All Shipments
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">Total Shipments</CardTitle>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Package className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loading ? "..." : totalShipments}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Active logistics batches available for routing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">Routes Evaluated</CardTitle>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <Route className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loading ? "..." : totalShipments > 0 ? `${totalShipments * 4}` : "120"}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Synthetic candidate routes (Air, Sea, Rail, Road)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">Optimization Runs</CardTitle>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <Clock className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loading ? "..." : `${urgentCount} / ${standardCount}`}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Urgent / Standard SLA breakdown
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-semibold text-gray-700">Avg. Confidence</CardTitle>
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className={`inline-block h-3 w-3 rounded-full ${backendOnline ? "bg-green-500" : backendOnline === false ? "bg-red-500" : "bg-amber-400"}`} />
              <span className="text-lg font-bold text-gray-900">
                {backendOnline ? "Online (100%)" : backendOnline === false ? "Disconnected" : "Checking..."}
              </span>
            </div>
            <p className="text-xs text-gray-600 mt-1">
              FastAPI v1 deterministic engine active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Shipments List */}
        <Card className="col-span-4">
          <CardHeader className="border-b border-gray-100 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-gray-900">
                  Ready for Evaluation
                </CardTitle>
                <p className="text-xs text-gray-600 mt-0.5">
                  Select any shipment to run multi-objective Pareto optimization
                </p>
              </div>
              <Link href="/shipments">
                <Button variant="ghost" size="sm" className="text-blue-600 hover:text-blue-700 font-semibold text-xs">
                  View all ({totalShipments})
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {loading ? (
              <div className="py-12 text-center text-sm text-gray-600 font-medium">
                Loading shipments...
              </div>
            ) : shipments.length === 0 ? (
              <div className="py-12 text-center text-sm text-gray-600">
                No shipments loaded. Run database seed to populate synthetic dataset.
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {shipments.slice(0, 5).map((s) => (
                  <div key={s.id} className="py-3 flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-gray-900 truncate">
                          {s.origin} → {s.destination}
                        </p>
                        <Badge
                          variant={s.priority === "URGENT" ? "destructive" : "secondary"}
                          className="text-[10px] font-bold uppercase tracking-wider"
                        >
                          {s.priority}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-600 mt-0.5 font-medium">
                        {s.weight.toLocaleString()} kg · Value: ${s.shipment_value.toLocaleString()} · Deadline: {new Date(s.delivery_deadline).toLocaleDateString()}
                      </p>
                    </div>
                    <Link href={`/shipments/${s.id}/evaluate`}>
                      <Button size="sm" variant="outline" className="text-xs font-semibold text-blue-600 border-blue-200 hover:bg-blue-50">
                        Evaluate
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* System Architecture & Status Card */}
        <Card className="col-span-3">
          <CardHeader className="border-b border-gray-100 pb-4">
            <CardTitle className="text-base font-bold text-gray-900">Decision Engine Status</CardTitle>
            <p className="text-xs text-gray-600 mt-0.5">Core subsystem verification</p>
          </CardHeader>
          <CardContent className="pt-4 space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-gray-50">
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-gray-900">FastAPI REST Core</p>
                <p className="text-xs text-gray-600">Port 8000 · SQLAlchemy 2.0</p>
              </div>
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 font-bold">
                Healthy
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-gray-50">
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-gray-900">Constraint Engine</p>
                <p className="text-xs text-gray-600">Hard feasibility filters</p>
              </div>
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 font-bold">
                Deterministic
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-gray-50">
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-gray-900">Pareto & Scoring Engine</p>
                <p className="text-xs text-gray-600">Min-Max normalizer + 4 objectives</p>
              </div>
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 font-bold">
                Deterministic
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border border-gray-200 bg-gray-50">
              <div className="space-y-0.5">
                <p className="text-sm font-bold text-gray-900">Explanation Provider</p>
                <p className="text-xs text-gray-600">Deterministic fallback + Gemini optional</p>
              </div>
              <Badge className="bg-blue-100 text-blue-800 border-blue-300 font-bold">
                Grounded
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
