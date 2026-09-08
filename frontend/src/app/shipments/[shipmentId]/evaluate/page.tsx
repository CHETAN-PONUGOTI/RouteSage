"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams, usePathname } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle, Info, Activity, ChevronDown, ChevronUp } from "lucide-react";
import { apiService } from "../../../../services/api";
import { Shipment, Route, OptimizationResult, OptimizationProfile } from "../../../../types/api";
import { Button } from "../../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";
import { LoadingState } from "../../../../components/ui/loading-state";
import { ErrorState } from "../../../../components/ui/error-state";
import { Alert, AlertDescription } from "../../../../components/ui/alert";
import { Input } from "../../../../components/ui/input";

export default function EvaluatePage() {
  const params = useParams();
  const shipmentId = params.shipmentId as string;
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const runId = searchParams.get("runId");

  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRouteId, setExpandedRouteId] = useState<string | null>(null);
  
  const [explanation, setExplanation] = useState<{ text: string, type: string } | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  const [profile, setProfile] = useState<OptimizationProfile>({
    name: "Custom Profile",
    cost_weight: 0.4,
    time_weight: 0.3,
    reliability_weight: 0.2,
    risk_weight: 0.1,
  });
  
  const [optimizing, setOptimizing] = useState(false);
  const [optError, setOptError] = useState<string | null>(null);
  const [result, setResult] = useState<OptimizationResult | null>(null);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [shipmentData, routeData, optData] = await Promise.all([
        apiService.getShipment(shipmentId),
        apiService.getRoutes(shipmentId).catch(() => []),
        runId ? apiService.getOptimizationRun(runId).catch((err) => { throw new Error(`Failed to load optimization run: ${err.message}`) }) : Promise.resolve(null)
      ]);
      
      setShipment(shipmentData);
      setRoutes(routeData);
      
      if (optData) {
        if (optData.shipment_id !== shipmentId) {
          throw new Error("Persisted optimization result does not belong to this shipment.");
        }
        setResult(optData);
        if (optData.profile) setProfile(optData.profile);
        
        // Fetch explanation for persisted run
        setLoadingExplanation(true);
        apiService.getExplanation(runId!)
          .then(res => setExplanation({ text: res.explanation, type: res.generated_by }))
          .catch(err => setExplanation({ text: "Explanation currently unavailable.", type: "error" }))
          .finally(() => setLoadingExplanation(false));
      }
    } catch (err: any) {
      setError(err.message || "Failed to load initial data");
    } finally {
      setLoading(false);
    }
  }, [shipmentId, runId]);

  useEffect(() => {
    if (shipmentId) {
      fetchInitialData();
    }
  }, [shipmentId, fetchInitialData]);

  const totalWeight = Number((profile.cost_weight + profile.time_weight + profile.reliability_weight + profile.risk_weight).toFixed(3));
  const isValidWeight = totalWeight === 1.0;

  const handleOptimize = async () => {
    if (!isValidWeight) return;
    setOptimizing(true);
    setOptError(null);
    try {
      const res = await apiService.runOptimization(shipmentId, profile);
      setResult(res);
      router.replace(`${pathname}?runId=${res.id}`, { scroll: false });
      
      setLoadingExplanation(true);
      apiService.getExplanation(res.id)
        .then(expRes => setExplanation({ text: expRes.explanation, type: expRes.generated_by }))
        .catch(err => setExplanation({ text: "Explanation currently unavailable.", type: "error" }))
        .finally(() => setLoadingExplanation(false));
    } catch (err: any) {
      setOptError(err.message || "Optimization failed");
    } finally {
      setOptimizing(false);
    }
  };

  if (loading) return <LoadingState message="Loading route data..." />;
  if (error) return <ErrorState message={error} onRetry={fetchInitialData} />;
  if (!shipment) return <ErrorState title="Not Found" message="Shipment could not be found." />;

  const recommendedRoute = result && result.recommended_route_id 
    ? routes.find(r => r.id === result.recommended_route_id) 
    : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <div className="flex items-center gap-4">
        <Link href={`/shipments/${shipmentId}`}>
          <Button variant="outline" size="icon" className="border-gray-300">
            <ArrowLeft className="h-5 w-5 text-gray-700" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">Evaluate Routes</h1>
          <p className="text-gray-600 mt-1 text-sm font-medium">
            {shipment.origin} &rarr; {shipment.destination} <span className="font-mono text-xs text-gray-500">(ID: {shipment.id})</span>
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader className="border-b border-gray-100 pb-3">
              <CardTitle className="text-lg font-bold text-gray-900">Optimization Profile</CardTitle>
              <p className="text-xs text-gray-600">Set relative importance weights (must sum to 1.0)</p>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {['cost', 'time', 'reliability', 'risk'].map((objective) => {
                const key = (objective + '_weight') as keyof OptimizationProfile;
                return (
                  <div key={objective} className="space-y-1.5">
                    <div className="flex justify-between items-center">
                      <label htmlFor={key} className="text-xs font-bold text-gray-700 uppercase tracking-wider capitalize">
                        {objective} Weight
                      </label>
                      <span className="text-xs font-mono font-bold text-gray-900">
                        {((profile[key] as number) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.01" 
                        className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        value={profile[key] as number}
                        onChange={(e) => setProfile({ ...profile, [key]: parseFloat(e.target.value) || 0 })}
                      />
                      <Input 
                        id={key}
                        type="number" 
                        step="0.01" 
                        min="0" 
                        max="1"
                        className="w-20 bg-white border-gray-300 text-gray-900 font-semibold text-right h-8"
                        value={profile[key] as number}
                        onChange={(e) => setProfile({ ...profile, [key]: parseFloat(e.target.value) || 0 })}
                      />
                    </div>
                  </div>
                );
              })}

              <div className={`p-3 rounded-lg border text-sm font-bold flex justify-between items-center ${isValidWeight ? 'bg-emerald-50 border-emerald-300 text-emerald-900' : 'bg-red-50 border-red-300 text-red-900'}`}>
                <span>Total Weight:</span>
                <span>{totalWeight.toFixed(2)}</span>
              </div>
              {!isValidWeight && (
                <p className="text-xs text-red-600 font-bold">Weights must sum exactly to 1.0</p>
              )}

              {routes.length > 0 ? (
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-sm" 
                  onClick={handleOptimize} 
                  disabled={!isValidWeight || optimizing}
                >
                  {optimizing ? "Evaluating..." : "Evaluate Routes"}
                </Button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-red-600 font-bold text-center mt-2 border p-3 rounded bg-red-50 border-red-200">
                    No candidate routes have been added to this shipment.
                  </p>
                  <Link href={`/shipments/${shipmentId}/routes/new`} className="block">
                    <Button className="w-full bg-blue-100 hover:bg-blue-200 text-blue-700 font-bold">
                      + Add Candidate Route
                    </Button>
                  </Link>
                </div>
              )}
</CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader className="border-b border-gray-100 pb-3">
                <CardTitle className="text-lg font-bold text-gray-900">Trade-offs (Pareto)</CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="space-y-6 text-sm">
                  {/* Scatter Plot */}
                  {result.feasible_routes && result.feasible_routes.length > 0 && (
                    <div className="w-full border rounded-lg bg-gray-50 p-4">
                      <h4 className="font-bold text-gray-700 mb-4 text-center">Cost vs Transit Time</h4>
                      <div className="relative w-full h-48 border-l-2 border-b-2 border-gray-300">
                        <div className="absolute -left-12 top-1/2 -rotate-90 text-xs font-bold text-gray-500">Transit Time</div>
                        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 text-xs font-bold text-gray-500">Total Cost</div>
                        
                        {(() => {
                           const feasible = routes.filter(r => result.feasible_routes.includes(r.id));
                           if (feasible.length === 0) return null;
                           const maxCost = Math.max(...feasible.map(r => r.total_cost)) * 1.1 || 1;
                           const minCost = Math.min(...feasible.map(r => r.total_cost)) * 0.9 || 0;
                           const maxTime = Math.max(...feasible.map(r => r.transit_time)) * 1.1 || 1;
                           const minTime = Math.min(...feasible.map(r => r.transit_time)) * 0.9 || 0;
                           
                           return feasible.map(r => {
                             const isPareto = result.tradeoffs?.pareto_efficient?.includes(r.id);
                             const isRecommended = result.recommended_route_id === r.id;
                             
                             const left = `${((r.total_cost - minCost) / (maxCost - minCost)) * 100}%`;
                             const bottom = `${((r.transit_time - minTime) / (maxTime - minTime)) * 100}%`;
                             
                             return (
                               <div key={r.id} className="absolute group" style={{ left, bottom, transform: 'translate(-50%, 50%)' }}>
                                 <div className={`w-4 h-4 rounded-full border-2 ${isRecommended ? 'bg-emerald-500 border-white z-20 w-5 h-5 shadow-lg' : isPareto ? 'bg-blue-500 border-white z-10' : 'bg-gray-300 border-gray-400 opacity-70'} cursor-pointer hover:scale-125 transition-transform`}></div>
                                 <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block w-48 bg-gray-900 text-white text-xs rounded p-2 z-30 shadow-xl pointer-events-none">
                                   <div className="font-bold border-b border-gray-700 pb-1 mb-1">{r.route_name} {isRecommended && '(Winner)'}</div>
                                   <div>Cost: ${r.total_cost.toLocaleString()}</div>
                                   <div>Time: {r.transit_time}h</div>
                                   <div>Score: {result.route_scores[r.id] ? (result.route_scores[r.id] * 100).toFixed(1) : '-'}</div>
                                   <div className={`mt-1 font-bold ${isPareto ? 'text-blue-300' : 'text-gray-400'}`}>
                                     {isPareto ? 'Pareto Efficient' : 'Dominated'}
                                   </div>
                                 </div>
                               </div>
                             );
                           });
                        })()}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-bold text-gray-900 flex items-center gap-2 mb-2">
                        <CheckCircle className="h-4 w-4 text-emerald-600" /> Pareto Efficient
                      </h4>
                      <ul className="list-disc pl-5 space-y-1 text-gray-700 font-medium">
                        {result.tradeoffs?.pareto_efficient?.map((id: string) => (
                          <li key={id}>{routes.find(r => r.id === id)?.route_name || id}</li>
                        ))}
                        {(!result.tradeoffs?.pareto_efficient || result.tradeoffs.pareto_efficient.length === 0) && (
                          <li className="text-gray-500 italic">None</li>
                        )}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-700 flex items-center gap-2 mb-2">
                        <XCircle className="h-4 w-4 text-gray-400" /> Dominated Routes
                      </h4>
                      <ul className="list-disc pl-5 space-y-1 text-gray-600">
                        {result.tradeoffs?.dominated?.map((id: string) => (
                          <li key={id}>{routes.find(r => r.id === id)?.route_name || id}</li>
                        ))}
                        {(!result.tradeoffs?.dominated || result.tradeoffs.dominated.length === 0) && (
                          <li className="text-gray-500 italic">None</li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>

              </CardContent>
            </Card>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {!result && !optimizing && (
            <Card className="h-full border-dashed border-gray-300 bg-gray-50 flex items-center justify-center min-h-[400px]">
              <div className="text-center text-gray-600 max-w-md p-6">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-bold text-gray-900 mb-2">Ready to Evaluate</h3>
                <p className="text-sm font-medium">Configure your optimization weights on the left and click &quot;Evaluate Routes&quot; to run the deterministic optimization engine.</p>
              </div>
            </Card>
          )}

          {optimizing && (
             <Card className="h-full flex items-center justify-center min-h-[400px]">
               <LoadingState message="Running multi-objective optimization..." />
             </Card>
          )}

          {result && !optimizing && (
            <>
              <Card className={`shadow-sm overflow-hidden border ${recommendedRoute ? 'border-emerald-300' : 'border-amber-300'}`}>
                <div className={`px-6 py-4 border-b ${recommendedRoute ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
                  <h2 className={`text-xl font-bold flex items-center gap-2 ${recommendedRoute ? 'text-emerald-950' : 'text-amber-950'}`}>
                    {recommendedRoute ? <><CheckCircle className="h-6 w-6 text-emerald-600" /> Recommended Route</> : <><AlertTriangle className="h-6 w-6 text-amber-600" /> No Feasible Route</>}
                  </h2>
                </div>
                <CardContent className="p-6">
                  {recommendedRoute ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-2xl font-extrabold text-gray-900">{recommendedRoute.route_name}</h3>
                          <p className="text-gray-600 font-medium text-sm mt-1">{recommendedRoute.legs.length} legs &bull; Total Score: {(result.route_scores[recommendedRoute.id] * 100).toFixed(1)}/100</p>
                        </div>
                        <Badge variant="default" className="bg-emerald-600 font-bold px-3 py-1 text-xs">Optimal</Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 py-4 border-y border-gray-100">
                        <div>
                          <p className="text-xs text-gray-600 font-bold uppercase tracking-wider">Cost</p>
                          <p className="font-extrabold text-xl text-gray-900 mt-1">${recommendedRoute.total_cost.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 font-bold uppercase tracking-wider">Transit Time</p>
                          <p className="font-extrabold text-xl text-gray-900 mt-1">{recommendedRoute.transit_time} hrs</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 font-bold uppercase tracking-wider">Reliability</p>
                          <p className="font-extrabold text-xl text-gray-900 mt-1">{(recommendedRoute.reliability * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 font-bold uppercase tracking-wider">Risk Score</p>
                          <p className="font-extrabold text-xl text-gray-900 mt-1">{(recommendedRoute.aggregate_risk * 10).toFixed(1)} / 10</p>
                        </div>
                      </div>

                      {result.sensitivity && (
                        <div className="mt-4 pt-4 flex items-center justify-between">
                          <div>
                            <h4 className="text-sm font-bold text-gray-900">Recommendation Stability</h4>
                            <p className="text-xs text-gray-600">Sensitivity analysis across ±20% priority shifts</p>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div className={`h-full ${result.sensitivity.is_stable ? 'bg-emerald-600' : 'bg-amber-500'}`} style={{ width: `${result.sensitivity.stability_score * 100}%` }}></div>
                            </div>
                            <span className="text-sm font-black text-gray-900">{(result.sensitivity.stability_score * 100).toFixed(0)}%</span>
                            <Badge className={result.sensitivity.is_stable ? "bg-emerald-600" : "bg-amber-500 text-white"}>
                              {result.sensitivity.is_stable ? "STABLE" : "SENSITIVE"}
                            </Badge>
                          </div>
                        </div>
                      )}

                    </div>
                  ) : (
                    <p className="text-gray-700 font-medium">All candidate routes violate one or more hard constraints. Please review the comparison table for details on constraint violations.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="bg-gray-50 border-b border-gray-200 py-3">
                  <div className="flex items-center gap-2">
                    <Info className="h-5 w-5 text-blue-600" />
                    <CardTitle className="text-lg font-bold text-gray-900">Why this route?</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  {loadingExplanation ? (
                    <div className="animate-pulse flex space-x-4">
                      <div className="flex-1 space-y-4 py-1">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                      </div>
                    </div>
                  ) : explanation ? (
                    <div className="space-y-2">
                      <p className="text-gray-900 text-sm leading-relaxed font-medium">{explanation.text}</p>
                      <div className="text-[11px] text-gray-500 font-mono mt-2 flex justify-end">
                        Explanation engine: <span className="font-bold ml-1 text-gray-700 uppercase">{explanation.type}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600 text-sm">Explanation currently unavailable.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="border-b border-gray-100 pb-3">
                  <CardTitle className="text-lg font-bold text-gray-900">Route Comparison</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto pt-3">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-900 font-bold uppercase bg-gray-100 border-b border-gray-200">
                      <tr>
                        <th className="px-4 py-3">Route</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Score</th>
                        <th className="px-4 py-3">Cost</th>
                        <th className="px-4 py-3">Time</th>
                        <th className="px-4 py-3">Reliability</th>
                        <th className="px-4 py-3">Risk</th>
                        <th className="px-4 py-3 min-w-[150px]">Breakdown (C/T/Rel/Rsk)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {routes.map((route) => {
                        const isFeasible = result.feasible_routes.includes(route.id);
                        const isRecommended = result.recommended_route_id === route.id;
                        const score = result.route_scores[route.id];
                        const breakdown = result.score_breakdown[route.id];
                        const violations = result.constraint_results[route.id] || [];

                        return (
                          <React.Fragment key={route.id}>
                            <tr className={isRecommended ? "bg-emerald-50/60 font-semibold" : ""}>
                              <td className="px-4 py-4 font-bold text-gray-900 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <button onClick={() => setExpandedRouteId(expandedRouteId === route.id ? null : route.id)} className="p-1 hover:bg-gray-200 rounded text-gray-600" aria-label="Toggle Route Legs">
                                    {expandedRouteId === route.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                  </button>
                                  <span>{route.route_name}</span>
                                  {isRecommended && <Badge className="bg-emerald-600 font-bold text-[10px] px-1.5 py-0">Rec</Badge>}
                                </div>
                              </td>
                              <td className="px-4 py-4">
                                {isFeasible ? (
                                  <Badge variant="outline" className="border-emerald-500 text-emerald-800 bg-emerald-50 font-bold">Feasible</Badge>
                                ) : (
                                  <div className="space-y-1">
                                    <Badge variant="destructive" className="font-bold">Infeasible</Badge>
                                    {violations.map((v, i) => <p key={i} className="text-xs text-red-600 font-semibold max-w-[150px] truncate" title={v}>{v}</p>)}
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-4 font-bold text-gray-900">
                                {score !== undefined ? (score * 100).toFixed(1) : "-"}
                              </td>
                              <td className="px-4 py-4 font-semibold text-gray-900">${route.total_cost.toLocaleString()}</td>
                              <td className="px-4 py-4 font-semibold text-gray-900">{route.transit_time}h</td>
                              <td className="px-4 py-4 font-semibold text-gray-900">{(route.reliability * 100).toFixed(1)}%</td>
                              <td className="px-4 py-4 font-semibold text-gray-900">{(route.aggregate_risk * 10).toFixed(1)}</td>
                              <td className="px-4 py-4">
                                {breakdown ? (
                                  <div className="w-full flex h-4 rounded overflow-hidden bg-gray-200">
                                    <div style={{ width: (breakdown.cost || 0) * 100 + "%" }} className="bg-blue-600" title={"Cost"} />
                                    <div style={{ width: (breakdown.time || 0) * 100 + "%" }} className="bg-amber-500" title={"Time"} />
                                    <div style={{ width: (breakdown.reliability || 0) * 100 + "%" }} className="bg-purple-600" title={"Rel"} />
                                    <div style={{ width: (breakdown.risk || 0) * 100 + "%" }} className="bg-rose-600" title={"Risk"} />
                                  </div>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                            </tr>
                            {expandedRouteId === route.id && (
                              <tr className="bg-gray-50 border-b">
                                <td colSpan={8} className="px-8 py-4">
                                  <div className="text-sm">
                                    <h4 className="font-semibold mb-3">Route Legs</h4>
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                      {route.legs.map((leg, idx) => (
                                        <div key={idx} className="bg-white p-3 rounded border shadow-sm flex flex-col space-y-2">
                                          <div className="flex justify-between items-center font-medium">
                                            <span>{leg.origin} &rarr; {leg.destination}</span>
                                            <Badge variant="outline">{leg.transport_mode}</Badge>
                                          </div>
                                          <div className="text-xs text-gray-500 flex justify-between">
                                            <span>Duration: {leg.duration}h</span>
                                            <span>Cost: ${leg.cost.toLocaleString()}</span>
                                          </div>
                                          {leg.risk_factors && leg.risk_factors.length > 0 && (
                                            <div className="text-xs text-red-600 mt-1">
                                              <span className="font-semibold">Risks: </span>
                                              {leg.risk_factors.join(", ")}
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </tbody>
                  </table>
                  
                  {result.feasible_routes.length > 0 && (
                     <div className="mt-4 flex items-center gap-4 text-xs text-gray-500">
                       <span className="flex items-center gap-1"><div className="w-3 h-3 bg-blue-500 rounded-sm"></div> Cost</span>
                       <span className="flex items-center gap-1"><div className="w-3 h-3 bg-orange-500 rounded-sm"></div> Time</span>
                       <span className="flex items-center gap-1"><div className="w-3 h-3 bg-purple-500 rounded-sm"></div> Reliability</span>
                       <span className="flex items-center gap-1"><div className="w-3 h-3 bg-red-500 rounded-sm"></div> Risk</span>
                     </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
