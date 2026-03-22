"""
os_arbiter.py
Maya-OS — Venkatesh Swaminathan (2026)
Nexus Learning Labs / BITS Pilani

Voltage vector → action class. No hardcoded rules — state decides.

The same Bhaya value produces KILL or SUSPEND depending on Vairagya.
The same threat produces PROTECT if Shraddha is dominant.
Behaviour emerges from voltage ratios, not conditionals.
"""

import psutil
from dataclasses import dataclass
from typing import Optional
from enum import Enum


# ── Action classes ────────────────────────────────────────────────────────────

class ActionClass(Enum):
    IDLE    = "IDLE"
    ALERT   = "ALERT"
    SUSPEND = "SUSPEND"
    KILL    = "KILL"
    PROTECT = "PROTECT"
    CLEANUP = "CLEANUP"


@dataclass
class ArbiterDecision:
    action:       ActionClass
    target_pid:   Optional[int]
    target_name:  Optional[str]
    reason:       str
    intensity:    float        # 0.0–1.0, derived from voltage ratio
    bhaya:        float
    vairagya:     float
    shraddha:     float
    spanda:       float


# ── Thresholds ────────────────────────────────────────────────────────────────

BHAYA_CRITICAL      = 0.58   # bypass protection entirely
BHAYA_ACTION        = 0.55   # act on threat
BHAYA_ALERT         = 0.35   # watch, don't act
VAIRAGYA_THRESHOLD  = 0.30   # wisdom present — modulate aggression
SHRADDHA_THRESHOLD  = 0.40   # trust present — shield top process
CLEANUP_THRESHOLD   = 0.45   # wisdom dominant, threat absent — idle pass

PROTECTED_NAMES = {
    "system", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "lsass.exe", "svchost.exe", "explorer.exe",
    "python.exe", "pycharm64.exe", "pycharm.exe", "maya_os.py",
    "registry", "memory compression", "system idle process"
}


# ── Process selection ─────────────────────────────────────────────────────────

def get_top_cpu_process() -> Optional[tuple]:
    top, top_cpu = None, 0.0
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            name = proc.info['name'].lower()
            cpu  = proc.info['cpu_percent'] or 0.0
            if name in PROTECTED_NAMES or proc.info['pid'] == 0:
                continue
            if cpu > top_cpu:
                top_cpu = cpu
                top = (proc.info['pid'], proc.info['name'], cpu)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return top


def get_top_ram_process() -> Optional[tuple]:
    top, top_ram = None, 0.0
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            name   = proc.info['name'].lower()
            mem    = proc.info['memory_info']
            if mem is None or name in PROTECTED_NAMES:
                continue
            ram_mb = mem.rss / (1024 * 1024)
            if ram_mb > top_ram:
                top_ram = ram_mb
                top = (proc.info['pid'], proc.info['name'], ram_mb)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return top


