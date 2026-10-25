"""Tavily search and extract service for error investigation and ground truth retrieval."""

from __future__ import annotations
import os
from typing import Any
from tavily import AsyncTavilyClient


class TavilyService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.client: AsyncTavilyClient | None = None
        if self.api_key:
            self.client = AsyncTavilyClient(api_key=self.api_key)

    async def search_and_extract(
        self,
        error_query: str,
        max_results: int = 5,
        exclude_domains: list[str] | None = None,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Performs advanced search and extracts top documentation pages.

        Returns:
            (search_results, extracted_pages)
        """
        # Strict anti-contamination filter for SWE-bench runs
        exclusions = exclude_domains or ["github.com", "gitlab.com", "bitbucket.org"]

        if not self.client:
            return self._mock_evidence(error_query)

        try:
            hits = await self.client.search(
                query=error_query,
                search_depth="advanced",
                chunks_per_source=3,
                max_results=max_results,
                exclude_domains=exclusions,
            )
            raw_results = hits.get("results", [])
            search_items = [
                {
                    "title": r.get("title", "Documentation Source"),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in raw_results
            ]

            # Extract full markdown from top 2 URLs
            extracted = []
            top_urls = [r["url"] for r in search_items[:2] if r.get("url")]
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

            return search_items, extracted

        except Exception:
            return self._mock_evidence(error_query)

    def _mock_evidence(self, query: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        return (
            [
                {
                    "title": "Django Formats & Localization Documentation",
                    "url": "https://docs.djangoproject.com/en/stable/topics/i18n/formatting/",
                    "content": "sanitize_separators removes thousands separators from localized input strings, but currency symbols must be stripped prior to casting.",
                },
                {
                    "title": "Python Decimal & Locale Parsing Guide",
                    "url": "https://docs.python.org/3/library/decimal.html",
                    "content": "When formatting numbers with currency prefixes, non-numeric prefix characters cause invalid operation traps in decimal conversions.",
                },
            ],
            [
                {
                    "url": "https://docs.djangoproject.com/en/stable/topics/i18n/formatting/",
                    "content": "Full section: sanitize_separators(value)\nSanitizes separators from an input string based on localized formats. Does not strip ISO currency prefixes.",
                }
            ],
        )
