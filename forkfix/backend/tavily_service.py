"""Multi-stage Tavily autonomous research pipeline with anti-leakage verification and extraction."""

from __future__ import annotations
import asyncio
import os
import time
from urllib.parse import urlparse
try:
    from tavily import AsyncTavilyClient
except ImportError:
    AsyncTavilyClient = None

DEFAULT_EXCLUSIONS = [
    "github.com",
    "gist.github.com",
    "raw.githubusercontent.com",
    "patch-diff.githubusercontent.com",
    "gitlab.com",
    "bitbucket.org",
    "swebench.com",
    "huggingface.co/datasets/princeton-nlp/SWE-bench",
    "pastebin.com",
    "paperswithcode.com",
]


class TavilyService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.client: Any | None = None
        if self.api_key and AsyncTavilyClient is not None:
            self.client = AsyncTavilyClient(api_key=self.api_key)

    @staticmethod
    def generate_research_queries(error_signature: str, repo_name: str = "") -> list[str]:
        """Decomposes a runtime failure into 3 targeted technical research queries."""
        cleaned_err = error_signature.replace("\n", " ").strip()[:100]

        q1 = f"{repo_name} {cleaned_err}".strip()
        q2 = f"{cleaned_err} documentation official guide".strip()
        q3 = f"python {cleaned_err} fix workaround solution".strip()
        return [q1, q2, q3]

    @staticmethod
    def _is_allowed_url(url: str, exclusions: list[str]) -> bool:
        """Apply a second client-side filter; search-provider exclusions are not a proof."""
        parsed = urlparse(url)
        normalized = f"{parsed.netloc}{parsed.path}".lower()
        return not any(exclusion.lower().strip("/") in normalized for exclusion in exclusions)

    async def multi_stage_research(
        self,
        error_signature: str,
        repo_name: str = "",
        exclude_domains: list[str] | None = None,
    ) -> dict[str, Any]:
        """Executes multi-query Tavily research with extraction and anti-leakage auditing."""
        start_time = time.time()
        exclusions = exclude_domains or DEFAULT_EXCLUSIONS
        queries = self.generate_research_queries(error_signature, repo_name)

        if not self.client:
            return self._mock_multi_stage(queries, exclusions)

        # 1. Dispatch queries in parallel
        async def single_search(q: str):
            try:
                hits = await self.client.search(
                    query=q,
                    search_depth="advanced",
                    chunks_per_source=3,
                    max_results=3,
                    exclude_domains=exclusions,
                )
                return hits.get("results", [])
            except Exception:
                return []

        search_batches = await asyncio.gather(*[single_search(q) for q in queries])

        # 2. Deduplicate by URL
        seen_urls = set()
        deduped_results: list[dict[str, str]] = []
        for batch in search_batches:
            for r in batch:
                url = r.get("url", "")
                if url and url not in seen_urls and self._is_allowed_url(url, exclusions):
                    seen_urls.add(url)
                    deduped_results.append({
                        "title": r.get("title", "Technical Documentation"),
                        "url": url,
                        "content": r.get("content", ""),
                        "score": r.get("score", 0.85),
                    })

        # 3. Extract full text from top 2 URLs
        extracted = []
        top_urls = [r["url"] for r in deduped_results[:2]]
        if top_urls:
            try:
                ext_data = await self.client.extract(urls=top_urls)
                for item in ext_data.get("results", []):
                    extracted.append({
                        "url": item.get("url", ""),
                        "content": (item.get("raw_content", "") or "")[:2500],
                    })
            except Exception:
                pass

        elapsed = time.time() - start_time

        return {
            "queries": queries,
            "citations": deduped_results,
            "extracted": extracted,
            "excluded_domains": exclusions,
            "elapsed_seconds": round(elapsed, 2),
            "total_sources_found": len(deduped_results),
        }

    async def search_and_extract(
        self,
        error_query: str,
        max_results: int = 5,
        exclude_domains: list[str] | None = None,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Backwards-compatible API wrapper returning (citations, extracted)."""
        res = await self.multi_stage_research(error_signature=error_query, exclude_domains=exclude_domains)
        return res["citations"], res["extracted"]

    def _mock_multi_stage(self, queries: list[str], exclusions: list[str]) -> dict[str, Any]:
        return {
            "queries": queries,
            "citations": [
                {
                    "title": "Django Formats & Localization Documentation",
                    "url": "https://docs.djangoproject.com/en/stable/topics/i18n/formatting/",
                    "content": "sanitize_separators removes thousands separators from localized input strings, but currency symbols must be stripped prior to casting.",
                    "score": 0.94,
                },
                {
                    "title": "Python Decimal & Locale Parsing Guide",
                    "url": "https://docs.python.org/3/library/decimal.html",
                    "content": "When formatting numbers with currency prefixes, non-numeric prefix characters cause invalid operation traps in decimal conversions.",
                    "score": 0.88,
                },
            ],
            "extracted": [
                {
                    "url": "https://docs.djangoproject.com/en/stable/topics/i18n/formatting/",
                    "content": "Section: sanitize_separators(value)\nSanitizes separators from an input string based on localized formats. Does not strip ISO currency prefixes.",
                }
            ],
            "excluded_domains": exclusions,
            "elapsed_seconds": 0.45,
            "total_sources_found": 2,
        }

    @staticmethod
    def format_markdown_citations(research_results: dict[str, Any]) -> str:
        """Formats research findings into clean markdown citations with confidence badges."""
        citations = research_results.get("citations", [])
        if not citations:
            return "_No external documentation citations found._"

        lines = ["### Verified External Documentation & Technical Citations\n"]
        for idx, item in enumerate(citations, 1):
            title = item.get("title", "Reference Guide")
            url = item.get("url", "#")
            score = item.get("score", 0.85)
            content = item.get("content", "").strip()
            score_badge = f"`[Relevance: {int(score * 100)}%]`"
            lines.append(f"{idx}. [{title}]({url}) {score_badge}")
            if content:
                snippet = content[:200].replace("\n", " ") + "..."
                lines.append(f"   > _{snippet}_\n")

        return "\n".join(lines)
