"""
syscall_executor.py
Maya-OS — Venkatesh Swaminathan (2026)
Nexus Learning Labs / BITS Pilani

Executes arbiter decisions at the OS level.
Safety contract is non-negotiable and runs before every action.

dry_run=True  — logs intended actions, touches nothing (default)
dry_run=False — live execution; pass --live flag to maya_os.py
"""

import psutil
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from MayaOS.core.os_arbiter import ActionClass, ArbiterDecision


# ── Execution result ──────────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    success:      bool
    action:       str
    target_pid:   Optional[int]
    target_name:  Optional[str]
    message:      str
    timestamp:    str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ── Safety contract ───────────────────────────────────────────────────────────

KILL_INTENSITY_MINIMUM = 0.70

PROTECTED_NAMES = {
    "system", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "lsass.exe", "svchost.exe", "explorer.exe",
    "python.exe", "pycharm64.exe", "pycharm.exe",
    "registry", "memory compression", "system idle process"
}


def _is_safe_target(pid: Optional[int], name: Optional[str]) -> tuple[bool, str]:
    if pid is None:
        return False, "No target PID"
    if name and name.lower() in PROTECTED_NAMES:
        return False, f"{name} is protected"
    try:
        proc = psutil.Process(pid)
        if proc.pid <= 4:
            return False, "System-level PID"
    except psutil.NoSuchProcess:
        return False, "Process no longer exists"
    except psutil.AccessDenied:
        return False, "Access denied"
    return True, "OK"


# ── Executor ──────────────────────────────────────────────────────────────────

class SyscallExecutor:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

        logging.basicConfig(
            filename="maya_os_execution.log",
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s"
        )
        self.logger = logging.getLogger("MayaOS.Executor")
        mode = "DRY-RUN" if dry_run else "LIVE"
        self.logger.info(f"SyscallExecutor initialised — {mode} mode")

    def execute(self, decision: ArbiterDecision) -> ExecutionResult:
        safe, reason = _is_safe_target(decision.target_pid, decision.target_name)
        self._log_decision(decision, safe, reason)

        if decision.action == ActionClass.IDLE:
            return ExecutionResult(True, "IDLE", None, None, "No action — system nominal")

        if decision.action == ActionClass.ALERT:
            return self._handle_alert(decision)

        if decision.action == ActionClass.PROTECT:
            return self._handle_protect(decision)

        if not safe:
            return ExecutionResult(
                False, decision.action.value,
                decision.target_pid, decision.target_name,
                f"Safety check failed: {reason}"
            )

        dispatch = {
            ActionClass.SUSPEND: self._handle_suspend,
            ActionClass.KILL:    self._handle_kill,
            ActionClass.CLEANUP: self._handle_cleanup,
        }
        handler = dispatch.get(decision.action)
        if handler:
            return handler(decision)

        return ExecutionResult(False, "UNKNOWN", None, None, "Unrecognised action class")

    def _handle_alert(self, d: ArbiterDecision) -> ExecutionResult:
        msg = f"[ALERT] Bhaya={d.bhaya:.3f} — monitoring {d.target_name} (PID {d.target_pid})"
        self.logger.warning(msg)
        return ExecutionResult(True, "ALERT", d.target_pid, d.target_name, msg)

    def _handle_protect(self, d: ArbiterDecision) -> ExecutionResult:
        msg = f"[PROTECT] Shraddha={d.shraddha:.3f} — {d.target_name} (PID {d.target_pid}) trusted"
        self.logger.info(msg)
        return ExecutionResult(True, "PROTECT", d.target_pid, d.target_name, msg)

    def _handle_suspend(self, d: ArbiterDecision) -> ExecutionResult:
        prefix = f"[SUSPEND] {d.target_name} (PID {d.target_pid})"
        if self.dry_run:
            msg = f"{prefix} — DRY-RUN"
            self.logger.info(msg)
            return ExecutionResult(True, "SUSPEND", d.target_pid, d.target_name, msg)
        try:
            psutil.Process(d.target_pid).suspend()
            msg = f"{prefix} — suspended. Vairagya={d.vairagya:.3f} moderated fear."
            self.logger.info(msg)
            return ExecutionResult(True, "SUSPEND", d.target_pid, d.target_name, msg)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            msg = f"{prefix} — failed: {e}"
            self.logger.error(msg)
            return ExecutionResult(False, "SUSPEND", d.target_pid, d.target_name, msg)

    def _handle_kill(self, d: ArbiterDecision) -> ExecutionResult:
        prefix = f"[KILL] {d.target_name} (PID {d.target_pid})"
        if d.intensity < KILL_INTENSITY_MINIMUM:
            msg = f"{prefix} — blocked: intensity {d.intensity:.3f} below minimum {KILL_INTENSITY_MINIMUM}"
            self.logger.warning(msg)
            return ExecutionResult(False, "KILL", d.target_pid, d.target_name, msg)
        if self.dry_run:
            msg = f"{prefix} — DRY-RUN (intensity={d.intensity:.3f})"
            self.logger.info(msg)
            return ExecutionResult(True, "KILL", d.target_pid, d.target_name, msg)
        try:
            psutil.Process(d.target_pid).kill()
            msg = f"{prefix} — killed. Bhaya={d.bhaya:.3f} unmoderated."
            self.logger.warning(msg)
            return ExecutionResult(True, "KILL", d.target_pid, d.target_name, msg)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            msg = f"{prefix} — failed: {e}"
            self.logger.error(msg)
            return ExecutionResult(False, "KILL", d.target_pid, d.target_name, msg)

    def _handle_cleanup(self, d: ArbiterDecision) -> ExecutionResult:
        prefix = f"[CLEANUP] {d.target_name} (PID {d.target_pid})"
        if self.dry_run:
            msg = f"{prefix} — DRY-RUN"
            self.logger.info(msg)
            return ExecutionResult(True, "CLEANUP", d.target_pid, d.target_name, msg)
        try:
            psutil.Process(d.target_pid).terminate()
            msg = f"{prefix} — terminated. Vairagya cleanup pass."
            self.logger.info(msg)
            return ExecutionResult(True, "CLEANUP", d.target_pid, d.target_name, msg)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            msg = f"{prefix} — failed: {e}"
            self.logger.error(msg)
            return ExecutionResult(False, "CLEANUP", d.target_pid, d.target_name, msg)

    def _log_decision(self, d: ArbiterDecision, safe: bool, reason: str):
        self.logger.info(
            f"DECISION | {d.action.value} | {d.target_name} | pid={d.target_pid} "
            f"| B={d.bhaya:.3f} V={d.vairagya:.3f} S={d.shraddha:.3f} Sp={d.spanda:.3f} "
            f"| safe={safe} | {reason}"
        )
