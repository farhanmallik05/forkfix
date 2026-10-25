"""FastAPI web and SSE streaming server for Forkfix with SQLite persistence and rate limiting."""

from __future__ import annotations
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .auth import check_rate_limit, verify_admin_key
from .database import get_db
from .events import EventEmitter
from .nemotron import NemotronClient
from .orchestrator import ForkfixOrchestrator
from .sandbox import get_sandbox_engine
from .tavily_service import TavilyService

app = FastAPI(
    title="Forkfix API",
    version="0.2.0",
    description="Parallel Reality Debugging platform powered by Nebius Token Factory & NVIDIA Nemotron",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory registry of active run emitters
active_emitters: dict[str, EventEmitter] = {}
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


class RunRequest(BaseModel):
    issue_text: str
    base_image_uuid: str = "mock-swe-base"
    engine: str | None = None


class ForkRequest(BaseModel):
    run_id: str
    snapshot_uuid: str
    issue_text: str
    hint: str
    tier: str = "super"


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "engine": os.getenv("SANDBOX_ENGINE", "mock"),
        "has_nebius_key": bool(os.getenv("NEBIUS_API_KEY")),
        "has_tavily_key": bool(os.getenv("TAVILY_API_KEY")),
        "database": "sqlite",
    }


@app.post("/api/run", dependencies=[Depends(check_rate_limit)])
async def start_run(req: RunRequest):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    db = get_db()
    db.create_run(run_id=run_id, issue_text=req.issue_text, base_image_uuid=req.base_image_uuid)

    emitter = EventEmitter(run_id=run_id)
    active_emitters[run_id] = emitter

    engine = get_sandbox_engine(req.engine)
    nemotron = NemotronClient()
    tavily = TavilyService()
    orchestrator = ForkfixOrchestrator(engine=engine, nemotron=nemotron, tavily=tavily)

    # Launch execution as an asynchronous background task
    asyncio.create_task(
        orchestrator.execute_fix(
            base_image_uuid=req.base_image_uuid,
            issue_text=req.issue_text,
            emitter=emitter,
        )
    )

    return {"run_id": run_id, "status": "started"}


@app.get("/api/stream/{run_id}")
async def stream_run(run_id: str, request: Request):
    emitter = active_emitters.get(run_id)
    if not emitter:
        # Fallback to reading from persisted log if run exists on disk
        log_file = Path("runs") / run_id / "events.jsonl"
        if not log_file.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        emitter = EventEmitter(run_id=run_id)
        active_emitters[run_id] = emitter

    queue = emitter.subscribe()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield {
                        "event": data.get("event_type", "message"),
                        "data": json.dumps(data),
                    }
                    if data.get("event_type") in ("winner_selected", "unresolved"):
                        break
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep SSE connection alive
                    yield {"comment": "ping"}
        finally:
            emitter.unsubscribe(queue)

    return EventSourceResponse(event_generator())


@app.post("/api/fork", dependencies=[Depends(check_rate_limit)])
async def fork_reality(req: ForkRequest):
    """Time Travel: Fork a new branch from any prior snapshot node with human hints."""
    emitter = active_emitters.get(req.run_id)
    if not emitter:
        emitter = EventEmitter(run_id=req.run_id)
        active_emitters[req.run_id] = emitter

    engine = get_sandbox_engine()
    nemotron = NemotronClient()
    orchestrator = ForkfixOrchestrator(engine=engine, nemotron=nemotron)

    branch_id = f"custom-b-{uuid.uuid4().hex[:4]}"

    asyncio.create_task(
        orchestrator.run_branch(
            branch_id=branch_id,
            start_uuid=req.snapshot_uuid,
            issue_text=req.issue_text,
            emitter=emitter,
            tier=req.tier,
            hint=req.hint,
        )
    )

    return {"status": "forked", "branch_id": branch_id}


@app.get("/api/runs")
async def list_runs(limit: int = 50, offset: int = 0):
    """List historical runs from persistent SQLite database."""
    db = get_db()
    runs = db.list_runs(limit=limit, offset=offset)
    return {"runs": runs, "count": len(runs)}


@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: str):
    """Get single run audit details, branches, and steps."""
    db = get_db()
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found in database")
    return run


@app.get("/api/runs/{run_id}/tavily")
async def get_run_tavily_evidence(run_id: str):
    """Retrieve Tavily research queries, citations, and anti-leakage audit trail for a run."""
    log_file = Path("runs") / run_id / "events.jsonl"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Run log not found")

    tavily_events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                ev = json.loads(line)
                if ev.get("event_type") == "escalation_triggered":
                    tavily_events.append(ev)

    if not tavily_events:
        return {"run_id": run_id, "escalated": False, "message": "Run solved by fast tier without escalation"}

    return {"run_id": run_id, "escalated": True, "tavily_research": tavily_events[-1]}


@app.delete("/api/runs/{run_id}", dependencies=[Depends(verify_admin_key)])
async def delete_run(run_id: str):
    """Delete a run from persistent database."""
    db = get_db()
    deleted = db.delete_run(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    if run_id in active_emitters:
        del active_emitters[run_id]
    return {"status": "deleted", "run_id": run_id}


@app.get("/api/fixtures")
async def list_fixtures():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = []
    for f in FIXTURES_DIR.glob("*.jsonl"):
        fixtures.append({"name": f.stem, "path": f.name})
    return {"fixtures": fixtures}


@app.get("/api/fixtures/{fixture_name}")
async def get_fixture(fixture_name: str):
    target = FIXTURES_DIR / f"{fixture_name}.jsonl"
    if not target.exists():
        target = FIXTURES_DIR / fixture_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Fixture not found")

    events = []
    with open(target, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return {"fixture": fixture_name, "events": events}
