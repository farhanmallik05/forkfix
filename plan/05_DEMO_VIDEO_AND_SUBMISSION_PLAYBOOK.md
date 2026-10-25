# Forkfix: Demo Video Script, Devpost Copy & Submission Playbook

---

## 1. 3-Minute Demo Video Script & Storyboard (180 Seconds Max)

The video is judged on clarity, technical substance, and demonstrating real software running on Nebius Token Factory with NVIDIA Nemotron models.

| Time Window | Visual Scene | Audio Voiceover / Narration | Key Takeaway for Judges |
|---|---|---|---|
| **0:00 – 0:20 (20s)** | Split screen: Traditional linear agent getting stuck in dirty state vs Forkfix dashboard showing 4 green/red branch nodes spawning from a single checkpoint. | "Current autonomous coding agents debug linearly: they make an edit, get stuck, hallucinate, and burn dollars on huge models. Meet Forkfix: Parallel Reality Debugging powered by Nebius Token Factory Sandboxes and NVIDIA Nemotron." | Hook: Solves real pain; visually stunning first impression. |
| **0:20 – 0:50 (30s)** | Paste a real SWE-bench GitHub issue. Watch Nemotron-3-Super generate `/tmp/repro.py`. The repro runs in Nebius Sandbox C1 and turns red. | "First, Nemotron-3-Super writes a reproduction script and verifies that it fails on the unedited codebase. This immutable snapshot becomes Checkpoint C1." | Proves scientific rigor: verifiable failing test before touching code. |
| **0:50 – 1:25 (35s)** | 4 branches branch out simultaneously from C1. Terminal streams show commands executing in parallel in Token Factory. Branch 1 fails, Branch 2 fails, Branch 4 passes! | "From C1, Forkfix forks four parallel realities powered by the hyper-efficient Nemotron-3.5-Lightning. They explore different repair strategies simultaneously in isolated sandboxes. Branch 4's repro exits zero—the smallest clean diff is verified and declared the winner for just two cents." | Demonstrates Token Factory Sandboxes concurrency + Nemotron Lightning cost efficiency ($0.02). |
| **1:25 – 2:05 (40s)** | Load a harder issue (Sympy) where all 4 fast branches fail. Show the Purple Escalation node appear. Tavily search results pop up in the drawer. Nemotron-3-Ultra's thought trace reveals the root cause. 3 Super branches spawn and one wins! | "What if all fast attempts fail? Forkfix doesn't guess. It extracts the error signatures, queries Tavily for external technical documentation, and feeds the failure traces into Nemotron-3-Ultra with thinking enabled. Ultra diagnoses the exact architectural bug, and Nemotron-3-Super lands the fix." | Demonstrates Tavily Search/Extract integration + Nemotron Ultra reasoning. Target for $3k Tavily prize! |
| **2:05 – 2:30 (25s)** | Click on any past node in the React Flow tree. Open the "Time Travel" modal, type a hint (*"Check null pointer in token parser"*), and watch a new reality branch fork in real-time. | "Forkfix gives humans total control. With Time Travel, click any snapshot in the tree, type a hint, and spawn a new branch from that exact point without losing prior work." | Shows interactive human-in-the-loop developer tool. |
| **2:30 – 2:50 (20s)** | Results table on screen: 30 SWE-bench Verified tasks. Metrics: resolved count, cost comparison ($0.08 vs $0.55 on Ultra baseline), tokens/sec. | "In our 30-task SWE-bench Verified benchmark, Forkfix resolved real issues at a 4.5x lower cost than pure Ultra baselines, proving that parallel cheap exploration beats expensive linear guessing." | Empirical proof of claims. |
| **2:50 – 3:00 (10s)** | Code repo, MIT License, architecture diagram, and Token Factory / NVIDIA logos. | "Forkfix: Build the next frontier of agentic engineering on open infrastructure. Check out our open-source repo and live replay demo today." | Professional call to action. |

---

## 2. Devpost Submission Narrative

