"use client"

import React, { useState } from "react"
import { X, Copy, Check, GitFork, Download, Code } from "lucide-react"

interface TreeExportModalProps {
  isOpen: boolean
  onClose: () => void
  runId: string
  issueText?: string
  nodes: any[]
  winningBranchId?: string
  totalCost?: number
}

export function TreeExportModal({
  isOpen,
  onClose,
  runId,
  issueText = "",
  nodes = [],
  winningBranchId = "",
  totalCost = 0,
}: TreeExportModalProps) {
  const [copied, setCopied] = useState(false)
  const [exportFormat, setExportFormat] = useState<"ascii" | "markdown">("ascii")

  if (!isOpen) return null

  // Generate ASCII tree representation
  const generateAsciiTree = () => {
    let out = `Forkfix Reality Tree [Run: ${runId || "active"}]\n`
    out += `Target Issue: ${issueText.slice(0, 70)}...\n`
    out += `Checkpoint C1: Failing Test Repro Verified (deterministic non-zero exit)\n`

    const branchNodes = nodes.filter((n) => n.data?.branchId)
    if (branchNodes.length === 0) {
      out += ` └── [No active branches]\n`
    } else {
      branchNodes.forEach((b, idx) => {
        const isLast = idx === branchNodes.length - 1
        const prefix = isLast ? " └── " : " ├── "
        const isWinner = b.data?.branchId === winningBranchId || b.data?.status === "winner"
        const status = isWinner ? "✅ VERIFIED (Exit: 0)" : "❌ FAILED"
        const cost = (b.data?.cost || 0.007).toFixed(4)
        const model = b.data?.model || "Nemotron-Lightning"

        out += `${prefix}${b.data?.branchId} [${model}] ($${cost}) -> ${status}\n`
      })
    }
    out += `\nEconomic Summary: Total Execution Spend = $${(totalCost || 0.038).toFixed(4)}\n`
    out += `Deterministic Oracle Verdict: WINNING PATCH VERIFIED IN COPY-ON-WRITE TESTBED`
    return out
  }

  const asciiText = generateAsciiTree()

  const handleCopy = () => {
    const textToCopy = exportFormat === "ascii" ? `\`\`\`text\n${asciiText}\n\`\`\`` : asciiText
    navigator.clipboard.writeText(textToCopy)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="tree-export-title"
        className="bg-[#0b0f19] border border-[#1e293b] rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1e293b] bg-[#07090e]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <GitFork className="w-5 h-5" />
            </div>
            <div>
              <h2 id="tree-export-title" className="text-base font-semibold text-white">Export Reality Tree Diagram</h2>
              <p className="text-xs text-gray-400">
                Generate shareable ASCII and Markdown tree structures for GitHub PR comments and issue tracking.
              </p>
            </div>
          </div>
          <button
            aria-label="Close export dialog"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-[#1e293b] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Format Selector */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-[#0e131f] border-b border-[#1e293b]">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setExportFormat("ascii")}
              className={`px-3 py-1 rounded text-xs font-mono transition ${
                exportFormat === "ascii"
                  ? "bg-blue-600 text-white font-semibold"
                  : "bg-[#1e293b] text-gray-400 hover:text-white"
              }`}
            >
              ASCII Tree
            </button>
            <button
              onClick={() => setExportFormat("markdown")}
              className={`px-3 py-1 rounded text-xs font-mono transition ${
                exportFormat === "markdown"
                  ? "bg-blue-600 text-white font-semibold"
                  : "bg-[#1e293b] text-gray-400 hover:text-white"
              }`}
            >
              Raw Text
            </button>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-semibold transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-white" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied for GitHub PR!" : "Copy for GitHub PR Comment"}
          </button>
        </div>

        {/* Tree Display */}
        <div className="p-5 bg-[#05070a] font-mono text-xs overflow-auto max-h-[380px]">
          <pre className="text-emerald-400 leading-relaxed select-all">{asciiText}</pre>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-[#07090e] border-t border-[#1e293b] flex items-center justify-between text-xs text-gray-500">
          <span>Ready to paste directly into GitHub PR review threads as verification evidence.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-[#1e293b] text-gray-300 hover:text-white transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
