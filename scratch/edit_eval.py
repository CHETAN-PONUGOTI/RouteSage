import re

with open('frontend/src/app/shipments/[shipmentId]/evaluate/page.tsx', 'r') as f:
    content = f.read()

# 1. Update Optimization Profile (Sliders + Add Route button)
profile_replacement = """<CardTitle className="text-lg font-bold text-gray-900">Optimization Profile</CardTitle>
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
"""
content = re.sub(r'<CardTitle className="text-lg font-bold text-gray-900">Optimization Profile</CardTitle>.*?</CardHeader>\s*<CardContent className="space-y-4 pt-4">.*?</CardContent>', profile_replacement + '</CardContent>', content, flags=re.DOTALL)

# 2. Add Scatter Plot to Pareto Card
pareto_replacement = """<CardTitle className="text-lg font-bold text-gray-900">Trade-offs (Pareto)</CardTitle>
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
"""
content = re.sub(r'<CardTitle className="text-lg font-bold text-gray-900">Trade-offs \(Pareto\)</CardTitle>.*?</CardHeader>\s*<CardContent className="pt-4">.*?</CardContent>', pareto_replacement + '\n              </CardContent>', content, flags=re.DOTALL)


# 3. Add Sensitivity to the Recommendation Section
sensitivity_block = """
              {result.sensitivity && (
                <div className="mt-4 pt-4 border-t border-emerald-100 flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-emerald-900">Recommendation Stability</h4>
                    <p className="text-xs text-emerald-700">Sensitivity analysis across ±20% priority shifts</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-emerald-200 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-700" style={{ width: `${result.sensitivity.stability_score * 100}%` }}></div>
                    </div>
                    <span className="text-sm font-black text-emerald-900">{(result.sensitivity.stability_score * 100).toFixed(0)}%</span>
                    <Badge className={result.sensitivity.is_stable ? "bg-emerald-600" : "bg-amber-500 text-white"}>
                      {result.sensitivity.is_stable ? "STABLE" : "SENSITIVE"}
                    </Badge>
                  </div>
                </div>
              )}
"""

content = re.sub(r'(<div className="space-y-1">\s*<p className="text-sm font-medium text-emerald-800">Total Score</p>\s*<p className="text-2xl font-black text-emerald-900">{(result\.route_scores\[result\.recommended_route_id\] \* 100)\.toFixed\(1\)} <span className="text-sm text-emerald-700 font-bold">/ 100</span></p>\s*</div>\s*</div>)', r'\1' + sensitivity_block, content, count=1)


with open('frontend/src/app/shipments/[shipmentId]/evaluate/page.tsx', 'w') as f:
    f.write(content)
