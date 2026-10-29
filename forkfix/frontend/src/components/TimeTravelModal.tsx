"use client"

import React, { useState } from "react"

interface TimeTravelModalProps {
  isOpen: boolean
  onClose: () => void
  snapshotUuid: string
  branchId: string
  stepIdx?: number
  onFork: (hint: string, tier: string) => Promise<void>
}

export const TimeTravelModal: React.FC<TimeTravelModalProps> = ({
  isOpen,
  onClose,
  snapshotUuid,
  branchId,
  stepIdx,
  onFork,
}) => {
  const [hint, setHint] = useState("")
  const [tier, setTier] = useState("super")
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!hint.trim()) return
    setIsSubmitting(true)
    try {
      await onFork(hint, tier)
      onClose()
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="time-travel-title"
        className="w-full max-w-lg bg-obsidian-900 border border-obsidian-700 rounded-xl shadow-2xl p-6 text-gray-200 animate-in fade-in zoom-in-95 duration-200"
      >
        <div className="flex items-center justify-between pb-3 border-b border-obsidian-700">
          <div className="flex items-center space-x-2">
            <span className="text-cyber-emerald text-lg" aria-hidden="true">⚡</span>
            <h3 id="time-travel-title" className="font-semibold text-white text-base">
              Fork Reality from Snapshot
            </h3>
          </div>
          <button
            aria-label="Close dialog"
            onClick={onClose}
            className="text-gray-400 hover:text-white transition text-sm p-1"
          >
            ✕
          </button>
        </div>

        <div className="my-4 p-3 bg-obsidian-850 rounded-lg border border-obsidian-700 text-xs font-mono space-y-1">
          <div className="text-gray-400">
            Source Branch: <span className="text-cyber-emerald">{branchId}</span>
          </div>
          {stepIdx !== undefined && (
            <div className="text-gray-400">
              Step Index: <span className="text-cyber-cyan">{stepIdx}</span>
            </div>
          )}
          <div className="text-gray-400 truncate">
            Snapshot UUID: <span className="text-cyber-amber">{snapshotUuid}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Select Model Tier for New Branch
            </label>
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value)}
              className="w-full bg-obsidian-850 border border-obsidian-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyber-emerald"
            >
              <option value="fast">Nemotron-3.5-Lightning ($0.06/M) — Fast Exploration</option>
              <option value="super">Nemotron-3-Super-120B ($0.30/M) — Balanced Reasoning</option>
              <option value="ultra">Nemotron-3-Ultra-550B ($1.00/M) — Maximum Synthesis</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Your Guidance / Human Hint
            </label>
            <textarea
              rows={3}
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              placeholder="e.g. Look at sanitize_separators in formats.py line 142. Currency symbols need regex stripping before decimal conversion..."
              className="w-full bg-obsidian-850 border border-obsidian-700 rounded-lg p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyber-emerald font-mono"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-obsidian-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !hint.trim()}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-cyber-emerald hover:bg-emerald-400 text-obsidian-950 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg shadow-cyber-emerald/20"
            >
              {isSubmitting ? "Forking Sandbox..." : "Launch Parallel Reality"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
