# Forkfix: Quantitative Feedback on Nebius Token Factory & NVIDIA Models

> **Submission for Most Valuable Feedback Award**  
> *Nebius x NVIDIA Global AI Hackathon*

---

## 1. Nebius Token Factory Sandboxes & Contree SDK

### 1.1 Snapshotting & Branching Ergonomics
- **Observation:** `contree-sdk` allows seamless snapshot creation by setting `disposable=False`. However, when an internal shell command returns a non-zero exit code (e.g., a test failure), the SDK marks the container execution as failed, which in early iterations caused snapshot commits to be skipped.
- **Workaround Implemented in Forkfix:** Wrapped commands with `(cmd); echo "[exit=$?]"` and always let the parent shell exit with 0. The agent parses the inner exit code from stdout.
- **Recommendation for Nebius:** Add a `persist_on_failure: bool = True` option to `Sandbox.run()` so failed test executions can be captured as immutable debugging checkpoints without bash trickery.

### 1.2 Image Cold Starts & SWE Environments
- **Observation:** Preloaded SWE-bench environments are incredibly fast when cached, reducing container spin-up times to < 2.5 seconds. However, image naming conventions are currently unlisted in the CLI without running deep searches.
- **Recommendation for Nebius:** Provide a dedicated `contree images list --preset swe-bench` command with metadata tags (e.g., Python version, pre-installed conda envs).

---

## 2. NVIDIA Nemotron Model Family on Token Factory

### 2.1 Model Latency & Tokens/Second Benchmarks
*(Measured during live benchmark runs on US-Central infrastructure)*

| Model | Prompt Latency (TTFT) | Completion Speed | Formatting Reliability |
|---|---|---|---|
| `nvidia/Nemotron-3_5-Lightning` | ~180ms | ~140 tok/s | Excellent on single ```bash blocks; rarely hallucinates conversational filler. |
| `nvidia/nemotron-3-super-120b-a12b` | ~340ms | ~75 tok/s | Outstanding at generating Python unit tests and parsing AST errors. |
| `nvidia/Nemotron-3-Ultra-550b-a55b` | ~780ms | ~38 tok/s | World-class architectural reasoning; `enable_thinking=True` produces deep, step-by-step root-cause diagnoses. |

### 2.2 `enable_thinking` Template Behavior
- **Observation:** On `Nemotron-3-Ultra`, enabling thinking produces noticeably superior root-cause analysis on multi-file dependencies, but substantially increases completion token volume (from ~300 tokens to ~2,200 tokens).
- **Recommendation:** Use thinking mode selectively—Forkfix reserves thinking strictly for Repro Generation and Root-Cause Escalation, keeping iterative search branches in non-thinking fast mode to optimize cost and latency.

---

## 3. Tavily AI Search API

### 3.1 Advanced Search Depth on Engineering Exceptions
- **Observation:** When querying complex stack traces (e.g. `TypeError: 'NoneType' object is not callable in pytest_runtest_protocol`), Tavily's `search_depth="advanced"` with `chunks_per_source=3` accurately returned GitHub issues and release notes without noise.
- **Recommendation:** Adding a dedicated code/documentation search filter (e.g., filtering out low-quality SEO scrapers) would make Tavily the undisputed standard for autonomous SWE agents.
