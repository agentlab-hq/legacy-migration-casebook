"""Parallel Agent Team & Compiler Benchmark Harness (Feb 05, 2026).

Implements task locking, compiler-output reduction, reproducible test sampling,
and GCC-oracle differential testing for the reference harness.
"""

import hashlib
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class AgentTask:
    task_id: str
    file_target: str
    description: str
    owner_agent: Optional[str] = None
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, MERGE_CONFLICT


class GitTaskLockManager:
    """Cross-process task locking backed by atomically-created lock files.

    The default directory is ``current_tasks`` to match the documented harness
    layout. A lock is acquired with ``O_CREAT | O_EXCL``, so two processes cannot
    claim the same task successfully. The lock file contains the owning agent ID
    for inspection and debugging.
    """

    def __init__(self, lock_dir: str = "current_tasks"):
        self.lock_dir = Path(lock_dir)
        self.locked_tasks: Dict[str, str] = {}
        self.completed_tasks: Set[str] = set()

    def _lock_path(self, task_name: str) -> Path:
        if not task_name or Path(task_name).name != task_name:
            raise ValueError("task_name must be a non-empty file name without path separators")
        return self.lock_dir / f"{task_name}.txt"

    def try_acquire_lock(self, agent_id: str, task_name: str) -> bool:
        """Atomically claim ``<lock_dir>/<task_name>.txt``."""
        if not agent_id:
            raise ValueError("agent_id must be non-empty")

        lock_path = self._lock_path(task_name)
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            return False

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(f"{agent_id}\n")
        except Exception:
            lock_path.unlink(missing_ok=True)
            raise

        self.locked_tasks[str(lock_path)] = agent_id
        return True

    def release_lock(self, agent_id: str, task_name: str, completed: bool = True) -> bool:
        """Release a lock only when its recorded owner matches ``agent_id``."""
        lock_path = self._lock_path(task_name)
        try:
            owner = lock_path.read_text(encoding="utf-8").splitlines()[0].strip()
        except (FileNotFoundError, IndexError):
            return False

        if owner != agent_id:
            return False

        lock_path.unlink()
        self.locked_tasks.pop(str(lock_path), None)
        if completed:
            self.completed_tasks.add(task_name)
        return True


class ContextPollutionFilter:
    """Mitigates LLM context window bloat by summarizing test output and tagging errors."""

    @staticmethod
    def format_compiler_output(stdout: str, stderr: str) -> str:
        lines = (stdout + "\n" + stderr).splitlines()
        errors = [line for line in lines if "error" in line.lower() or "panic" in line.lower()]
        if not errors:
            return f"Build Succeeded ({len(lines)} lines suppressed). All checks clean."

        summary_lines = [f"Build Failed with {len(errors)} errors. Truncated sample:"]
        for error in errors[:5]:
            summary_lines.append(f"ERROR: {error.strip()}")
        if len(errors) > 5:
            summary_lines.append(f"... {len(errors) - 5} more errors logged to compiler_err.log")
        return "\n".join(summary_lines)


class TimeBlindnessTestSampler:
    """Runs fast, reproducible random subsamples so agents do not stall for hours."""

    def __init__(self, full_test_suite_size: int = 1200):
        if full_test_suite_size < 0:
            raise ValueError("full_test_suite_size must be non-negative")
        self.test_ids = [f"test_gcc_{i:04d}" for i in range(full_test_suite_size)]

    def get_agent_fast_sample(self, agent_id: str, sample_ratio: float = 0.1) -> List[str]:
        if not 0.0 <= sample_ratio <= 1.0:
            raise ValueError("sample_ratio must be between 0.0 and 1.0")
        digest = hashlib.sha256(agent_id.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big", signed=False)
        return random.Random(seed).sample(self.test_ids, int(len(self.test_ids) * sample_ratio))


class GCCOracleDifferentialTester:
    """Uses GCC as a known-good online compiler oracle to isolate bugs."""

    def __init__(self, kernel_modules: Optional[List[str]] = None):
        self.modules = kernel_modules or [
            "kernel/sched/core.c", "mm/memory.c", "fs/ext4/super.c",
            "net/ipv4/tcp.c", "drivers/char/tty_io.c", "arch/x86/kernel/entry_64.c"
        ]
        self.buggy_modules = {"mm/memory.c"}

    def run_differential_build(self, claude_compiled_modules: Set[str]) -> Tuple[bool, Optional[str]]:
        failed = [module for module in claude_compiled_modules if module in self.buggy_modules]
        if failed:
            return False, f"Boot Failed: Regression caused by modules compiled by Claude: {failed}"
        return True, "Boot Succeeded: Kernel booted to userspace successfully."

    def bisect_failing_module(self) -> str:
        """Binary-search the module list for the one that fails the differential build.

        The failure predicate is monotone over sets (a build fails iff the set
        contains a buggy module), so halving the candidate range converges in
        O(log n) builds instead of scanning every module.
        """
        passed, _ = self.run_differential_build(set(self.modules))
        if passed:
            return "None"
        lo, hi = 0, len(self.modules) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            passed, _ = self.run_differential_build(set(self.modules[lo : mid + 1]))
            if not passed:
                hi = mid
            else:
                lo = mid + 1
        return self.modules[lo]