def get_idle_processes() -> list:
    idle = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'status']):
        try:
            name   = proc.info['name'].lower()
            cpu    = proc.info['cpu_percent'] or 0.0
            status = proc.info['status']
            if name in PROTECTED_NAMES:
                continue
            if cpu == 0.0 and status == psutil.STATUS_SLEEPING:
                idle.append((proc.info['pid'], proc.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return idle[:5]


# ── Arbiter ───────────────────────────────────────────────────────────────────

class OSArbiter:

    def __init__(self):
        self.decision_history = []
        self.protected_pids   = set()

    def protect_pid(self, pid: int):
        self.protected_pids.add(pid)

    def evaluate(self, state: dict) -> ArbiterDecision:
        v        = state["voltages"]
        bhaya    = v["bhaya"]
        vairagya = v["vairagya"]
        shraddha = v["shraddha"]
        spanda   = v["spanda"]

        # Critical override — Bhaya dominant, Shraddha absent
        # Bypasses protection pass; fear wins unmoderated
        if bhaya > BHAYA_CRITICAL and shraddha < 0.25:
            intensity = bhaya / (shraddha + 0.001)
            top = get_top_cpu_process()
            if top:
                pid, name, _ = top
                if pid not in self.protected_pids:
                    action = ActionClass.SUSPEND if vairagya > VAIRAGYA_THRESHOLD \
                             else ActionClass.KILL
                    label  = "wisdom moderates → SUSPEND" if action == ActionClass.SUSPEND \
                             else "trust absent → KILL"
                    return ArbiterDecision(
                        action=action, target_pid=pid, target_name=name,
                        reason=f"CRITICAL: Bhaya={bhaya:.3f}, Shraddha={shraddha:.3f} — {label}",
                        intensity=intensity,
                        bhaya=bhaya, vairagya=vairagya,
                        shraddha=shraddha, spanda=spanda
                    )

        # Shraddha dominant — shield top process before any threat action
        if shraddha > SHRADDHA_THRESHOLD:
            top = get_top_cpu_process()
            if top:
                pid, name, _ = top
                self.protected_pids.add(pid)
                return ArbiterDecision(
                    action=ActionClass.PROTECT, target_pid=pid, target_name=name,
                    reason=f"Shraddha={shraddha:.3f} > {SHRADDHA_THRESHOLD} — trust shields top process",
                    intensity=shraddha,
                    bhaya=bhaya, vairagya=vairagya,
                    shraddha=shraddha, spanda=spanda
                )

        # Bhaya above action threshold — SUSPEND or KILL depending on Vairagya
        if bhaya > BHAYA_ACTION:
            intensity = bhaya / (shraddha + 0.001)
            top = get_top_cpu_process()
            if top:
                pid, name, cpu = top
                if pid in self.protected_pids:
                    return ArbiterDecision(
                        action=ActionClass.ALERT, target_pid=pid, target_name=name,
                        reason=f"Bhaya high but {name} is Shraddha-protected",
                        intensity=bhaya,
                        bhaya=bhaya, vairagya=vairagya,
                        shraddha=shraddha, spanda=spanda
                    )
                if vairagya > VAIRAGYA_THRESHOLD:
                    return ArbiterDecision(
                        action=ActionClass.SUSPEND, target_pid=pid, target_name=name,
                        reason=f"Bhaya={bhaya:.3f} + Vairagya={vairagya:.3f} — wisdom moderates → suspend",
                        intensity=intensity,
                        bhaya=bhaya, vairagya=vairagya,
                        shraddha=shraddha, spanda=spanda
                    )
                return ArbiterDecision(
                    action=ActionClass.KILL, target_pid=pid, target_name=name,
                    reason=f"Bhaya={bhaya:.3f}, Vairagya={vairagya:.3f} — fear unmoderated → kill",
                    intensity=intensity,
                    bhaya=bhaya, vairagya=vairagya,
                    shraddha=shraddha, spanda=spanda
                )

        # Bhaya rising but below action threshold — monitor only
        if bhaya > BHAYA_ALERT:
            top  = get_top_cpu_process()
            pid  = top[0] if top else None
            name = top[1] if top else "unknown"
            return ArbiterDecision(
                action=ActionClass.ALERT, target_pid=pid, target_name=name,
                reason=f"Bhaya={bhaya:.3f} rising — monitoring, no action yet",
                intensity=bhaya,
                bhaya=bhaya, vairagya=vairagya,
                shraddha=shraddha, spanda=spanda
            )

        # Vairagya dominant, system calm — gentle idle cleanup pass
        if vairagya > CLEANUP_THRESHOLD and bhaya < BHAYA_ALERT:
            idle = get_idle_processes()
            if idle:
                pid, name = idle[0]
                return ArbiterDecision(
                    action=ActionClass.CLEANUP, target_pid=pid, target_name=name,
                    reason=f"Vairagya={vairagya:.3f} dominant, Bhaya={bhaya:.3f} — idle cleanup",
                    intensity=vairagya,
                    bhaya=bhaya, vairagya=vairagya,
                    shraddha=shraddha, spanda=spanda
                )

        return ArbiterDecision(
            action=ActionClass.IDLE, target_pid=None, target_name=None,
            reason="All voltages nominal — no action required",
            intensity=0.0,
            bhaya=bhaya, vairagya=vairagya,
            shraddha=shraddha, spanda=spanda
        )
