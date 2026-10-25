# Forkfix: Frontend UI/UX Specification

## 1. Aesthetic Direction & Design Philosophy

Forkfix is built for discerning software engineers and hackathon judges. It rejects generic white-label admin templates in favor of a **modern, high-density, cyber-minimalist engineering console**.

- **Palette:** Deep Obsidian black (`#0B0D11`), muted slate borders (`#1E222B`), cybernetic Emerald green (`#10B981`) for passing branches, Crimson red (`#EF4444`) for failing attempts, and Electric Violet (`#8B5CF6`) for Tavily + Ultra escalation.
- **Typography:**
  - Code & Telemetry: `JetBrains Mono` or `Fira Code`.
  - Display & Headings: `Plus Jakarta Sans` or `Inter`.
- **Motion:** Subtle CSS spring transitions, glowing edge paths along winning branches, and animated pulse indicators on active Sandbox containers.

---

## 2. Page Layout Structure

```
+-----------------------------------------------------------------------------------------+
| [FORKFIX LOGO]  Issue: django/django#31422   [Mode: Replay / Live]   [Spent: $0.048]   |
+-----------------------------------------------------------------------------------------+
|                                    |                                                    |
|  LEFT PANEL (60%):                 |  RIGHT PANEL (40%):                                |
|  Interactive Reality Graph         |  Context, Telemetry & Diff Inspector               |
|  (React Flow Canvas)               |                                                    |
|                                    |  +-----------------------------------------------+ |
|  [Root: Issue #31422]              |  | TAB 1: Winning Diff (diff2html)               | |
|         │                          |  | TAB 2: Live Shell Logs (Active Branch)        | |
|  [C1: Failing Repro Verified]      |  | TAB 3: Tavily Ground Truth & Citations        | |
|    ├── Branch 1 (Lightning) ❌    |  | TAB 4: Cost & Token Economics Matrix          | |
|    ├── Branch 2 (Lightning) ❌    |  +-----------------------------------------------+ |
|    ├── Branch 3 (Lightning) ❌    |                                                    |
|    └── Branch 4 (Lightning) ✅ 🏆 |  [Active Step Terminal Output]                     |
|                                    |  $ git diff                                        |
|  (Or if escalated:)                |  + return self._format_currency(val)               |
|  [Tavily Search: Docs Extracted]   |  - return str(val)                                 |
|         │                          |                                                    |
|  [Ultra-550b Diagnosis]            |  [Time Travel Action Button]                       |
|    └── Branch E1 (Super) ✅        |  [⚡ Fork From This Snapshot with Custom Hint...]   |
|                                    |                                                    |
+-----------------------------------------------------------------------------------------+
| BOTTOM CONTROLS: [Replay Scrubber: ▶ ⏸ 2x 4x]  [Step 14/22]  [Load Sample Fixture ▾]     |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Core Interactive Components

### 3.1 Interactive Reality Graph (`@xyflow/react`)
- **Custom Nodes:**
  - `CheckpointNode`: Displays snapshot UUID, repro status badge (Red = repro confirmed failing), timestamp.
  - `BranchNode`: Displays branch identifier (`b1`..`b4`), model badge (`Nemotron Lightning`), step counter (`12/25`), cost ticker (`$0.012`), and status indicator (Active / Green Pass / Red Fail).
  - `EscalationNode`: Highlighted in electric purple; shows Tavily query badge and Ultra diagnosis pill.
  - `WinnerNode`: Highlighted in glowing emerald with trophy badge and direct link to the winning diff.
- **Edge Styling:**
  - Default: Muted dark grey connecting lines.
  - Active: Animated dashed stroke with glowing particles.
  - Winning Path: Bold emerald solid line with pulse animation tracing the path from root to final patch.
- **Node Interaction:**
  - Clicking any node opens its exact shell commands, terminal outputs, and git diff in the right-hand inspector.
  - Hovering previews execution latency and tokens consumed.

### 3.2 Time-Travel & Hint Modal
- When a user selects any node in the graph, an action bar presents:
  `Fork New Reality from Snapshot [UUID]`
- Opens a sleek modal:
  - Input field: *"Enter guidance or hint for Nemotron (e.g. 'Check edge cases where limit is 0')..."*
  - Model selector dropdown: Default `Nemotron-3-Super` or `Nemotron-3.5-Lightning`.
  - Confirm button: Dispatches a new branch run from that exact snapshot UUID.
  - The graph dynamically spawns a new branch live on the canvas!

### 3.3 Patch Inspector (`diff2html` / Syntax Highlighter)
- Renders GitHub-quality split or unified diffs.
- Shows file stats: lines added, lines deleted, patch size in bytes.
- Direct "Copy Patch" and "Download .patch" actions.

### 3.4 Tavily Ground Truth Drawer
- Whenever escalation is triggered, this tab lights up:
  - Displays search queries executed by Tavily.
  - Clickable source cards with title, domain badge, relevance snippet, and full extracted markdown toggle.
  - Proves the agent grounded its reasoning in real-world documentation.

### 3.5 Telemetry & Cost Dial
- Real-time gauge tracking:
  - Total Spend ($0.0000 format, updating per LLM response).
  - Savings vs Pure Ultra baseline (e.g. *"4.2x Cheaper than Ultra"*).
  - Total tokens generated (prompt vs completion).
  - Sandboxes active in parallel.

---

## 4. Replay Scrubber & Zero-Latency Judge Mode

To guarantee judges can experience the full interactive product even without live cloud credentials:
- A prominent toolbar toggle: `Mode: [🟢 Live Sandbox | ⚡ Instant Replay]`.
- Replay mode includes a task picker:
  - *Django #31422 (Resolved on Branch 4 - $0.04)*
  - *Sympy #18059 (Escalated via Tavily + Ultra - $0.14)*
  - *Pytest #7234 (Fast Pass on Branch 1 - $0.02)*
- A timeline scrubber allowing playback at `1x`, `2x`, `4x` speed, or jumping straight to the winning patch.
