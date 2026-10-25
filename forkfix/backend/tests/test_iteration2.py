"""Unit tests for Iteration 2: Adaptive temperature, AST error parser, patch scorer, and analytics."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from forkfix.backend.prompt_engine import AdaptiveTemperatureScheduler, PromptEngine
from forkfix.backend.ast_parser import ASTErrorExtractor
from forkfix.backend.patch_scorer import PatchScorer
from forkfix.backend.analytics import EconomicsAnalytics


def test_adaptive_temperature():
    # Early steps: low temperature for deterministic syntax checks
    t0 = AdaptiveTemperatureScheduler.get_temperature(step_idx=0, tier="fast")
    assert t0 == 0.2

    # Mid steps: balanced creative code edit
    t5 = AdaptiveTemperatureScheduler.get_temperature(step_idx=5, tier="fast")
    assert t5 == 0.6

    # Late steps: divergent fallback search
    t18 = AdaptiveTemperatureScheduler.get_temperature(step_idx=18, tier="fast")
    assert t18 == 0.85

    # Ultra tier uses disciplined 0.4
    tu = AdaptiveTemperatureScheduler.get_temperature(step_idx=2, tier="ultra")
    assert tu == 0.4


def test_ast_error_extractor():
    # Test syntax error parsing
    syntax_stderr = (
        '  File "/testbed/django/utils/formats.py", line 142\n'
        '    def sanitize_separators(value)\n'
        '                                  ^\n'
        'SyntaxError: expected \':\'\n'
    )
    parsed = ASTErrorExtractor.parse_stderr(syntax_stderr)
    assert parsed["has_errors"] is True
    assert parsed["file"] == "/testbed/django/utils/formats.py"
    assert parsed["line"] == 142
    assert parsed["error_type"] == "SyntaxError"
    assert parsed["is_syntax"] is True

    # Test runtime assertion error
    assertion_stderr = "AssertionError: expected sanitized numeric string, got raw symbol\n"
    parsed_assert = ASTErrorExtractor.parse_stderr(assertion_stderr)
    assert parsed_assert["has_errors"] is True
    assert parsed_assert["error_type"] == "AssertionError"


def test_patch_scorer():
    # Surgical 1-file patch
    clean_patch = (
        "diff --git a/django/utils/formats.py b/django/utils/formats.py\n"
        "--- a/django/utils/formats.py\n"
        "+++ b/django/utils/formats.py\n"
        "@@ -142,2 +142,3 @@ def sanitize_separators(value):\n"
        "+    value = re.sub(r'^[\\$\\€]', '', str(value))\n"
    )
    clean_eval = PatchScorer.evaluate_patch(clean_patch)
    assert clean_eval["is_valid"] is True
    assert clean_eval["file_count"] == 1
    assert clean_eval["score"] >= 0.9

    # Dirty patch with debug keyword
    dirty_patch = (
        "diff --git a/django/utils/formats.py b/django/utils/formats.py\n"
        "--- a/django/utils/formats.py\n"
        "+++ b/django/utils/formats.py\n"
        "+    print('DEBUGGING FORMATS')\n"
    )
    dirty_eval = PatchScorer.evaluate_patch(dirty_patch)
    assert dirty_eval["score"] < clean_eval["score"]


def test_economics_analytics():
    roi = EconomicsAnalytics.calculate_roi(actual_cost=0.0384, actual_seconds=15.8)
    assert roi["actual_cost"] == 0.0384
    devin_comp = roi["comparisons"]["devin"]
    assert devin_comp["multiplier"] > 50  # Over 50x cheaper than Devin
    ultra_comp = roi["comparisons"]["nemotron_ultra_monolith"]
    assert ultra_comp["multiplier"] > 10  # Over 10x cheaper than pure Ultra
    assert roi["annual_savings_1000_issues"] > 400.0
