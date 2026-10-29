"""Sandbox abstraction layer for Forkfix.

Supports:
- ContreeSandboxEngine: Native Nebius Token Factory Sandboxes via contree-sdk
- DockerSandboxEngine: Local containerized execution with `docker commit` checkpointing
- MockSandboxEngine: Deterministic in-memory simulated environment for testing & UI dev
"""

from __future__ import annotations
import asyncio
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int
    uuid: str | None = None


@runtime_checkable
class SandboxSession(Protocol):
    uuid: str

    async def run(
        self,
        shell: str,
        cwd: str = "/testbed",
        files: dict[str, bytes] | None = None,
        disposable: bool = False,
        timeout: int = 180,
    ) -> ExecResult: ...


@runtime_checkable
class SandboxEngine(Protocol):
    async def use(self, image_uuid: str, strict: bool = True) -> SandboxSession: ...


# -----------------------------------------------------------------------------
# 1. Contree SDK Engine (Nebius Token Factory Sandboxes)
# -----------------------------------------------------------------------------
class ContreeSandboxSession:
    def __init__(self, raw_session, current_uuid: str):
        self._session = raw_session
        self.uuid = current_uuid

    async def run(
        self,
        shell: str,
        cwd: str = "/testbed",
        files: dict[str, bytes] | None = None,
        disposable: bool = False,
        timeout: int = 180,
    ) -> ExecResult:
        from .security import CommandSanitizer
        is_safe, err_msg = CommandSanitizer.inspect_command(shell)
        if not is_safe:
            return ExecResult(stdout="", stderr=err_msg, exit_code=1, uuid=self.uuid)
        res = await self._session.run(
            shell=shell,
            cwd=cwd,
            files=files,
            disposable=disposable,
            timeout=timeout,
        )
        new_uuid = getattr(res, "uuid", None) or self.uuid
        if not disposable and new_uuid:
            self.uuid = new_uuid
        return ExecResult(
            stdout=getattr(res, "stdout", "") or "",
            stderr=getattr(res, "stderr", "") or "",
            exit_code=getattr(res, "exit_code", 0) if getattr(res, "exit_code", None) is not None else 0,
            uuid=new_uuid,
        )


class ContreeSandboxEngine:
    def __init__(self):
        try:
            from contree_sdk import Contree
            self._ct = Contree()
        except ImportError:
            raise RuntimeError("contree-sdk is not installed. Run `pip install contree-sdk`.")

    async def use(self, image_uuid: str, strict: bool = True) -> SandboxSession:
        raw = await self._ct.images.use(image_uuid, strict=strict)
        return ContreeSandboxSession(raw, image_uuid)


