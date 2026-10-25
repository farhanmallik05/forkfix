"""Unit tests for Iteration 3: Tavily multi-stage research, query decomposition, and anti-leakage filter."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from forkfix.backend.tavily_service import TavilyService, DEFAULT_EXCLUSIONS


def test_tavily_query_decomposition():
    queries = TavilyService.generate_research_queries(
        error_signature="AssertionError: expected sanitized numeric string",
        repo_name="django/django",
    )
    assert len(queries) == 3
    assert "django/django" in queries[0]
    assert "official guide" in queries[1] or "documentation" in queries[1]
    assert "fix" in queries[2] or "workaround" in queries[2]


@pytest.mark.asyncio
async def test_tavily_multi_stage_research():
    service = TavilyService()  # Uses mock if no key
    res = await service.multi_stage_research(
        error_signature="TypeError: sanitize_separators() missing required argument",
        repo_name="django/django",
    )

    assert "queries" in res
    assert len(res["queries"]) == 3
    assert "citations" in res
    assert len(res["citations"]) > 0
    assert "extracted" in res
    assert len(res["extracted"]) > 0
    assert "excluded_domains" in res
    assert "github.com" in res["excluded_domains"]
    assert "gitlab.com" in res["excluded_domains"]


def test_anti_leakage_defaults():
    assert "github.com" in DEFAULT_EXCLUSIONS
    assert "gitlab.com" in DEFAULT_EXCLUSIONS
    assert "bitbucket.org" in DEFAULT_EXCLUSIONS
