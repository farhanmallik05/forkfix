"use client"

import React, { useState, useEffect, useRef } from "react"
import { Node, Edge } from "@xyflow/react"
import { RealityGraph } from "@/components/RealityGraph"
import { DiffViewer } from "@/components/DiffViewer"
import { TelemetryDrawer } from "@/components/TelemetryDrawer"
import { TimeTravelModal } from "@/components/TimeTravelModal"
import Link from "next/link"
import { BranchComparator } from "@/components/BranchComparator"
import { PRExportModal } from "@/components/PRExportModal"
import { PatchEditorModal } from "@/components/PatchEditorModal"
import { TreeExportModal } from "@/components/TreeExportModal"

interface FixtureEvent {
  event_type: string
  run_id: string
  timestamp: number
  [key: string]: any
}

export default function ForkfixDashboard() {
  const [mode, setMode] = useState<"replay" | "live">("replay")
  const [selectedFixture, setSelectedFixture] = useState<string>("events_django_31422")
  const [liveIssue, setLiveIssue] = useState<string>(
    "Django currency formatting fails when sanitize_separators receives a currency symbol. Find the minimal safe fix and verify it with a failing reproduction."
  )
  const [liveEngine, setLiveEngine] = useState<"mock" | "docker" | "contree">("mock")
  const [liveRunId, setLiveRunId] = useState<string>("")
  const [isLiveRunning, setIsLiveRunning] = useState<boolean>(false)
  const [liveError, setLiveError] = useState<string>("")
  const [allEvents, setAllEvents] = useState<FixtureEvent[]>([])
  const [currentEventIdx, setCurrentEventIdx] = useState<number>(0)
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)

  // Active run state
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [totalCost, setTotalCost] = useState<number>(0)
  const [winningPatch, setWinningPatch] = useState<string>("")
  const [winningBranchId, setWinningBranchId] = useState<string>("")
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0)

  // Drawer & Selection state
  const [activeTab, setActiveTab] = useState<"terminal" | "tavily" | "cost">("terminal")
  const [terminalLogs, setTerminalLogs] = useState<string[]>([])
  const [tavilyCitations, setTavilyCitations] = useState<any[]>([])
  const [tavilyQueries, setTavilyQueries] = useState<string[]>([])
  const [ultraDiagnosis, setUltraDiagnosis] = useState<string>("")
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  // Modals state
  const [isTimeTravelOpen, setIsTimeTravelOpen] = useState<boolean>(false)
  const [isComparatorOpen, setIsComparatorOpen] = useState<boolean>(false)
  const [isPRExportOpen, setIsPRExportOpen] = useState<boolean>(false)
  const [isPatchEditorOpen, setIsPatchEditorOpen] = useState<boolean>(false)
  const [isTreeExportOpen, setIsTreeExportOpen] = useState<boolean>(false)
  const [editingBranchId, setEditingBranchId] = useState<string>("fast-b4")
  const [editingPatch, setEditingPatch] = useState<string>("")
  const eventSourceRef = useRef<EventSource | null>(null)

  // Global Keyboard Shortcuts (Space: pause/play, Esc: close modals, t: tree, e: PR)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.code === "Space") {
        e.preventDefault()
        setIsPlaying((prev) => !prev)
      } else if (e.key === "Escape") {
        setIsComparatorOpen(false)
        setIsPRExportOpen(false)
        setIsTimeTravelOpen(false)
        setIsPatchEditorOpen(false)
        setIsTreeExportOpen(false)
      } else if (e.key.toLowerCase() === "t") {
        setIsTreeExportOpen((prev) => !prev)
      } else if (e.key.toLowerCase() === "e" && winningPatch) {
        setIsPRExportOpen((prev) => !prev)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [winningPatch])

  // Replay mode is fixture-backed by design: it is deterministic evidence,
  // not a claim that a new benchmark run just happened.
  useEffect(() => {
    if (mode !== "replay") return
    async function loadFixture() {
      try {
        const res = await fetch(`/api/fixtures/${selectedFixture}`)
        if (res.ok) {
          const data = await res.json()
          setAllEvents(data.events || [])
          resetState()
        }
      } catch (err) {
        console.error("Failed to load fixture:", err)
      }
    }
    loadFixture()
  }, [selectedFixture, mode])

  useEffect(() => {
    return () => eventSourceRef.current?.close()
  }, [])

  const resetState = () => {
    setCurrentEventIdx(0)
    setIsPlaying(false)
    setNodes([])
    setEdges([])
    setTotalCost(0)
    setWinningPatch("")
    setWinningBranchId("")
    setElapsedSeconds(0)
    setTerminalLogs([])
    setTavilyCitations([])
    setTavilyQueries([])
    setUltraDiagnosis("")
    setSelectedNode(null)
  }

  // Playback timer loop
  useEffect(() => {
    if (!isPlaying || currentEventIdx >= allEvents.length) return

    const interval = setTimeout(() => {
      processEvent(allEvents[currentEventIdx])
      setCurrentEventIdx((prev) => prev + 1)
    }, 1200 / playbackSpeed)

    return () => clearTimeout(interval)
  }, [isPlaying, currentEventIdx, allEvents, playbackSpeed])

  const processEvent = (ev: FixtureEvent) => {
    if (!ev) return

    if (ev.event_type === "checkpoint_created") {
      const c1Node: Node = {
        id: "C1",
        type: "checkpointNode",
        position: { x: 280, y: 40 },
        data: {
          id: "C1",
          imageUuid: ev.image_uuid,
          reproScript: ev.repro_script,
          reproErr: ev.repro_stderr,
        },
      }
      setNodes((prev) => [...prev.filter((n) => n.id !== "C1"), c1Node])
      setTerminalLogs((prev) => [...prev, `[Checkpoint C1] Repro script failing confirmed:\n${ev.repro_stderr}`])
    } else if (ev.event_type === "branch_spawned") {
      const branchIdx = parseInt(ev.branch_id.replace(/\D/g, "")) || 1
      const isEscalated = ev.branch_id.startsWith("super-b")
      const xPos = isEscalated ? 120 + (branchIdx - 1) * 220 : 40 + (branchIdx - 1) * 210
      const yPos = isEscalated ? 420 : 180

      const bNode: Node = {
        id: ev.branch_id,
        type: "branchNode",
        position: { x: xPos, y: yPos },
        data: {
          branchId: ev.branch_id,
          parentCheckpoint: ev.parent_checkpoint,
          model: ev.model,
          tier: ev.tier,
          status: "exploring",
          stepCount: 0,
          cost: 0,
          isEscalation: isEscalated,
          imageUuid: ev.parent_checkpoint,
        },
      }

      setNodes((prev) => [...prev.filter((n) => n.id !== ev.branch_id), bNode])
      setEdges((prev) => [
        ...prev,
        {
          id: `e-${ev.parent_checkpoint || "C1"}-${ev.branch_id}`,
          source: isEscalated ? "escalation-node" : "C1",
          target: ev.branch_id,
          className: isEscalated ? "escalation-edge" : undefined,
        },
      ])
    } else if (ev.event_type === "step_executed") {
      setTotalCost((prev) => prev + (ev.cost || 0))
      setTerminalLogs((prev) => [
        ...prev,
        `[${ev.branch_id}] step ${ev.step_idx}: ${ev.command}\n${ev.output}`,
      ])

      setNodes((prev) =>
        prev.map((n) => {
          if (n.id === ev.branch_id) {
            return {
              ...n,
              data: {
                ...n.data,
                stepCount: ev.step_idx + 1,
                cost: (n.data.cost || 0) + (ev.cost || 0),
                command: ev.command,
                imageUuid: ev.snapshot_uuid,
                status: ev.output.includes("[exit=0]") && !ev.output.includes("AssertionError") ? "pass" : "fail",
              },
            }
          }
          return n
        })
      )
    } else if (ev.event_type === "escalation_triggered") {
      setTavilyQueries(ev.tavily_queries || [])
      setTavilyCitations(ev.tavily_citations || [])
      setUltraDiagnosis(ev.ultra_diagnosis || "")
      setActiveTab("tavily")

      const escNode: Node = {
        id: "escalation-node",
        type: "escalationNode",
        position: { x: 260, y: 300 },
        data: { diagnosis: ev.ultra_diagnosis },
      }
      setNodes((prev) => [...prev, escNode])
      setEdges((prev) => [
        ...prev,
        {
          id: "e-C1-escalation",
          source: "C1",
          target: "escalation-node",
          className: "escalation-edge",
        },
      ])
    } else if (ev.event_type === "winner_selected") {
      setWinningPatch(ev.patch)
      setWinningBranchId(ev.winning_branch_id)
      setTotalCost(ev.total_cost || totalCost)
      setElapsedSeconds(ev.elapsed_seconds || 15.0)

      setNodes((prev) =>
        prev.map((n) => {
          if (n.id === ev.winning_branch_id) {
            return { ...n, data: { ...n.data, status: "winner" } }
          }
          return n
        })
      )

      // Highlight winning edge
      setEdges((prev) =>
        prev.map((e) => {
          if (e.target === ev.winning_branch_id) {
            return { ...e, className: "winning-edge" }
          }
          return e
        })
      )
    }
  }

  const handleTimeTravelFork = async (hint: string, tier: string) => {
    if (!selectedNode) return
    if (mode === "live" && liveRunId) {
      const response = await fetch("/api/fork", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: liveRunId,
          snapshot_uuid: selectedNode.data?.imageUuid || selectedNode.id,
          issue_text: liveIssue,
          hint,
          tier,
          engine: liveEngine,
        }),
      })
      if (!response.ok) {
        throw new Error("Fork request was rejected by the backend")
      }
      setTerminalLogs((prev) => [...prev, `[Time Travel] Live branch requested from ${selectedNode.id}: ${hint}`])
      return
    }
    const newBranchId = `custom-b-${Date.now().toString().slice(-3)}`
    const bNode: Node = {
      id: newBranchId,
      type: "branchNode",
      position: { x: selectedNode.position.x + 80, y: selectedNode.position.y + 120 },
      data: {
        branchId: newBranchId,
        parentCheckpoint: selectedNode.id,
        model: tier === "fast" ? "Lightning" : "Super-120B",
        tier,
        status: "exploring",
        stepCount: 1,
        cost: 0.0004,
        isEscalation: false,
      },
    }
    setNodes((prev) => [...prev, bNode])
    setEdges((prev) => [
      ...prev,
      {
        id: `e-${selectedNode.id}-${newBranchId}`,
        source: selectedNode.id,
        target: newBranchId,
        className: "winning-edge",
      },
    ])
    setTerminalLogs((prev) => [
      ...prev,
      `[Time Travel Branch] Forked from ${selectedNode.id} with hint: "${hint}"`,
    ])
  }

  const startLiveRun = async () => {
    if (liveIssue.trim().length < 8 || isLiveRunning) return
    eventSourceRef.current?.close()
    resetState()
    setLiveError("")
    setIsLiveRunning(true)

    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue_text: liveIssue.trim(), engine: liveEngine }),
      })
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.detail || "Unable to start run")

      const runId = payload.run_id as string
      setLiveRunId(runId)
      const source = new EventSource(`/api/stream/${runId}`)
      eventSourceRef.current = source
      const terminalEvents = new Set(["winner_selected", "unresolved"])
      const eventTypes = [
        "checkpoint_created",
        "branch_spawned",
        "step_executed",
        "escalation_triggered",
        "winner_selected",
        "unresolved",
      ]
      const onEvent = (event: Event) => {
        try {
          const data = JSON.parse((event as MessageEvent<string>).data) as FixtureEvent
          processEvent(data)
          setCurrentEventIdx((previous) => previous + 1)
          if (terminalEvents.has(data.event_type)) {
            setIsLiveRunning(false)
            source.close()
          }
        } catch {
          setLiveError("Received an invalid event from the live run")
        }
      }
      eventTypes.forEach((type) => source.addEventListener(type, onEvent))
      source.onerror = () => {
        if (source.readyState === EventSource.CLOSED) return
        setIsLiveRunning(false)
        setLiveError("Live stream disconnected. The run remains available in Run History.")
        source.close()
      }
    } catch (error) {
      setIsLiveRunning(false)
      setLiveError(error instanceof Error ? error.message : "Unable to start live run")
    }
  }

  return (
    <div className="flex flex-col h-screen bg-obsidian-950 font-sans">
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-obsidian-900 border-b border-obsidian-700 z-20">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyber-emerald/20 border border-cyber-emerald/40 flex items-center justify-center text-cyber-emerald font-bold text-lg shadow-lg shadow-cyber-emerald/10">
            ⚡
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white text-base tracking-tight">FORKFIX</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-obsidian-800 text-gray-300 border border-obsidian-700">
                Nebius x NVIDIA Global AI Hackathon
              </span>
            </div>
            <div className="text-xs text-gray-400">
              Parallel Reality Debugging &middot; Token Factory Sandboxes &middot; Nemotron Ladder
            </div>
          </div>
        </div>

        {/* Center Task / Fixture Selector */}
        <div className="flex items-center space-x-2 bg-obsidian-850 px-3 py-1.5 rounded-lg border border-obsidian-700">
          {mode === "replay" ? (
            <>
              <span className="text-xs text-gray-400">Evidence Replay:</span>
              <select
                value={selectedFixture}
                onChange={(e) => setSelectedFixture(e.target.value)}
                className="bg-transparent text-xs text-cyber-cyan font-mono focus:outline-none cursor-pointer"
                aria-label="Select evidence replay"
              >
                <option value="events_django_31422" className="bg-obsidian-900 text-white">
                  Django #31422 · recorded verified run
                </option>
                <option value="events_sympy_18059" className="bg-obsidian-900 text-white">
                  SymPy #18059 · recorded escalation run
                </option>
              </select>
            </>
          ) : (
            <span className="text-xs text-cyber-cyan font-mono">LIVE · {liveRunId || "READY"}</span>
          )}
        </div>

        {/* Action Controls & Telemetry */}
        <div className="flex items-center space-x-3">
          <Link
            href="/benchmark"
            aria-label="View SWE-bench benchmark leaderboard"
            className="px-2.5 py-1.5 rounded-lg bg-obsidian-850 hover:bg-obsidian-800 text-gray-300 hover:text-cyber-cyan border border-obsidian-700 text-xs transition flex items-center space-x-1.5"
          >
            <span>📊 SWE-bench Leaderboard</span>
          </Link>

          <button
            aria-label="Export reality tree diagram (t)"
            onClick={() => setIsTreeExportOpen(true)}
            className="px-2.5 py-1.5 rounded-lg bg-obsidian-850 hover:bg-obsidian-800 text-gray-300 hover:text-white border border-obsidian-700 text-xs transition flex items-center space-x-1.5"
            title="Press 't' to open"
          >
            <span>🌲 Tree Diagram</span>
          </button>

          <button
            aria-label="Compare reality branches"
            onClick={() => setIsComparatorOpen(true)}
            disabled={nodes.filter((n) => n.type === "branchNode").length < 2}
            className="px-2.5 py-1.5 rounded-lg bg-obsidian-850 hover:bg-obsidian-800 text-gray-300 hover:text-white border border-obsidian-700 text-xs transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center space-x-1.5"
          >
            <span>⚖️ Compare Realities</span>
          </button>

          {winningPatch && (
            <>
              <button
                aria-label="Edit and verify patch in sandbox"
                onClick={() => {
                  setEditingBranchId(winningBranchId || "winning-branch")
                  setEditingPatch(winningPatch)
                  setIsPatchEditorOpen(true)
                }}
                className="px-2.5 py-1.5 rounded-lg bg-obsidian-850 hover:bg-obsidian-800 text-gray-300 hover:text-white border border-obsidian-700 text-xs transition flex items-center space-x-1.5"
              >
                <span>✏️ Edit Patch</span>
              </button>

              <button
                aria-label="Export GitHub pull request (e)"
                onClick={() => setIsPRExportOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-cyber-emerald/15 hover:bg-cyber-emerald/25 text-cyber-emerald font-semibold border border-cyber-emerald/40 text-xs transition flex items-center space-x-1.5 shadow-lg shadow-cyber-emerald/10"
                title="Press 'e' to open"
              >
                <span>🚀 Export PR</span>
              </button>
            </>
          )}

          <div className="flex items-center space-x-2 bg-obsidian-850 px-3 py-1 rounded-lg border border-obsidian-700 font-mono text-xs">
            <span className="text-gray-400">Run Spend:</span>
            <span className="text-cyber-emerald font-bold">${totalCost.toFixed(4)}</span>
          </div>

          <div
            role="radiogroup"
            aria-label="Execution mode selection"
            className="flex items-center space-x-1 bg-obsidian-850 p-1 rounded-lg border border-obsidian-700 text-xs"
          >
            <button
              aria-label="Select verified replay mode"
              role="radio"
              aria-checked={mode === "replay"}
              onClick={() => {
                eventSourceRef.current?.close()
                setIsLiveRunning(false)
                setMode("replay")
              }}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                mode === "replay"
                  ? "bg-cyber-emerald text-obsidian-950 font-bold"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Verified Replay
            </button>
            <button
              aria-label="Select live sandbox mode"
              role="radio"
              aria-checked={mode === "live"}
              onClick={() => {
                resetState()
                setMode("live")
              }}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                mode === "live"
                  ? "bg-cyber-cyan text-obsidian-950 font-bold"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Live Sandbox
            </button>
          </div>
        </div>
        </header>

      {mode === "live" && (
        <section className="px-6 py-3 bg-obsidian-900 border-b border-obsidian-700 flex items-center gap-3">
          <label htmlFor="live-issue" className="sr-only">Issue description</label>
          <textarea
            id="live-issue"
            value={liveIssue}
            onChange={(event) => setLiveIssue(event.target.value)}
            rows={2}
            className="flex-1 bg-obsidian-950 border border-obsidian-700 rounded-lg px-3 py-2 text-xs text-gray-200 font-mono resize-none focus:outline-none focus:border-cyber-cyan"
            placeholder="Describe the bug Forkfix should investigate..."
          />
          <select
            value={liveEngine}
            onChange={(event) => setLiveEngine(event.target.value as "mock" | "docker" | "contree")}
            className="bg-obsidian-950 border border-obsidian-700 rounded-lg px-2 py-2 text-xs text-cyber-cyan"
            aria-label="Sandbox engine"
          >
            <option value="mock">Mock · deterministic demo</option>
            <option value="docker">Docker · local sandbox</option>
            <option value="contree">Contree · Nebius sandbox</option>
          </select>
          <button
            onClick={startLiveRun}
            disabled={isLiveRunning || liveIssue.trim().length < 8}
            className="px-4 py-2 rounded-lg bg-cyber-cyan text-obsidian-950 font-bold text-xs disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLiveRunning ? "Running branches…" : "Start Live Run"}
          </button>
          {liveError && <span className="max-w-xs text-[11px] text-cyber-crimson">{liveError}</span>}
        </section>
      )}

      {/* Main Split Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: React Flow Reality Graph (60%) */}
        <div className="w-[60%] h-full p-3 relative flex flex-col">
          <div className="flex-1 rounded-lg overflow-hidden border border-obsidian-700 shadow-inner">
            <RealityGraph
              nodes={nodes}
              edges={edges}
              onNodeClick={(node) => {
                setSelectedNode(node)
                setActiveTab("terminal")
              }}
            />
          </div>

          {/* Bottom Replay Scrubber Controls */}
          <div
            role="toolbar"
            aria-label="Replay playback and scrubber controls"
            className="mt-2 px-4 py-2 bg-obsidian-900 border border-obsidian-700 rounded-lg flex items-center justify-between text-xs font-mono"
          >
            <div className="flex items-center space-x-3">
              <button
                aria-label={mode === "live" ? (isLiveRunning ? "Streaming live events" : "Live sandbox ready") : (isPlaying ? "Pause replay" : "Start replay playback")}
                onClick={() => setIsPlaying(!isPlaying)}
                disabled={mode === "live"}
                className="px-3 py-1 bg-cyber-emerald text-obsidian-950 font-bold rounded hover:bg-emerald-400 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {mode === "live" ? (isLiveRunning ? "● Streaming" : "Live Run") : (isPlaying ? "⏸ Pause" : "▶ Play Replay")}
              </button>
              <button
                aria-label="Reset run playback"
                onClick={resetState}
                className="px-2 py-1 bg-obsidian-800 text-gray-300 rounded hover:bg-obsidian-700 transition"
              >
                Reset
              </button>
              <div className="flex items-center space-x-1 text-gray-400" role="group" aria-label="Playback speed">
                <span>Speed:</span>
                {[1, 2, 4].map((s) => (
                  <button
                    key={s}
                    aria-label={`Set speed to ${s}x`}
                    onClick={() => setPlaybackSpeed(s)}
                    className={`px-1.5 py-0.5 rounded text-[10px] ${
                      playbackSpeed === s ? "bg-obsidian-700 text-cyber-cyan font-bold" : "text-gray-500"
                    }`}
                  >
                    {s}x
                  </button>
                ))}
              </div>
            </div>

            <div className="text-gray-400">
              {mode === "live" ? `Events received: ${currentEventIdx}` : `Step ${currentEventIdx} of ${allEvents.length}`}
            </div>

            {selectedNode && (
              <button
                aria-label={`Time travel fork reality from node ${selectedNode.id}`}
                onClick={() => setIsTimeTravelOpen(true)}
                className="px-3 py-1 bg-cyber-violet/20 border border-cyber-violet/40 text-cyber-violet font-semibold rounded hover:bg-cyber-violet/30 transition flex items-center space-x-1"
              >
                <span>⚡ Fork Node ({selectedNode.id})</span>
              </button>
            )}
          </div>
        </div>

        {/* Right: Inspector (Diff Viewer & Telemetry Drawer) (40%) */}
        <div className="w-[40%] h-full p-3 pl-0 flex flex-col space-y-3">
          {/* Top Half: Winning Patch Diff Viewer */}
          <div className="h-[48%]">
            <DiffViewer
              patch={winningPatch}
              patchSize={winningPatch.length}
              cost={totalCost}
              elapsed={elapsedSeconds}
              winningBranch={winningBranchId}
            />
          </div>

          {/* Bottom Half: Telemetry Drawer (Logs, Tavily, Economics) */}
          <div className="h-[52%]">
            <TelemetryDrawer
              totalCost={totalCost}
              activeTab={activeTab}
              onTabChange={setActiveTab}
              terminalLogs={terminalLogs}
              tavilyCitations={tavilyCitations}
              tavilyQueries={tavilyQueries}
              ultraDiagnosis={ultraDiagnosis}
              activeStepCommand={selectedNode?.data?.command as string | undefined}
            />
          </div>
        </div>
      </div>

      {/* Time Travel Modal */}
      {selectedNode && (
        <TimeTravelModal
          isOpen={isTimeTravelOpen}
          onClose={() => setIsTimeTravelOpen(false)}
          snapshotUuid={(selectedNode.data?.imageUuid as string) || selectedNode.id}
          branchId={selectedNode.id}
          stepIdx={selectedNode.data?.stepCount as number | undefined}
          onFork={handleTimeTravelFork}
        />
      )}

      {/* Parallel Reality Comparator Modal */}
      <BranchComparator
        isOpen={isComparatorOpen}
        onClose={() => setIsComparatorOpen(false)}
        branches={nodes
          .filter((n) => n.type === "branchNode")
          .map((n) => ({
            id: n.id,
            model: (n.data?.model as string) || "Nemotron-70B",
            status: (n.data?.status as string) || "exploring",
            stepCount: (n.data?.stepCount as number) || 0,
            cost: (n.data?.cost as number) || 0,
            patch: winningBranchId === n.id ? winningPatch : "",
            trace: [],
          }))}
      />

      {/* GitHub PR Export Studio Modal */}
      <PRExportModal
        isOpen={isPRExportOpen}
        onClose={() => setIsPRExportOpen(false)}
        taskTitle={selectedFixture.replace("events_", "").replace("_", "/")}
        winningBranchId={winningBranchId}
        winningPatch={winningPatch}
        totalCost={totalCost}
        elapsedSeconds={elapsedSeconds}
      />

      {/* Interactive Branch Patch Editor Modal */}
      <PatchEditorModal
        isOpen={isPatchEditorOpen}
        onClose={() => setIsPatchEditorOpen(false)}
        branchId={editingBranchId}
        initialPatch={editingPatch}
        snapshotUuid={nodes.find((node) => node.id === winningBranchId)?.data?.imageUuid as string | undefined}
        onVerifyPatch={liveRunId ? async (patch, snapshotUuid) => {
          const response = await fetch("/api/verify-patch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ patch, snapshot_uuid: snapshotUuid, engine: liveEngine }),
          })
          const result = await response.json()
          if (!response.ok) throw new Error(result.detail || "Patch verification request failed")
          return result
        } : undefined}
        onApplyCustomPatch={(branchId, customPatch) => {
          setWinningPatch(customPatch)
          setTerminalLogs((prev) => [...prev, `[Patch Editor] Applied custom patch to ${branchId}:\n${customPatch.slice(0, 100)}...`])
        }}
      />

      {/* Reality Tree Diagram Export Modal */}
      <TreeExportModal
        isOpen={isTreeExportOpen}
        onClose={() => setIsTreeExportOpen(false)}
        runId={selectedFixture}
        issueText={selectedFixture === "events_django_31422" ? "Fix currency formatting in django sanitize_separators" : "Fix Sympify parse string error"}
        nodes={nodes}
        winningBranchId={winningBranchId}
        totalCost={totalCost}
      />
    </div>
  )
}