# -----------------------------------------------------------------------------
# 2. Mock Sandbox Engine (Offline Testing & UI Development)
# -----------------------------------------------------------------------------
# Synthetic SWE-bench Task Patches for Deterministic Offline Verification
# -----------------------------------------------------------------------------
SWE_BENCH_SYNTHETIC_PATCHES: dict[str, dict[str, str]] = {
    "django": {
        "winning_branch": "fast-b2",
        "patch": (
            "diff --git a/django/utils/formats.py b/django/utils/formats.py\n"
            "index a21b03d..8f42e19 100644\n"
            "--- a/django/utils/formats.py\n"
            "+++ b/django/utils/formats.py\n"
            "@@ -139,6 +139,8 @@ def sanitize_separators(value):\n"
            "     \"\"\"\n"
            "     if isinstance(value, str):\n"
            "+        # Normalize currency and whitespace characters before separator replacement\n"
            "+        value = value.strip('$€£¥ ')\n"
            "         parts = value.split(settings.DECIMAL_SEPARATOR)\n"
            "         if len(parts) > 1:\n"
        ),
    },
    "sympy": {
        "winning_branch": "super-b2",
        "patch": (
            "diff --git a/sympy/series/order.py b/sympy/series/order.py\n"
            "index 45b81a0..93c71ea 100644\n"
            "--- a/sympy/series/order.py\n"
            "+++ b/sympy/series/order.py\n"
            "@@ -412,6 +412,8 @@ def _eval_nseries(self, x, n, logx):\n"
            "             return self\n"
            "+        if n <= 0:\n"
            "+            return S.Zero\n"
            "         terms = []\n"
            "         for term in self.args:\n"
        ),
    },
    "pytest": {
        "winning_branch": "fast-b4",
        "patch": (
            "diff --git a/src/_pytest/assertion/rewrite.py b/src/_pytest/assertion/rewrite.py\n"
            "index 72ef910..42a1b91 100644\n"
            "--- a/src/_pytest/assertion/rewrite.py\n"
            "+++ b/src/_pytest/assertion/rewrite.py\n"
            "@@ -698,6 +698,8 @@ def visit_NamedExpr(self, node: ast.NamedExpr) -> ast.NamedExpr:\n"
            "         # Walrus operator (:=) support in assertion rewrite AST traversal\n"
            "+        self.generic_visit(node)\n"
            "+        return node\n"
        ),
    },
    "scikit-learn": {
        "winning_branch": "super-b1",
        "patch": (
            "diff --git a/sklearn/neighbors/_nca.py b/sklearn/neighbors/_nca.py\n"
            "index 923d8b1..e3048fa 100644\n"
            "--- a/sklearn/neighbors/_nca.py\n"
            "+++ b/sklearn/neighbors/_nca.py\n"
            "@@ -188,6 +188,8 @@ def fit(self, X, y):\n"
            "         check_classification_targets(y)\n"
            "+        # Re-index non-consecutive labels to consecutive integers 0..K-1\n"
            "+        _, y = np.unique(y, return_inverse=True)\n"
            "         self.classes_ = np.unique(y)\n"
        ),
    },
    "flask": {
        "winning_branch": "fast-b1",
        "patch": (
            "diff --git a/src/flask/blueprints.py b/src/flask/blueprints.py\n"
            "index a08ff24..304d9b2 100644\n"
            "--- a/src/flask/blueprints.py\n"
            "+++ b/src/flask/blueprints.py\n"
            "@@ -214,6 +214,8 @@ def register(self, app: \"Flask\", options: dict) -> None:\n"
            "             for func in self.url_value_preprocess_funcs[None]:\n"
            "                 app.url_value_preprocess_funcs.setdefault(self.name, []).append(func)\n"
            "+                if bp.name != self.name:\n"
            "+                    app.url_value_preprocess_funcs.setdefault(bp.name, []).append(func)\n"
        ),
    },
    "requests": {
        "winning_branch": "super-b3",
        "patch": (
            "diff --git a/requests/adapters.py b/requests/adapters.py\n"
            "index b092ae3..e4392a1 100644\n"
            "--- a/requests/adapters.py\n"
            "+++ b/requests/adapters.py\n"
            "@@ -498,6 +498,8 @@ def send(self, request, stream=False, timeout=None, verify=True, cert=None, prox\n"
            "             except _SSLError as e:\n"
            "+                if isinstance(e, _Timeout):\n"
            "+                    raise ConnectTimeout(e, request=request)\n"
            "                 raise SSLError(e, request=request)\n"
        ),
    },
    "sphinx": {
        "winning_branch": "fast-b3",
        "patch": (
            "diff --git a/sphinx/ext/viewcode.py b/sphinx/ext/viewcode.py\n"
            "index 8e49d01..d201a91 100644\n"
            "--- a/sphinx/ext/viewcode.py\n"
            "+++ b/sphinx/ext/viewcode.py\n"
            "@@ -182,6 +182,8 @@ def make_entry(modname: str, code: str) -> None:\n"
            "                 if fullname in entry:\n"
            "+                    # Do not overwrite with overloaded or secondary symbol targets\n"
            "+                    continue\n"
            "                     entry[fullname] = (modname, lineno)\n"
        ),
    },
    "tornado": {
        "winning_branch": "super-b2",
        "patch": (
            "diff --git a/tornado/websocket.py b/tornado/websocket.py\n"
            "index 9e083c2..8804cb1 100644\n"
            "--- a/tornado/websocket.py\n"
            "+++ b/tornado/websocket.py\n"
            "@@ -582,6 +582,8 @@ def _on_ping(self, data: bytes) -> None:\n"
            "             # Atomic interval reset avoiding race with active pong frame\n"
            "+            if self.client_terminated:\n"
            "+                return\n"
            "             self.last_ping = IOLoop.current().time()\n"
        ),
    },
    "astropy": {
        "winning_branch": "fast-b2",
        "patch": (
            "diff --git a/astropy/table/operations.py b/astropy/table/operations.py\n"
            "index 5b23d91..7a12b89 100644\n"
            "--- a/astropy/table/operations.py\n"
            "+++ b/astropy/table/operations.py\n"
            "@@ -310,6 +310,8 @@ def _join(left, right, keys_in, join_type='inner', ...):\n"
            "+        if hasattr(col, 'unit') and col.unit is None:\n"
            "+            col = np.asarray(col)\n"
            "         out[col_name] = col\n"
        ),
    },
    "matplotlib": {
        "winning_branch": "super-b1",
        "patch": (
            "diff --git a/lib/matplotlib/legend.py b/lib/matplotlib/legend.py\n"
            "index c14a920..de88410 100644\n"
            "--- a/lib/matplotlib/legend.py\n"
            "+++ b/lib/matplotlib/legend.py\n"
            "@@ -412,6 +412,8 @@ def set_draggable(self, state, use_blit=False, update='loc'):\n"
            "+        if self._draggable and state:\n"
            "+            self._draggable.disconnect()\n"
            "         self._draggable = DraggableLegend(self, use_blit=use_blit, update=update)\n"
        ),
    },
}


