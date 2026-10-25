"""Automated test suite for Forkfix backend."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from forkfix.backend.sandbox import MockSandboxEngine, get_sandbox_engine
from forkfix.backend.nemotron import NemotronClient, TIER_CONFIG
from forkfix.backend.events import EventEmitter, CheckpointCreatedEvent
from forkfix.backend.orchestrator import ForkfixOrchestrator
from forkfix.backend.tavily_service import TavilyService


@pytest.mark.asyncio
async def test_mock_sandbox_execution():
    engine = MockSandboxEngine()
    session = await engine.use("mock-swe-base")
    assert session.uuid == "mock-swe-base"

    # Test running a mock command
    res = await session.run(shell="echo hello", disposable=False)
    assert res.exit_code == 0
    assert "mock-snap-1" in session.uuid

    # Test git diff
    diff_res = await session.run(shell="git diff", disposable=True)
    assert diff_res.exit_code == 0


@pytest.mark.asyncio
async def test_nemotron_client_pricing():
    client = NemotronClient()  # Uses mock response if no key
    content, cost, usage = await client.ask("fast", [{"role": "user", "content": "Test prompt"}])
    assert content != ""
    assert cost >= 0.0
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage

    # Verify pricing formula
    p_in, p_out = TIER_CONFIG["fast"][1], TIER_CONFIG["fast"][2]
    expected_cost = (usage["prompt_tokens"] * p_in + usage["completion_tokens"] * p_out) / 1_000_000.0
    assert pytest.approx(cost, 1e-6) == expected_cost


@pytest.mark.asyncio
async def test_event_emitter(tmp_path):
    emitter = EventEmitter(run_id="test-run-123", log_dir=str(tmp_path))
    q = emitter.subscribe()

    event = CheckpointCreatedEvent(
        run_id="test-run-123",
        checkpoint_id="C1",
        image_uuid="img-snap-test",
        repro_script="print('test')",
        repro_stderr="AssertionError",
    )
    await emitter.emit(event)

    received = await asyncio.wait_for(q.get(), timeout=2.0)
    assert received["event_type"] == "checkpoint_created"
    assert received["checkpoint_id"] == "C1"
    assert emitter.log_path.exists()


@pytest.mark.asyncio
async def test_tavily_mock_service():
    tavily = TavilyService()
    hits, extracted = await tavily.search_and_extract("AssertionError currency separator")
    assert len(hits) > 0
    assert "url" in hits[0]
    assert len(extracted) > 0


@pytest.mark.asyncio
async def test_orchestrator_end_to_end(tmp_path):
    engine = MockSandboxEngine()
    # Configure mock engine to pass on winning patch
    engine.snapshots["mock-swe-base"].git_diff = "diff --git a/test.py b/test.py\n+fixed"
    engine.snapshots["mock-swe-base"].repro_passes = True

    nemotron = NemotronClient()
    tavily = TavilyService()
    emitter = EventEmitter(run_id="test-orchestration", log_dir=str(tmp_path))

    orchestrator = ForkfixOrchestrator(engine=engine, nemotron=nemotron, tavily=tavily)
    result = await orchestrator.execute_fix(
        base_image_uuid="mock-swe-base",
        issue_text="Django currency formatting bug",
        emitter=emitter,
    )

    assert result["status"] == "resolved"
    assert result["winner"] is not None
    assert result["cost"] > 0
