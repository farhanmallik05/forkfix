"""AST and traceback diagnostic parser for Python testbed executions."""

from __future__ import annotations
import re
from typing import Any

TRACEBACK_PATTERN = re.compile(
    r'File\s+"(?P<file>[^"]+)",\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<func>\w+))?\n(?:\s+.*?\n)?(?P<error_type>[A-Za-z]+Error|AssertionError|Exception):\s*(?P<msg>.*)',
    re.MULTILINE,
)

SYNTAX_ERROR_PATTERN = re.compile(
    r'File\s+"(?P<file>[^"]+)",\s+line\s+(?P<line>\d+)(?:[\s\S]*?)(?P<error_type>SyntaxError|IndentationError|TabError):\s*(?P<msg>.*)'
)


class ASTErrorExtractor:
    @staticmethod
    def parse_stderr(stderr: str) -> dict[str, Any]:
        """Extracts file, line number, and error message from Python stderr."""
        if not stderr or not stderr.strip():
            return {"has_errors": False}

        # Check for syntax/indentation errors first
        syntax_match = SYNTAX_ERROR_PATTERN.search(stderr)
        if syntax_match:
            return {
                "has_errors": True,
                "file": syntax_match.group("file"),
                "line": int(syntax_match.group("line")),
                "error_type": syntax_match.group("error_type"),
                "message": syntax_match.group("msg").strip(),
                "is_syntax": True,
            }

        # Check for runtime/assertion errors
        tb_matches = list(TRACEBACK_PATTERN.finditer(stderr))
        if tb_matches:
            last_match = tb_matches[-1]
            return {
                "has_errors": True,
                "file": last_match.group("file"),
                "line": int(last_match.group("line")),
                "function": last_match.group("func") or "global",
                "error_type": last_match.group("error_type"),
                "message": last_match.group("msg").strip(),
                "is_syntax": False,
            }

        if "AssertionError" in stderr:
            return {
                "has_errors": True,
                "error_type": "AssertionError",
                "message": stderr.split("AssertionError:")[-1].strip().split("\n")[0],
                "file": "unknown",
                "line": 0,
                "is_syntax": False,
            }

        return {"has_errors": False}
