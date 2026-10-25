"""Unit tests for Sprint Iteration 2:
Multi-Perspective Tavily Grounding, Traceback Slicing, Annealed Temperature, and 4-Way Hypothesis Prompts.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forkfix.backend.tavily_service import TavilyService, DEFAULT_EXCLUSIONS
from forkfix.backend.ast_parser import ASTErrorExtractor
from forkfix.backend.prompt_engine import AdaptiveTemperatureScheduler, PromptEngine


def test_tavily_anti_leakage_expanded_exclusions():
    assert "swebench.com" in DEFAULT_EXCLUSIONS
    assert "github.com" in DEFAULT_EXCLUSIONS
    assert "gitlab.com" in DEFAULT_EXCLUSIONS
    assert any("SWE-bench" in x for x in DEFAULT_EXCLUSIONS)


def test_format_markdown_citations():
    mock_results = {
        "citations": [
            {
                "title": "Python Math Module",
                "url": "https://docs.python.org/3/library/math.html",
                "score": 0.95,
                "content": "math.isclose provides tolerance-based floating point comparisons.",
            }
        ]
    }
    formatted = TavilyService.format_markdown_citations(mock_results)
    assert "[Python Math Module](https://docs.python.org/3/library/math.html)" in formatted
    assert "[Relevance: 95%]" in formatted
    assert "math.isclose" in formatted


def test_traceback_slicing_library_isolation():
    stderr_sample = (
        'Traceback (most recent call last):\n'
        '  File "/usr/lib/python3.12/site-packages/pytest/runner.py", line 120, in runtest\n'
        '    execute_call()\n'
        '  File "/testbed/app/calculator.py", line 45, in compute\n'
        '    return a / b\n'
        'ZeroDivisionError: division by zero'
    )
    frames = ASTErrorExtractor.slice_traceback(stderr_sample)
    assert len(frames) == 2

    # First frame is library code
    assert frames[0]["is_library"] is True
    assert "site-packages" in frames[0]["file"]

    # Second frame is application code
    assert frames[1]["is_library"] is False
    assert frames[1]["file"] == "/testbed/app/calculator.py"
    assert frames[1]["line"] == 45
    assert frames[1]["error_type"] == "ZeroDivisionError"


def test_adaptive_temperature_annealing():
    scheduler = AdaptiveTemperatureScheduler()

    # Syntax error forces strict determinism (0.15)
    t_syntax = scheduler.anneal_temperature(base_temp=0.7, failure_count=3, is_syntax_error=True)
    assert t_syntax == 0.15

    # First attempt: base temperature preserved
    t_initial = scheduler.anneal_temperature(base_temp=0.4, failure_count=0)
    assert t_initial == 0.40

    # Mild retries (1-2 failures): moderate temperature
    t_retry = scheduler.anneal_temperature(base_temp=0.2, failure_count=1)
    assert t_retry == 0.50

    # Deep deadlock (>=3 failures): creative divergent exploration (0.75)
    t_divergent = scheduler.anneal_temperature(base_temp=0.2, failure_count=4)
    assert t_divergent == 0.75


def test_4way_hypothesis_prompt_generation():
    issue = "Fix ZeroDivisionError in compute function when denominator is 0"
    traceback_info = {
        "has_errors": True,
        "file": "/testbed/app/calculator.py",
        "line": 45,
        "error_type": "ZeroDivisionError",
        "message": "division by zero",
    }
    citations = "- [Python Math](https://docs.python.org/3/): handle division by zero with guard."

    prompts = PromptEngine.build_4way_hypothesis_prompts(
        issue_text=issue,
        traceback_info=traceback_info,
        tavily_citations=citations,
    )

    assert len(prompts) == 4
    branch_names = [p["branch_name"] for p in prompts]
    assert branch_names == ["Branch-Alpha", "Branch-Beta", "Branch-Gamma", "Branch-Delta"]

    # Verify distinct mandates
    assert any("boundary" in p["strategy"].lower() for p in prompts)
    assert any("type" in p["strategy"].lower() for p in prompts)
    assert any("drift" in p["strategy"].lower() for p in prompts)
    assert any("exception" in p["strategy"].lower() for p in prompts)

    # Verify context inclusion
    for p in prompts:
        assert "ZeroDivisionError" in p["prompt"]
        assert "calculator.py:45" in p["prompt"]
        assert "Verified Documentation Evidence" in p["prompt"]
