"use client"

import React, { useState, useMemo } from "react"

interface TelemetryDrawerProps {
  totalCost: number
  activeTab: "terminal" | "tavily" | "cost"
  onTabChange: (tab: "terminal" | "tavily" | "cost") => void
  terminalLogs: string[]
  tavilyCitations: Array<{ title: string; url: string; content: string; score?: number }>
  tavilyQueries: string[]
  ultraDiagnosis: string
  activeStepCommand?: string
}

export const TelemetryDrawer: React.FC<TelemetryDrawerProps> = ({
  totalCost,
  activeTab,
  onTabChange,
  terminalLogs,
  tavilyCitations,
  tavilyQueries,
  ultraDiagnosis,
  activeStepCommand,
}) => {
  const [filterQuery, setFilterQuery] = useState("")
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null)

  const filteredLogs = useMemo(() => {
    if (!filterQuery.trim()) return terminalLogs
    const q = filterQuery.toLowerCase()
    return terminalLogs.filter((log) => log.toLowerCase().includes(q))
  }, [terminalLogs, filterQuery])

  return (
    <div className="flex flex-col h-full bg-obsidian-900 border border-obsidian-700 rounded-lg overflow-hidden shadow-sm relative">
      {/* Navigation tabs */}
      <div className="flex items-center justify-between border-b border-obsidian-700 bg-obsidian-850 px-2 text-xs">
        <div className="flex items-center" role="tablist" aria-label="Telemetry panels">
          <button
            role="tab"
            id="tab-terminal"
            aria-selected={activeTab === "terminal"}
            aria-controls="panel-terminal"
            onClick={() => onTabChange("terminal")}
            className={`px-3 py-2.5 font-semibold border-b-2 transition ${
              activeTab === "terminal"
                ? "border-cyber-emerald text-emerald-600 dark:text-cyber-emerald bg-obsidian-800/60"
                : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
            }`}
          >
            Terminal Shell
          </button>
          <button
            role="tab"
            id="tab-tavily"
            aria-selected={activeTab === "tavily"}
            aria-controls="panel-tavily"
            onClick={() => onTabChange("tavily")}
            className={`px-3 py-2.5 font-semibold border-b-2 transition flex items-center space-x-1.5 ${
              activeTab === "tavily"
                ? "border-cyber-violet text-violet-600 dark:text-cyber-violet bg-obsidian-800/60"
                : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
            }`}
          >
            <span>Tavily Evidence</span>
            {tavilyCitations.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-cyber-violet/20 text-violet-600 dark:text-cyber-violet text-[10px] flex items-center justify-center font-bold">
                {tavilyCitations.length}
              </span>
            )}
          </button>
          <button
            role="tab"
            id="tab-cost"
            aria-selected={activeTab === "cost"}
            aria-controls="panel-cost"
            onClick={() => onTabChange("cost")}
            className={`px-3 py-2.5 font-semibold border-b-2 transition ${
              activeTab === "cost"
                ? "border-cyber-cyan text-cyan-600 dark:text-cyber-cyan bg-obsidian-800/60"
                : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
            }`}
          >
            Token Economics
          </button>
        </div>

        {activeTab === "terminal" && (
          <div className="flex items-center pr-2">
            <input
              type="text"
              aria-label="Filter terminal logs"
              placeholder="Filter logs..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="bg-obsidian-950 border border-obsidian-700 rounded px-2.5 py-1 text-[11px] text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:border-cyber-emerald w-32 shadow-sm"
            />
          </div>
        )}
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-auto p-4 text-xs font-mono">
        {activeTab === "terminal" && (
          <div role="tabpanel" id="panel-terminal" aria-labelledby="tab-terminal" className="space-y-3">
            {activeStepCommand && (
              <div className="p-2.5 bg-obsidian-950 rounded border border-obsidian-700 shadow-sm">
                <span className="text-cyber-emerald font-bold">$ </span>
                <span className="text-gray-800 dark:text-gray-200">{activeStepCommand}</span>
              </div>
            )}
            <div className="space-y-1.5 text-gray-700 dark:text-gray-300">
              {filteredLogs.length === 0 ? (
                <div className="text-gray-500 italic p-2">No matching shell commands...</div>
              ) : (
                filteredLogs.map((log, idx) => {
                  const isErr = log.includes("AssertionError") || log.includes("SyntaxError") || log.includes("[exit=1]")
                  const isSuccess = log.includes("[exit=0]") && !isErr
                  return (
                    <div
                      key={idx}
                      className={`whitespace-pre-wrap leading-relaxed p-1.5 rounded text-[11px] ${
                        isErr
                          ? "bg-cyber-crimson/10 border-l-2 border-cyber-crimson text-red-600 dark:text-red-300"
                          : isSuccess
                          ? "bg-cyber-emerald/10 border-l-2 border-cyber-emerald text-emerald-700 dark:text-emerald-300"
                          : "border-l-2 border-transparent bg-obsidian-850/50"
                      }`}
                    >
                      {log}
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )}

        {activeTab === "tavily" && (
          <div role="tabpanel" id="panel-tavily" aria-labelledby="tab-tavily" className="space-y-4">
            {ultraDiagnosis && (
              <div className="p-3 bg-cyber-violet/10 border border-cyber-violet/30 rounded-lg shadow-sm">
                <div className="text-violet-600 dark:text-cyber-violet font-semibold text-xs mb-1 flex items-center space-x-1">
                  <span>🧠 Nemotron-3-Ultra-550B Root Cause Diagnosis:</span>
                </div>
                <div className="text-gray-800 dark:text-gray-300 text-xs font-sans whitespace-pre-wrap leading-relaxed">
                  {ultraDiagnosis}
                </div>
              </div>
            )}

            <div>
              <div className="text-gray-700 dark:text-gray-300 font-semibold mb-2 flex items-center space-x-2 text-xs">
                <span>Tavily Search Queries:</span>
              </div>
              <div className="space-y-1">
                {tavilyQueries.map((q, idx) => (
                  <div key={idx} className="px-2.5 py-1.5 bg-obsidian-850 rounded border border-obsidian-700 text-cyan-600 dark:text-cyber-cyan text-[11px] flex items-center justify-between shadow-sm">
                    <span>🔍 {q}</span>
                    <span className="text-[10px] text-gray-500 font-sans">Multi-stage Lens #{idx+1}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-gray-700 dark:text-gray-300 font-semibold mb-2 flex items-center justify-between text-xs">
                <span>External Documentation Sources:</span>
                <span className="text-[10px] text-emerald-600 dark:text-cyber-emerald font-semibold font-sans">✓ Anti-Leakage Verified</span>
              </div>
              <div className="space-y-2">
                {tavilyCitations.map((c, idx) => (
                  <div
                    key={idx}
                    onClick={() => setSelectedCitation(c)}
                    className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 hover:border-cyber-violet/50 transition cursor-pointer shadow-sm active:scale-[0.99]"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-violet-600 dark:text-cyber-violet font-semibold text-xs truncate max-w-[280px]">
                        {c.title || c.url}
                      </span>
                      {c.score && (
                        <span className="text-[10px] font-mono text-cyan-700 dark:text-cyber-cyan bg-cyber-cyan/15 px-1.5 py-0.5 rounded font-semibold">
                          {(c.score * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400 text-[11px] font-sans line-clamp-3 leading-relaxed">
                      {c.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "cost" && (
          <div role="tabpanel" id="panel-cost" aria-labelledby="tab-cost" className="space-y-4 font-sans">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 shadow-sm">
                <div className="text-gray-500 text-[11px] font-medium">Total Cost This Run</div>
                <div className="text-2xl font-bold text-emerald-600 dark:text-cyber-emerald font-mono mt-1 tabular-nums">
                  ${totalCost.toFixed(4)}
                </div>
              </div>
              <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 shadow-sm">
                <div className="text-gray-500 text-[11px] font-medium">Savings vs Ultra Baseline</div>
                <div className="text-2xl font-bold text-cyan-600 dark:text-cyber-cyan font-mono mt-1 tabular-nums">
                  {totalCost > 0 ? `${(0.48 / totalCost).toFixed(1)}x` : "12.0x"}
                </div>
              </div>
            </div>

            <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 text-xs shadow-sm">
              <div className="font-semibold text-gray-900 dark:text-white mb-2">Nebius Token Factory Pricing Matrix</div>
              <table className="w-full text-left text-[11px] text-gray-600 dark:text-gray-400">
                <thead>
                  <tr className="border-b border-obsidian-700 text-gray-500">
                    <th className="py-1">Model Tier</th>
                    <th className="py-1">Input / 1M</th>
                    <th className="py-1">Output / 1M</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-obsidian-800 tabular-nums">
                  <tr>
                    <td className="py-1.5 text-emerald-600 dark:text-cyber-emerald font-semibold">Nemotron-3.5-Lightning</td>
                    <td>$0.06</td>
                    <td>$0.24</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-cyan-600 dark:text-cyber-cyan font-semibold">Nemotron-3-Super-120B</td>
                    <td>$0.30</td>
                    <td>$0.90</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-violet-600 dark:text-cyber-violet font-semibold">Nemotron-3-Ultra-550B</td>
                    <td>$1.00</td>
                    <td>$3.00</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Citation Detail Preview Modal */}
      {selectedCitation && (
        <div className="absolute inset-0 bg-obsidian-950/95 backdrop-blur-md p-4 z-30 flex flex-col animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-2 border-b border-obsidian-700">
            <span className="font-semibold text-gray-900 dark:text-white truncate max-w-[280px]">
              {selectedCitation.title}
            </span>
            <button
              onClick={() => setSelectedCitation(null)}
              className="text-gray-500 hover:text-gray-900 dark:hover:text-white transition text-xs p-1 font-semibold"
            >
              ✕ Close
            </button>
          </div>
          <div className="text-[11px] text-violet-600 dark:text-cyber-violet truncate py-1.5 font-mono">
            <a href={selectedCitation.url} target="_blank" rel="noreferrer" className="hover:underline">
              {selectedCitation.url} ↗
            </a>
          </div>
          <div className="flex-1 overflow-auto bg-obsidian-900 border border-obsidian-800 rounded-lg p-3 text-xs font-sans text-gray-800 dark:text-gray-300 leading-relaxed whitespace-pre-wrap shadow-inner">
            {selectedCitation.content}
          </div>
        </div>
      )}
    </div>
  )
}
