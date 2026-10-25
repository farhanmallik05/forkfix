"use client"

import React, { useState } from "react"

interface TelemetryDrawerProps {
  totalCost: number
  activeTab: "terminal" | "tavily" | "cost"
  onTabChange: (tab: "terminal" | "tavily" | "cost") => void
  terminalLogs: string[]
  tavilyCitations: Array<{ title: string; url: string; content: string }>
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
  return (
    <div className="flex flex-col h-full bg-obsidian-900 border border-obsidian-700 rounded-lg overflow-hidden shadow-2xl">
      {/* Navigation tabs */}
      <div className="flex items-center border-b border-obsidian-700 bg-obsidian-850 px-2 text-xs">
        <button
          onClick={() => onTabChange("terminal")}
          className={`px-3 py-2.5 font-medium border-b-2 transition ${
            activeTab === "terminal"
              ? "border-cyber-emerald text-cyber-emerald bg-obsidian-800/60"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Terminal Shell
        </button>
        <button
          onClick={() => onTabChange("tavily")}
          className={`px-3 py-2.5 font-medium border-b-2 transition flex items-center space-x-1.5 ${
            activeTab === "tavily"
              ? "border-cyber-violet text-cyber-violet bg-obsidian-800/60"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          <span>Tavily Evidence</span>
          {tavilyCitations.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-cyber-violet/20 text-cyber-violet text-[10px] flex items-center justify-center font-bold">
              {tavilyCitations.length}
            </span>
          )}
        </button>
        <button
          onClick={() => onTabChange("cost")}
          className={`px-3 py-2.5 font-medium border-b-2 transition ${
            activeTab === "cost"
              ? "border-cyber-cyan text-cyber-cyan bg-obsidian-800/60"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Token Economics
        </button>
      </div>

      {/* Tab Contents */}
      <div className="flex-1 overflow-auto p-4 text-xs font-mono">
        {activeTab === "terminal" && (
          <div className="space-y-3">
            {activeStepCommand && (
              <div className="p-2.5 bg-obsidian-950 rounded border border-obsidian-700">
                <span className="text-cyber-emerald font-bold">$ </span>
                <span className="text-gray-200">{activeStepCommand}</span>
              </div>
            )}
            <div className="space-y-1.5 text-gray-300">
              {terminalLogs.length === 0 ? (
                <div className="text-gray-500 italic">No shell commands executed yet...</div>
              ) : (
                terminalLogs.map((log, idx) => (
                  <div key={idx} className="whitespace-pre-wrap leading-relaxed">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === "tavily" && (
          <div className="space-y-4">
            {ultraDiagnosis && (
              <div className="p-3 bg-cyber-violet/10 border border-cyber-violet/30 rounded-lg">
                <div className="text-cyber-violet font-semibold text-xs mb-1 flex items-center space-x-1">
                  <span>🧠 Nemotron-3-Ultra-550B Root Cause Diagnosis:</span>
                </div>
                <div className="text-gray-300 text-xs font-sans whitespace-pre-wrap leading-relaxed">
                  {ultraDiagnosis}
                </div>
              </div>
            )}

            <div>
              <div className="text-gray-400 font-semibold mb-2 flex items-center space-x-2">
                <span>Tavily Search Queries:</span>
              </div>
              <div className="space-y-1">
                {tavilyQueries.map((q, idx) => (
                  <div key={idx} className="px-2.5 py-1.5 bg-obsidian-850 rounded border border-obsidian-700 text-cyber-cyan text-[11px]">
                    🔍 {q}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-gray-400 font-semibold mb-2">
                External Documentation Sources (Anti-Leakage Exclusions Applied):
              </div>
              <div className="space-y-2">
                {tavilyCitations.map((c, idx) => (
                  <div key={idx} className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 hover:border-cyber-violet/50 transition">
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyber-violet hover:underline font-semibold block mb-1 text-xs"
                    >
                      {c.title || c.url}
                    </a>
                    <div className="text-gray-400 text-[11px] font-sans line-clamp-3">
                      {c.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "cost" && (
          <div className="space-y-4 font-sans">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700">
                <div className="text-gray-500 text-[11px]">Total Cost This Run</div>
                <div className="text-2xl font-bold text-cyber-emerald font-mono mt-1">
                  ${totalCost.toFixed(4)}
                </div>
              </div>
              <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700">
                <div className="text-gray-500 text-[11px]">Savings vs Ultra Baseline</div>
                <div className="text-2xl font-bold text-cyber-cyan font-mono mt-1">
                  {totalCost > 0 ? `${(0.48 / totalCost).toFixed(1)}x` : "12.0x"}
                </div>
              </div>
            </div>

            <div className="p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 text-xs">
              <div className="font-semibold text-white mb-2">Nebius Token Factory Pricing Matrix</div>
              <table className="w-full text-left text-[11px] text-gray-400">
                <thead>
                  <tr className="border-b border-obsidian-700 text-gray-500">
                    <th className="py-1">Model Tier</th>
                    <th className="py-1">Input / 1M</th>
                    <th className="py-1">Output / 1M</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-obsidian-800">
                  <tr>
                    <td className="py-1.5 text-cyber-emerald font-medium">Nemotron-3.5-Lightning</td>
                    <td>$0.06</td>
                    <td>$0.24</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-cyber-cyan font-medium">Nemotron-3-Super-120B</td>
                    <td>$0.30</td>
                    <td>$0.90</td>
                  </tr>
                  <tr>
                    <td className="py-1.5 text-cyber-violet font-medium">Nemotron-3-Ultra-550B</td>
                    <td>$1.00</td>
                    <td>$3.00</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
