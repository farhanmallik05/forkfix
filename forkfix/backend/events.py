"""Event schemas and dual SSE/JSONL emitter for real-time and replay modes."""

from __future__ import annotations
import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_type: str
    run_id: str
    timestamp: float = Field(default_factory=time.time)


class CheckpointCreatedEvent(BaseEvent):
    event_type: Literal["checkpoint_created"] = "checkpoint_created"
    checkpoint_id: str
    image_uuid: str
    repro_script: str
    repro_stderr: str


class BranchSpawnedEvent(BaseEvent):
    event_type: Literal["branch_spawned"] = "branch_spawned"
    branch_id: str
    parent_checkpoint: str
    tier: str
    model: str
    hint: str = ""


class StepExecutedEvent(BaseEvent):
    event_type: Literal["step_executed"] = "step_executed"
    branch_id: str
    step_idx: int
    tier: str
    command: str
    output: str
    cost: float
    cumulative_cost: float
    snapshot_uuid: str


class EscalationTriggeredEvent(BaseEvent):
    event_type: Literal["escalation_triggered"] = "escalation_triggered"
    reason: str
    tavily_queries: list[str]
    tavily_citations: list[dict[str, Any]]
    ultra_diagnosis: str


class WinnerSelectedEvent(BaseEvent):
    event_type: Literal["winner_selected"] = "winner_selected"
    winning_branch_id: str
    patch: str
    patch_size_bytes: int
    total_cost: float
    elapsed_seconds: float


class UnresolvedEvent(BaseEvent):
    event_type: Literal["unresolved"] = "unresolved"
    total_cost: float
    branches_attempted: int
    message: str


AnyForkfixEvent = (
    CheckpointCreatedEvent
    | BranchSpawnedEvent
    | StepExecutedEvent
    | EscalationTriggeredEvent
    | WinnerSelectedEvent
    | UnresolvedEvent
)


class EventEmitter:
    def __init__(self, run_id: str, log_dir: str = "runs"):
        self.run_id = run_id
        self.log_path = Path(log_dir) / run_id / "events.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.queues: list[asyncio.Queue[dict[str, Any]]] = []

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]):
        if q in self.queues:
            self.queues.remove(q)

    async def emit(self, event: BaseModel | dict[str, Any]):
        data = event.model_dump() if isinstance(event, BaseModel) else dict(event)

        # Sanitize any output or payload strings
        from .security import CommandSanitizer
        if "output" in data and isinstance(data["output"], str):
            data["output"] = CommandSanitizer.sanitize_logs(data["output"])

        # 1. Append to events.jsonl
        line = json.dumps(data) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)

        # 2. Record to SQLite database
        try:
            from .database import get_db
            db = get_db()
            event_type = data.get("event_type", "unknown")
            db.record_event(self.run_id, event_type, data)

            if event_type == "branch_spawned":
                db.record_branch(
                    run_id=self.run_id,
                    branch_id=data.get("branch_id", ""),
                    parent_checkpoint=data.get("parent_checkpoint", ""),
                    tier=data.get("tier", "fast"),
                    model=data.get("model", ""),
                    hint=data.get("hint", ""),
                )
            elif event_type == "step_executed":
                db.record_step(
                    run_id=self.run_id,
                    branch_id=data.get("branch_id", ""),
                    step_idx=data.get("step_idx", 0),
                    command=data.get("command", ""),
                    output=data.get("output", ""),
                    cost=data.get("cost", 0.0),
                    snapshot_uuid=data.get("snapshot_uuid", ""),
                )
            elif event_type == "winner_selected":
                db.update_run_status(
                    run_id=self.run_id,
                    status="resolved",
                    total_cost=data.get("total_cost"),
                    elapsed_seconds=data.get("elapsed_seconds"),
                    winning_branch_id=data.get("winning_branch_id"),
                    winning_patch=data.get("patch"),
                )
            elif event_type == "unresolved":
                db.update_run_status(
                    run_id=self.run_id,
                    status="unresolved",
                    total_cost=data.get("total_cost"),
                )
        except Exception:
            pass  # Non-blocking database write

        # 3. Dispatch to SSE subscribers
        for q in list(self.queues):
            try:
                q.put_nowait(data)
            except Exception:
                pass
