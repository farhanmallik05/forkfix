"""Git patch quality scoring and cleanliness verification."""

from __future__ import annotations
import re
from typing import Any


class PatchScorer:
    @staticmethod
    def evaluate_patch(patch: str) -> dict[str, Any]:
        """Calculates patch surgical precision, cleanliness, and quality score (0.0 to 1.0)."""
        if not patch or not patch.strip():
            return {
                "score": 0.0,
                "is_valid": False,
                "file_count": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "reason": "Empty patch",
            }

        files_modified = re.findall(r"^diff --git a/(.*?) b/", patch, re.MULTILINE)
        file_count = len(files_modified)

        lines = patch.split("\n")
        lines_added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
        lines_deleted = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))

        score = 1.0

        # Penalize excessive file sprawl (surgical fixes are preferred in open-source review)
        if file_count > 3:
            score -= 0.3
        elif file_count == 1:
            score += 0.1  # Bonus for single-file surgical fix

        # Check for unwanted debug statements left in patch
        debug_keywords = ["print(", "console.log(", "import pdb; pdb.set_trace()", "breakpoint()"]
        for kw in debug_keywords:
            if any(kw in l for l in lines if l.startswith("+")):
                score -= 0.25

        # Check for whitespace-only edits
        if lines_added == lines_deleted and lines_added > 0:
            added_text = "".join(l[1:].strip() for l in lines if l.startswith("+") and not l.startswith("+++"))
            deleted_text = "".join(l[1:].strip() for l in lines if l.startswith("-") and not l.startswith("---"))
            if added_text == deleted_text:
                score -= 0.5  # Pure whitespace churn

        bounded_score = max(0.1, min(1.0, round(score, 2)))

        return {
            "score": bounded_score,
            "is_valid": True,
            "file_count": file_count,
            "files": files_modified,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "size_bytes": len(patch),
        }
