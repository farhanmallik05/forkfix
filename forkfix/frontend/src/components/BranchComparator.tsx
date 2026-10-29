"use client"

import React, { useState } from "react"
import { DiffViewer } from "./DiffViewer"

interface BranchItem {
  id: string
  model: string
  status: string
  stepCount: number
  cost: number
  patch: string
  trace: Array<{ cmd: string; out: string; cost: number }>
}

interface BranchComparatorProps {
  isOpen: boolean
  onClose: () => void
  branches: BranchItem[]
}

export const BranchComparator: React.FC<BranchComparatorProps> = ({
  isOpen,
  onClose,
  branches,
}) => {
  const [leftId, setLeftId] = useState<string>(branches[0]?.id || "")
  const [rightId, setRightId] = useState<string>(branches[1]?.id || branches[0]?.id || "")

  if (!isOpen) return null

  const leftBranch = branches.find((b) => b.id === leftId) || branches[0]
  const rightBranch = branches.find((b) => b.id === rightId) || branches[1] || branches[0]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="comparator-title"
        className="w-full max-w-6xl h-[88vh] bg-obsidian-900 border border-obsidian-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-obsidian-700 bg-obsidian-850">
          <div className="flex items-center space-x-3">
            <span className="text-cyber-cyan text-xl" aria-hidden="true">⚖️</span>
            <div>
              <h3 id="comparator-title" className="font-bold text-white text-base">Parallel Reality Comparator</h3>
              <p className="text-xs text-gray-400">
                Compare execution commands, test logs, and patches between two concurrent branches
              </p>
            </div>
          </div>
          <button
            aria-label="Close branch comparator"
            onClick={onClose}
            className="text-gray-400 hover:text-white transition p-1 text-sm"
          >
            ✕
          </button>
        </div>

        {/* Comparison Selectors */}
        <div className="grid grid-cols-2 gap-4 px-6 py-3 bg-obsidian-950 border-b border-obsidian-700 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-gray-400 font-medium">Left Branch:</span>
            <select
              value={leftId}
              onChange={(e) => setLeftId(e.target.value)}
              className="bg-obsidian-850 border border-obsidian-700 text-cyber-emerald rounded px-2.5 py-1.5 focus:outline-none"
            >
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.id} ({b.model}) — {b.status} (${b.cost.toFixed(4)})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-gray-400 font-medium">Right Branch:</span>
            <select
              value={rightId}
              onChange={(e) => setRightId(e.target.value)}
              className="bg-obsidian-850 border border-obsidian-700 text-cyber-cyan rounded px-2.5 py-1.5 focus:outline-none"
            >
              {branches.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.id} ({b.model}) — {b.status} (${b.cost.toFixed(4)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Split Comparison Body */}
        <div className="flex-1 grid grid-cols-2 gap-4 p-6 overflow-hidden">
          {/* Left Branch Pane */}
          <div className="flex flex-col h-full bg-obsidian-950 border border-obsidian-700 rounded-xl overflow-hidden p-3 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono border-b border-obsidian-800 pb-2">
              <span className="font-bold text-cyber-emerald">{leftBranch?.id}</span>
              <span className="text-gray-400">{leftBranch?.stepCount} steps &middot; ${leftBranch?.cost.toFixed(4)}</span>
            </div>
            <div className="flex-1 overflow-auto">
              <DiffViewer patch={leftBranch?.patch || ""} winningBranch={leftBranch?.id} />
            </div>
          </div>

          {/* Right Branch Pane */}
          <div className="flex flex-col h-full bg-obsidian-950 border border-obsidian-700 rounded-xl overflow-hidden p-3 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono border-b border-obsidian-800 pb-2">
              <span className="font-bold text-cyber-cyan">{rightBranch?.id}</span>
              <span className="text-gray-400">{rightBranch?.stepCount} steps &middot; ${rightBranch?.cost.toFixed(4)}</span>
            </div>
            <div className="flex-1 overflow-auto">
              <DiffViewer patch={rightBranch?.patch || ""} winningBranch={rightBranch?.id} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
