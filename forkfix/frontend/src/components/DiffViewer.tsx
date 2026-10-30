"use client"

import React, { useMemo, useState } from "react"
import * as Diff2Html from "diff2html"

interface DiffViewerProps {
  patch: string
  patchSize?: number
  cost?: number
  elapsed?: number
  winningBranch?: string
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  patch,
  patchSize,
  cost,
  elapsed,
  winningBranch,
}) => {
  const [copied, setCopied] = useState(false)

  const htmlDiff = useMemo(() => {
    if (!patch || !patch.trim()) return ""
    try {
      return Diff2Html.html(patch, {
        drawFileList: false,
        matching: "lines",
        outputFormat: "side-by-side",
      } as any)
    } catch (e) {
      return `<pre class="p-4 text-xs font-mono text-gray-700 dark:text-gray-300">${patch}</pre>`
    }
  }, [patch])

  const handleCopy = () => {
    navigator.clipboard.writeText(patch)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!patch || !patch.trim()) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 border border-dashed border-obsidian-700 rounded-lg p-6 text-center bg-obsidian-900/50">
        <svg
          className="w-12 h-12 mb-3 text-obsidian-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">No verified patch generated yet</span>
        <span className="text-xs text-gray-500 mt-1 max-w-sm">
          Branch race in progress. The winning minimal passing patch will appear here automatically.
        </span>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-obsidian-900 border border-obsidian-700 rounded-lg overflow-hidden shadow-sm">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-obsidian-850 border-b border-obsidian-700 text-xs">
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-cyber-emerald/15 text-emerald-600 dark:text-cyber-emerald border border-cyber-emerald/30">
            🏆 Winner: {winningBranch || "Verified Patch"}
          </span>
          {patchSize !== undefined && (
            <span className="text-gray-500 dark:text-gray-400 font-mono tabular-nums">
              {patchSize} bytes
            </span>
          )}
        </div>
        <div className="flex items-center space-x-3 text-gray-500 dark:text-gray-400 font-mono tabular-nums">
          {cost !== undefined && (
            <span className="text-emerald-600 dark:text-cyber-emerald font-semibold">
              ${cost.toFixed(4)}
            </span>
          )}
          {elapsed !== undefined && (
            <span>{elapsed.toFixed(1)}s elapsed</span>
          )}
          <button
            onClick={handleCopy}
            className="px-2.5 py-1 rounded bg-obsidian-700 hover:bg-obsidian-600 text-gray-700 dark:text-gray-200 transition text-[11px] font-medium active:scale-95 border border-obsidian-600/50"
          >
            {copied ? "✓ Copied" : "Copy Patch"}
          </button>
        </div>
      </div>

      {/* Diff HTML output */}
      <div
        className="overflow-auto flex-1 p-2 text-xs font-mono"
        dangerouslySetInnerHTML={{ __html: htmlDiff }}
      />
    </div>
  )
}
