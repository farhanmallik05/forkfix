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
