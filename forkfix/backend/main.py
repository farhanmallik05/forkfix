"""FastAPI web and SSE streaming server for Forkfix with SQLite persistence and rate limiting."""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
import json
import os
import uuid
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .auth import check_rate_limit, verify_admin_key
from .database import get_db
from .events import EventEmitter
from .nemotron import NemotronClient
from .orchestrator import CHECK_CMD, REPO_DIR, ForkfixOrchestrator
from .sandbox import get_sandbox_engine
from .security import verify_github_signature
from .tavily_service import TavilyService

# In-memory registry of active run emitters
active_emitters: dict[str, EventEmitter] = {}
active_tasks: dict[str, asyncio.Task[Any]] = {}
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Reconcile any unfinalized runs left from previous server crashes/restarts
    try:
        reconciled = get_db().reconcile_interrupted_runs()
        if reconciled > 0:
            print(f"[Forkfix Startup] Reconciled {reconciled} interrupted run(s) to safe state.")
    except Exception as exc:
        print(f"[Forkfix Startup] Startup run reconciliation warning: {exc}")
    yield
    # Shutdown: cancel in-flight tasks cleanly
    for task in list(active_tasks.values()):
        if not task.done():
            task.cancel()


app = FastAPI(
    title="Forkfix API",
    version="0.2.0",
    description="Parallel Reality Debugging platform powered by Nebius Token Factory & NVIDIA Nemotron",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory registry of active run emitters
active_emitters: dict[str, EventEmitter] = {}
active_tasks: dict[str, asyncio.Task[Any]] = {}
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


class RunRequest(BaseModel):
    issue_text: str = Field(min_length=8, max_length=20_000)
    base_image_uuid: str = "mock-swe-base"
    engine: str | None = None


class ForkRequest(BaseModel):
    run_id: str
    snapshot_uuid: str
    issue_text: str
    hint: str
    tier: str = "super"
    engine: str | None = None


class PatchVerifyRequest(BaseModel):
    snapshot_uuid: str = Field(min_length=1, max_length=500)
    patch: str = Field(min_length=1, max_length=500_000)
    engine: str | None = None


async def _run_with_failure_capture(
    run_id: str,
    orchestrator: ForkfixOrchestrator,
    base_image_uuid: str,
    issue_text: str,
    emitter: EventEmitter,
) -> None:
    """Run orchestration without leaving a permanently-running database row."""
    try:
        await orchestrator.execute_fix(
            base_image_uuid=base_image_uuid,
            issue_text=issue_text,
            emitter=emitter,
        )
    except Exception as exc:
        # Never expose credentials or a full traceback through the event stream.
        message = f"Execution failed safely: {type(exc).__name__}: {str(exc)[:500]}"
        await emitter.emit({
            "event_type": "unresolved",
            "run_id": run_id,
            "total_cost": 0.0,
            "branches_attempted": 0,
            "message": message,
        })
    finally:
        active_tasks.pop(run_id, None)


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
    active_tasks[run_id] = asyncio.create_task(
        _run_with_failure_capture(
            run_id=run_id,
            orchestrator=orchestrator,
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

    engine = get_sandbox_engine(req.engine)
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


@app.post("/api/verify-patch", dependencies=[Depends(check_rate_limit)])
async def verify_patch(req: PatchVerifyRequest):
    """Apply a candidate diff in a disposable snapshot and run the oracle."""
    engine = get_sandbox_engine(req.engine)
    session = await engine.use(req.snapshot_uuid, strict=True)
    apply_result = await session.run(
        shell="git apply --check /tmp/forkfix-candidate.patch && git apply /tmp/forkfix-candidate.patch",
        cwd=REPO_DIR,
        files={"/tmp/forkfix-candidate.patch": req.patch.encode("utf-8")},
        disposable=False,
        timeout=120,
    )
    if apply_result.exit_code != 0:
        return {
            "verified": False,
            "stage": "patch_apply",
            "exit_code": apply_result.exit_code,
            "output": (apply_result.stdout + apply_result.stderr)[-4000:],
        }

    verification_session = await engine.use(apply_result.uuid or session.uuid, strict=True)
    check = await verification_session.run(
        shell=CHECK_CMD,
        cwd=REPO_DIR,
        disposable=True,
        timeout=180,
    )
    output = (check.stdout + check.stderr)[-4000:]
    return {
        "verified": check.exit_code == 0,
        "stage": "oracle",
        "exit_code": check.exit_code,
        "output": output,
        "snapshot_uuid": apply_result.uuid or session.uuid,
    }


@app.get("/api/benchmark")
async def get_benchmark_results():
    """Returns the latest SWE-bench evaluation run summary."""
    summary_file = Path(__file__).resolve().parent.parent / "eval" / "results" / "benchmark_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"total_tasks": 0, "resolved_tasks": 0, "resolve_rate_percent": 0.0, "task_details": []}


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


@app.post("/api/webhook/github")
async def github_webhook(request: Request):
    """Receives GitHub issue webhooks and dispatches parallel reality resolution."""
    raw_payload = await request.body()
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not verify_github_signature(
        raw_payload,
        request.headers.get("x-hub-signature-256"),
        webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

    try:
        payload: dict[str, Any] = json.loads(raw_payload or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    action = payload.get("action", "")
    issue = payload.get("issue", {})
    repo = payload.get("repository", {})

    if action not in ("opened", "labeled"):
        return {"status": "ignored", "reason": f"Action '{action}' is not handled."}

    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "")
    issue_number = issue.get("number", 0)
    repo_name = repo.get("full_name", "unknown/repo")

    issue_text = f"{issue_title}\n\n{issue_body}".strip()
    if not issue_text:
        return {"status": "ignored", "reason": "Empty issue text."}

    run_id = f"gh-{issue_number}-{uuid.uuid4().hex[:6]}"
    db = get_db()
    db.create_run(run_id=run_id, issue_text=issue_text, base_image_uuid="mock-swe-base")
    emitter = EventEmitter(run_id=run_id)
    active_emitters[run_id] = emitter
    orchestrator = ForkfixOrchestrator(
        engine=get_sandbox_engine(),
        nemotron=NemotronClient(),
        tavily=TavilyService(),
    )
    active_tasks[run_id] = asyncio.create_task(
        _run_with_failure_capture(
            run_id=run_id,
            orchestrator=orchestrator,
            base_image_uuid="mock-swe-base",
            issue_text=issue_text,
            emitter=emitter,
        )
    )

    return {
        "status": "queued",
        "run_id": run_id,
        "issue_number": issue_number,
        "repo": repo_name,
        "message": f"Forkfix parallel reality resolution dispatched for issue #{issue_number}",
    }
