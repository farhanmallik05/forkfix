"""Generates a clean Markdown evaluation report from benchmark_summary.json."""

from __future__ import annotations
import json
from pathlib import Path
import sys

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def generate_markdown_report(summary_path: Path | None = None, output_path: Path | None = None) -> str:
    summary_file = summary_path or (RESULTS_DIR / "benchmark_summary.json")
    if not summary_file.exists():
        return f"Error: {summary_file} not found."

    with open(summary_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = data.get("total_tasks", 0)
    resolved = data.get("resolved_tasks", 0)
    rate = data.get("resolve_rate_percent", 0.0)
    avg_cost = data.get("avg_cost_per_task", 0.0)
    baseline_cost = data.get("ultra_only_baseline_cost_per_task", 0.48)
    cost_factor = data.get("cost_reduction_factor", 1.0)
    engine = data.get("engine", "mock")

    lines = [
        "# Forkfix SWE-bench Evaluation Report",
        "",
        f"**Engine:** `{engine}` | **Tasks Evaluated:** `{total}` | **Resolution Rate:** `{rate}%` ({resolved}/{total})",
        f"**Average Cost per Task:** `${avg_cost:.4f}` | **Sequential Ultra Baseline:** `${baseline_cost:.2f}` | **Efficiency Advantage:** `{cost_factor}x`",
        "",
        "## Task-by-Task Execution Breakdown",
        "",
        "| Task ID | Repository | Status | Elapsed (s) | Cost ($) | Patch Bytes |",
        "|---|---|---|---:|---:|---:|",
    ]

    for item in data.get("task_details", []):
        status_badge = "✅ Resolved" if item.get("status") == "resolved" else "❌ Unresolved"
        task_id = item.get("task_id", "")
        repo = item.get("repo", "")
        elapsed = item.get("elapsed_seconds", 0.0)
        cost = item.get("total_cost", 0.0)
        patch_size = item.get("patch_size", 0)
        lines.append(f"| `{task_id}` | `{repo}` | {status_badge} | {elapsed:.2f}s | ${cost:.4f} | {patch_size} B |")

    lines.extend([
        "",
        "## Methodology & Disclosure",
        f"- **Verification Engine:** Evaluated on `{engine}` sandbox engine with deterministic synthetic reproduction oracles to validate concurrency, state isolation, and $/1M token accounting without cloud GPU overhead.",
        "- **Parallel Exploration:** Fast tier branches (Nemotron-3.5-Lightning) race simultaneously with diversified hypothesis prompts.",
        "- **Checkpoint Isolation:** Checkpoint C1 verifies reproduction script failure prior to branching.",
        "- **Oracle Rigor:** Passing candidate patches undergo dual-pass verification to eliminate non-deterministic false positives.",
        "- **Cost Accounting:** Direct token expenditure tracked via $/1M token pricing matrix.",
    ])

    report_md = "\n".join(lines) + "\n"
    target_out = output_path or (RESULTS_DIR / "BENCHMARK_REPORT.md")
    with open(target_out, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Report written to {target_out}")
    return report_md


if __name__ == "__main__":
    generate_markdown_report()
