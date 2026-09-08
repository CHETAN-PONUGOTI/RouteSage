"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { apiService } from "../../../../../services/api";
import { Route, RouteLeg, RiskFactor } from "../../../../../types/api";
import { Button } from "../../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../../components/ui/card";
import { Input } from "../../../../../components/ui/input";
import { LoadingState } from "../../../../../components/ui/loading-state";

export default function RouteEditorPage() {
  const params = useParams();
  const shipmentId = params.shipmentId as string;
  const routeIdParam = params.routeId as string;
  const router = useRouter();

  const isNew = routeIdParam === "new";

  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [routeData, setRouteData] = useState<Partial<Route>>({
    route_name: "",
    total_cost: 0,
    transit_time: 0,
    delay_probability: 0,
    reliability: 0,
    aggregate_risk: 0,
    legs: []
  });

  const loadRoute = useCallback(async () => {
    if (isNew) return;
    try {
      const routes = await apiService.getRoutes(shipmentId);
      const existing = routes.find(r => r.id === routeIdParam);
      if (existing) {
        setRouteData(existing);
      } else {
        setError("Route not found.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load route");
    } finally {
      setLoading(false);
    }
  }, [isNew, shipmentId, routeIdParam]);

  useEffect(() => {
    loadRoute();
  }, [loadRoute]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        await apiService.createRoutes(shipmentId, [routeData]);
      } else {
        await apiService.updateRoute(shipmentId, routeIdParam, routeData);
      }
      router.push(`/shipments/${shipmentId}`);
    } catch (err: any) {
      setError(err.message || "Failed to save route");
    } finally {
      setSaving(false);
    }
  };

  const addLeg = () => {
    const newLeg: RouteLeg = {
      sequence: (routeData.legs?.length || 0) + 1,
      origin: "",
      destination: "",
      transport_mode: "ROAD",
      duration: 0,
      cost: 0,
      risk_factors: []
    };
    setRouteData({ ...routeData, legs: [...(routeData.legs || []), newLeg] });
  };

  const updateLeg = (index: number, field: keyof RouteLeg, value: any) => {
    const updatedLegs = [...(routeData.legs || [])];
    updatedLegs[index] = { ...updatedLegs[index], [field]: value };
    
    // Attempt auto-recalculate total cost & time if the user is typing
    const newTotalCost = updatedLegs.reduce((sum, leg) => sum + (leg.cost || 0), 0);
    const newTotalTime = updatedLegs.reduce((sum, leg) => sum + (leg.duration || 0), 0);
    
    setRouteData({ ...routeData, legs: updatedLegs, total_cost: newTotalCost, transit_time: newTotalTime });
  };

  const removeLeg = (index: number) => {
    const updatedLegs = (routeData.legs || []).filter((_, i) => i !== index).map((leg, i) => ({ ...leg, sequence: i + 1 }));
    const newTotalCost = updatedLegs.reduce((sum, leg) => sum + (leg.cost || 0), 0);
    const newTotalTime = updatedLegs.reduce((sum, leg) => sum + (leg.duration || 0), 0);
    setRouteData({ ...routeData, legs: updatedLegs, total_cost: newTotalCost, transit_time: newTotalTime });
  };

  if (loading) return <LoadingState message="Loading route details..." />;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex items-center gap-4">
        <Link href={`/shipments/${shipmentId}`}>
          <Button variant="outline" size="icon" className="border-gray-300">
            <ArrowLeft className="h-5 w-5 text-gray-700" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            {isNew ? "Create Candidate Route" : "Edit Candidate Route"}
          </h1>
        </div>
      </div>

      {error && <div className="p-4 bg-red-50 text-red-600 rounded">{error}</div>}

      <Card>
        <CardHeader>
          <CardTitle>Route Overview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1">Route Name</label>
              <Input value={routeData.route_name || ""} onChange={(e) => setRouteData({ ...routeData, route_name: e.target.value })} placeholder="e.g. Express Air" />
            </div>
          </div>
          
          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-1">Total Cost ($)</label>
              <Input type="number" value={routeData.total_cost || 0} onChange={(e) => setRouteData({ ...routeData, total_cost: parseFloat(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Transit Time (h)</label>
              <Input type="number" value={routeData.transit_time || 0} onChange={(e) => setRouteData({ ...routeData, transit_time: parseFloat(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Reliability (0-1)</label>
              <Input type="number" step="0.01" max="1" min="0" value={routeData.reliability || 0} onChange={(e) => setRouteData({ ...routeData, reliability: parseFloat(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-1">Risk (0-1)</label>
              <Input type="number" step="0.01" max="1" min="0" value={routeData.aggregate_risk || 0} onChange={(e) => setRouteData({ ...routeData, aggregate_risk: parseFloat(e.target.value) || 0 })} />
            </div>
          </div>
          <div>
              <label className="block text-sm font-semibold mb-1">Delay Probability (0-1)</label>
              <Input type="number" step="0.01" max="1" min="0" className="w-1/4" value={routeData.delay_probability || 0} onChange={(e) => setRouteData({ ...routeData, delay_probability: parseFloat(e.target.value) || 0 })} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Route Legs</CardTitle>
          <Button size="sm" variant="outline" onClick={addLeg}><Plus className="h-4 w-4 mr-2"/> Add Leg</Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {!routeData.legs || routeData.legs.length === 0 ? (
            <div className="text-center p-6 text-gray-500 bg-gray-50 rounded border border-dashed">
              No route legs added yet.
            </div>
          ) : (
            routeData.legs.map((leg, idx) => (
              <div key={idx} className="p-4 border rounded relative bg-white">
                <div className="absolute top-4 right-4">
                  <Button variant="ghost" size="icon" onClick={() => removeLeg(idx)} className="text-red-500 hover:text-red-700 hover:bg-red-50">
                    <Trash2 className="h-4 w-4"/>
                  </Button>
                </div>
                <h4 className="font-semibold text-sm mb-3">Leg {leg.sequence}</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <label className="text-xs font-semibold text-gray-600 block mb-1">Origin</label>
                    <Input value={leg.origin} onChange={(e) => updateLeg(idx, "origin", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 block mb-1">Destination</label>
                    <Input value={leg.destination} onChange={(e) => updateLeg(idx, "destination", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 block mb-1">Mode</label>
                    <select className="w-full border rounded p-2 text-sm" value={leg.transport_mode} onChange={(e) => updateLeg(idx, "transport_mode", e.target.value)}>
                      <option value="ROAD">Road</option>
                      <option value="RAIL">Rail</option>
                      <option value="SEA">Sea</option>
                      <option value="AIR">Air</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 block mb-1">Duration (h)</label>
                    <Input type="number" value={leg.duration} onChange={(e) => updateLeg(idx, "duration", parseFloat(e.target.value) || 0)} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-600 block mb-1">Cost ($)</label>
                    <Input type="number" value={leg.cost} onChange={(e) => updateLeg(idx, "cost", parseFloat(e.target.value) || 0)} />
                  </div>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-4">
        <Link href={`/shipments/${shipmentId}`}>
          <Button variant="outline">Cancel</Button>
        </Link>
        <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white font-bold">
          {saving ? "Saving..." : "Save Route"}
        </Button>
      </div>
    </div>
  );
}
