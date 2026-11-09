# Cross-Layer Reliability Closure for AI-Assisted ECG Edge Systems

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Vivado](https://img.shields.io/badge/Vivado-2017.4%2B-red.svg)](https://www.xilinx.com/products/design-tools/vivado.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A closed-loop reliability framework integrating **Hardware (BIST/Shadow)**, **Signal Quality Index (SQI)**, and **AI Uncertainty (MC-Dropout)** to eliminate unsafe, overconfident predictions and verify signal recovery under injected hardware and sensor faults in edge ECG monitoring devices.

---

## 📑 Table of Contents
- [Architecture Overview](#architecture-overview)
- [Key Results](#key-results)
- [Repository Structure](#repository-structure)
- [Prerequisites & Installation](#prerequisites--installation)
- [How to Run](#how-to-run)
  - [1. Hardware Layer Simulation (FPGA & Vivado)](#1-hardware-layer-simulation-fpga--vivado)
  - [2. Python Bit-Exact Signature Verification](#2-python-bit-exact-signature-verification)
  - [3. Dataset Preparation & Fault Injection (Phase 2)](#3-dataset-preparation--fault-injection-phase-2)
  - [4. SQI & MC-Dropout Feature Extraction](#4-sqi--mc-dropout-feature-extraction)
  - [5. Multimodal Fusion Evaluation (Phase 3)](#5-multimodal-fusion-evaluation-phase-3)
- [License](#license)

---

## 🏛️ Architecture Overview

Real-world physiological monitoring systems deployed at the edge face compounded failure modes: sensor contact disconnects, baseline wander noise, and transient/permanent silicon hardware degradation. This project proposes a cross-layer reliability closure across three tiers:

1. **Hardware Layer (RTL / FPGA):**
   - Fixed-point 8-tap Finite Impulse Response (FIR) filter in SystemVerilog.
   - Saboteur module injecting stuck-at faults (630 total faults across accumulator, multiplier products, and coefficient registers).
   - Built-In Self-Test (BIST) controller featuring an on-chip Linear Feedback Shift Register (LFSR, 8,192 pseudo-random patterns) and Multiple Input Signature Register (MISR) golden signature comparator.
2. **AI/ML Layer (1D-CNN):**
   - Deep 1D Convolutional Neural Network trained on the MIT-BIH Arrhythmia Database (inter-patient split).
   - Monte-Carlo Dropout (MC-Dropout) sampling to quantify epistemic and predictive uncertainty under noisy or corrupted inputs.
3. **Control & Fusion Layer:**
   - Multi-metric Signal Quality Index (SQI) analysis.
   - Calibrated Gradient-Boosted Fusion model predicting $P(\text{harm})$ and categorizing root causes (Sensor, Hardware, or Physiological) paired with an independent verifier.

```
       +-------------------------------------------------------+
       |                  Raw ECG Lead Signal                  |
       +---------------------------+---------------------------+
                                   |
                +------------------+------------------+
                |                                     |
                v                                     v
   +-------------------------+           +-------------------------+
   | Hardware Tier (FPGA)    |           | Sensing Tier (SQI)      |
   | - 8-Tap FIR Filter      |           | - Skewness & Kurtosis   |
   | - Stuck-at Saboteur     |           | - Baseline Wander / SNR |
   | - LFSR/MISR BIST Check  |           | - Energy Ratios         |
   +------------+------------+           +------------+------------+
                |                                     |
                +------------------+------------------+
                                   |
                                   v
                     +---------------------------+
                     | ML Tier (1D-CNN)          |
                     | - Arrhythmia Detection    |
                     | - MC-Dropout Uncertainty  |
                     +-------------+-------------+
                                   |
                                   v
                     +---------------------------+
                     | Cross-Layer Fusion Engine |
                     | - Predict P(harm)         |
                     | - Calibrated Baselines    |
                     | - Root Cause Isolation    |
                     +---------------------------+
```

---

## 📊 Key Results

- **BIST Hardware Coverage:** 492 / 630 stuck-at faults (**78.1%**) detected in Vivado RTL simulation; adjusted coverage reaches **96.5%** after accounting for functionally redundant faults.
- **Fusion Safety (RQ2):** The calibrated cross-layer fusion model achieves lowest Unsafe-Confident Rate (UCR) with an AUROC of **0.834** and Expected Calibration Error (ECE) of **0.0092**.
- **Complementary Evidence (RQ1):** Hardware BIST reliably captures stuck-at faults ($80\% - 100\%$), while SQI and MC-Dropout uncertainty cover sensor disconnects and noise artifacts.

---

## 📁 Repository Structure

```
├── check.py                        # Standalone script validating BIST coverage against bit-exact model
├── model.py                        # Reference bit-exact Python model of FIR filter & fault injection
├── poster.xpr                      # Xilinx Vivado 2017.4+ Project File
├── poster.srcs/                    # FPGA Hardware Design (RTL & Testbenches)
│   ├── sources_1/new/
│   │   ├── fir_top.sv              # Top-level module integrating FIR core and BIST controller
│   │   ├── fir_core.sv             # 8-tap FIR filter with saboteur fault injection
│   │   └── bist_ctrl.v             # LFSR pattern generator & MISR signature compressor
│   └── sim_1/new/
│       └── tb_bist_campaign.v      # Comprehensive testbench running 630-fault injection campaign
├── py/
│   ├── reliab_phase1/rel/          # Phase 1: Hardware fault modeling & coverage analysis
│   │   ├── bist_py.py              # Bit-exact Python LFSR/MISR signature simulation
│   │   ├── bist_py_coverage.csv    # Fault detection coverage matrix from Python
│   │   ├── compare_rtl_csv.py      # RTL simulation vs Python signature comparator
│   │   ├── analyze_misses.py       # Redundancy & testability analysis for undetected faults
│   │   └── model.py                # FIR and fault injector definition
│   ├── reliab_phase2/rel/          # Phase 2: MIT-BIH dataset generation & fault injection
│   │   ├── make_dataset.py         # Downloads MIT-BIH and creates fault-injected twin datasets
│   │   ├── check_dataset.py        # Dataset verification and integrity check
│   │   ├── build_features.py       # Computes SQI metrics and MC-Dropout uncertainty scores
│   │   ├── evaluate.py             # Baseline evaluation & fusion training
│   │   ├── results/                # Visualizations (RQ1 heatmap, RQ2 risk-coverage)
│   │   └── data/README.md          # Detailed dataset documentation
│   └── reliab_phase3/rel/          # Phase 3: Calibrated fusion, baselines & root cause isolation
│       ├── evaluate.py             # Multi-model evaluation (B0-B4 baselines vs Calibrated Fusion)
│       ├── build_features.py       # Feature pipeline with held-out fault classes
│       └── undetected_analysis.csv # Analysis of safety under unobservable faults
├── requirements.txt                # Python environment dependencies
├── .gitignore                      # Exclusion rules for Vivado builds, datasets, and cache
└── CLEANUP_AND_PUSH_REPORT.md      # Detailed manifest of pushed vs excluded files
```

---

## ⚙️ Prerequisites & Installation

### 1. Hardware Prerequisites
* **Xilinx Vivado Design Suite** (v2017.4 or newer).
* Compatible target device: `xc7vx485tffg1157-1` (Virtex-7) or any Xilinx 7-series FPGA.

### 2. Software Prerequisites
* **Python 3.8+**
* Install required packages:
  ```bash
  pip install -r requirements.txt
  ```

---

## 🚀 How to Run

### 1. Hardware Layer Simulation (FPGA & Vivado)

1. Launch **Xilinx Vivado** and open the project:
   ```bash
   vivado poster.xpr
   ```
2. Run behavioral simulation using the testbench:
   * In Vivado GUI: click **Flow Navigator** -> **Run Simulation** -> **Run Behavioral Simulation**.
   * Or run via Tcl console:
     ```tcl
     launch_simulation -simset sim_1
     run all
     ```
3. The testbench `tb_bist_campaign.v` executes an automated campaign sweeping through 630 stuck-at faults across accumulator, multiplier, and coefficient taps, producing `bist_coverage.csv`.

---

### 2. Python Bit-Exact Signature Verification

To verify that the RTL simulation bit-identically matches the mathematical Python model:
```bash
cd py/reliab_phase1/rel
python bist_py.py
python analyze_misses.py
```
This runs 8,192 LFSR cycles across all 630 fault scenarios in seconds and reports adjusted coverage.

---

### 3. Dataset Preparation & Fault Injection (Phase 2)

The dataset generation script downloads the MIT-BIH Arrhythmia Database via `wfdb`, partitions it into inter-patient splits (DS1 train/val, DS2 test), and creates fault-injected signal windows with corresponding fault-free twin baselines:

```bash
cd py/reliab_phase2/rel

# Option A: Full real dataset generation (~10-20 mins, downloads MIT-BIH recordings)
python make_dataset.py

# Option B: Fast synthetic self-test (no internet required)
python make_dataset.py --synthetic
```

To verify dataset dimensions and fault-distribution integrity:
```bash
python check_dataset.py
```

---

### 4. SQI & MC-Dropout Feature Extraction

Extract signal quality indices (skewness, kurtosis, baseline wander, high-frequency noise) and compute 1D-CNN Monte-Carlo dropout uncertainty estimates:
```bash
python build_features.py
```
This produces `data/features.npz` containing features, predictions, and fault indicators across all train/test splits.

---

### 5. Multimodal Fusion Evaluation (Phase 3)

Train and evaluate the cross-layer fusion model against single-layer baselines (Hardware-only, SQI-only, Uncertainty-only):
```bash
cd py/reliab_phase3/rel
python evaluate.py
```
Outputs:
- **Baseline Comparisons (B0-B4):** Evaluates Unsafe-Confident Rate (UCR), AUROC, and calibration error.
- **RQ1 Heatmap:** Visualizes fault detection coverage across hardware and software paths.
- **RQ2 Risk-Coverage Curves:** Generates coverage vs selective risk plots saved to `results/`.
- **Root Cause Isolation:** Predicts whether an anomaly stems from Sensor (S), Hardware (H), or True Arrhythmia / Physiology (C).

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
