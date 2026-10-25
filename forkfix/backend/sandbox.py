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
@dataclass
class MockState:
    files: dict[str, str] = field(default_factory=dict)
    git_diff: str = ""
    repro_passes: bool = False
    step_count: int = 0


class MockSandboxSession:
    def __init__(self, uuid: str, state: MockState, engine: MockSandboxEngine):
        self.uuid = uuid
        self.state = state
        self.engine = engine

    async def run(
        self,
        shell: str,
        cwd: str = "/testbed",
        files: dict[str, bytes] | None = None,
        disposable: bool = False,
        timeout: int = 180,
    ) -> ExecResult:
        # Simulate small network/command latency
        await asyncio.sleep(0.05)

        if files:
            for path, content in files.items():
                self.state.files[path] = content.decode("utf-8", errors="replace")

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

        if "git diff" in shell:
            return ExecResult(stdout=self.state.git_diff, stderr="", exit_code=0, uuid=self.uuid)

        # Standard step mutation
        self.state.step_count += 1
        new_uuid = f"mock-snap-{self.state.step_count}-{os.urandom(2).hex()}"
        if not disposable:
            # Fork a new state if needed
            self.uuid = new_uuid
            self.engine.snapshots[new_uuid] = MockState(
                files=dict(self.state.files),
                git_diff=self.state.git_diff,
                repro_passes=self.state.repro_passes,
                step_count=self.state.step_count,
            )

        return ExecResult(
            stdout=f"Updated files. [exit=0]",
            stderr="",
            exit_code=0,
            uuid=new_uuid if not disposable else self.uuid,
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
        return MockSandboxSession(image_uuid, state, self)


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
            temp_dir = tempfile.mkdtemp(prefix="forkfix-files-")
            for rel_path, data in files.items():
                dest = Path(temp_dir) / rel_path.lstrip("/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
            file_mounts = ["-v", f"{temp_dir}:{cwd}"]

        cmd = [
            "docker", "run", "--name", container_name,
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

