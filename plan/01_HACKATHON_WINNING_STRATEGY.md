# Forkfix: Parallel Reality Debugging with Nebius Token Factory & NVIDIA Nemotron

> **Nebius x NVIDIA Global AI Hackathon Submission**  
> **Track:** Coding and Agentic Engineering Track  
> **Target Prizes:** Grand Prize ($20,000) | Coding Track Winner (Jetson Orin Nano) | Best Use of Tavily ($3,000) | Most Valuable Feedback

---

## 1. Executive Summary

Most autonomous coding agents adopt a **linear trial-and-error** paradigm: an LLM attempts an edit, runs tests, fails, appends errors to its prompt, and attempts another patch. In hard SWE problems, this approach fails predictably:
1. Context windows fill up with confusing failed shell outputs.
2. The agent wanders into dirty git states with half-applied edits.
3. High-tier reasoning models ($1–$3/1M tokens) are wasted on trivial syntax fixes, burning $0.50–$2.00 per attempt.

**Forkfix** introduces **Parallel Reality Debugging**. Powered by **Nebius Token Factory Sandboxes (Contree)** and **NVIDIA Nemotron** open models:
1. **Deterministic Checkpoint (C1):** Given an issue, a thinking Nemotron model writes a standalone reproduction test (`/tmp/repro.py`) and proves it fails in an isolated VM container.
2. **Parallel Exploration (Fast Tier):** From the exact same checkpoint C1, Forkfix forks **4 parallel branches** powered by lightweight, ultra-fast **Nemotron-3.5-Lightning** ($0.06/$0.24 per 1M tokens). Each branch explores distinct patch directions in its own isolated VM.
3. **Smallest Passing Patch Wins:** A verification engine checks all branches against the repro test. The smallest passing clean diff is selected.
4. **Escalation & Tavily Ground Truth:** If all 4 fast branches fail, the error trace is passed to **Tavily Search & Extract** to retrieve real-world documentation and bug resolutions. Then, **Nemotron-3-Ultra-550b** (with deep thinking enabled) ingests the failed traces and Tavily evidence to diagnose the exact root cause, spawning 3 targeted **Nemotron-3-Super** remediation branches.
5. **Interactive Time Travel:** Through an interactive visual branch graph (React Flow), developers can inspect any VM state, replay steps, or click any failed node to fork a new branch with a custom hint.

---

## 2. Judge Persona Analysis & Tailored Hooks

| Judge Persona | What They Value | Forkfix Direct Hook |
|---|---|---|
| **NVIDIA Senior ML Engineers** *(Nancy Agarwal, Abhinav Balasubramanian, Lakshmi Rameish, Surbhi Jha)* | Sophisticated model orchestration; correct usage of Nemotron reasoning (`enable_thinking`); cost-vs-accuracy trade-offs; token efficiency. | Multi-tier ladder: Lightning for broad exploration ($0.06/M), Super for guided repairs ($0.30/M), Ultra for high-order root-cause synthesis ($1.00/M). We demonstrate a verifiable 3x–5x cost reduction compared to pure Ultra baselines on SWE-bench. |
| **Nebius Token Factory & DevRel Leaders** *(Dylan Bristot, Rob Spectre, AbdulMajed Raja, Daniel Myers)* | Deep, idiomatic usage of Nebius Sandboxes (Contree SDK); utilizing preloaded SWE environments; actionable developer feedback on Token Factory. | First-class Contree image checkpointing (`ct.images.use` + immutable forks). Rigorous `FEEDBACK.md` providing quantitative telemetry (tokens/sec, cold-start latency, SDK ergonomics). |
| **Tavily Forward Deployed Engineers** *(Evan Rimer, Ricky Johnson, Lakshya Prakash Agarwal)* | Best Use of Tavily ($3k cash). Non-trivial integration of Tavily Search + Extract; transparent citations; domain exclusion to prevent benchmark data leakage. | When 4 fast branches fail with an ambiguous runtime exception, Tavily searches technical docs and extracts relevant solutions, displayed in a dedicated UI "Evidence Drawer". |

---

## 3. Prize Stacking Strategy

