"""
affective_engine.py
Maya-OS — Venkatesh Swaminathan (2026)
Nexus Learning Labs / BITS Pilani

Four LIF neurons read live system metrics every 500ms and output
a voltage vector that drives OS arbitration decisions.

Neuron design inherits from Swaminathan (2026):
https://doi.org/10.5281/zenodo.19151563
"""

import time
import math
import psutil
from dataclasses import dataclass, field
from typing import Dict, Tuple
from datetime import datetime


# ── Neuron config ─────────────────────────────────────────────────────────────

@dataclass
class NeuronConfig:
    name: str
    tau: float           # membrane decay constant
    threshold: float     # firing threshold
    reset_voltage: float = 0.0
    rest_voltage: float  = 0.0


NEURON_CONFIGS = {
    "bhaya":    NeuronConfig("Bhaya",    tau=3,  threshold=0.65),
    "vairagya": NeuronConfig("Vairagya", tau=20, threshold=0.50),
    "shraddha": NeuronConfig("Shraddha", tau=10, threshold=0.55),
    "spanda":   NeuronConfig("Spanda",   tau=5,  threshold=0.60),
}

# Cross-neuron synaptic weights [source][target]
# Order: bhaya, vairagya, shraddha, spanda
INITIAL_WEIGHTS = [
    [ 0.00, -0.30,  0.10,  0.20],
    [-0.20,  0.00,  0.25, -0.10],
    [ 0.15,  0.20,  0.00,  0.30],
    [ 0.10, -0.10,  0.10,  0.00],
]

NEURON_ORDER = ["bhaya", "vairagya", "shraddha", "spanda"]


# ── LIF neuron ────────────────────────────────────────────────────────────────

@dataclass
class LIFNeuron:
    config: NeuronConfig
    voltage: float = 0.0
    fired: bool    = False
    fire_count: int = 0

    def integrate(self, input_current: float, dt: float = 0.5) -> bool:
        # dV/dt = -V/τ + I
        leak = -self.voltage / self.config.tau
        self.voltage += (leak + input_current) * dt
        self.voltage = max(0.0, min(self.voltage, 1.0))

        if self.voltage >= self.config.threshold:
            self.fired      = True
            self.fire_count += 1
            self.voltage    = self.config.reset_voltage
            return True

        self.fired = False
        return False


# ── Engine ────────────────────────────────────────────────────────────────────

class AffectiveEngine:
    """
    Reads system state → produces affective voltage vector → caller drives arbitration.
    Fixed weights in Phase 1; Hebbian plasticity planned for Phase 2.
    """

    def __init__(self):
        self.neurons: Dict[str, LIFNeuron] = {
            name: LIFNeuron(config=cfg)
            for name, cfg in NEURON_CONFIGS.items()
        }
        self.weights        = [row[:] for row in INITIAL_WEIGHTS]
        self.tick           = 0
        self.last_cpu       = 0.0
        self.last_ram       = 0.0
        self.known_pids: set = set()
        self._freeze_synapses = False   # set True to block weight matrix for one tick

        self._seed_known_processes()

    def _seed_known_processes(self):
        for proc in psutil.process_iter(['pid']):
            try:
                self.known_pids.add(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def _read_system_signals(self) -> Dict[str, float]:
        cpu = psutil.cpu_percent(interval=0.1) / 100.0
        ram = psutil.virtual_memory().percent / 100.0

        current_pids   = set()
        unknown_count  = 0
        for proc in psutil.process_iter(['pid']):
            try:
                pid = proc.info['pid']
                current_pids.add(pid)
                if pid not in self.known_pids:
                    unknown_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        self.known_pids = current_pids

        unknown_signal = min(unknown_count / 5.0, 1.0)

        # Spanda peaks during working hours (9–18h local)
        hour        = datetime.now().hour
        spanda_time = math.sin(math.pi * max(0, hour - 7) / 12.0) \
                      if 7 <= hour <= 19 else 0.05

        self.last_cpu = cpu
        self.last_ram = ram

        return {
            "bhaya":    (cpu * 0.5) + (ram * 0.3) + (unknown_signal * 0.2),
            "vairagya": ((1.0 - cpu) * 0.4) + ((1.0 - ram) * 0.4) + 0.05,
            "shraddha": (1.0 - unknown_signal) * 0.6 + (1.0 - cpu) * 0.4,
            "spanda":   spanda_time * 0.7 + (cpu * 0.3),
        }

    def _apply_synaptic_influence(self, base_signals: Dict[str, float]) -> Dict[str, float]:
        # Skip weight propagation for one tick when freeze flag is set
        if self._freeze_synapses:
            self._freeze_synapses = False
            return base_signals

        modulated = dict(base_signals)
        for src_idx, src_name in enumerate(NEURON_ORDER):
            if self.neurons[src_name].fired:
                for tgt_idx, tgt_name in enumerate(NEURON_ORDER):
                    if src_idx != tgt_idx:
                        modulated[tgt_name] += self.weights[src_idx][tgt_idx] * 0.3

        return {k: max(0.0, min(v, 1.0)) for k, v in modulated.items()}

    def inject_intent(self, intent_signal: Dict[str, float]):
        """Direct voltage injection from conversational input."""
        for name, boost in intent_signal.items():
            if name in self.neurons:
                self.neurons[name].voltage = max(
                    0.0, min(self.neurons[name].voltage + boost, 1.0)
                )

    def tick_update(self) -> Dict:
        """One 500ms tick: read system → modulate → integrate → return state snapshot."""
        self.tick += 1

        base_signals      = self._read_system_signals()
        modulated_signals = self._apply_synaptic_influence(base_signals)

        fired_map = {}
        for name in NEURON_ORDER:
            fired_map[name] = self.neurons[name].integrate(modulated_signals[name])

        return {
            "tick":      self.tick,
            "timestamp": datetime.now().isoformat(),
            "voltages":  {n: round(self.neurons[n].voltage, 4) for n in NEURON_ORDER},
            "fired":     fired_map,
            "inputs":    modulated_signals,
            "cpu":       round(self.last_cpu, 3),
            "ram":       round(self.last_ram, 3),
        }

    def get_voltage_vector(self) -> Tuple[float, float, float, float]:
        return tuple(self.neurons[n].voltage for n in NEURON_ORDER)
