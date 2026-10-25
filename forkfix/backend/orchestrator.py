"""Core orchestration engine for Forkfix: Checkpoint C1, 4x parallel branch race, oracle verification, and Tavily+Ultra escalation."""

from __future__ import annotations
import asyncio
import os
import re
import time
from typing import Any

from .events import (
    BranchSpawnedEvent,
    CheckpointCreatedEvent,
    EscalationTriggeredEvent,
    EventEmitter,
    StepExecutedEvent,
    UnresolvedEvent,
    WinnerSelectedEvent,
)
from .nemotron import NemotronClient, TIER_CONFIG
from .sandbox import ExecResult, SandboxEngine, SandboxSession
from .tavily_service import TavilyService

REPO_DIR = os.getenv("REPO_DIR", "/testbed")
CHECK_CMD = f"PYTHONPATH=. python /tmp/repro.py"

F = "`" * 3
BASH_PATTERN = re.compile(F + r"bash\n(.*?)" + F, re.DOTALL)
PY_PATTERN = re.compile(F + r"python\n(.*?)" + F, re.DOTALL)

SYSTEM_PROMPT = (
    f"You fix a GitHub issue in the repository located at {REPO_DIR}.\n"
    f"Each turn reply with exactly one {F}bash block.\n"
    "Files persist between turns; shell variables do not. Keep scratch files in /tmp.\n"
    "Inspect, edit code, then re-run /tmp/repro.py. When the repro passes, reply with only: DONE"
)


