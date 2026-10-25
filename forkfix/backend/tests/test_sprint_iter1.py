"""Unit tests for Sprint Iteration 1:
Universal Multi-Language Testbed, Flakiness Detection, Output Normalization, and Oracle Verification.
"""

import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forkfix.backend.test_runner import TestRunner
from forkfix.backend.sandbox import MockSandboxEngine, ExecResult


def test_multi_language_test_detection():
    # Python
    cmd_py = TestRunner.detect_test_command(target_file="tests/test_currency.py")
    assert "pytest" in cmd_py

    # TypeScript
    cmd_ts = TestRunner.detect_test_command(target_file="src/index.test.ts")
    assert "vitest" in cmd_ts

    # Rust
    cmd_rs = TestRunner.detect_test_command(target_file="tests/integration.rs")
    assert "cargo test" in cmd_rs

    # Go
    cmd_go = TestRunner.detect_test_command(target_file="pkg/parser_test.go")
    assert "go test" in cmd_go


def test_output_normalization():
    # ANSI color codes + memory addresses + timestamps
    noisy_output = (
        "\x1b[31mFAILED\x1b[0m test_calc at object at 0x7f8b2c410 in 2.34s\n"
        "AssertionError: Expected 42 but got 0 (took 150ms)"
    )
    normalized = TestRunner.normalize_output(noisy_output)

    assert "\x1b[31m" not in normalized
    assert "0x<MEM_ADDR>" in normalized
    assert "<DURATION>" in normalized
    assert "FAILED" in normalized


def test_reproduction_script_synthesis():
    issue = "Calling calculate_tax(100, 0.2) returns None instead of 20.0"
    script = TestRunner.synthesize_reproduction_script(issue, repo_type="python")

    assert "def test_reproduction():" in script
    assert "calculate_tax" in script
    assert "assert result is not None" in script
    assert "sys.exit(1)" in script


def test_oracle_transition_enforcement():
    # Valid transition: non-zero to zero
    ok, msg = TestRunner.verify_oracle_transition(
        pre_exit=1,
        post_exit=0,
        post_output="All 1 tests passed in 0.05s",
        modified_files=["app/calculator.py"],
    )
    assert ok is True

    # Invalid: pre-fix was already passing
    ok2, msg2 = TestRunner.verify_oracle_transition(
        pre_exit=0,
        post_exit=0,
        post_output="passed",
    )
    assert ok2 is False
    assert "Pre-fix command already exited with 0" in msg2

    # Invalid: post-fix still fails
    ok3, msg3 = TestRunner.verify_oracle_transition(
        pre_exit=1,
        post_exit=2,
        post_output="SyntaxError: invalid syntax",
    )
    assert ok3 is False

    # Invalid: post-fix touched disallowed security file
    ok4, msg4 = TestRunner.verify_oracle_transition(
        pre_exit=1,
        post_exit=0,
        post_output="clean",
        modified_files=["/etc/passwd", "src/code.py"],
        disallowed_prefixes=["/etc", ".github/workflows"],
    )
    assert ok4 is False
    assert "Security/Integrity Violation" in msg4


@pytest.mark.asyncio
async def test_flakiness_detector_deterministic_failure():
    engine = MockSandboxEngine()
    session = await engine.use("mock-base")

    # In MockSandboxEngine, default exec returns exit_code=1 for /tmp/repro.py before patch
    deterministic, summary = await TestRunner.verify_deterministic_failure(
        session=session,
        repro_cmd="python /tmp/repro.py",
        runs=3,
    )
    assert deterministic is True
    assert "AssertionError" in summary or "deterministic" in summary.lower() or len(summary) > 0
