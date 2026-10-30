"use client"

import React, { useMemo } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Handle,
  Position,
} from "@xyflow/react"

interface RealityGraphProps {
  nodes: Node[]
  edges: Edge[]
  onNodeClick: (node: Node) => void
}

// -----------------------------------------------------------------------------
// Custom Node Components
// -----------------------------------------------------------------------------
const CheckpointNode = ({ data }: { data: any }) => (
  <div className="px-3.5 py-2.5 rounded-lg bg-obsidian-900 border-2 border-cyber-amber text-xs font-mono shadow-md min-w-[190px]">
    <Handle type="target" position={Position.Top} className="!bg-cyber-amber !w-2.5 !h-2.5" />
    <div className="flex items-center justify-between mb-1">
      <span className="font-bold text-cyber-amber">Checkpoint {data.id}</span>
      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyber-crimson/15 text-cyber-crimson font-semibold border border-cyber-crimson/30">
        Repro Red
      </span>
    </div>
    <div className="text-[11px] text-gray-500 dark:text-gray-400 truncate">{data.imageUuid}</div>
    <Handle type="source" position={Position.Bottom} className="!bg-cyber-amber !w-2.5 !h-2.5" />
  </div>
)

const BranchNode = ({ data }: { data: any }) => {
  const isWinner = data.status === "winner"
  const isFail = data.status === "fail"
  const isEscalation = data.isEscalation

  let borderClass = "border-obsidian-700 bg-obsidian-900 hover:border-obsidian-600"
  let badgeClass = "bg-obsidian-850 text-gray-500 border border-obsidian-700"
  let statusText = "Exploring"

  if (isWinner) {
    borderClass = "border-2 border-cyber-emerald bg-cyber-emerald/10 shadow-lg shadow-cyber-emerald/15"
    badgeClass = "bg-cyber-emerald/20 text-emerald-600 dark:text-cyber-emerald font-bold border border-cyber-emerald/30"
    statusText = "Passed 🏆"
  } else if (isFail) {
    borderClass = "border border-cyber-crimson/40 bg-cyber-crimson/5"
    badgeClass = "bg-cyber-crimson/15 text-cyber-crimson border border-cyber-crimson/25"
    statusText = "Failed"
  } else if (isEscalation) {
    borderClass = "border-2 border-cyber-violet bg-cyber-violet/10 shadow-lg shadow-cyber-violet/15"
    badgeClass = "bg-cyber-violet/20 text-violet-600 dark:text-cyber-violet font-semibold border border-cyber-violet/30"
    statusText = "Escalated"
  }

  return (
    <div className={`px-3.5 py-2.5 rounded-lg text-xs font-mono shadow-sm min-w-[200px] cursor-pointer transition ${borderClass}`}>
      <Handle type="target" position={Position.Top} className="!bg-cyber-emerald !w-2 !h-2" />
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-bold text-gray-900 dark:text-white">{data.branchId}</span>
        <span className={`px-1.5 py-0.5 rounded text-[10px] ${badgeClass}`}>
          {statusText}
        </span>
      </div>
      <div className="text-[11px] text-gray-500 dark:text-gray-400 mb-1 flex items-center justify-between">
        <span className="text-cyan-600 dark:text-cyber-cyan font-medium">{data.model || "Lightning"}</span>
        <span>{data.stepCount || 0} steps</span>
      </div>
      <div className="text-[10px] text-gray-500 flex items-center justify-between border-t border-obsidian-700 pt-1 mt-1 tabular-nums">
        <span>Cost:</span>
        <span className="text-emerald-600 dark:text-cyber-emerald font-semibold">${(data.cost || 0).toFixed(4)}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-cyber-emerald !w-2 !h-2" />
    </div>
  )
}

