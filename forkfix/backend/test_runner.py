"""Multi-framework test execution and failure discovery for Forkfix sandboxes."""

from __future__ import annotations
import re
from typing import Any
from .sandbox import ExecResult, SandboxSession


class TestRunner:
    @staticmethod
    def detect_test_command(repo_dir: str, target_file: str = "") -> str:
        """Determines optimal test execution command based on repository conventions."""
        if target_file and target_file.endswith(".py"):
            return f"PYTHONPATH=. pytest -q {target_file}"
        return "PYTHONPATH=. pytest -q"

    @staticmethod
    async def run_verification(
        session: SandboxSession,
        repro_cmd: str = "PYTHONPATH=. python /tmp/repro.py",
        cwd: str = "/testbed",
        timeout: int = 180,
    ) -> tuple[bool, str, int]:
        """Executes verification command in a disposable session run.

        Returns:
            (passes: bool, output: str, exit_code: int)
        """
        res: ExecResult = await session.run(
            shell=repro_cmd,
            cwd=cwd,
            disposable=True,
            timeout=timeout,
        )
        output = (res.stdout or "") + (res.stderr or "")
        passes = res.exit_code == 0 and "AssertionError" not in output and "FAILED" not in output
        return passes, output, res.exit_code
