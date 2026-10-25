# Forkfix: Evaluation & Benchmarking Methodology

## 1. Evaluation Objectives

To win the hackathon's **Technological Implementation** and **Potential Impact** criteria, Forkfix does not merely claim to be effective—it provides **reproducible, audited empirical evidence** on the gold standard for software engineering agents: **SWE-bench Verified**.

We answer three concrete questions that judges can verify:
1. **Resolution Efficacy:** Does parallel reality branching resolve real GitHub issues that linear agents miss?
2. **Economic Efficiency:** Does the Nemotron tiered ladder achieve higher or equal resolution at a fraction of the cost of pure Ultra-550b?
3. **Escalation Lift:** How many tasks failed by cheap exploration are rescued by Tavily web evidence + Nemotron-3-Ultra-550b?

---

## 2. Benchmark Task Selection (30-Task Verified Slice)

We curate 30 representative tasks from **SWE-bench Verified** across diverse Python ecosystems:
- **`django/django`** (Web framework, database ORM, complex SQL query parsing)
- **`sympy/sympy`** (Symbolic math, algorithmic solvers, edge-case arithmetic)
- **`scikit-learn/scikit-learn`** (ML pipelines, numerical tolerance, matrix manipulations)
- **`pytest-dev/pytest`** (Testing infrastructure, AST rewriting, CLI argument parsing)
- **`pallets/flask`** (Routing, WSGI contexts, request handling)
- **`requests/requests`** (HTTP transport, SSL adapters, header encoding)

Selection Criteria:
- Verified test reproducibility.
- Pure Python environments supported out-of-the-box in Token Factory Sandboxes.
- Moderate repo footprint to ensure fast sandbox provisioning.

---

## 3. Scientific Rigor & Strict Anti-Leakage Protocol

> [!CAUTION]
> **Data Contamination Prevention:**
> A major concern in hackathons using SWE-bench is test leakage. Nebius publishes SWE-rebench; their judges know how easy it is to accidentally cheat by exposing the test patch.

Forkfix strictly enforces the following anti-contamination rules:
1. **Zero Access to Ground-Truth Patches:** The agent's prompt contains *only* the user's issue description. The ground-truth patch (`patch.diff`) and SWE-bench test definitions (`FAIL_TO_PASS`, `PASS_TO_PASS`) are strictly isolated in the offline evaluation harness.
2. **Autonomous Repro Generation:** The agent must synthesize its own `/tmp/repro.py` based solely on the problem description.
3. **Tavily Exclusions:** During benchmark runs, Tavily queries explicitly enforce:
   `exclude_domains=["github.com", "gitlab.com", "bitbucket.org"]`
   This guarantees that Tavily retrieves technical documentation, API specs, and syntax references rather than the upstream pull request that resolved the issue.
4. **Post-Hoc SWE-bench Validation:** After Forkfix selects the winning patch, the harness applies the candidate patch to a clean testbed container and executes the official SWE-bench evaluation script (`eval_patch.py`).

---

## 4. Comparative Baselines

We measure three distinct system configurations:

| Configuration | Architecture | Models Used | Expected Cost / Task |
|---|---|---|---|
| **Baseline A: Single Linear Ultra** | Standard single-branch agent (25 steps) | `nvidia/Nemotron-3-Ultra-550b-a55b` | $0.45 – $0.90 |
| **Baseline B: Forkfix Fast Only** | 4 parallel branches without escalation | `nvidia/Nemotron-3_5-Lightning` | $0.04 – $0.08 |
| **Forkfix Full (Ours)** | 4x Fast branches -> Tavily + Ultra diagnosis -> 3x Super remediation | Lightning -> Tavily + Ultra -> Super | **$0.07 – $0.18** (Blended) |

---

## 5. Metrics Tracked & Reported

All metrics are logged in `eval/results/benchmark_summary.json` and rendered in the live UI results table:

1. **Pass Rate (% Resolved):**
   $$\text{Resolve Rate} = \frac{\text{Tasks Passing SWE-bench Verification}}{\text{Total Tasks (30)}} \times 100$$
2. **Cost per Resolved Task ($/task):**
   $$\text{Economic Efficiency} = \frac{\text{Total Token Cost for All Runs}}{\text{Number of Successfully Resolved Tasks}}$$
3. **Resolution Latency (Wall-Clock Seconds):**
   Wall-clock time to green patch (leveraging Token Factory async parallelism).
4. **Escalation Rescue Rate (%):**
   Percentage of tasks that failed all 4 fast branches but succeeded on the Tavily + Ultra escalation path.
5. **Token Consumption by Tier:**
   Detailed breakdown of prompt and completion tokens across Lightning, Super, and Ultra.

---

## 6. Pre-Recorded Golden Replay Fixtures

For judges reviewing the project without active Nebius credentials:
- Every evaluated benchmark run is serialized into `forkfix/frontend/public/fixtures/events_{task_id}.jsonl`.
- The UI contains an interactive dropdown selector:
  *"Load Verified SWE-bench Run: Django #31422 (Resolved for $0.04)"*.
- The replay loads the complete event sequence with exact timing, terminal outputs, branch graph, and diff preview, providing an undeniable proof of performance.
