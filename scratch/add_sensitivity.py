import re

with open('frontend/src/app/shipments/[shipmentId]/evaluate/page.tsx', 'r') as f:
    content = f.read()

sensitivity_block = """
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
"""

# We replace the metrics block end `</div>` with `</div>\n` + sensitivity_block
content = re.sub(
    r'(<p className=\"font-extrabold text-xl text-gray-900 mt-1\">\{\(recommendedRoute\.aggregate_risk \* 10\)\.toFixed\(1\)\} / 10</p>\s*</div>\s*</div>)',
    r'\1\n' + sensitivity_block,
    content
)

with open('frontend/src/app/shipments/[shipmentId]/evaluate/page.tsx', 'w') as f:
    f.write(content)
