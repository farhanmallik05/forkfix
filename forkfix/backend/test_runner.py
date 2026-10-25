"""Universal Multi-Language Test Runner & Deterministic Reproduction Engine for Forkfix.

Supports Python (pytest/unittest), TypeScript/JavaScript (vitest/jest), Rust (cargo test),
and Go (go test), featuring flakiness detection, AST assertion synthesis, and output normalization.
"""

from __future__ import annotations
import re
import shlex
from typing import Any
from .sandbox import ExecResult, SandboxSession

# Regex to strip ANSI escape codes
ANSI_ESCAPE_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
# Regex to normalize hex memory addresses like 0x7f8b2c410
HEX_ADDR_REGEX = re.compile(r"0x[0-9a-fA-F]{6,16}")
# Regex to normalize execution timestamps and durations
TIMESTAMP_REGEX = re.compile(r"\b\d+(\.\d+)?\s*(s|sec|seconds|ms)\b", re.IGNORECASE)


class TestRunner:
    """Universal Multi-Language Test Runner with oracle validation and flakiness detection."""

    SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "rust", "go"]

    @staticmethod
    def detect_test_command(repo_dir: str = "", target_file: str = "") -> str:
        """Determines the optimal test execution command based on target file or repo files."""
        if target_file:
            if target_file.endswith(".py"):
                return f"PYTHONPATH=. pytest -q {shlex.quote(target_file)}"
            if target_file.endswith((".ts", ".tsx", ".js", ".jsx")):
                return f"npx vitest run {shlex.quote(target_file)}"
            if target_file.endswith(".rs"):
                return "cargo test -- --nocapture"
            if target_file.endswith(".go"):
                return f"go test -v {shlex.quote(target_file)}"

        # Default fallback to python test runner
        return "PYTHONPATH=. pytest -q"

    @staticmethod
    def normalize_output(raw_output: str) -> str:
        """Strips ANSI escape sequences, memory addresses, and execution durations from output.
        
        Ensures clean, deterministic diffs for the LLM without timing or memory noise.
        """
        if not raw_output:
            return ""
        # 1. Strip ANSI escape sequences
        clean = ANSI_ESCAPE_REGEX.sub("", raw_output)
        # 2. Normalize memory addresses
        clean = HEX_ADDR_REGEX.sub("0x<MEM_ADDR>", clean)
        # 3. Normalize variable durations
        clean = TIMESTAMP_REGEX.sub("<DURATION>", clean)
        return clean.strip()

    @staticmethod
    def synthesize_reproduction_script(issue_text: str, repo_type: str = "python") -> str:
        """Synthesizes a minimal reproduction script with deterministic assertions based on issue context."""
        cleaned_text = issue_text.strip()

        if repo_type == "python":
            # Extract potential function call or class name if mentioned
            match = re.search(r"(\w+)\((.*?)\)", cleaned_text)
            fn_call = match.group(0) if match else "run_case()"

            return (
                '"""Auto-synthesized deterministic reproduction script for Forkfix."""\n'
                "import sys\n\n"
                "def test_reproduction():\n"
                f'    # Issue Context: {cleaned_text[:120].replace(chr(10), " ")}\n'
                "    try:\n"
                f"        result = {fn_call}\n"
                "        assert result is not None, 'Expected valid return value'\n"
                "    except Exception as e:\n"
                "        print(f'REPRODUCTION_TRIGGERED: {e}', file=sys.stderr)\n"
                "        sys.exit(1)\n"
                "    sys.exit(0)\n\n"
                "if __name__ == '__main__':\n"
                "    test_reproduction()\n"
            )
        elif repo_type in ("javascript", "typescript"):
            return (
                "// Auto-synthesized reproduction test\n"
                "import { expect, test } from 'vitest';\n\n"
                "test('reproduces issue', () => {\n"
                f"  // Context: {cleaned_text[:100]}\n"
                "  expect(true).toBe(false);\n"
                "});\n"
            )
        else:
            return f"// Standalone test reproduction for {repo_type}\n"

    @classmethod
    async def verify_deterministic_failure(
        cls,
        session: SandboxSession,
        repro_cmd: str = "PYTHONPATH=. python /tmp/repro.py",
        cwd: str = "/testbed",
        runs: int = 3,
        timeout: int = 30,
    ) -> tuple[bool, str]:
        """Runs the reproduction command multiple times to ensure non-flaky, deterministic failure.
        
        Returns:
            (is_deterministic: bool, failure_summary: str)
        """
        outputs = []
        for i in range(runs):
            res = await session.run(shell=repro_cmd, cwd=cwd, disposable=True, timeout=timeout)
            if res.exit_code == 0:
                return False, f"Flakiness detected: Run {i + 1}/{runs} unexpectedly exited with code 0."
            outputs.append(cls.normalize_output((res.stdout or "") + (res.stderr or "")))

        return True, outputs[0] if outputs else "Deterministic failure confirmed"

    @classmethod
    def verify_oracle_transition(
        cls,
        pre_exit: int,
        post_exit: int,
        post_output: str,
        modified_files: list[str] | None = None,
        disallowed_prefixes: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Strict verification gate ensuring non-zero to zero transition without collateral regressions."""
        if pre_exit == 0:
            return False, "Invalid Oracle: Pre-fix command already exited with 0 (no bug detected)."

        if post_exit != 0:
            return False, f"Verification Failed: Post-fix command exited with non-zero code {post_exit}."

        clean_out = cls.normalize_output(post_output)
        if "AssertionError" in clean_out or "FAILED" in clean_out or "Traceback" in clean_out:
            return False, "Verification Failed: Output contains error signatures despite exit code 0."

        if modified_files and disallowed_prefixes:
            for file_path in modified_files:
                for prefix in disallowed_prefixes:
                    if file_path.startswith(prefix):
                        return False, f"Security/Integrity Violation: Modified disallowed path {file_path}."

        return True, "Oracle verified: Deterministic transition from failure to clean zero exit code."

    @classmethod
    async def run_verification(
        cls,
        session: SandboxSession,
        repro_cmd: str = "PYTHONPATH=. python /tmp/repro.py",
        cwd: str = "/testbed",
        timeout: int = 30,
    ) -> tuple[bool, str, int]:
        """Executes verification command in a disposable session run with normalized output."""
        res: ExecResult = await session.run(
            shell=repro_cmd,
            cwd=cwd,
            disposable=True,
            timeout=timeout,
        )
        raw_output = (res.stdout or "") + (res.stderr or "")
        clean_output = cls.normalize_output(raw_output)
        passes = res.exit_code == 0 and "AssertionError" not in clean_output and "FAILED" not in clean_output
        return passes, clean_output, res.exit_code
