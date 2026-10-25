"""Nemotron client with Token Factory endpoint integration, tiered pricing, and thinking mode."""

from __future__ import annotations
import os
import re
from typing import Any
from openai import AsyncOpenAI

# Official Nebius Token Factory pricing ($ / 1M tokens)
TIER_CONFIG: dict[str, tuple[str, float, float]] = {
    # tier_name: (model_id, input_price_per_1m, output_price_per_1m)
    "fast": ("nvidia/Nemotron-3_5-Lightning", 0.06, 0.24),
    "super": ("nvidia/nemotron-3-super-120b-a12b", 0.30, 0.90),
    "ultra": ("nvidia/Nemotron-3-Ultra-550b-a55b", 1.00, 3.00),
}

DEFAULT_BASE_URL = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")


class NemotronClient:
    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL):
        self.api_key = api_key or os.getenv("NEBIUS_API_KEY", "")
        self.client: AsyncOpenAI | None = None
        if self.api_key:
            self.client = AsyncOpenAI(
                base_url=base_url,
                api_key=self.api_key,
                max_retries=6,
            )

    async def ask(
        self,
        tier: str,
        messages: list[dict[str, str]],
        think: bool = False,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> tuple[str, float, dict[str, int]]:
        """Ask a Nemotron model tier.

        Returns:
            (content_string, cost_in_dollars, usage_dict)
        """
        if tier not in TIER_CONFIG:
            raise ValueError(f"Unknown tier '{tier}'. Expected one of {list(TIER_CONFIG.keys())}")

        model_id, p_in, p_out = TIER_CONFIG[tier]
        effective_max_tokens = max_tokens or (8192 if think else 2048)

        # Mock / fallback response if no API key is provided
        if not self.client:
            return self._mock_response(tier, messages, think)

        extra_body: dict[str, Any] = {}
        if think:
            extra_body["chat_template_kwargs"] = {"enable_thinking": True}

        try:
            response = await self.client.chat.completions.create(
                model=model_id,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=effective_max_tokens,
                extra_body=extra_body if extra_body else None,
            )
        except Exception as e:
            # If endpoint rejects chat_template_kwargs, gracefully retry without it
            if "chat_template_kwargs" in str(e) and extra_body:
                response = await self.client.chat.completions.create(
                    model=model_id,
                    messages=messages,  # type: ignore
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                )
            else:
                raise e

        content = response.choices[0].message.content or ""
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        cost = (prompt_tokens * p_in + completion_tokens * p_out) / 1_000_000.0
        return content, cost, {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

    def _mock_response(
        self, tier: str, messages: list[dict[str, str]], think: bool
    ) -> tuple[str, float, dict[str, int]]:
        model_id, p_in, p_out = TIER_CONFIG[tier]
        last_msg = messages[-1]["content"] if messages else ""

        if "standalone Python script" in last_msg or "repro.py" in last_msg:
            content = (
                "```python\n"
                "import sys\n"
                "# Standalone reproduction script for currency formatting issue\n"
                "from django.utils.formats import sanitize_separators\n"
                "val = '$12.000'\n"
                "if val == '$12.000':\n"
                "    sys.stderr.write('AssertionError: currency format expected clean separator\\n')\n"
                "    sys.exit(1)\n"
                "sys.exit(0)\n"
                "```"
            )
            prompt_tokens, completion_tokens = 120, 80
            cost = (prompt_tokens * p_in + completion_tokens * p_out) / 1_000_000.0
            return content, cost, {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

        if tier == "ultra" and think:
            content = (
                "<thinking>\nThe failure across 4 branches is caused by an unstripped dollar sign in the format validator.\n"
                "The sanitize_separators function in django/utils/formats.py does not handle custom currency symbols before casting.\n"
                "</thinking>\n"
                "Root cause: `sanitize_separators` in `django/utils/formats.py` receives currency strings before symbol stripping.\n"
                "Fix: In `django/utils/formats.py`, strip leading currency symbols or update the regex match."
            )
            prompt_tokens, completion_tokens = 450, 350
            cost = (prompt_tokens * p_in + completion_tokens * p_out) / 1_000_000.0
            return content, cost, {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

        # Iterative branch step
        content = (
            "```bash\n"
            "sed -i 's/val = \"$12.000\"/val = \"$12.00\"/g' /tmp/repro.py && python /tmp/repro.py\n"
            "```\n"
            "DONE"
        )
        prompt_tokens, completion_tokens = 90, 40
        cost = (prompt_tokens * p_in + completion_tokens * p_out) / 1_000_000.0
        return content, cost, {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}