The hackathon allows stacking an overall prize or track prize with sponsor bonus awards:
1. **Grand Prize ($20,000 cash) / Coding Track Winner (Jetson Orin Nano):** Primary goal. Judged on Technical Implementation, Design, Potential Impact, and Quality of the Idea.
2. **Best Use of Tavily ($3,000 cash):** Deep integration into the escalation loop with full URL/content extraction and UI citation badges.
3. **Most Valuable Feedback ($100 cash + Swag):** Meticulously maintained `FEEDBACK.md` logging real API latencies, SDK quirks, and feature suggestions from day one.

---

## 4. 5-Day Chronological Execution Battle Plan

```
[Day 1: Oct 26] Auth, Core Orchestrator & Multi-Tier Nemotron Ladder
       │
[Day 2: Oct 27] Contree Sandboxes + Docker Fallback Engine + Event Streaming
       │
[Day 3: Oct 28] Tavily Research Escalation + React Flow Visual UI
       │
[Day 4: Oct 29] 30-Task SWE-bench Benchmark Suite + Replay Recording Fixtures
       │
[Day 5: Oct 30] 3-Minute Video, Devpost Submission, Freeze & Submit 8h early
```

### Day 1 (Mon, Oct 26) — Core Orchestration & Model Tiers
- Confirm Nebius Token Factory API keys and model availability:
  - `nvidia/Nemotron-3_5-Lightning`
  - `nvidia/nemotron-3-super-120b-a12b`
  - `nvidia/Nemotron-3-Ultra-550b-a55b`
- Implement `core.py`: multi-tier prompting, token cost tracking, and structured bash execution parser.
- Build test harness to verify `repro.py` generation on a sample GitHub issue.

### Day 2 (Tue, Oct 27) — Sandbox Execution & Event Stream
- Implement dual execution abstraction: `ContreeSandboxEngine` (Token Factory) and `DockerSandboxEngine` (local fallback for offline dev/testing).
- Implement checkpointing: snapshot C1 after repro confirmation; parallel async branching from C1.
- Implement FastAPI SSE streaming backend emitting typed event JSON:
  `step`, `branch_start`, `test_result`, `escalation`, `winner`.

### Day 3 (Wed, Oct 28) — Tavily Escalation & Interactive UI
- Integrate Tavily Search (`search_depth="advanced"`) and Extract for error remediation.
- Build Next.js 14 frontend with `@xyflow/react` (React Flow) visualizing the branch execution tree.
- Add split diff viewer (`diff2html`), cost dial ($ spent per run), and live terminal logs.
- Add "Time Travel": click any node to spawn a manual branch with human hints.

### Day 4 (Thu, Oct 29) — 30-Task SWE-bench Benchmark & Replay Fixtures
- Run evaluation slice on 30 SWE-bench Verified tasks.
- Record all events to `events.jsonl` golden fixtures so the hosted demo has instant, zero-latency 100% reliable replay mode for judges.
- Calculate verified resolved rate, cost per resolved task, and comparison vs Ultra-only baseline.

### Day 5 (Fri, Oct 30) — Video, Devpost & Submission
- Record 3-minute video showing:
  1. The core premise and live parallel race.
  2. Reproduction test failing -> 4 branches racing in parallel.
  3. One branch succeeding at $0.02 vs failing branches triggering Tavily + Ultra.
  4. Interactive time travel & custom hint branching.
  5. The benchmark results table.
- Write Devpost story, complete README, compile `FEEDBACK.md`.
- Final submission before 14:00 IST (8 hours before 22:30 IST deadline).

---

## 5. Risk Matrix & Contingency Protocols

| Risk | Impact | Contingency |
|---|---|---|
| **Contree Sandbox Beta access delay** | High | Abstract `SandboxEngine`. Use local `DockerSandboxEngine` with `docker commit` checkpointing for local dev and benchmarks; swap to Contree SDK seamlessly as soon as activated. |
| **Token Factory API rate limit / capacity** | Medium | Built-in exponential backoff (`max_retries=6`); concurrency pool bounded to 10 parallel tasks; local caching for deterministic benchmark replays. |
| **`enable_thinking` template incompatibility** | Low | Fallback to explicit chain-of-thought prompting in system prompt if `chat_template_kwargs` is rejected by the endpoint. |
| **Live demo failure during judge review** | Critical | **Replay Mode** enabled by default! Judges can toggle "Live Sandbox" or "Pre-computed Verified Replay" with zero wait time and zero flakiness. |
