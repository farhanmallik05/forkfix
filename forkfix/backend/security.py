"""Security guardrails, command sanitizer, and sensitive data redaction for Forkfix."""

from __future__ import annotations
import re

# Blocklist of high-risk patterns that indicate host breakout or unrecoverable destruction
DANGEROUS_PATTERNS = [
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+(/|/\*|/etc|/boot|/root)(\s+|$)",
    r"\brm\s+(-rf?|-fr?)\s+(/|/\*|/etc|/boot|/root)(\s+|$)",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",  # Fork bomb
    r"\bmkfs(\.[a-z0-9]+)?\b",
    r"\bdd\s+if=.*?of=(/dev/[a-z]+)\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\binit\s+0\b",
    r"\bchmod\s+-R\s+777\s+/\b",
    r">\s*/dev/sd[a-z]\b",
]

SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{12,})['\"]?"), r"\1: [REDACTED]"),
    (re.compile(r"tvly-[a-zA-Z0-9_-]{20,}"), "[REDACTED_TAVILY_KEY]"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}"), "Bearer [REDACTED_TOKEN]"),
]


class CommandSanitizer:
    @staticmethod
    def inspect_command(command: str) -> tuple[bool, str]:
        """Validates command against destructive breakout patterns.

        Returns:
            (is_safe, error_message_if_unsafe)
        """
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return False, f"Command rejected by security guardrail: Matched restricted pattern '{pattern}'"
        return True, ""

    @staticmethod
    def sanitize_logs(text: str) -> str:
        """Redacts sensitive credentials and tokens from output strings."""
        sanitized = text
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized
