"""Unit tests for Iteration 1: Database persistence, security guardrails, and rate limiting."""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from forkfix.backend.database import Database
from forkfix.backend.security import CommandSanitizer
from forkfix.backend.auth import RateLimiter


def test_database_crud(tmp_path):
    db_file = tmp_path / "test_forkfix.db"
    db = Database(str(db_file))

    # 1. Create run
    run = db.create_run("run-test-01", "Fix currency formatting in django")
    assert run["run_id"] == "run-test-01"
    assert run["status"] == "running"

    # 2. Record branch
    db.record_branch("run-test-01", "fast-b1", "img-c1", "fast", "Nemotron-Lightning", hint="test hint")

    # 3. Record step
    db.record_step(
        "run-test-01", "fast-b1", 0, "pytest", "1 failed", 0.0005, "img-snap-01"
    )

    # 4. Record event
    db.record_event("run-test-01", "test_event", {"status": "ok"})

    # 5. Update run status
    db.update_run_status("run-test-01", "resolved", total_cost=0.035, winning_branch_id="fast-b1", winning_patch="+patch")

    # 6. Retrieve run
    fetched = db.get_run("run-test-01")
    assert fetched is not None
    assert fetched["status"] == "resolved"
    assert fetched["winning_branch_id"] == "fast-b1"
    assert len(fetched["branches"]) == 1
    assert fetched["branches"][0]["step_count"] == 1
    assert fetched["branches"][0]["cost"] == 0.0005

    # 7. List runs
    runs = db.list_runs()
    assert len(runs) == 1

    # 8. Delete run
    deleted = db.delete_run("run-test-01")
    assert deleted is True
    assert db.get_run("run-test-01") is None


def test_command_sanitizer():
    # Dangerous commands
    safe, msg = CommandSanitizer.inspect_command("rm -rf /")
    assert safe is False
    assert "security guardrail" in msg

    safe, msg = CommandSanitizer.inspect_command("rm -fr /etc")
    assert safe is False

    safe, msg = CommandSanitizer.inspect_command(":(){ :|:& };:")
    assert safe is False

    # Safe commands
    safe, msg = CommandSanitizer.inspect_command("git diff && pytest /testbed/tests")
    assert safe is True
    assert msg == ""

    safe, msg = CommandSanitizer.inspect_command("sed -i 's/foo/bar/g' /tmp/repro.py")
    assert safe is True


def test_secret_redaction():
    raw_log = "Error connecting with tvly-abc1234567890abcdef1234 and Bearer sk-9876543210abcdef9876"
    sanitized = CommandSanitizer.sanitize_logs(raw_log)
    assert "tvly-abc" not in sanitized
    assert "[REDACTED_TAVILY_KEY]" in sanitized
    assert "sk-9876" not in sanitized
    assert "[REDACTED_TOKEN]" in sanitized


def test_rate_limiter():
    limiter = RateLimiter(capacity=3, refill_seconds=10.0)
    assert limiter.is_allowed("192.168.1.1") is True
    assert limiter.is_allowed("192.168.1.1") is True
    assert limiter.is_allowed("192.168.1.1") is True
    # 4th request within 10s window rejected
    assert limiter.is_allowed("192.168.1.1") is False
    # Different IP allowed
    assert limiter.is_allowed("192.168.1.2") is True
