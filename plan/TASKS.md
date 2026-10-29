# Forkfix: Master Work Breakdown Structure & Tasks (WBS)

## Phase 0: Project Scaffolding & Compliance Setup [COMPLETED]
- [x] **Task 0.1: Initialize Main Project Structure**
  - Directory layout in `forkfix/`: `backend/`, `frontend/`, `eval/`, `data/`.
  - Apache-2.0 `LICENSE` at root.
  - `.env.example` with `NEBIUS_API_KEY`, `TAVILY_API_KEY`, `REPO_DIR`, `PORT`.
- [x] **Task 0.2: Feedback Logging System**
  - Created `forkfix/FEEDBACK.md` with quantitative telemetry and SDK suggestions.
- [x] **Task 0.3: Environment & Dependency Management**
  - Backend: `pyproject.toml` with `fastapi`, `uvicorn`, `openai`, `tavily-python`, `contree-sdk`, `pydantic`.
  - Frontend: `package.json` with Next.js 14, Tailwind CSS, `@xyflow/react`, `diff2html`, `lucide-react`.

---

## Phase 1: Core Engine & Multi-Tier Agent Orchestration [COMPLETED]
- [x] **Task 1.1: Sandbox Abstraction Layer**
  - Implemented `SandboxSession` and `SandboxEngine` protocol interfaces in `backend/sandbox.py`.
  - Implemented `ContreeSandboxEngine` using `contree-sdk` with snapshot tracking.
  - Implemented `DockerSandboxEngine` as local fallback for development and CI testing.
  - Implemented `MockSandboxEngine` for rapid UI and SSE testing with simulated state steps.
- [x] **Task 1.2: Tri-Tier Nemotron Client**
  - Implemented `backend/nemotron.py` with Token Factory endpoint wrapper.
  - Supported `fast` (`Nemotron-3.5-Lightning`), `super` (`nemotron-3-super-120b`), and `ultra` (`Nemotron-3-Ultra-550b`).
  - Implemented `enable_thinking` template kwargs toggling and fallback.
  - Real-time token usage and cost accounting ($/1M token pricing map).
- [x] **Task 1.3: Repro Generator & Checkpoint C1 Creator**
  - Implemented `prepare_checkpoint_c1()` in `backend/orchestrator.py`.
  - Synthesized isolated `/tmp/repro.py`.
  - Verified script fails on clean repo; captured initial stderr/stdout; tagged snapshot as Checkpoint C1.
- [x] **Task 1.4: Parallel Branching & Verification Engine**
  - Implemented `run_branch()` and `race()` in `backend/orchestrator.py`.
  - Spawned 4 concurrent branches from C1 using `asyncio.gather`.
  - Implemented bash block parser, timeout safeguards, and $0.15 budget limits.
  - Implemented minimal passing diff selection on zero-exit transition.

---

## Phase 2: Tavily Research & Diagnostics Escalation [COMPLETED]
- [x] **Task 2.1: Tavily Search & Extract Service**
  - Implemented `backend/tavily_service.py`.
  - Configured `search_depth="advanced"`, `chunks_per_source=3`, and anti-leakage domain exclusion filter (`exclude_domains=["github.com", "gitlab.com", "bitbucket.org", "swebench.com"]`).
  - Extracted technical documentation content for top URLs.
- [x] **Task 2.2: Nemotron Ultra Deep Reasoning Pipeline**
  - Digested failure traces from exhausted branches.
  - Prompted `Nemotron-3-Ultra-550b` (with thinking enabled) to identify root cause and code location.
  - Formatted structured diagnosis and launched guided remediation branches with `Nemotron-3-Super`.

---

## Phase 3: SSE Streaming, Event Persistence & Time Travel API [COMPLETED]
- [x] **Task 3.1: Typed Event Architecture**
  - Defined Pydantic event models in `backend/events.py` (`checkpoint_created`, `branch_spawned`, `step_executed`, `escalation_triggered`, `winner_selected`).
  - Implemented unified `EventEmitter` writing simultaneously to SSE queues and SQLite run tables.
- [x] **Task 3.2: FastAPI Application Endpoints**
  - `POST /api/run`: Start new debugging run for a given issue and repo/image UUID.
  - `GET /api/stream/{run_id}`: Real-time Server-Sent Events (SSE) feed.
  - `GET /api/runs`: List historical runs.
  - `GET /api/runs/{run_id}/events`: Retrieve serialized event log for instant replay.
  - `POST /api/fork`: Time-travel endpoint to fork a new branch from any prior snapshot node with human hints.
  - `POST /api/webhook/github`: Webhook endpoint for automated issue triage.

