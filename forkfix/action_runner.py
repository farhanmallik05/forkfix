"""Small, real CLI entry point used by the composite GitHub Action."""

from __future__ import annotations

import argparse
import asyncio
import os
import uuid

from .backend.database import get_db
from .backend.events import EventEmitter
from .backend.nemotron import NemotronClient
from .backend.orchestrator import ForkfixOrchestrator
from .backend.sandbox import get_sandbox_engine
from .backend.tavily_service import TavilyService


def _set_output(name: str, value: str) -> None:
    output_file = os.getenv("GITHUB_OUTPUT")
    if not output_file:
        try:
            print(f"{name}={value}")
        except UnicodeEncodeError:
            print(f"{name}={value.encode('ascii', errors='replace').decode('ascii')}")
        return
    delimiter = f"FORKFIX_{uuid.uuid4().hex}"
    with open(output_file, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


async def run(args: argparse.Namespace) -> dict[str, object]:
    run_id = f"action-{uuid.uuid4().hex[:8]}"
    get_db().create_run(run_id, args.issue_text, args.base_image_uuid)
    emitter = EventEmitter(run_id)
    orchestrator = ForkfixOrchestrator(
        engine=get_sandbox_engine(args.engine),
        nemotron=NemotronClient(),
        tavily=TavilyService(),
    )
    return await orchestrator.execute_fix(
        base_image_uuid=args.base_image_uuid,
        issue_text=args.issue_text,
        emitter=emitter,
        fast_branch_count=args.max_branches,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Forkfix from GitHub Actions")
    parser.add_argument("--issue-text", required=True)
    parser.add_argument("--engine", default=os.getenv("SANDBOX_ENGINE", "mock"))
    parser.add_argument("--base-image-uuid", default="mock-swe-base")
    parser.add_argument("--max-branches", type=int, default=4)
    args = parser.parse_args()
    result = asyncio.run(run(args))
    winner = result.get("winner") or {}
    _set_output("status", str(result.get("status", "unresolved")))
    _set_output("winning_patch", str(winner.get("patch", "")))
    _set_output("total_cost", f"{float(result.get('cost', 0.0)):.6f}")
    print(f"Forkfix status={result.get('status')} cost={float(result.get('cost', 0.0)):.6f}")


if __name__ == "__main__":
    main()
