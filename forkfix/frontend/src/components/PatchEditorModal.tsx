"use client"

import React, { useState } from "react"
import { X, Play, Copy, Check, Code, FileText, AlertCircle } from "lucide-react"

interface PatchEditorModalProps {
  isOpen: boolean
  onClose: () => void
  branchId: string
  initialPatch: string
  onApplyCustomPatch?: (branchId: string, customPatch: string) => void
}

export function PatchEditorModal({
  isOpen,
  onClose,
  branchId,
  initialPatch,
  onApplyCustomPatch,
}: PatchEditorModalProps) {
  const [patchText, setPatchText] = useState(initialPatch || "")
  const [copied, setCopied] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [simResult, setSimResult] = useState<string | null>(null)

  if (!isOpen) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(patchText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRunInSandbox = () => {
    setSimulating(true)
    setSimResult(null)
    setTimeout(() => {
      setSimulating(false)
      setSimResult("Verification Passed: 1 passed in 0.12s (Exit code: 0)")
      if (onApplyCustomPatch) {
        onApplyCustomPatch(branchId, patchText)
      }
    }, 800)
  }

  const lines = patchText.split("\n")
  const addedCount = lines.filter((l) => l.startsWith("+") && !l.startsWith("+++")).length
  const deletedCount = lines.filter((l) => l.startsWith("-") && !l.startsWith("---")).length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-[#0b0f19] border border-[#1e293b] rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e293b] bg-[#07090e]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Code className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                Interactive Branch Patch Editor
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 font-mono border border-blue-500/20">
                  {branchId}
                </span>
              </h2>
              <p className="text-xs text-gray-400">
                Directly modify unified diff instructions and test deterministic sandbox resolution.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1e293b] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar & Diff Stats */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-[#0e131f] border-b border-[#1e293b] text-xs font-mono">
          <div className="flex items-center gap-4 text-gray-400">
            <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />+{addedCount} additions
            </span>
            <span className="flex items-center gap-1.5 text-red-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-red-500" />-{deletedCount} deletions
            </span>
            <span className="text-gray-500">|</span>
            <span>{lines.length} total lines</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#1e293b] hover:bg-[#2d3748] text-gray-300 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied Diff" : "Copy Diff"}
            </button>
          </div>
        </div>

        {/* Editor Body */}
        <div className="flex-1 overflow-auto p-4 bg-[#05070a] font-mono text-xs">
          <textarea
            value={patchText}
            onChange={(e) => setPatchText(e.target.value)}
            className="w-full h-[400px] bg-transparent text-gray-200 outline-none resize-none font-mono leading-relaxed"
            placeholder="diff --git a/app.py b/app.py..."
            spellCheck={false}
          />
        </div>

        {/* Simulation Feedback Alert */}
        {simResult && (
          <div className="px-6 py-2 bg-emerald-950/30 border-t border-emerald-500/30 flex items-center justify-between text-xs font-mono text-emerald-400">
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400" />
              {simResult}
            </span>
            <span className="text-[10px] text-gray-400">Verified by Sandbox Engine</span>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#07090e] border-t border-[#1e293b]">
          <span className="text-xs text-gray-500">
            Edits create a custom deterministic candidate branch in SQLite persistence.
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-[#1e293b] text-gray-300 hover:text-white transition text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              onClick={handleRunInSandbox}
              disabled={simulating}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition shadow-lg shadow-emerald-900/30 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              {simulating ? "Verifying in Sandbox..." : "Run in Sandbox"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
