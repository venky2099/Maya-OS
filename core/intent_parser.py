"""
intent_parser.py
Maya-OS — Venkatesh Swaminathan (2026)
Nexus Learning Labs / BITS Pilani

Maps natural language input to neuron injection signals.
Phase 1: keyword matching. Phase 2: LLM-based semantic parsing.

Each intent returns a dict of {neuron_name: voltage_delta}.
Positive delta excites, negative delta suppresses.
"""

from typing import Dict, Optional


# ── Intent definitions ────────────────────────────────────────────────────────
# Format: keyword → {neuron: delta}
# Deltas are applied directly to membrane voltage via AffectiveEngine.inject_intent()

INTENT_MAP: Dict[str, Dict[str, float]] = {
    # Threat signals — raise Bhaya, suppress trust/wisdom
    "attack":       {"bhaya": +0.35, "shraddha": -0.15},
    "threat":       {"bhaya": +0.35, "shraddha": -0.15},
    "danger":       {"bhaya": +0.30},
    "emergency":    {"bhaya": +0.45, "shraddha": -0.20},
    "kill":         {"bhaya": +0.40, "vairagya": -0.25, "shraddha": -0.20},
    "ransomware":   {"bhaya": +0.50, "shraddha": -0.30, "vairagya": -0.20},
    "intrusion":    {"bhaya": +0.45, "shraddha": -0.20},

    # Focus / trust signals — raise Shraddha, dampen fear
    "focus":        {"shraddha": +0.30, "bhaya": -0.10},
    "working":      {"shraddha": +0.25, "spanda": +0.15},
    "research":     {"shraddha": +0.30, "vairagya": +0.10},
    "writing":      {"shraddha": +0.25, "spanda": +0.10},
    "coding":       {"shraddha": +0.25, "spanda": +0.15},

    # Calm / release signals — raise Vairagya
    "calm":         {"vairagya": +0.35, "bhaya": -0.20},
    "relax":        {"vairagya": +0.30, "bhaya": -0.15},
    "done":         {"vairagya": +0.35, "spanda": -0.10},
    "break":        {"vairagya": +0.30, "spanda": -0.10},
    "clean up":     {"vairagya": +0.45, "bhaya": -0.15},
    "cleanup":      {"vairagya": +0.45, "bhaya": -0.15},
    "shutdown":     {"vairagya": +0.40, "spanda": -0.20},

    # Greeting / arousal signals — raise Spanda
    "hello":        {"spanda": +0.15, "shraddha": +0.10},
    "good morning": {"spanda": +0.20, "shraddha": +0.15},
    "wake up":      {"spanda": +0.25},
    "start":        {"spanda": +0.20, "shraddha": +0.10},
}

# Keywords that trigger status display rather than injection
STATUS_KEYWORDS = {"status", "how are you", "state", "voltages", "report"}

# Stress test keyword — handled separately in maya_os.py (double-pump logic)
STRESS_TEST_KEYWORD = "stress test"


# ── Parser ────────────────────────────────────────────────────────────────────

class IntentParser:
    """
    Phase 1 keyword parser.
    Scans user input for known intent keywords and accumulates voltage deltas.
    Multiple keywords in one utterance stack additively.
    """

    def parse(self, user_input: str) -> Dict:
        """
        Returns one of:
            {"_status": True}           — display status, no injection
            {"_stress_test": True}      — trigger double-pump stress sequence
            {"neuron": delta, ...}      — inject into engine
            {"spanda": +0.05}           — default acknowledgement (no match)
        """
        text = user_input.lower().strip()

        if any(k in text for k in STATUS_KEYWORDS):
            return {"_status": True}

        if STRESS_TEST_KEYWORD in text:
            return {"_stress_test": True}

        injection: Dict[str, float] = {}
        matched = False

        for keyword, signals in INTENT_MAP.items():
            if keyword in text:
                for neuron, delta in signals.items():
                    injection[neuron] = injection.get(neuron, 0.0) + delta
                matched = True

        if not matched:
            # Default: mild aliveness boost — Maya acknowledges the utterance
            return {"spanda": +0.05}

        # Clamp accumulated deltas to [-1.0, +1.0]
        return {k: max(-1.0, min(v, 1.0)) for k, v in injection.items()}

    def describe(self, injection: Dict) -> str:
        """Human-readable summary of what an injection will do."""
        if injection.get("_status"):
            return "Status request."
        if injection.get("_stress_test"):
            return "Stress test: forced Bhaya spike, Shraddha suppressed."
        parts = []
        for neuron, delta in injection.items():
            direction = "↑" if delta > 0 else "↓"
            parts.append(f"{neuron.capitalize()} {direction}{abs(delta):.2f}")
        return ", ".join(parts) if parts else "No signal."


# ── Convenience function ──────────────────────────────────────────────────────

_default_parser = IntentParser()

def parse_intent(user_input: str) -> Dict:
    """Module-level convenience wrapper around IntentParser.parse()."""
    return _default_parser.parse(user_input)
