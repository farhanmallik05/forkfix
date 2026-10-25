"""Unit tests for Sprint Iteration 4:
GitHub Action bot comment generation, git apply script synthesis, and webhook ingestion.
"""

import sys
import yaml
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from forkfix.backend.github_bot import GitHubBot
from forkfix.backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_github_pr_comment_generation():
    comment = GitHubBot.generate_pr_comment(
        run_id="run-django-31422",
        issue_number=31422,
        repo_name="django/django",
        winning_branch_id="fast-b4",
        winning_patch="diff --git a/django/utils/formats.py b/django/utils/formats.py\n+fixed",
        total_cost=0.0382,
        elapsed_seconds=21.4,
        ascii_tree="Root -> C1 -> Branch 4 (WIN)",
        repro_cmd="pytest tests/i18n/test_formatting.py",
    )

    assert "#31422" in comment
    assert "django/django" in comment
    assert "fast-b4" in comment
    assert "$0.0382" in comment
    assert "62.1x cheaper than Devin" in comment
    assert "git checkout -b forkfix/31422" in comment
    assert "Oracle Exit Code: 0" in comment
    assert "Root -> C1 -> Branch 4 (WIN)" in comment


def test_git_apply_script_synthesis():
    script = GitHubBot.generate_git_apply_script(
        repo_name="pallets/flask",
        issue_id="4060",
        patch_content="diff --git a/src/flask/app.py b/src/flask/app.py\n+pass",
    )

    assert "#!/usr/bin/env bash" in script
    assert "git checkout -b forkfix/4060" in script
    assert "git apply -v -" in script
    assert "diff --git a/src/flask/app.py" in script


def test_github_webhook_endpoint():
    # Valid opened issue webhook
    payload = {
        "action": "opened",
        "issue": {
            "number": 128,
            "title": "Fix memory leak in websocket handler",
            "body": "When reconnecting rapidly, socket file descriptors leak.",
        },
        "repository": {
            "full_name": "acme/gateway",
        },
    }

    res = client.post("/api/webhook/github", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "queued"
    assert data["issue_number"] == 128
    assert "gh-128-" in data["run_id"]

    # Unsupported action
    res_unsupported = client.post("/api/webhook/github", json={"action": "deleted"})
    assert res_unsupported.status_code == 200
    assert res_unsupported.json()["status"] == "ignored"


def test_action_yml_manifest_integrity():
    action_path = PROJECT_ROOT / "action.yml"
    assert action_path.exists()

    with open(action_path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    assert content["name"] == "Forkfix Parallel Reality Debugger"
    assert "inputs" in content
    assert "nebius_api_key" in content["inputs"]
    assert "issue_text" in content["inputs"]
    assert "outputs" in content
    assert "winning_patch" in content["outputs"]
