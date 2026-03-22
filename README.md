# Maya-OS
### An Affective Spiking Neural Network as a Conversational OS Arbitration Layer

**Venkatesh Swaminathan** — Nexus Learning Labs / BITS Pilani, Bengaluru, India  
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19160123.svg)](https://doi.org/10.5281/zenodo.19160122)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-lightgrey.svg)](https://microsoft.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> *"The OS does not follow rules. It follows its own emotional state."*

---

## What This Is

Maya-OS is the first implementation of an affective SNN deployed as a live, conversational operating system arbitration layer. Four LIF neurons — **Bhaya** (fear), **Vairagya** (wisdom), **Shraddha** (trust), **Spanda** (aliveness) — read your machine's CPU, RAM, and process state every 500ms. Their emergent voltage dynamics govern whether processes are protected, monitored, suspended, or killed.

You talk to it. It responds by acting on your OS.

This is the second paper in the Maya research series. The foundational SNN architecture is from:  
**Swaminathan, V. (2026). Nociceptive Metaplasticity and Graceful Decay in SNNs.**  
→ https://doi.org/10.5281/zenodo.19151562  
→ https://github.com/venky2099/Maya-Nexus-Core

---

## Key Results

Across 5 experimental sessions (133 ticks, Windows 11, dry-run mode):

| Finding | Result |
|---|---|
| Autonomous threat accumulation | Bhaya climbed 0.09 → 0.641 from live CPU/RAM signals alone |
| Emergent safety primitive | Shraddha blocked aggressive action in 100% of threshold crossings |
| LIF action potential confirmed | bhaya_fired=1, voltage reset to 0.000, multiple sessions |
| Intent-driven modulation | Conversational input directly altered neuronal voltage |
| Homeostatic recovery | Trust rebuilt autonomously from 0.000 → 0.500 in 4 ticks post-suppression |

**Action distribution across all sessions:**

```
PROTECT  52 / 133  (39.1%)
ALERT    41 / 133  (30.8%)
IDLE     19 / 133  (14.3%)
SUSPEND   0 / 133  (emergent safety — Shraddha dominant)
KILL      0 / 133  (emergent safety — Shraddha dominant)
CLEANUP   0 / 133
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  LAYER 5  Voice / Text Interface             │
│           You speak. Maya listens.           │
├─────────────────────────────────────────────┤
│  LAYER 4  Intent Parser                      │
│           Words → voltage injection signals  │
├─────────────────────────────────────────────┤
│  LAYER 3  Affective Engine          ← BRAIN  │
│           4 LIF neurons, 4×4 weight matrix   │
│           reads CPU / RAM / processes        │
├─────────────────────────────────────────────┤
│  LAYER 2  OS Arbiter                         │
│           voltage vector → action class      │
│           no hardcoded rules                 │
├─────────────────────────────────────────────┤
│  LAYER 1  Syscall Executor                   │
│           psutil · pywin32 · subprocess      │
│           full safety contract enforced      │
└─────────────────────────────────────────────┘
```

### Neuron Design

| Neuron | Sanskrit | τ | Threshold | OS Role |
|--------|----------|---|-----------|---------|
| Fear/Threat | Bhaya | 3 | 0.65 | CPU %, RAM %, unknown processes |
| Wisdom/Release | Vairagya | 20 | 0.50 | Idle state, RAM recovery, time of day |
| Trust | Shraddha | 10 | 0.55 | Known processes, focus intent |
| Aliveness | Spanda | 5 | 0.60 | Time-of-day sinusoid, activity level |

---

## Quickstart

```bash
git clone https://github.com/venky2099/Maya-OS
cd Maya-OS
pip install -r requirements.txt
python -m MayaOS.maya_os
```

Maya runs in **dry-run mode by default** — no real OS actions. To enable live execution:

```bash
python -m MayaOS.maya_os --live
```

### Commands

```
hello          → Spanda + Shraddha boost
focus          → Shraddha boost, Bhaya dampened
stress test    → Forced Bhaya spike (demonstrates threat response)
calm down      → Vairagya boost
clean up       → Vairagya dominant, triggers CLEANUP pass
status         → Print live voltage state
quit           → Graceful shutdown
```

---

## Reproduce the Paper's Results

```bash
# Run a session
python -m MayaOS.maya_os

# Generate figures from latest CSV
python -m MayaOS.analysis.plot_session

# Generate figures from a specific session
python -m MayaOS.analysis.plot_session MayaOS/logs/maya_os_20260322_120245.csv
```

Session CSVs from the paper's five experimental runs are archived in `MayaOS/logs/`.  
Each CSV contains 20 columns per tick as specified in `MayaOS/logger/decision_log.py`.

---

## Project Structure

```
Maya-OS/
├── MayaOS/
│   ├── core/
│   │   ├── affective_engine.py   # LIF neurons, weight matrix, system signal integration
│   │   ├── intent_parser.py      # natural language → voltage injection
│   │   ├── os_arbiter.py         # voltage vector → action class
│   │   └── syscall_executor.py   # OS-level execution with safety contract
│   ├── interface/                # voice I/O (Phase 2)
│   ├── logger/
│   │   └── decision_log.py       # 20-column CSV per tick
│   ├── analysis/
│   │   └── plot_session.py       # publication-quality figure generation
│   ├── logs/                     # experimental session CSVs
│   └── config/
│       └── thresholds.yaml       # tunable voltage thresholds
├── maya_os.py                    # main entry point
├── requirements.txt
└── README.md
```

---

## Citation

If you use Maya-OS in your research:

```bibtex
@misc{swaminathan2026mayaos,
  author    = {Swaminathan, Venkatesh},
  title     = {Maya-OS: An Affective Spiking Neural Network as a
               Conversational Operating System Arbitration Layer},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19160122},
  url       = {https://doi.org/10.5281/zenodo.19160122}
}
```

### Prior Work (foundational architecture)

```bibtex
@misc{swaminathan2026nociceptive,
  author    = {Swaminathan, Venkatesh},
  title     = {Nociceptive Metaplasticity and Graceful Decay in Spiking
               Neural Networks: Towards Survival-Driven Continual Learning},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19151562},
  url       = {https://doi.org/10.5281/zenodo.19151562}
}
```

---

## Safety Note

Maya-OS includes a multi-layer safety contract in `syscall_executor.py`:
- Permanent protected process list (all Windows system processes)
- KILL intensity gate (intensity > 0.70 required before any termination)
- Dry-run mode default — no real actions without explicit `--live` flag

All experimental results in the paper were collected in dry-run mode.

---

*Nexus Learning Labs · Bengaluru, India · 2026*
