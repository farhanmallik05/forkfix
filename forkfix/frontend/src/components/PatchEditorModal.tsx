"use client"

import React, { useState } from "react"
import { X, Play, Copy, Check, Code, FileText, AlertCircle } from "lucide-react"

interface PatchEditorModalProps {
  isOpen: boolean
  onClose: () => void
  branchId: string
  initialPatch: string
  snapshotUuid?: string
  onVerifyPatch?: (patch: string, snapshotUuid: string) => Promise<{ verified: boolean; output?: string }>
  onApplyCustomPatch?: (branchId: string, customPatch: string) => void
}

export function PatchEditorModal({
  isOpen,
  onClose,
  branchId,
  initialPatch,
  snapshotUuid,
  onVerifyPatch,
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

  const handleRunInSandbox = async () => {
    setSimulating(true)
    setSimResult(null)
    try {
      if (!onVerifyPatch || !snapshotUuid) {
        setSimResult("Draft saved locally. Switch to Live Sandbox to run a real oracle.")
        onApplyCustomPatch?.(branchId, patchText)
        return
      }
      const result = await onVerifyPatch(patchText, snapshotUuid)
      if (result.verified) {
        setSimResult(`Verification Passed: exit code 0${result.output ? ` — ${result.output.slice(-120)}` : ""}`)
        onApplyCustomPatch?.(branchId, patchText)
      } else {
        setSimResult(`Verification rejected: ${result.output?.slice(-240) || "candidate did not pass the oracle"}`)
      }
    } catch (error) {
      setSimResult(error instanceof Error ? error.message : "Sandbox verification failed")
    } finally {
      setSimulating(false)
    }
  }

  const lines = patchText.split("\n")
  const addedCount = lines.filter((l) => l.startsWith("+") && !l.startsWith("+++")).length
  const deletedCount = lines.filter((l) => l.startsWith("-") && !l.startsWith("---")).length

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="patch-editor-title"
        className="w-full max-w-4xl bg-obsidian-900 border border-obsidian-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-obsidian-850 border-b border-obsidian-700">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyber-emerald/15 text-emerald-600 dark:text-cyber-emerald border border-cyber-emerald/30">
              <Code className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="patch-editor-title" className="text-base font-bold text-gray-900 dark:text-white">
                  Patch Studio & Oracle Sandbox
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-obsidian-800 text-cyan-600 dark:text-cyber-cyan border border-obsidian-700">
                  {branchId}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                Inspect, modify, and test candidates against the Checkpoint C1 oracle.
              </p>
            </div>
          </div>
          <button
            aria-label="Close patch editor"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-obsidian-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Toolbar & Diff Stats */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-obsidian-850 border-b border-obsidian-700 text-xs font-mono">
          <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400">
            <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />+{addedCount} additions
            </span>
            <span className="flex items-center gap-1.5 text-red-600 dark:text-red-400 font-semibold">
              <span className="w-2 h-2 rounded-full bg-red-500" />-{deletedCount} deletions
            </span>
            <span className="text-gray-400">|</span>
            <span>{lines.length} total lines</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-obsidian-800 hover:bg-obsidian-700 text-gray-800 dark:text-gray-200 transition font-medium border border-obsidian-700 shadow-sm active:scale-95"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? "Copied Diff" : "Copy Diff"}
            </button>
          </div>
        </div>

        {/* Editor Body */}
        <div className="flex-1 overflow-auto p-4 bg-obsidian-950 font-mono text-xs shadow-inner">
          <textarea
            value={patchText}
            onChange={(e) => setPatchText(e.target.value)}
            className="w-full h-[400px] bg-transparent text-gray-900 dark:text-gray-200 outline-none resize-none font-mono leading-relaxed"
            placeholder="diff --git a/app.py b/app.py..."
            spellCheck={false}
          />
        </div>

        {/* Simulation Feedback Alert */}
        {simResult && (
          <div className="px-6 py-2 bg-emerald-500/10 border-t border-emerald-500/20 flex items-center justify-between text-xs font-mono text-emerald-700 dark:text-emerald-400">
            <span className="flex items-center gap-2 font-medium">
              <Check className="w-4 h-4 text-emerald-500" />
              {simResult}
            </span>
            <span className="text-[10px] text-gray-500">
              {onVerifyPatch ? "Verified by Sandbox Engine" : "Draft only — no live snapshot selected"}
            </span>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-obsidian-850 border-t border-obsidian-700">
          <span className="text-xs text-gray-500">
            Edits create a custom deterministic candidate branch in SQLite persistence.
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-gray-600 dark:text-gray-300 hover:bg-obsidian-800 transition"
            >
              Cancel
            </button>
            <button
              onClick={handleRunInSandbox}
              disabled={simulating}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-cyber-emerald hover:bg-emerald-500 text-obsidian-950 font-bold text-xs transition shadow-md disabled:opacity-50 active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {simulating ? "Verifying In Sandbox..." : "Verify In Sandbox"}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
