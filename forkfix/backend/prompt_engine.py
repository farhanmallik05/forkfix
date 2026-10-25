"""Prompt synthesis and adaptive temperature scheduling for Nemotron model tiers."""

from __future__ import annotations
from typing import Any


class AdaptiveTemperatureScheduler:
    @staticmethod
    def get_temperature(step_idx: int, tier: str) -> float:
        """Calculates adaptive sampling temperature based on step progress and model tier."""
        if tier == "ultra":
            # Ultra reasoning benefits from a controlled, disciplined temperature
            return 0.4

        # Fast and Super tiers adapt across iteration depth
        if step_idx <= 2:
            # Deterministic exploration (grep, file reading, exact localization)
            return 0.2
        elif step_idx <= 12:
            # Creative patch synthesis
            return 0.6
        else:
            # Broad divergent search when early attempts have stalled
            return 0.85

    @staticmethod
    def anneal_temperature(base_temp: float, failure_count: int, is_syntax_error: bool = False) -> float:
        """Dynamically anneals temperature based on error type and consecutive retry count."""
        if is_syntax_error:
            # Enforce deterministic token output on invalid code syntax
            return 0.15

        if failure_count == 0:
            return round(base_temp, 2)
        elif failure_count in (1, 2):
            return 0.50
        else:
            # Broaden search space if stuck in a dead-end
            return 0.75


class PromptEngine:
    @staticmethod
    def build_step_prompt(
        issue_text: str,
        recent_commands: list[dict[str, Any]],
        ast_diagnostics: dict[str, Any] | None = None,
        hint: str = "",
    ) -> list[dict[str, str]]:
        """Constructs an AST-aware context prompt for Nemotron code generation."""
        context_parts = [f"Issue Description:\n{issue_text}"]

        if hint:
            context_parts.append(f"Expert Hint / Direction:\n{hint}")

        if ast_diagnostics and ast_diagnostics.get("has_errors"):
            context_parts.append(
                f"Static / AST Diagnostic Alert:\n"
                f"- File: {ast_diagnostics.get('file')}\n"
                f"- Line: {ast_diagnostics.get('line')}\n"
                f"- Error: {ast_diagnostics.get('error_type')}: {ast_diagnostics.get('message')}\n"
                "Fix this precise location first before running full test suites."
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a principal software engineer fixing a bug.\n"
                    "Each turn reply with exactly one ```bash block containing shell commands.\n"
                    "Keep edits minimal and targeted. When tests pass cleanly, reply with only: DONE"
                ),
            },
            {"role": "user", "content": "\n\n".join(context_parts)},
        ]

        for entry in recent_commands[-4:]:
            messages.append({"role": "assistant", "content": f"```bash\n{entry.get('cmd', '')}\n```"})
            messages.append({"role": "user", "content": entry.get("out", "")})

        return messages

    @staticmethod
    def build_4way_hypothesis_prompts(
        issue_text: str,
        traceback_info: dict[str, Any] | None = None,
        tavily_citations: str = "",
    ) -> list[dict[str, str]]:
        """Generates 4 distinct hypothesis prompts for parallel reality branching.
        
        Branches:
        1. Boundary & Off-by-one Edge Cases
        2. Type Coercion & Null Safety Guards
        3. Upstream API Drift & Deprecated Method Adaptation
        4. Exception Hierarchy & Error Propagation Handling
        """
        strategies = [
            ("Branch-Alpha", "Focus on boundary conditions, empty collections, slice bounds, and off-by-one logic."),
            ("Branch-Beta", "Focus on strict type verification, NoneType guards, and defensive cast checks."),
            ("Branch-Gamma", "Focus on library version drift, renamed parameters, or signature compatibility."),
            ("Branch-Delta", "Focus on exception swallowing, missing re-raise statements, and error fallback handlers."),
        ]

        prompts = []
        err_msg = ""
        if traceback_info and traceback_info.get("has_errors"):
            err_msg = f"\nFailing Location: {traceback_info.get('file')}:{traceback_info.get('line')} ({traceback_info.get('error_type')}: {traceback_info.get('message')})"

        for branch_name, strategy in strategies:
            prompt_content = (
                f"### Task: Bug Resolution via Parallel Reality Branching\n"
                f"**Branch Identity:** `{branch_name}`\n"
                f"**Branch Mandate:** {strategy}\n\n"
                f"**Issue Description:**\n{issue_text}\n"
                f"{err_msg}\n\n"
            )
            if tavily_citations:
                prompt_content += f"**Verified Documentation Evidence:**\n{tavily_citations}\n\n"

            prompt_content += "Synthesize a minimal, robust patch following strictly your assigned branch mandate."
            prompts.append({
                "branch_name": branch_name,
                "strategy": strategy,
                "prompt": prompt_content,
            })

        return prompts