def clip(text: str, max_chars: int = 5000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n\n[...output clipped...]\n\n" + text[-half:]


class ForkfixOrchestrator:
    def __init__(
        self,
        engine: SandboxEngine,
        nemotron: NemotronClient | None = None,
        tavily: TavilyService | None = None,
    ):
        self.engine = engine
        self.nemotron = nemotron or NemotronClient()
        self.tavily = tavily or TavilyService()

    async def prepare_checkpoint_c1(
        self,
        base_image_uuid: str,
        issue_text: str,
        emitter: EventEmitter,
    ) -> tuple[str, str]:
        """Synthesizes /tmp/repro.py, verifies it fails on base repo, and snapshots Checkpoint C1."""
        prompt = (
            "Write a standalone Python script (/tmp/repro.py) that reproduces this issue.\n"
            "The script MUST exit with a non-zero code (e.g. exit 1 or raise AssertionError) "
            "because of this bug, and exit with code 0 once the bug is properly fixed.\n"
            f"Reply with one {F}python block only.\n\n"
            f"Issue Description:\n{issue_text}"
        )

        content, cost, _ = await self.nemotron.ask("super", [{"role": "user", "content": prompt}], think=True)
        match = PY_PATTERN.search(content)
        repro_code = match.group(1).strip() if match else "import sys; sys.exit(1)"

        base_session = await self.engine.use(base_image_uuid, strict=True)
        res = await base_session.run(
            shell="true",
            files={"/tmp/repro.py": repro_code.encode("utf-8")},
            disposable=False,
            timeout=60,
        )
        c1_uuid = res.uuid or base_image_uuid

        # Verify that the repro actually fails on clean unmodified repo
        verify_session = await self.engine.use(c1_uuid, strict=True)
        pre_check = await verify_session.run(shell=CHECK_CMD, cwd=REPO_DIR, disposable=True, timeout=120)
        repro_err = (pre_check.stderr or pre_check.stdout or "Repro script failed as expected")[-400:]

        await emitter.emit(
            CheckpointCreatedEvent(
                run_id=emitter.run_id,
                checkpoint_id="C1",
                image_uuid=c1_uuid,
                repro_script=repro_code,
                repro_stderr=repro_err,
            )
        )
        return c1_uuid, repro_err

    async def run_branch(
        self,
        branch_id: str,
        start_uuid: str,
        issue_text: str,
        emitter: EventEmitter,
        tier: str = "fast",
        max_steps: int = 25,
        budget_dollars: float = 0.20,
        hint: str = "",
    ) -> dict[str, Any]:
        """Executes an isolated repair trajectory from a given snapshot UUID."""
        model_name = TIER_CONFIG[tier][0]
        await emitter.emit(
            BranchSpawnedEvent(
                run_id=emitter.run_id,
                branch_id=branch_id,
                parent_checkpoint=start_uuid,
                tier=tier,
                model=model_name,
                hint=hint,
            )
        )

        session = await self.engine.use(start_uuid, strict=True)
        current_uuid = start_uuid
        spent = 0.0
        trace: list[dict[str, Any]] = []

        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": issue_text + (f"\n\nGuidance/Hint:\n{hint}" if hint else "")},
        ]

        for step_idx in range(max_steps):
            from .prompt_engine import AdaptiveTemperatureScheduler
            temp = AdaptiveTemperatureScheduler.get_temperature(step_idx, tier)

            reply, cost, _ = await self.nemotron.ask(tier, messages, think=False, temperature=temp)
            spent += cost
            messages.append({"role": "assistant", "content": reply})

            bash_match = BASH_PATTERN.search(reply)
            if not bash_match:
                if "DONE" in reply:
                    break
                messages.append({"role": "user", "content": f"Reply with one {F}bash block, or DONE."})
                continue

            cmd = bash_match.group(1).strip()
            # Wrap execution so shell exits 0 and allows sandbox snapshot commit
            wrapped_cmd = f'({cmd}); echo "[exit=$?]"'
            step_res = await session.run(shell=wrapped_cmd, cwd=REPO_DIR, disposable=False, timeout=180)
            if step_res.uuid:
                current_uuid = step_res.uuid
                session = await self.engine.use(current_uuid, strict=True)

            obs = clip((step_res.stdout or "") + (step_res.stderr or ""))
            trace_entry = {
                "step_idx": step_idx,
                "tier": tier,
                "command": cmd,
                "output": obs,
                "cost": round(cost, 6),
                "cumulative_cost": round(spent, 6),
                "snapshot_uuid": current_uuid,
            }
            trace.append(trace_entry)

            await emitter.emit(
                StepExecutedEvent(
                    run_id=emitter.run_id,
                    branch_id=branch_id,
                    step_idx=step_idx,
                    tier=tier,
                    command=cmd,
                    output=obs,
                    cost=round(cost, 6),
                    cumulative_cost=round(spent, 6),
                    snapshot_uuid=current_uuid,
                )
            )

            # Check for Python AST/traceback errors and guide model
            from .ast_parser import ASTErrorExtractor
            diag = ASTErrorExtractor.parse_stderr(obs)
            feedback = obs
            if diag.get("has_errors") and diag.get("file") != "unknown":
                feedback += f"\n\n[Diagnostic Alert]: {diag.get('error_type')} detected in {diag.get('file')} line {diag.get('line')}: {diag.get('message')}"

            messages.append({"role": "user", "content": feedback})
            if spent >= budget_dollars:
                break

        # Capture patch
        diff_res = await session.run(shell="git diff", cwd=REPO_DIR, disposable=True, timeout=60)
        patch = diff_res.stdout or ""

        return {
            "branch_id": branch_id,
            "tier": tier,
            "image_uuid": current_uuid,
            "patch": patch,
            "cost": spent,
            "trace": trace,
        }

    async def race_parallel_branches(
        self,
        start_uuid: str,
        issue_text: str,
        branch_count: int,
        emitter: EventEmitter,
        tier: str = "fast",
        prefix: str = "b",
        hint: str = "",
    ) -> list[dict[str, Any]]:
        """Spawns N concurrent branches from start_uuid."""
        tasks = [
            self.run_branch(
                branch_id=f"{prefix}{idx+1}",
                start_uuid=start_uuid,
                issue_text=issue_text,
                emitter=emitter,
                tier=tier,
                hint=hint,
            )
            for idx in range(branch_count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]

    async def evaluate_winner(self, runs: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Verifies each branch against the repro test. Returns highest-quality passing diff."""
        from .patch_scorer import PatchScorer

        async def verify_run(run: dict[str, Any]) -> bool:
            if not run.get("patch", "").strip():
                return False
            check_session = await self.engine.use(run["image_uuid"], strict=True)
            res = await check_session.run(shell=CHECK_CMD, cwd=REPO_DIR, disposable=True, timeout=180)
            return res.exit_code == 0

        verifications = await asyncio.gather(*[verify_run(r) for r in runs])
        passing_runs = [r for r, is_ok in zip(runs, verifications) if is_ok]

        if not passing_runs:
            return None

        # Score passing patches for surgical quality and cleanliness
        for r in passing_runs:
            evaluation = PatchScorer.evaluate_patch(r["patch"])
            r["patch_quality"] = evaluation

        # Rank by score descending, then length ascending
        return max(passing_runs, key=lambda r: (r.get("patch_quality", {}).get("score", 0), -len(r["patch"])))

    async def execute_fix(
        self,
        base_image_uuid: str,
        issue_text: str,
        emitter: EventEmitter,
    ) -> dict[str, Any]:
        """Main end-to-end Forkfix workflow."""
        start_time = time.time()
        c1_uuid, repro_err = await self.prepare_checkpoint_c1(base_image_uuid, issue_text, emitter)

        # Stage 1: 4x Fast Parallel Exploration (Nemotron-3.5-Lightning)
        fast_runs = await self.race_parallel_branches(
            start_uuid=c1_uuid,
            issue_text=issue_text,
            branch_count=4,
            emitter=emitter,
            tier="fast",
            prefix="fast-b",
        )
        total_spent = sum(r["cost"] for r in fast_runs)

        best = await self.evaluate_winner(fast_runs)
        if best:
            elapsed = time.time() - start_time
            await emitter.emit(
                WinnerSelectedEvent(
                    run_id=emitter.run_id,
                    winning_branch_id=best["branch_id"],
                    patch=best["patch"],
                    patch_size_bytes=len(best["patch"]),
                    total_cost=round(total_spent, 5),
                    elapsed_seconds=round(elapsed, 2),
                )
            )
            return {"status": "resolved", "winner": best, "cost": total_spent, "elapsed": elapsed}

        # Stage 2: Tavily Ground Truth + Nemotron-3-Ultra Escalation
        citations, extracted = await self.tavily.search_and_extract(repro_err)
        traces_digest = "\n\n".join(
            f"Branch {r['branch_id']}: Last output: " + (r["trace"][-1]["output"] if r["trace"] else "none")
            for r in fast_runs
        )
        web_context = "\n\n".join(f"[{item['url']}]:\n{item['content']}" for item in citations[:3])

        ultra_prompt = (
            f"Issue:\n{issue_text}\n\n"
            f"Four fast branches failed to fix the issue. Error summary:\n{repro_err}\n\n"
            f"Recent trace steps:\n{traces_digest}\n\n"
            f"Web Documentation Evidence (via Tavily):\n{web_context}\n\n"
            "Analyze the root cause and provide the exact filenames, functions, and algorithmic adjustments required."
        )

        diagnosis, ultra_cost, _ = await self.nemotron.ask("ultra", [{"role": "user", "content": ultra_prompt}], think=True)
        total_spent += ultra_cost

        await emitter.emit(
            EscalationTriggeredEvent(
                run_id=emitter.run_id,
                reason="All 4 fast branches failed repro verification",
                tavily_queries=[repro_err[:120]],
                tavily_citations=citations,
                ultra_diagnosis=diagnosis,
            )
        )

        # Stage 3: 3x Super Targeted Remediation Branches (Nemotron-3-Super)
        super_runs = await self.race_parallel_branches(
            start_uuid=c1_uuid,
            issue_text=issue_text,
            branch_count=3,
            emitter=emitter,
            tier="super",
            prefix="super-b",
            hint=f"Root Cause Diagnosis:\n{diagnosis}",
        )
        total_spent += sum(r["cost"] for r in super_runs)
        best = await self.evaluate_winner(super_runs)

        elapsed = time.time() - start_time
        if best:
            await emitter.emit(
                WinnerSelectedEvent(
                    run_id=emitter.run_id,
                    winning_branch_id=best["branch_id"],
                    patch=best["patch"],
                    patch_size_bytes=len(best["patch"]),
                    total_cost=round(total_spent, 5),
                    elapsed_seconds=round(elapsed, 2),
                )
            )
            return {"status": "resolved", "winner": best, "cost": total_spent, "elapsed": elapsed}

        await emitter.emit(
            UnresolvedEvent(
                run_id=emitter.run_id,
                total_cost=round(total_spent, 5),
                branches_attempted=len(fast_runs) + len(super_runs),
                message="All exploration and escalation branches exhausted without clean passing patch",
            )
        )
        return {"status": "unresolved", "cost": total_spent, "elapsed": elapsed}