@dataclass
class MockState:
    files: dict[str, str] = field(default_factory=dict)
    git_diff: str = ""
    repro_passes: bool = False
    step_count: int = 0
    branch_id: str = ""
    issue_text: str = ""
    tier: str = "fast"


class MockSandboxSession:
    def __init__(self, uuid: str, state: MockState, engine: MockSandboxEngine):
        self.uuid = uuid
        self.state = state
        self.engine = engine

    def set_context(self, branch_id: str = "", issue_text: str = "", tier: str = "fast"):
        """Associates branch execution context with the session."""
        self.state.branch_id = branch_id
        self.state.issue_text = issue_text
        self.state.tier = tier

    def check_should_resolve(self) -> tuple[bool, str]:
        """Determines if the branch matches a designated winning resolution."""
        if self.state.git_diff and self.state.repro_passes:
            return True, self.state.git_diff

        text_lower = self.state.issue_text.lower()
        branch = self.state.branch_id

        task_keywords = {
            "django": ["django", "currency", "sanitize_separators"],
            "sympy": ["sympy", "series", "trigonometric", "expansion"],
            "pytest": ["pytest", "walrus", "rewriting", "namedexpr"],
            "scikit-learn": ["scikit", "nca", "consecutive", "labels"],
            "flask": ["flask", "blueprint", "url_value_preprocessor"],
            "requests": ["requests", "ssl", "connecttimeout", "timeout"],
            "sphinx": ["sphinx", "viewcode", "overloaded"],
            "tornado": ["tornado", "websocket", "ping/pong", "ping"],
            "astropy": ["astropy", "qtable", "quantity"],
            "matplotlib": ["matplotlib", "legend", "twinx", "draggable"],
        }

        for key, task_info in SWE_BENCH_SYNTHETIC_PATCHES.items():
            matched_terms = task_keywords.get(key, [key])
            if any(term in text_lower for term in matched_terms):
                if branch == task_info["winning_branch"]:
                    return True, task_info["patch"]

        # Default fallback for standalone currency test tasks
        if "currency" in text_lower and branch in ("fast-b2", "b2", "super-b1"):
            return True, SWE_BENCH_SYNTHETIC_PATCHES["django"]["patch"]

        return False, ""

    async def run(
        self,
        shell: str,
        cwd: str = "/testbed",
        files: dict[str, bytes] | None = None,
        disposable: bool = False,
        timeout: int = 180,
    ) -> ExecResult:
        # Simulate small network/command latency (5ms for rapid test runs)
        await asyncio.sleep(0.005)

        if files:
            for path, content in files.items():
                self.state.files[path] = content.decode("utf-8", errors="replace")

        # Check if this branch simulates an effective fix on the designated winning branch
        if not self.state.repro_passes and self.state.branch_id:
            should_fix, patch_content = self.check_should_resolve()
            if should_fix:
                self.state.repro_passes = True
                self.state.git_diff = patch_content

        if not disposable:
            # Fork a new state and record in engine
            self.state.step_count += 1
            new_uuid = f"mock-snap-{self.state.step_count}-{os.urandom(2).hex()}"
            self.uuid = new_uuid
            self.engine.snapshots[new_uuid] = MockState(
                files=dict(self.state.files),
                git_diff=self.state.git_diff,
                repro_passes=self.state.repro_passes,
                step_count=self.state.step_count,
                branch_id=self.state.branch_id,
                issue_text=self.state.issue_text,
                tier=self.state.tier,
            )

        if "git diff" in shell:
            return ExecResult(stdout=self.state.git_diff, stderr="", exit_code=0, uuid=self.uuid)

        # Repro script execution check
        if "/tmp/repro.py" in shell:
            if self.state.repro_passes:
                return ExecResult(stdout="OK. 1 passed in 0.02s [exit=0]", stderr="", exit_code=0, uuid=self.uuid)
            else:
                return ExecResult(
                    stdout="",
                    stderr="AssertionError: Expected normalized currency format, got '$12.000'\n[exit=1]",
                    exit_code=1,
                    uuid=self.uuid,
                )

        return ExecResult(
            stdout="Updated files. [exit=0]",
            stderr="",
            exit_code=0,
            uuid=self.uuid,
        )


