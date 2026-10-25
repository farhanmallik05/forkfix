# Forkfix ⚡

> **Parallel Reality Debugging on Open Infrastructure**  
> *Submitted to the Nebius x NVIDIA Global AI Hackathon (Coding and Agentic Engineering Track)*

---

## What is Forkfix?

Most coding agents debug linearly: they make an edit, get stuck, hallucinate, and burn high-tier reasoning tokens on repetitive failures.

**Forkfix** replaces linear trial-and-error with **Parallel Reality Debugging**:
1. **Deterministic Checkpoint (C1):** A thinking model (`nvidia/nemotron-3-super-120b-a12b`) synthesizes a standalone `/tmp/repro.py` and proves it fails in an isolated sandbox.
2. **Parallel Exploration (Fast Tier):** From the exact same checkpoint C1, Forkfix forks **4 concurrent reality branches** powered by the hyper-efficient `nvidia/Nemotron-3_5-Lightning` ($0.06/$0.24 per 1M tokens).
3. **Oracle Verification:** All branches run their tests in isolated sandboxes. The smallest clean passing git diff is selected as the winner.
4. **Tavily + Nemotron-3-Ultra Escalation:** If all fast attempts fail, error signatures are queried via **Tavily Search & Extract**, and fed alongside the 4 failure traces into `nvidia/Nemotron-3-Ultra-550b-a55b` with thinking enabled. Ultra diagnoses the root cause and directs 3 targeted remediation branches.
5. **Interactive Time Travel:** Developers can inspect any node in the React Flow execution tree, click any past snapshot, and fork a new branch with custom human guidance.

---

## How Nebius & NVIDIA Open Infrastructure Accelerate Forkfix

| Component | Technology | Why It Matters |
|---|---|---|
| **VM-Level Sandboxing & Branching** | Nebius Token Factory Sandboxes (`contree-sdk`) | Enables zero-copy, copy-on-write branching from Checkpoint C1 across 4 parallel VM environments. |
| **Fast Parallel Exploration** | `nvidia/Nemotron-3_5-Lightning` | Super-low latency and extreme cost efficiency ($0.06/M input tokens) allows broad state-space exploration for pennies. |
| **Failing Repro & Remediation** | `nvidia/nemotron-3-super-120b-a12b` | Balanced 120B reasoning powerhouse for test generation and guided fixes. |
| **Root-Cause Architectural Synthesis** | `nvidia/Nemotron-3-Ultra-550b-a55b` | 550B flagship reasoning model with `enable_thinking` for deep diagnosis when all junior branches fail. |
| **Real-World Error Research** | Tavily Search & Extract | Ground-truth technical documentation injection without benchmark data contamination. |

---

## Quickstart

### Prerequisites
- Python 3.12+
- Node.js 18+
- Nebius Token Factory API Key & Project ID
- Tavily API Key

### 1. Setup Backend
```bash
cd forkfix/backend
cp ../.env.example .env
# Edit .env with your NEBIUS_API_KEY and TAVILY_API_KEY

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 2. Setup Frontend
```bash
cd forkfix/frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to interact with the Forkfix dashboard.

---

## Replay Mode (Zero Credentials Required for Judges)

If you are evaluating this repository without active Token Factory Sandbox beta access:
1. Open the UI at `http://localhost:3000`.
2. Toggle **Mode: Instant Replay**.
3. Select any verified SWE-bench benchmark task (e.g., `Django #31422` or `Sympy #18059`).
4. Watch the verified parallel race, terminal logs, and patch diff with zero latency and 100% reproducibility.

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
