"""
decision_log.py
Maya-OS — Venkatesh Swaminathan (2026)
Nexus Learning Labs / BITS Pilani

One CSV row per tick. This file is the paper's dataset.
Schema is fixed — do not add columns mid-session.
"""

import csv
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from collections import Counter


CSV_COLUMNS = [
    "timestamp", "tick",
    "bhaya", "vairagya", "shraddha", "spanda",
    "bhaya_fired", "vairagya_fired", "shraddha_fired", "spanda_fired",
    "cpu_percent", "ram_percent",
    "action_class", "target_pid", "target_name",
    "intensity", "execution_success", "reason",
    "intent_injected", "session_id",
]


@dataclass
class LogRow:
    timestamp:         str
    tick:              int
    bhaya:             float
    vairagya:          float
    shraddha:          float
    spanda:            float
    bhaya_fired:       bool
    vairagya_fired:    bool
    shraddha_fired:    bool
    spanda_fired:      bool
    cpu_percent:       float
    ram_percent:       float
    action_class:      str
    target_pid:        Optional[int]
    target_name:       Optional[str]
    intensity:         float
    execution_success: bool
    reason:            str
    intent_injected:   bool
    session_id:        str


class DecisionLogger:

    def __init__(self, log_dir: str = "logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path   = os.path.join(log_dir, f"maya_os_{self.session_id}.csv")
        self.row_count  = 0

        with open(self.log_path, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()

        print(f"[Logger] Session {self.session_id} → {self.log_path}")

    def log(self,
            engine_state:    dict,
            arbiter_decision,
            executor_result,
            intent_injected: bool = False) -> LogRow:

        v   = engine_state["voltages"]
        frd = engine_state["fired"]

        row = LogRow(
            timestamp         = engine_state["timestamp"],
            tick              = engine_state["tick"],
            bhaya             = v["bhaya"],
            vairagya          = v["vairagya"],
            shraddha          = v["shraddha"],
            spanda            = v["spanda"],
            bhaya_fired       = frd["bhaya"],
            vairagya_fired    = frd["vairagya"],
            shraddha_fired    = frd["shraddha"],
            spanda_fired      = frd["spanda"],
            cpu_percent       = engine_state["cpu"] * 100,
            ram_percent       = engine_state["ram"] * 100,
            action_class      = arbiter_decision.action.value,
            target_pid        = arbiter_decision.target_pid,
            target_name       = arbiter_decision.target_name,
            intensity         = arbiter_decision.intensity,
            execution_success = executor_result.success,
            reason            = executor_result.message[:120],
            intent_injected   = intent_injected,
            session_id        = self.session_id,
        )

        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CSV_COLUMNS).writerow({
                "timestamp":         row.timestamp,
                "tick":              row.tick,
                "bhaya":             round(row.bhaya, 4),
                "vairagya":          round(row.vairagya, 4),
                "shraddha":          round(row.shraddha, 4),
                "spanda":            round(row.spanda, 4),
                "bhaya_fired":       int(row.bhaya_fired),
                "vairagya_fired":    int(row.vairagya_fired),
                "shraddha_fired":    int(row.shraddha_fired),
                "spanda_fired":      int(row.spanda_fired),
                "cpu_percent":       round(row.cpu_percent, 2),
                "ram_percent":       round(row.ram_percent, 2),
                "action_class":      row.action_class,
                "target_pid":        row.target_pid or "",
                "target_name":       row.target_name or "",
                "intensity":         round(row.intensity, 4),
                "execution_success": int(row.execution_success),
                "reason":            row.reason,
                "intent_injected":   int(row.intent_injected),
                "session_id":        row.session_id,
            })

        self.row_count += 1
        return row

    def summary(self) -> dict:
        counts = Counter()
        with open(self.log_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                counts[r["action_class"]] += 1
        return {
            "session_id":  self.session_id,
            "total_ticks": self.row_count,
            "log_path":    self.log_path,
            "actions":     dict(counts),
        }
