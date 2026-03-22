"""
Maya-OS Session Analyser
========================
Generates publication-quality figures from decision log CSV.
Figure 1: Voltage trajectories + action events
Figure 2: Action class distribution
Figure 3: CPU load vs Bhaya correlation
"""

import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
import os


def load_csv(path: str) -> list:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def plot_session(csv_path: str):
    rows = load_csv(csv_path)

    ticks     = [int(r["tick"])       for r in rows]
    bhaya     = [float(r["bhaya"])    for r in rows]
    vairagya  = [float(r["vairagya"]) for r in rows]
    shraddha  = [float(r["shraddha"]) for r in rows]
    spanda    = [float(r["spanda"])   for r in rows]
    cpu       = [float(r["cpu_percent"]) for r in rows]
    actions   = [r["action_class"]    for r in rows]

    # Action event markers
    protect_ticks = [ticks[i] for i, a in enumerate(actions) if a == "PROTECT"]
    alert_ticks   = [ticks[i] for i, a in enumerate(actions) if a == "ALERT"]
    suspend_ticks = [ticks[i] for i, a in enumerate(actions) if a == "SUSPEND"]
    kill_ticks    = [ticks[i] for i, a in enumerate(actions) if a == "KILL"]
    cleanup_ticks = [ticks[i] for i, a in enumerate(actions) if a == "CLEANUP"]

    protect_b  = [bhaya[i] for i, a in enumerate(actions) if a == "PROTECT"]
    alert_b    = [bhaya[i] for i, a in enumerate(actions) if a == "ALERT"]

    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle(
        "Maya-OS: Affective State Dynamics and OS Arbitration\n"
        "Swaminathan, V. (2026) — Nexus Learning Labs / BITS Pilani",
        fontsize=13, fontweight="bold", y=0.98
    )

    # ── Figure 1: Voltage Trajectories ───────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(ticks, bhaya,    color="#E74C3C", linewidth=2,   label="Bhaya (Fear/Threat)    τ=3")
    ax1.plot(ticks, vairagya, color="#3498DB", linewidth=2,   label="Vairagya (Wisdom)       τ=20")
    ax1.plot(ticks, shraddha, color="#2ECC71", linewidth=2,   label="Shraddha (Trust)        τ=10")
    ax1.plot(ticks, spanda,   color="#F39C12", linewidth=1.5, label="Spanda (Aliveness)      τ=5",
             linestyle="--", alpha=0.8)

    # Threshold lines
    ax1.axhline(y=0.55, color="#E74C3C", linestyle=":", alpha=0.5, linewidth=1)
    ax1.axhline(y=0.35, color="#E74C3C", linestyle=":", alpha=0.3, linewidth=1)
    ax1.axhline(y=0.40, color="#2ECC71", linestyle=":", alpha=0.4, linewidth=1)
    ax1.text(ticks[-1]+0.3, 0.55, "Kill threshold",  color="#E74C3C", fontsize=8, va="center")
    ax1.text(ticks[-1]+0.3, 0.35, "Alert threshold", color="#E74C3C", fontsize=8, va="center", alpha=0.6)
    ax1.text(ticks[-1]+0.3, 0.40, "Protect threshold", color="#2ECC71", fontsize=8, va="center", alpha=0.7)

    # Action event markers on voltage curve
    ax1.scatter(protect_ticks, protect_b, marker="^", color="#2ECC71",
                s=80, zorder=5, label="PROTECT fired")
    ax1.scatter(alert_ticks,   alert_b,   marker="o", color="#E74C3C",
                s=60, zorder=5, label="ALERT fired")

    ax1.set_ylabel("Membrane Voltage (normalised)", fontsize=10)
    ax1.set_title("(A) LIF Neuron Voltage Trajectories with Action Events", fontsize=11)
    ax1.legend(loc="upper left", fontsize=8, ncol=2)
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, alpha=0.3)

    # ── Figure 2: Action Class Distribution ──────────────────────────────────
    ax2 = axes[1]
    from collections import Counter
    action_counts = Counter(actions)
    action_labels = list(action_counts.keys())
    action_values = list(action_counts.values())

    COLOR_MAP = {
        "IDLE":    "#95A5A6",
        "ALERT":   "#F39C12",
        "PROTECT": "#2ECC71",
        "SUSPEND": "#E67E22",
        "KILL":    "#E74C3C",
        "CLEANUP": "#3498DB",
    }
    bar_colors = [COLOR_MAP.get(a, "#BDC3C7") for a in action_labels]

    bars = ax2.bar(action_labels, action_values, color=bar_colors,
                   edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, action_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 str(val), ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax2.set_ylabel("Frequency (ticks)", fontsize=10)
    ax2.set_title("(B) Action Class Distribution — Emergent OS Decisions", fontsize=11)
    ax2.grid(True, axis="y", alpha=0.3)

    # ── Figure 3: CPU Load vs Bhaya Correlation ───────────────────────────────
    ax3 = axes[2]
    ax3_twin = ax3.twinx()

    ax3.fill_between(ticks, cpu, alpha=0.25, color="#E74C3C", label="CPU %")
    ax3.plot(ticks, cpu,   color="#E74C3C", linewidth=1.5, alpha=0.7)
    ax3_twin.plot(ticks, bhaya, color="#C0392B", linewidth=2.5, label="Bhaya voltage")

    ax3.set_ylabel("CPU Utilisation (%)", fontsize=10, color="#E74C3C")
    ax3_twin.set_ylabel("Bhaya Voltage", fontsize=10, color="#C0392B")
    ax3.set_xlabel("Tick", fontsize=10)
    ax3.set_title("(C) CPU Load Correlation with Bhaya Accumulation", fontsize=11)

    # Correlation coefficient
    corr = np.corrcoef(cpu, bhaya)[0, 1]
    ax3.text(0.02, 0.88, f"Pearson r = {corr:.3f}",
             transform=ax3.transAxes, fontsize=10,
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))

    ax3.grid(True, alpha=0.3)

    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    out_path = csv_path.replace(".csv", "_figures.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\n✓ Figures saved → {out_path}")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Auto-find latest CSV in logs/
        log_dir = "MayaOS/logs"
        csvs = [f for f in os.listdir(log_dir) if f.endswith(".csv")]
        if not csvs:
            print("No CSV found in MayaOS/logs/")
            sys.exit(1)
        latest = sorted(csvs)[-1]
        csv_path = os.path.join(log_dir, latest)
        print(f"Auto-loading: {csv_path}")
    else:
        csv_path = sys.argv[1]

    plot_session(csv_path)