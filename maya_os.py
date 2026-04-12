import verify_provenance  # Maya Research Series -- Nexus Learning Labs, Bengaluru
verify_provenance.stamp()  # logs canary + ORCID on every run
"""
Maya-OS — Main Entry Point
==========================
The HAL moment. You talk. She acts.

Commands Maya understands:
    "focus"          → Shraddha boost   (protect work processes)
    "under attack"   → Bhaya spike      (trigger threat response)
    "calm down"      → Vairagya boost   (force graceful state)
    "stress test"    → Double-pump Bhaya, suppress Shraddha (forces KILL/SUSPEND)
    "status"         → Print live state
    "quit" / "exit"  → Shutdown Maya

Maya runs her affective engine continuously in a background thread.
Your commands inject directly into her voltage state.
"""

import time
import threading
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MayaOS.core.affective_engine import AffectiveEngine
from MayaOS.core.os_arbiter       import OSArbiter
from MayaOS.core.syscall_executor import SyscallExecutor
from MayaOS.logger.decision_log   import DecisionLogger
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich         import box

console = Console()


# ─── Intent Map ───────────────────────────────────────────────────────────────

INTENT_MAP = {
    # Threat / stress triggers
    "attack":       {"bhaya": +0.35, "shraddha": -0.15},
    "threat":       {"bhaya": +0.35, "shraddha": -0.15},
    "danger":       {"bhaya": +0.30},
    "emergency":    {"bhaya": +0.45, "shraddha": -0.20},
    "kill":         {"bhaya": +0.40, "vairagya": -0.25, "shraddha": -0.20},

    # Calm / focus triggers
    "focus":        {"shraddha": +0.30, "bhaya": -0.10},
    "working":      {"shraddha": +0.25, "spanda": +0.15},
    "research":     {"shraddha": +0.30, "vairagya": +0.10},
    "calm":         {"vairagya": +0.35, "bhaya": -0.20},
    "relax":        {"vairagya": +0.30, "bhaya": -0.15},
    "clean up":     {"vairagya": +0.45, "bhaya": -0.15},
    "cleanup":      {"vairagya": +0.45, "bhaya": -0.15},

    # Greetings
    "hello":        {"spanda": +0.15, "shraddha": +0.10},
    "good morning": {"spanda": +0.20, "shraddha": +0.15},
}

# Maya's spoken responses per action class
MAYA_RESPONSES = {
    "IDLE":    [
        "All systems nominal. I am watching.",
        "System state is calm. No action needed.",
        "Voltages stable. Standing by.",
    ],
    "ALERT":   [
        "Bhaya is rising. I am monitoring the threat.",
        "Fear signal detected. Watching closely. Not acting yet.",
        "Threat pattern forming. Shraddha is holding.",
    ],
    "PROTECT": [
        "Trust is dominant. I am shielding this process.",
        "Shraddha has fired. The process is protected.",
        "I recognise this. It is safe. I will guard it.",
    ],
    "SUSPEND": [
        "Wisdom moderates fear. Suspending gracefully.",
        "Vairagya is present. I suspend, not destroy.",
        "Fear acknowledged. Wisdom applied. Process suspended.",
    ],
    "KILL":    [
        "Bhaya is unmoderated. Terminating.",
        "Fear exceeds trust. No wisdom to temper it. Killing process.",
        "Threat confirmed. Shraddha absent. Executing kill.",
    ],
    "CLEANUP": [
        "Vairagya is high. The system is idle. Cleaning.",
        "Wisdom pass initiated. Releasing dormant processes.",
        "Graceful cleanup. Nothing is forced. Everything is released.",
    ],
}


def maya_speak(action: str, target: str = None) -> str:
    responses = MAYA_RESPONSES.get(action, ["..."])
    line = random.choice(responses)
    if target and action in ("SUSPEND", "KILL", "PROTECT", "ALERT"):
        line += f" [{target}]"
    return line


# ─── Intent Parser ────────────────────────────────────────────────────────────

