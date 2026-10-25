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
  <div className="px-3.5 py-2.5 rounded-lg bg-obsidian-900 border-2 border-cyber-amber text-xs font-mono shadow-lg min-w-[190px]">
    <Handle type="target" position={Position.Top} className="!bg-cyber-amber !w-2.5 !h-2.5" />
    <div className="flex items-center justify-between mb-1">
      <span className="font-bold text-cyber-amber">Checkpoint {data.id}</span>
      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyber-crimson/20 text-cyber-crimson font-semibold">
        Repro Red
      </span>
    </div>
    <div className="text-[11px] text-gray-400 truncate">{data.imageUuid}</div>
    <Handle type="source" position={Position.Bottom} className="!bg-cyber-amber !w-2.5 !h-2.5" />
  </div>
)

const BranchNode = ({ data }: { data: any }) => {
  const isWinner = data.status === "winner"
  const isFail = data.status === "fail"
  const isEscalation = data.isEscalation

  let borderClass = "border-obsidian-700 bg-obsidian-900"
  let badgeClass = "bg-obsidian-800 text-gray-400"
  let statusText = "Exploring"

  if (isWinner) {
    borderClass = "border-2 border-cyber-emerald bg-cyber-emerald/10 shadow-lg shadow-cyber-emerald/20"
    badgeClass = "bg-cyber-emerald/20 text-cyber-emerald font-bold"
    statusText = "Passed 🏆"
  } else if (isFail) {
    borderClass = "border border-cyber-crimson/50 bg-cyber-crimson/5"
    badgeClass = "bg-cyber-crimson/20 text-cyber-crimson"
    statusText = "Failed"
  } else if (isEscalation) {
    borderClass = "border-2 border-cyber-violet bg-cyber-violet/10 shadow-lg shadow-cyber-violet/20"
    badgeClass = "bg-cyber-violet/20 text-cyber-violet font-semibold"
    statusText = "Escalated"
  }

  return (
    <div className={`px-3.5 py-2.5 rounded-lg text-xs font-mono shadow-md min-w-[200px] cursor-pointer transition ${borderClass}`}>
      <Handle type="target" position={Position.Top} className="!bg-cyber-emerald !w-2 !h-2" />
      <div className="flex items-center justify-between mb-1.5">
        <span className="font-bold text-white">{data.branchId}</span>
        <span className={`px-1.5 py-0.5 rounded text-[10px] ${badgeClass}`}>
          {statusText}
        </span>
      </div>
      <div className="text-[11px] text-gray-400 mb-1 flex items-center justify-between">
        <span className="text-cyber-cyan">{data.model || "Lightning"}</span>
        <span>{data.stepCount || 0} steps</span>
      </div>
      <div className="text-[10px] text-gray-500 flex items-center justify-between border-t border-obsidian-800 pt-1 mt-1">
        <span>Cost:</span>
        <span className="text-cyber-emerald font-semibold">${(data.cost || 0).toFixed(4)}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-cyber-emerald !w-2 !h-2" />
    </div>
  )
}

const EscalationNode = ({ data }: { data: any }) => (
  <div className="px-4 py-3 rounded-lg bg-obsidian-900 border-2 border-cyber-violet text-xs font-mono shadow-xl min-w-[220px]">
    <Handle type="target" position={Position.Top} className="!bg-cyber-violet !w-2.5 !h-2.5" />
    <div className="flex items-center justify-between mb-1.5">
      <span className="font-bold text-cyber-violet flex items-center space-x-1">
        <span>⚡ Tavily + Ultra</span>
      </span>
      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyber-violet/20 text-cyber-violet font-bold">
        Diagnosis
      </span>
    </div>
    <div className="text-[11px] text-gray-300 font-sans line-clamp-2">
      {data.diagnosis || "Analyzing failed traces..."}
    </div>
    <Handle type="source" position={Position.Bottom} className="!bg-cyber-violet !w-2.5 !h-2.5" />
  </div>
)

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

  return (
    <div className="w-full h-full bg-obsidian-950 rounded-lg overflow-hidden border border-obsidian-700 shadow-2xl relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick(node)}
        fitView
        className="bg-obsidian-950"
      >
        <Background color="#161B22" gap={20} size={1} />
        <Controls className="!bg-obsidian-900 !border-obsidian-700 !fill-gray-300" />
        <MiniMap
          nodeColor={(n) => {
            if (n.type === "checkpointNode") return "#F59E0B"
            if (n.data?.status === "winner") return "#10B981"
            if (n.type === "escalationNode") return "#8B5CF6"
            return "#30363D"
          }}
          className="!bg-obsidian-900 !border-obsidian-700"
        />
      </ReactFlow>

      {/* Graph Legend overlay */}
      <div className="absolute top-3 left-3 bg-obsidian-900/90 backdrop-blur-sm border border-obsidian-700 px-3 py-2 rounded-lg text-[11px] font-mono space-y-1 z-10 pointer-events-none">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-amber"></span>
          <span className="text-gray-300">Checkpoint C1 (Failing Repro)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-emerald"></span>
          <span className="text-gray-300">Winning Reality Branch</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-violet"></span>
          <span className="text-gray-300">Tavily + Ultra Escalation</span>
        </div>
      </div>
    </div>
  )
}