const EscalationNode = ({ data }: { data: any }) => (
  <div className="px-4 py-3 rounded-lg bg-obsidian-900 border-2 border-cyber-violet text-xs font-mono shadow-md min-w-[220px]">
    <Handle type="target" position={Position.Top} className="!bg-cyber-violet !w-2.5 !h-2.5" />
    <div className="flex items-center justify-between mb-1.5">
      <span className="font-bold text-cyber-violet flex items-center space-x-1">
        <span>⚡ Tavily + Ultra</span>
      </span>
      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyber-violet/15 text-violet-600 dark:text-cyber-violet font-bold border border-cyber-violet/30">
        Diagnosis
      </span>
    </div>
    <div className="text-[11px] text-gray-700 dark:text-gray-300 font-sans line-clamp-2">
      {data.diagnosis || "Analyzing failed traces..."}
    </div>
    <Handle type="source" position={Position.Bottom} className="!bg-cyber-violet !w-2.5 !h-2.5" />
  </div>
)

// -----------------------------------------------------------------------------
// Hierarchical Sugiyama/Dagre layout math
// -----------------------------------------------------------------------------
function applyHierarchicalLayout(nodes: Node[], edges: Edge[]): Node[] {
  const X_CENTER = 400
  const Y_START = 40

  const checkpoints = nodes.filter((n) => n.type === "checkpointNode")
  const branches = nodes.filter((n) => n.type === "branchNode")
  const escalations = nodes.filter((n) => n.type === "escalationNode")
  const other = nodes.filter(
    (n) => n.type !== "checkpointNode" && n.type !== "branchNode" && n.type !== "escalationNode"
  )

  const layoutedNodes: Node[] = []

  // Rank 0: Checkpoint nodes
  checkpoints.forEach((node, i) => {
    layoutedNodes.push({
      ...node,
      position: { x: X_CENTER, y: Y_START + i * 160 },
    })
  })

  // Rank 1: Fast branches (fan out horizontally)
  const branchSpacing = 220
  branches.forEach((node, i) => {
    const x = X_CENTER + (i - (branches.length - 1) / 2) * branchSpacing
    layoutedNodes.push({
      ...node,
      position: { x, y: 220 },
    })
  })

  // Rank 2: Escalations
  escalations.forEach((node, i) => {
    const x = X_CENTER + (i - (escalations.length - 1) / 2) * 280
    layoutedNodes.push({
      ...node,
      position: { x, y: 420 },
    })
  })

  // Other nodes
  other.forEach((node, i) => {
    layoutedNodes.push({
      ...node,
      position: node.position || { x: X_CENTER + i * 200, y: 560 },
    })
  })

  return layoutedNodes
}

export const RealityGraph: React.FC<RealityGraphProps> = ({
  nodes,
  edges,
  onNodeClick,
}) => {
  const nodeTypes = useMemo(
    () => ({
      checkpointNode: CheckpointNode,
      branchNode: BranchNode,
      escalationNode: EscalationNode,
    }),
    []
  )

  const layoutedNodes = useMemo(() => applyHierarchicalLayout(nodes, edges), [nodes, edges])

  return (
    <div className="w-full h-full bg-obsidian-950 rounded-lg overflow-hidden border border-obsidian-700 shadow-sm relative">
      <ReactFlow
        nodes={layoutedNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick(node)}
        fitView
        className="bg-obsidian-950"
      >
        <Background color="#161B22" gap={20} size={1} />
        <Controls className="!bg-obsidian-900 !border-obsidian-700 !fill-gray-600 dark:!fill-gray-300" />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === "checkpointNode") return "#F59E0B"
            if (n.data?.status === "winner") return "#10B981"
            if (n.type === "escalationNode") return "#8B5CF6"
            return "#94A3B8"
          }}
          maskColor="rgba(148, 163, 184, 0.15)"
          className="!bg-obsidian-900 !border-obsidian-700 shadow-md"
        />
      </ReactFlow>

      {/* Graph Legend overlay */}
      <div className="absolute top-3 left-3 bg-obsidian-900/95 backdrop-blur-md border border-obsidian-700 px-3 py-2 rounded-lg text-[11px] font-mono space-y-1 z-10 pointer-events-none shadow-sm">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-amber"></span>
          <span className="text-gray-600 dark:text-gray-300 font-medium">Checkpoint C1 (Failing Repro)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-emerald"></span>
          <span className="text-gray-600 dark:text-gray-300 font-medium">Winning Reality Branch</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-violet"></span>
          <span className="text-gray-600 dark:text-gray-300 font-medium">Tavily + Ultra Escalation</span>
        </div>
      </div>
    </div>
  )
}
