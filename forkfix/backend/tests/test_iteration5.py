"""Unit tests for Iteration 4 & Iteration 5 features:
- SWE-bench benchmark metric calculation
- PR export payload generation
- Database run summary and persistence
- Deployment and CI configuration integrity
"""

import os
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forkfix.backend.database import Database
from forkfix.eval.run_benchmark import run_benchmark_suite, BENCHMARK_TASKS


@pytest.mark.asyncio
async def test_benchmark_suite_aggregation(tmp_path):
    """Test that SWE-bench benchmark suite runs mock tasks and aggregates metrics correctly."""
    summary = await run_benchmark_suite(engine_type="mock")
    assert "total_tasks" in summary
    assert summary["total_tasks"] == len(BENCHMARK_TASKS)
    assert "cost_reduction_factor" in summary
    assert summary["cost_reduction_factor"] > 0
    assert "task_details" in summary
    assert len(summary["task_details"]) == len(BENCHMARK_TASKS)


def test_database_persistence_and_retrieval(tmp_path):
    """Test full cycle of run saving, event logging, and run querying."""
    db_file = tmp_path / "test_forkfix.db"
    db = Database(db_path=str(db_file))

    run_id = "test-run-iter5"
    db.create_run(
        run_id=run_id,
        issue_text="Test issue description",
        base_image_uuid="mock-swe-base",
    )

    db.log_event(
        run_id=run_id,
        event_type="branch_forked",
        payload={"branch_id": "B1", "parent_id": "C1", "depth": 1},
    )

    db.update_run_status(
        run_id=run_id,
        status="resolved",
        total_cost=0.0345,
        elapsed_seconds=22.4,
        winning_branch_id="B1",
        winning_patch="diff --git a/file.py b/file.py\n+fixed",
    )

    run = db.get_run(run_id)
    assert run is not None
    assert run["status"] == "resolved"
    assert run["total_cost"] == 0.0345
    assert run["winning_branch_id"] == "B1"

    events = db.get_run_events(run_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "branch_forked"


def test_database_reconcile_interrupted_runs(tmp_path):
    """Test that interrupted runs left in running/started states are safely transitioned."""
    db_file = tmp_path / "test_reconcile.db"
    db = Database(db_path=str(db_file))

    db.create_run(run_id="run-interrupted-1", issue_text="Issue 1")
    db.create_run(run_id="run-interrupted-2", issue_text="Issue 2")
    db.update_run_status("run-interrupted-2", status="resolved")

    reconciled = db.reconcile_interrupted_runs()
    assert reconciled == 1

    run1 = db.get_run("run-interrupted-1")
    assert run1 is not None
    assert run1["status"] == "interrupted"

    run2 = db.get_run("run-interrupted-2")
    assert run2 is not None
    assert run2["status"] == "resolved"


def test_ci_and_deployment_files_exist():
    """Verify that CI workflow, Dockerfiles, and compose configurations are present."""
    root = PROJECT_ROOT
    ci_file = root / ".github" / "workflows" / "ci.yml"
    assert ci_file.exists(), "GitHub Actions CI workflow missing"

    compose_file = root / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml missing"

    backend_dockerfile = root / "forkfix" / "backend" / "Dockerfile"
    assert backend_dockerfile.exists(), "backend Dockerfile missing"

    frontend_dockerfile = root / "forkfix" / "frontend" / "Dockerfile"
    assert frontend_dockerfile.exists(), "frontend Dockerfile missing"

    vercel_config = root / "forkfix" / "frontend" / "vercel.json"
    assert vercel_config.exists(), "vercel.json missing"