---

## Phase 4: Modern Next.js UI & Interactive Reality Canvas [COMPLETED]
- [x] **Task 4.1: Design Tokens & Layout Shell**
  - Cyber-minimalist dark mode layout (`#07090C` canvas, slate cards, vibrant telemetry accents).
  - Header with issue switcher, live cost meter, active model badges, and mode toggle (`Live` vs `Replay`).
- [x] **Task 4.2: Interactive Reality Graph (`@xyflow/react`)**
  - Custom nodes: `CheckpointNode`, `BranchNode`, `StepNode`, `EscalationNode`, `WinnerNode`.
  - Dagre/Sugiyama hierarchical auto-layout engine.
  - Dynamic edge routing with emerald glow on winning branch.
- [x] **Task 4.3: Right-Hand Inspector & Diff Viewer**
  - Tabs: `Patch Inspector` (diff2html syntax colored), `Live Terminal`, `Tavily Ground Truth`, `Token Economics`.
  - Interactive modals: `PatchEditorModal`, `BranchComparator`, `TreeExportModal`, `PRExportModal`, `TimeTravelModal`.
- [x] **Task 4.4: Replay Mode & Scrubber Controls**
  - Play, pause, speed toggle (`1x`, `2x`, `4x`), timeline scrubber.
  - Pre-packaged golden fixtures from verified SWE-bench runs (`django-31422`, `sympy-18059`).

---

## Phase 5: SWE-bench Benchmark & GitHub Action Bot [COMPLETED]
- [x] **Task 5.1: 10-Task Industrial Benchmark Runner Harness**
  - Implemented `eval/run_benchmark.py` running the 10-task slice.
  - Concurrency management with `asyncio.Semaphore(5)`.
  - Metrics computation: cost reduction factor, average cost per task ($0.038).
- [x] **Task 5.2: Dedicated Leaderboard Page**
  - Built `/benchmark` page in Next.js 14.
  - Prerendered statically with zero TypeScript errors.
- [x] **Task 5.3: Official GitHub Action Bot**
  - Created `action.yml` and `.github/workflows/forkfix.yml`.
  - Implemented collapsible issue comment generation in `backend/github_bot.py`.
  - Verified offline with unit test suite (`test_sprint_iter4.py`).
- [x] **Task 5.4: Test Suite Validation**
  - 33/33 automated Pytest unit tests passing across 8 test suites.

---

## Phase 6: Live Cloud Deployment & Telemetry Verification [ACTIVE SPRINT]
- [ ] **Task 6.1: Deploy Frontend to Vercel**
  - Deploy `forkfix/frontend` to Vercel.
  - Verify that Verified Replay Mode is active on first page load.
  - Confirm public URL and mobile/desktop responsiveness.
- [ ] **Task 6.2: Deploy Backend to Railway**
  - Deploy `forkfix/backend` using `railway.json` / Dockerfile.
  - Verify healthcheck endpoint (`GET /api/health`).
- [ ] **Task 6.3: Capture Final Live Telemetry for `FEEDBACK.md`**
  - Run 1 live task with live `NEBIUS_API_KEY` to update latency and throughput metrics.

---

## Phase 7: Demo Video, Devpost Submission & Hard Freeze [SUBMISSION GATE]
- [ ] **Task 7.1: Record & Edit 3-Minute Video (175 Seconds)**
  - Record the 6 key scenes per master script in `plan/00_MASTER_HACKATHON_WINNING_PLAN.md`.
  - Add voiceover narration and callout annotations.
  - Upload to YouTube (Public / Unlisted) with custom thumbnail.
- [ ] **Task 7.2: Devpost Application Staging**
  - Paste submission narrative from `plan/06_DEVPOST_SUBMISSION_FINAL.md`.
  - Embed YouTube video and live Vercel demo URL.
  - Select Coding & Agentic Engineering Track.
  - Paste `forkfix/FEEDBACK.md` content into feedback section.
- [ ] **Task 7.3: Pre-Flight Verification & Early Submission**
  - Complete 25-point Pre-Flight Zero-Failure Checklist.
  - Submit Devpost application by Friday, Oct 30 at 14:00 IST (8 hours ahead of deadline).
  - HARD FREEZE on repository.