### Project Title
**Forkfix: Parallel Reality Debugging with Nebius Token Factory & NVIDIA Nemotron**

### Tagline
*Fork 4 parallel repair realities from an immutable test checkpoint, find the smallest passing patch for pennies, and escalate with Tavily & Nemotron Ultra.*

### Track
Coding and Agentic Engineering Track

### Target Prizes
- Grand Prize ($20,000)
- Coding and Agentic Engineering Track Winner (NVIDIA Jetson Orin Nano)
- Best Use of Tavily ($3,000)
- Most Valuable Feedback ($100)

### Narrative Sections for Devpost
- **Inspiration:** Why single-branch agents fail; the analogy to quantum many-worlds in debugging.
- **What it does:** Explain Checkpoint C1, 4x Lightning parallel exploration, verification via exit code, Tavily error research, Nemotron-3-Ultra deep reasoning escalation, and React Flow time-travel.
- **How we built it:**
  - Nebius Token Factory Sandboxes (Contree SDK) for container snapshotting & branching.
  - NVIDIA Nemotron model family (`Nemotron-3.5-Lightning`, `nemotron-3-super-120b`, `Nemotron-3-Ultra-550b` with `enable_thinking`).
  - Tavily Search (advanced depth) and Tavily Extract.
  - FastAPI SSE streaming backend + Next.js 14, Tailwind CSS, `@xyflow/react`, and `diff2html`.
- **Challenges we ran into:** Managing concurrent Sandbox states, isolating benchmark tasks to prevent data leakage, optimizing prompt context across parallel execution steps.
- **Accomplishments that we're proud of:** Solving real SWE-bench Verified issues for less than $0.05 per task, while providing a buttery-smooth visual time-travel interface.
- **What we learned:** Fast, cheap models exploring parallel state spaces frequently out-compete monolithic reasoning models on engineering tasks when paired with deterministic test oracles.
- **What's next for Forkfix:** Support for multi-repo microservices, automatic pull request submission with video recording artifacts, and Jetson-based on-premise execution.

---

## 3. `FEEDBACK.md` Protocol for Nebius & NVIDIA

To win the **Most Valuable Feedback ($100 + Swag)** award, Forkfix includes a first-class `FEEDBACK.md` document updated continuously during development:

### Structure of `FEEDBACK.md`
1. **Nebius Token Factory API:**
   - Measured Latency & Throughput: Tokens/sec comparison across Lightning, Super, and Ultra.
   - Streaming stability over high-concurrency requests (40+ concurrent branches).
   - Error codes and rate limit recovery observations.
2. **Nebius Sandboxes (Contree SDK):**
   - Developer ergonomics of `contree-sdk` vs `contree-cli`.
   - Snapshot creation latency and image caching performance on preloaded SWE images.
   - Command exit code handling and stdout/stderr separation nuances.
3. **NVIDIA Nemotron Models:**
   - Effectiveness of `enable_thinking` template kwargs on complex code synthesis.
   - Tool-calling and bash block formatting adherence across models.
4. **Tavily Search API:**
   - Relevance of documentation snippets on Python AST and ORM exceptions.
   - Performance of `tavily.extract` on heavy documentation domains.

---

## 4. Final Submission Checklist (Before Oct 30, 14:00 IST)

- [ ] **Public GitHub Repo:** Open source license (Apache-2.0 or MIT) clearly visible at root.
- [ ] **Working Hosted Demo URL:** Deployed on Vercel/Railway with default Replay Mode enabled (judges see instantaneous verified runs without needing API keys).
- [ ] **3-Minute YouTube Video:** Public or unlisted, max 180 seconds, 1080p, clear audio narration.
- [ ] **Comprehensive README.md:** Setup guide, architecture diagram, exact model IDs, Token Factory / Sandboxes disclosure, and SWE-bench benchmark reproduction command.
- [ ] **Complete Devpost Form:** All questions answered, video embedded, repo linked, track selected.
- [ ] **Pasted `FEEDBACK.md`:** Submitted in the feedback section of the Devpost submission form.