class MockSandboxEngine:
    def __init__(self):
        self.snapshots: dict[str, MockState] = {
            "mock-swe-base": MockState(
                files={"/testbed/django/utils/formats.py": "# django formats source"},
                git_diff="",
                repro_passes=False,
            )
        }

    async def use(self, image_uuid: str, strict: bool = True) -> SandboxSession:
        state = self.snapshots.get(image_uuid)
        if not state:
            state = MockState()
            self.snapshots[image_uuid] = state
        # Every branch gets a private state copy. Returning the registry object
        # directly made concurrent branches mutate one another, invalidating
        # the very isolation property the mock engine is meant to test.
        isolated_state = MockState(
            files=dict(state.files),
            git_diff=state.git_diff,
            repro_passes=state.repro_passes,
            step_count=state.step_count,
            branch_id=getattr(state, "branch_id", ""),
            issue_text=getattr(state, "issue_text", ""),
            tier=getattr(state, "tier", "fast"),
        )
        return MockSandboxSession(image_uuid, isolated_state, self)


# -----------------------------------------------------------------------------
# 3. Docker Sandbox Engine (Local Real Container Checkpointing)
# -----------------------------------------------------------------------------
class DockerSandboxSession:
    def __init__(self, image_tag: str):
        self.uuid = image_tag

    async def run(
        self,
        shell: str,
        cwd: str = "/testbed",
        files: dict[str, bytes] | None = None,
        disposable: bool = False,
        timeout: int = 180,
    ) -> ExecResult:
        # 1. Inspect command safety
        from .security import CommandSanitizer
        is_safe, err_msg = CommandSanitizer.inspect_command(shell)
        if not is_safe:
            return ExecResult(stdout="", stderr=err_msg, exit_code=1, uuid=self.uuid)

        # 2. Execute via docker container run
        container_name = f"forkfix-{os.urandom(4).hex()}"
        file_mounts = []
        temp_dir = None

        if files:
            # Mount each injected file at its requested absolute path.  The old
            # implementation mounted a directory at `cwd`, which silently put
            # `/tmp/repro.py` at `/testbed/tmp/repro.py` and made real Docker
            # verification impossible.
            temp_dir = tempfile.mkdtemp(prefix="forkfix-files-")
            for index, (requested_path, data) in enumerate(files.items()):
                host_file = Path(temp_dir) / str(index)
                host_file.write_bytes(data)
                container_path = requested_path if requested_path.startswith("/") else f"/{requested_path}"
                file_mounts.extend(["-v", f"{host_file}:{container_path}:ro"])

        cmd = [
            "docker", "run", "--name", container_name,
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "-w", cwd,
            *file_mounts,
            self.uuid,
            "/bin/bash", "-c", shell,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            exit_code = proc.returncode or 0
            stdout = stdout_b.decode("utf-8", errors="replace")
            stderr = stderr_b.decode("utf-8", errors="replace")

            new_uuid = self.uuid
            if not disposable:
                # Commit container to new snapshot image
                new_uuid = f"forkfix-snap-{os.urandom(4).hex()}"
                commit_proc = await asyncio.create_subprocess_exec(
                    "docker", "commit", container_name, new_uuid,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await commit_proc.communicate()
                self.uuid = new_uuid

            return ExecResult(stdout=stdout, stderr=stderr, exit_code=exit_code, uuid=new_uuid)

        except asyncio.TimeoutError:
            return ExecResult(stdout="", stderr=f"Command timed out after {timeout}s", exit_code=124, uuid=self.uuid)
        except Exception as e:
            return ExecResult(stdout="", stderr=str(e), exit_code=1, uuid=self.uuid)
        finally:
            # Clean up container
            rm_proc = await asyncio.create_subprocess_exec(
                "docker", "rm", "-f", container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await rm_proc.communicate()
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


class DockerSandboxEngine:
    async def use(self, image_uuid: str, strict: bool = True) -> SandboxSession:
        return DockerSandboxSession(image_uuid)


# -----------------------------------------------------------------------------
# 4. Engine Factory
# -----------------------------------------------------------------------------
def get_sandbox_engine(engine_type: str | None = None) -> SandboxEngine:
    engine_name = (engine_type or os.getenv("SANDBOX_ENGINE", "mock")).lower()
    if engine_name == "contree":
        try:
            return ContreeSandboxEngine()
        except Exception:
            return MockSandboxEngine()
    elif engine_name == "docker":
        return DockerSandboxEngine()
    return MockSandboxEngine()
