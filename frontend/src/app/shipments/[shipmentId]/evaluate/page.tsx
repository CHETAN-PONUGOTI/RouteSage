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
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Evaluate Routes</h1>
          <p className="text-gray-500 mt-1 text-sm">
            {shipment.origin} &rarr; {shipment.destination} (ID: {shipment.id})
          </p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Optimization Profile</CardTitle>
              <p className="text-sm text-gray-500">Set relative importance weights (must sum to 1.0)</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {['cost', 'time', 'reliability', 'risk'].map((objective) => {
                const key = (objective + '_weight') as keyof OptimizationProfile;
                return (
                  <div key={objective} className="space-y-1">
                    <label htmlFor={key} className="text-sm font-medium capitalize">{objective} Weight</label>
                    <Input 
                      id={key}
                      type="number" 
                      step="0.05" 
                      min="0" 
                      max="1"
                      value={profile[key] as number}
                      onChange={(e) => setProfile({ ...profile, [key]: parseFloat(e.target.value) || 0 })}
                    />
                  </div>
                );
              })}

              <div className={`p-3 rounded-md border text-sm font-medium flex justify-between items-center ${isValidWeight ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                <span>Total Weight:</span>
                <span>{totalWeight.toFixed(2)}</span>
              </div>
              {!isValidWeight && (
                <p className="text-xs text-red-600 font-medium">Weights must sum exactly to 1.0</p>
              )}

              <Button 
                className="w-full" 
                onClick={handleOptimize} 
                disabled={!isValidWeight || optimizing || routes.length === 0}
              >
                {optimizing ? "Evaluating..." : "Evaluate Routes"}
              </Button>

              {routes.length === 0 && (
                <p className="text-xs text-orange-600 text-center mt-2">No candidate routes available.</p>
              )}
              {optError && (
                <Alert variant="destructive" className="mt-4">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{optError}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {result && (
            <Card>
              <CardHeader>
                <CardTitle>Trade-offs (Pareto)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 text-sm">
                  <div>
                    <h4 className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-600" /> Pareto Efficient
                    </h4>
                    <ul className="list-disc pl-5 space-y-1 text-gray-600">
                      {result.tradeoffs?.pareto_efficient?.map((id: string) => (
                        <li key={id}>{routes.find(r => r.id === id)?.route_name || id}</li>
                      ))}
                      {(!result.tradeoffs?.pareto_efficient || result.tradeoffs.pareto_efficient.length === 0) && (
                        <li>None</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-700 flex items-center gap-2 mb-2">
                      <XCircle className="h-4 w-4 text-gray-400" /> Dominated Routes
                    </h4>
                    <ul className="list-disc pl-5 space-y-1 text-gray-500">
                      {result.tradeoffs?.dominated?.map((id: string) => (
                        <li key={id}>{routes.find(r => r.id === id)?.route_name || id}</li>
                      ))}
                      {(!result.tradeoffs?.dominated || result.tradeoffs.dominated.length === 0) && (
                        <li>None</li>
                      )}
                    </ul>
                  </div>
                  <Alert className="bg-blue-50 border-blue-100 text-blue-800 mt-4">
                    <Info className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-xs">
                      Pareto efficiency means no other route is strictly better across all objectives. The recommended route is chosen via your specific weights.
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          {!result && !optimizing && (
            <Card className="h-full border-dashed bg-gray-50 flex items-center justify-center min-h-[400px]">
              <div className="text-center text-gray-500 max-w-md p-6">
                <Activity className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-700 mb-2">Ready to Evaluate</h3>
                <p className="text-sm">Configure your optimization weights on the left and click &quot;Evaluate Routes&quot; to run the deterministic optimization engine.</p>
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
              <Card className={`shadow-sm overflow-hidden border ${recommendedRoute ? 'border-green-200' : 'border-orange-200'}`}>
                <div className={`px-6 py-4 border-b ${recommendedRoute ? 'bg-green-50 border-green-200' : 'bg-orange-50 border-orange-200'}`}>
                  <h2 className={`text-xl font-semibold flex items-center gap-2 ${recommendedRoute ? 'text-green-900' : 'text-orange-900'}`}>
                    {recommendedRoute ? <><CheckCircle className="h-6 w-6" /> Recommended Route</> : <><AlertTriangle className="h-6 w-6" /> No Feasible Route</>}
                  </h2>
                </div>
                <CardContent className="p-6">
                  {recommendedRoute ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-2xl font-bold">{recommendedRoute.route_name}</h3>
                          <p className="text-gray-500 text-sm mt-1">{recommendedRoute.legs.length} legs &bull; Total Score: {(result.route_scores[recommendedRoute.id] * 100).toFixed(1)}/100</p>
                        </div>
                        <Badge variant="default" className="bg-green-600">Optimal</Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 py-4 border-y">
                        <div>
                          <p className="text-sm text-gray-500 font-medium">Cost</p>
                          <p className="font-semibold text-lg">${recommendedRoute.total_cost.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 font-medium">Transit Time</p>
                          <p className="font-semibold text-lg">{recommendedRoute.transit_time} hrs</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 font-medium">Reliability</p>
                          <p className="font-semibold text-lg">{(recommendedRoute.reliability * 100).toFixed(1)}%</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 font-medium">Risk Score</p>
                          <p className="font-semibold text-lg">{(recommendedRoute.aggregate_risk * 10).toFixed(1)} / 10</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600">All candidate routes violate one or more hard constraints. Please review the comparison table for details on constraint violations.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="bg-gray-50 border-b py-3">
                  <div className="flex items-center gap-2">
                    <Info className="h-5 w-5 text-blue-600" />
                    <CardTitle className="text-lg">Why this route?</CardTitle>
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
                      <p className="text-gray-700 text-sm leading-relaxed">{explanation.text}</p>
                      <div className="text-[10px] text-gray-400 font-mono mt-2 flex justify-end">
                        Explanation generated by: {explanation.type}
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">Explanation currently unavailable.</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Route Comparison</CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
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
                    <tbody className="divide-y">
                      {routes.map((route) => {
                        const isFeasible = result.feasible_routes.includes(route.id);
                        const isRecommended = result.recommended_route_id === route.id;
                        const score = result.route_scores[route.id];
                        const breakdown = result.score_breakdown[route.id];
                        const violations = result.constraint_results[route.id] || [];

                        return (
                          <React.Fragment key={route.id}>
                            <tr className={isRecommended ? "bg-green-50/50" : ""}>
                              <td className="px-4 py-4 font-medium text-gray-900 whitespace-nowrap">
                                <div className="flex items-center gap-2">
                                  <button onClick={() => setExpandedRouteId(expandedRouteId === route.id ? null : route.id)} className="p-1 hover:bg-gray-200 rounded" aria-label="Toggle Route Legs">
                                    {expandedRouteId === route.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                  </button>
                                  <span>{route.route_name}</span>
                                  {isRecommended && <Badge className="bg-green-600 text-[10px] px-1.5 py-0">Rec</Badge>}
                                </div>
                              </td>
                              <td className="px-4 py-4">
                                {isFeasible ? (
                                  <Badge variant="outline" className="border-green-500 text-green-700">Feasible</Badge>
                                ) : (
                                  <div className="space-y-1">
                                    <Badge variant="destructive">Infeasible</Badge>
                                    {violations.map((v, i) => <p key={i} className="text-xs text-red-600 max-w-[150px] truncate" title={v}>{v}</p>)}
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-4 font-semibold">
                                {score !== undefined ? (score * 100).toFixed(1) : "-"}
                              </td>
                              <td className="px-4 py-4">${route.total_cost.toLocaleString()}</td>
                              <td className="px-4 py-4">{route.transit_time}h</td>
                              <td className="px-4 py-4">{(route.reliability * 100).toFixed(1)}%</td>
                              <td className="px-4 py-4">{(route.aggregate_risk * 10).toFixed(1)}</td>
                              <td className="px-4 py-4">
                                {breakdown ? (
                                  <div className="w-full flex h-4 rounded overflow-hidden bg-gray-100">
                                    <div style={{ width: (breakdown.cost || 0) * 100 + "%" }} className="bg-blue-500" title={"Cost"} />
                                    <div style={{ width: (breakdown.time || 0) * 100 + "%" }} className="bg-orange-500" title={"Time"} />
                                    <div style={{ width: (breakdown.reliability || 0) * 100 + "%" }} className="bg-purple-500" title={"Rel"} />
                                    <div style={{ width: (breakdown.risk || 0) * 100 + "%" }} className="bg-red-500" title={"Risk"} />
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
