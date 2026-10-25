# Forkfix: Master Work Breakdown Structure & Tasks (WBS)

## Phase 0: Project Scaffolding & Compliance Setup
- [ ] **Task 0.1: Initialize Main Project Structure**
  - Create directory layout in `forkfix/`: `backend/`, `frontend/`, `eval/`, `data/`.
  - Add Apache-2.0 `LICENSE` at root.
  - Add `.env.example` with `NEBIUS_API_KEY`, `TAVILY_API_KEY`, `REPO_DIR`, `PORT`.
- [ ] **Task 0.2: Feedback Logging System**
  - Create `forkfix/FEEDBACK.md` with baseline feedback points ready for telemetry logs.
- [ ] **Task 0.3: Environment & Dependency Management**
  - Backend: `pyproject.toml` with `fastapi`, `uvicorn`, `openai`, `tavily-python`, `contree-sdk`, `pydantic`.
  - Frontend: `package.json` with Next.js 14, Tailwind CSS, `@xyflow/react`, `diff2html`, `lucide-react`.

---

## Phase 1: Core Engine & Multi-Tier Agent Orchestration
- [ ] **Task 1.1: Sandbox Abstraction Layer**
  - Implement `SandboxSession` and `SandboxEngine` protocol interfaces in `backend/sandbox.py`.
  - Implement `ContreeSandboxEngine` using `contree-sdk` with snapshot tracking.
  - Implement `DockerSandboxEngine` as local fallback for development and CI testing.
  - Implement `MockSandboxEngine` for rapid UI and SSE testing with simulated state steps.
- [ ] **Task 1.2: Tri-Tier Nemotron Client**
  - Implement `backend/nemotron.py` with Token Factory endpoint wrapper.
  - Support `fast` (`Nemotron-3.5-Lightning`), `super` (`nemotron-3-super-120b`), and `ultra` (`Nemotron-3-Ultra-550b`).
  - Implement `enable_thinking` template kwargs toggling and fallback.
  - Add real-time token usage and cost accounting ($/1M token pricing map).
- [ ] **Task 1.3: Repro Generator & Checkpoint C1 Creator**
  - Implement `prepare()` in `backend/orchestrator.py`.
  - Prompt Nemotron-3-Super to generate isolated `/tmp/repro.py`.
  - Verify script fails on clean repo; capture initial stderr/stdout; tag snapshot as Checkpoint C1.
- [ ] **Task 1.4: Parallel Branching & Verification Engine**
  - Implement `branch()` and `race()` in `backend/orchestrator.py`.
  - Spawn 4 concurrent branches from C1 using `asyncio.gather`.
  - Implement bash block parser, timeout safeguards, and $0.15 budget limits.
  - Implement `winner()`: execute verification test in disposable runs; select the minimal passing diff.

---

## Phase 2: Tavily Research & Diagnostics Escalation
- [ ] **Task 2.1: Tavily Search & Extract Service**
  - Implement `backend/tavily_service.py`.
  - Configure `search_depth="advanced"`, `chunks_per_source=3`, and domain exclusion filter (`exclude_domains=["github.com", "gitlab.com"]`).
  - Extract detailed documentation content for top 2 URLs.
- [ ] **Task 2.2: Nemotron Ultra Deep Reasoning Pipeline**
  - Digest failure traces from all 4 exhausted branches.
  - Prompt `Nemotron-3-Ultra-550b` (with thinking enabled) to identify root cause and code location.
  - Format structured diagnosis and launch 3 guided remediation branches with `Nemotron-3-Super`.

---

## Phase 3: SSE Streaming, Event Persistence & Time Travel API
- [ ] **Task 3.1: Typed Event Architecture**
  - Define Pydantic event models in `backend/events.py` (`checkpoint_created`, `branch_spawned`, `step_executed`, `escalation_triggered`, `winner_selected`).
  - Implement unified `EventEmitter` writing simultaneously to SSE queues and `runs/{run_id}/events.jsonl`.
- [ ] **Task 3.2: FastAPI Application Endpoints**
  - `POST /api/run`: Start new debugging run for a given issue and repo/image UUID.
  - `GET /api/stream/{run_id}`: Real-time Server-Sent Events (SSE) feed.
  - `GET /api/runs`: List historical runs.
  - `GET /api/runs/{run_id}/events`: Retrieve serialized event log for instant replay.
  - `POST /api/fork`: Time-travel endpoint to fork a new branch from any prior snapshot node with human hints.

---

## Phase 4: Modern Next.js UI & Interactive Reality Canvas
- [ ] **Task 4.1: Design Tokens & Layout Shell**
  - Cyber-minimalist dark mode layout (`#0B0D11` background, slate cards, vibrant telemetry accents).
  - Header with issue switcher, live cost meter, active model badges, and mode toggle (`Live` vs `Replay`).
- [ ] **Task 4.2: Interactive Reality Graph (`@xyflow/react`)**
  - Custom nodes: `CheckpointNode`, `BranchNode`, `StepNode`, `EscalationNode`, `WinnerNode`.
  - Dynamic edge routing with emerald glow on winning branch.
  - Zoom, pan, and minimap controls.
- [ ] **Task 4.3: Right-Hand Inspector & Diff Viewer**
  - Tabs: `Patch Inspector` (diff2html syntax colored), `Live Terminal`, `Tavily Ground Truth`, `Token Economics`.
  - Interactive modal: "Time Travel: Fork from this Step" with hint input.
- [ ] **Task 4.4: Replay Mode & Scrubber Controls**
  - Play, pause, speed toggle (`1x`, `2x`, `4x`), timeline scrubber.
  - Pre-packaged golden fixtures from verified SWE-bench runs.

---

## Phase 5: SWE-bench Verified Evaluation Suite
- [ ] **Task 5.1: Benchmark Runner Harness**
  - Implement `eval/run_benchmark.py` running the 30-task slice.
  - Concurrency management (max 10 simultaneous runs to respect beta limits).
- [ ] **Task 5.2: Comparative Baselines**
  - Run 10 tasks on Single-Branch Ultra baseline.
  - Run 30 tasks on Forkfix Multi-Tier engine.
  - Compute resolve rate, cost per resolved task, and escalation rescue metrics.
- [ ] **Task 5.3: Benchmark Results Dashboard**
  - Generate markdown and JSON report: `eval/results/summary.json`.
  - Render comparative table in frontend `/benchmark` view.

---

## Phase 6: Demo Video, Documentation & Devpost Submission
- [ ] **Task 6.1: Record & Edit 3-Minute Video**
  - Record the 5 key scenes per storyboard.
  - Add voiceover narration, callout annotations, and background audio.
  - Upload to YouTube (Public / Unlisted).
- [ ] **Task 6.2: Finalize Repository Documentation**
  - Polish `forkfix/README.md` with architecture diagrams, quickstart instructions, and model disclosure.
  - Finalize `forkfix/FEEDBACK.md` with measured latencies and Token Factory suggestions.
- [ ] **Task 6.3: Devpost Submission & Final Verification**
  - Fill Devpost application fields.
  - Verify hosted demo on Vercel/Railway.
  - Submit 8 hours ahead of deadline.