def parse_intent(user_input: str) -> dict:
    text = user_input.lower().strip()

    if any(k in text for k in ("status", "how are you", "state")):
        return {"_status": True}

    # Stress test gets special handling — double pump
    if "stress test" in text:
        return {"_stress_test": True}

    injection = {}
    matched = False
    for keyword, signals in INTENT_MAP.items():
        if keyword in text and signals is not None:
            for neuron, delta in signals.items():
                injection[neuron] = injection.get(neuron, 0) + delta
            matched = True

    if not matched:
        injection = {"spanda": +0.05}

    return injection


# ─── Maya OS Core ─────────────────────────────────────────────────────────────

class MayaOS:

    def __init__(self, dry_run: bool = True):
        self.engine   = AffectiveEngine()
        self.arbiter  = OSArbiter()
        self.executor = SyscallExecutor(dry_run=dry_run)
        self.logger   = DecisionLogger(log_dir="MayaOS/logs")
        self.running  = False
        self.dry_run  = dry_run
        self.tick_count        = 0
        self.last_state        = None
        self.last_decision     = None
        self.last_result       = None
        self._intent_this_tick = False          # ← always initialised here
        self._lock = threading.Lock()

    def _background_tick(self):
        """Continuous engine loop in background thread."""
        while self.running:
            with self._lock:
                state    = self.engine.tick_update()
                decision = self.arbiter.evaluate(state)
                result   = self.executor.execute(decision)

                intent_flag            = self._intent_this_tick
                self._intent_this_tick = False   # reset after consuming

                self.logger.log(state, decision, result,
                                intent_injected=intent_flag)
                self.last_state    = state
                self.last_decision = decision
                self.last_result   = result
                self.tick_count   += 1
            time.sleep(0.5)

    def start(self):
        self.running = True
        self.thread  = threading.Thread(target=self._background_tick,
                                        daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def inject(self, signals: dict):
        """Inject intent signals directly into engine voltages."""
        with self._lock:
            self.engine.inject_intent(signals)
            self._intent_this_tick = True

    def stress_test(self):
        with self._lock:
            self.engine.neurons["bhaya"].voltage = 0.85
            self.engine.neurons["shraddha"].voltage = 0.02
            self.engine.neurons["vairagya"].voltage = 0.02
            self.engine._freeze_synapses = True  # block weight matrix for one tick
            self._intent_this_tick = True
        time.sleep(0.7)

    def get_status(self) -> dict:
        with self._lock:
            if self.last_state is None:
                return {}
            return {
                "tick":     self.last_state["tick"],
                "voltages": self.last_state["voltages"],
                "fired":    self.last_state["fired"],
                "action":   self.last_decision.action.value
                            if self.last_decision else "—",
                "target":   self.last_decision.target_name
                            if self.last_decision else "—",
                "intensity":self.last_decision.intensity
                            if self.last_decision else 0.0,
                "cpu":      self.last_state["cpu"] * 100,
                "ram":      self.last_state["ram"] * 100,
            }

    def print_status(self):
        s = self.get_status()
        if not s:
            console.print("[dim]No state yet...[/dim]")
            return
        v  = s["voltages"]
        fr = s["fired"]

        def fired_marker(name):
            return "[bold yellow]⚡FIRED[/bold yellow]" if fr.get(name) else ""

        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("Key",   style="dim",   width=14)
        table.add_column("Value", style="white", width=36)

        table.add_row("Tick",      str(s["tick"]))
        table.add_row("Bhaya",
            f"[red]{v['bhaya']:.4f}[/red]  {fired_marker('bhaya')}")
        table.add_row("Vairagya",
            f"[cyan]{v['vairagya']:.4f}[/cyan]  {fired_marker('vairagya')}")
        table.add_row("Shraddha",
            f"[green]{v['shraddha']:.4f}[/green]  {fired_marker('shraddha')}")
        table.add_row("Spanda",
            f"[yellow]{v['spanda']:.4f}[/yellow]  {fired_marker('spanda')}")
        table.add_row("Action",    f"[bold]{s['action']}[/bold]")
        table.add_row("Target",    s["target"] or "—")
        table.add_row("Intensity", f"{s['intensity']:.4f}")
        table.add_row("CPU",       f"{s['cpu']:.1f}%")
        table.add_row("RAM",       f"{s['ram']:.1f}%")

        console.print(Panel(table,
            title="[bold cyan]Maya Status[/bold cyan]",
            border_style="cyan", width=54))


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    console.print(Panel(
        "[bold cyan]Maya-OS[/bold cyan]\n"
        "[dim]Affective Neuromorphic Operating System[/dim]\n\n"
        "[white]Swaminathan, V. (2026)[/white]\n"
        "[dim]Nexus Learning Labs / BITS Pilani[/dim]\n\n"
        "[yellow]Commands: hello · focus · stress test · calm down\n"
        "          clean up · status · quit[/yellow]",
        title="[bold]Initialising[/bold]",
        border_style="cyan",
        width=60
    ))

    dry = "--live" not in sys.argv
    if not dry:
        console.print("[bold red]⚠  LIVE MODE — real OS actions will execute[/bold red]")
    else:
        console.print("[bold yellow]DRY-RUN MODE — no real OS actions[/bold yellow]\n")

    maya = MayaOS(dry_run=dry)
    maya.start()

    time.sleep(1.5)
    console.print("[bold green]Maya is awake.[/bold green]\n")

    while True:
        try:
            user_input = input("[You] → ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye", "shutdown"):
            console.print(
                "\n[cyan]Maya: Understood. Initiating graceful shutdown.[/cyan]")
            break

        intent = parse_intent(user_input)

        # ── Status ────────────────────────────────────────────────────────────
        if intent.get("_status"):
            maya.print_status()
            continue

        # ── Stress Test (special double-pump) ─────────────────────────────────
        if intent.get("_stress_test"):
            maya.stress_test()
            s = maya.get_status()
            if s:
                action   = s["action"]
                target   = s["target"]
                response = maya_speak(action, target)
                ACTION_COLOR = {
                    "IDLE":    "dim white",
                    "ALERT":   "yellow",
                    "SUSPEND": "orange3",
                    "KILL":    "bold red",
                    "PROTECT": "bold green",
                    "CLEANUP": "cyan",
                }
                color = ACTION_COLOR.get(action, "white")
                v = s["voltages"]
                console.print(
                    f"[cyan]Maya:[/cyan] {response}\n"
                    f"       [dim]B={v['bhaya']:.3f} "
                    f"V={v['vairagya']:.3f} "
                    f"S={v['shraddha']:.3f} "
                    f"Sp={v['spanda']:.3f} → "
                    f"[{color}]{action}[/{color}][/dim]"
                )
            continue

        # ── Normal Intent ─────────────────────────────────────────────────────
        maya.inject(intent)
        time.sleep(0.6)

        s = maya.get_status()
        if s:
            action   = s["action"]
            target   = s["target"]
            response = maya_speak(action, target)
            ACTION_COLOR = {
                "IDLE":    "dim white",
                "ALERT":   "yellow",
                "SUSPEND": "orange3",
                "KILL":    "bold red",
                "PROTECT": "bold green",
                "CLEANUP": "cyan",
            }
            color = ACTION_COLOR.get(action, "white")
            v = s["voltages"]
            console.print(
                f"[cyan]Maya:[/cyan] {response}\n"
                f"       [dim]B={v['bhaya']:.3f} "
                f"V={v['vairagya']:.3f} "
                f"S={v['shraddha']:.3f} "
                f"Sp={v['spanda']:.3f} → "
                f"[{color}]{action}[/{color}][/dim]"
            )

    maya.stop()
    summary = maya.logger.summary()
    console.print(
        f"\n[dim]Session complete. "
        f"{summary['total_ticks']} ticks logged.[/dim]")
    console.print(f"[dim]Actions: {summary['actions']}[/dim]")
    console.print(f"[dim]Log: {summary['log_path']}[/dim]\n")


if __name__ == "__main__":
    main()