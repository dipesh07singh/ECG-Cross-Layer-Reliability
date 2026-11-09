# Repository Cleanup, Exclusion & Push Manifest

This document provides a complete audit and transparent record of all actions taken to clean, configure, and push the **ECG Cross-Layer Reliability Closure** project repository to GitHub: `https://github.com/dipesh07singh/ECG-Cross-Layer-Reliability`.

---

## 1. Executive Summary

| Metric | Before Cleanup | After Cleanup / Tracking | Reduction |
| :--- | :--- | :--- | :--- |
| **Total Disk Size** | ~2.29 GB | ~0.4 MB tracked / ~573 MB local | **> 99.9% tracked payload reduction** |
| **Pushed Payload** | N/A (Failed GitHub 100MB limit) | **< 1 MB across logical commits** | 100% compliant with GitHub limits |
| **Sensitive Info Exposed** | 0 secrets found | 0 secrets found | Verified secure |
| **Source Code Altered** | None | None | **Strict zero code modification enforced** |

---

## 2. Cleaned / Deleted Files & Folders

The following temporary, redundant, or orphaned files were safely removed from the local workspace:

| Path Cleaned / Deleted | Size | Category | Reason for Deletion |
| :--- | :--- | :--- | :--- |
| `poster.sim/` | **1,521 MB (1.52 GB)** | Vivado simulation artifacts | Ephemeral simulation run directory containing waveform databases (`tb_bist_campaign_behav.wdb`: 106.9 MB), runtime xsim dumps (two files @ 707 MB each), simulation executable (`xsimk.exe`), `.c`, `.sdb`, `.log`, and `.jou` files. Automatically regenerated whenever Vivado simulation is run. |
| `py/reliab_phase2/rel/.git/` | **198.2 MB** | Orphaned nested Git repository | Old internal repository folder tracking previous commits of 344MB `.npz` files to an alternate repository (`Dips-bt25ece02-alt/ECG-Cross-Layer-Reliability`). Removing it prevents Git submodule conflicts and history bloat. |
| `py/reliab_phase1.zip` | 6.4 KB | Duplicate archive | Redundant zip archive of extracted folder `py/reliab_phase1`. |
| `py/reliab_phase2.zip` | 10.3 KB | Duplicate archive | Redundant zip archive of extracted folder `py/reliab_phase2`. |
| `py/reliab_phase3.zip` | 16.7 KB | Duplicate archive | Redundant zip archive of extracted folder `py/reliab_phase3`. |
| `**/__pycache__/` | ~4 KB | Python bytecode | Temporary `.pyc` compiled files (`model.cpython-314.pyc`). |

---

## 3. Files Safely Ignored in `.gitignore` (Retained Locally, Not Pushed)

The following heavy assets and runtime artifacts are retained locally on disk but explicitly ignored from Git tracking:

| Ignored Path | Size | Category | Reason & Reproduction |
| :--- | :--- | :--- | :--- |
| `py/reliab_phase2/rel/data/dataset.npz` | **328.9 MB** | Heavy Generated Dataset | Exceeds GitHub's 100MB file limit. Can be generated locally at any time using `python make_dataset.py`. |
| `py/reliab_phase2/rel/data/cache/*.npz` | **234.6 MB** | Raw Signal Cache | 45 cached MIT-BIH recordings downloaded via `wfdb`. Auto-downloaded and cached on demand by `make_dataset.py`. |
| `py/reliab_phase2/rel/data/features.npz` | **9.1 MB** | Feature Matrix | Derived feature matrix produced on demand by running `python build_features.py`. |
| `poster.cache/` | 317 Bytes | Vivado Project Cache | Temporary GUI cache used by Xilinx Vivado. |
| `poster.hw/` | 290 Bytes | Vivado Hardware State | Hardware manager state file. |
| `poster.ip_user_files/` | 130 Bytes | Vivado IP Placeholder | Standard IP configuration directory. |

---

## 4. Confirmed List of Files Pushed to GitHub

All vital project assets, source codes, configuration files, testbenches, analysis scripts, result figures, and documentation have been safely committed and pushed.

### A. Repository Configuration & Documentation
- `.gitignore`: Comprehensive exclusion rules for Vivado builds, datasets, virtualenvs, and secrets.
- `requirements.txt`: Python package dependencies.
- `README.md`: Comprehensive project overview, architecture diagram, Vivado setup, and how-to-run guide.
- `CLEANUP_AND_PUSH_REPORT.md`: This audit manifest.

### B. FPGA Hardware Design (RTL & Testbenches)
- `poster.xpr`: Primary Xilinx Vivado project definition file.
- `poster.srcs/sources_1/new/fir_top.sv`: Top-level module integrating FIR core with BIST.
- `poster.srcs/sources_1/new/fir_core.sv`: 8-tap FIR filter with saboteur fault injection.
- `poster.srcs/sources_1/new/bist_ctrl.v`: LFSR pseudo-random generator & MISR signature compressor.
- `poster.srcs/sim_1/new/tb_bist_campaign.v`: Verilog testbench executing 630-fault injection campaign.
- `check.py`: Quick verification script testing fault coverage against the bit-exact model.
- `model.py`: Root bit-exact Python model of FIR filter and fault injection.

### C. Phase 1: Hardware Fault Modeling & Python Verification
- `py/reliab_phase1/rel/model.py`: Reference FIR filter and fault model.
- `py/reliab_phase1/rel/bist_py.py`: Python LFSR/MISR simulation and signature calculation.
- `py/reliab_phase1/rel/compare_rtl_csv.py`: Comparator between RTL simulation and Python signatures.
- `py/reliab_phase1/rel/analyze_misses.py`: Testability and redundancy analyzer.
- `py/reliab_phase1/rel/bist_py_coverage.csv`: Fault detection coverage log.
- `py/reliab_phase1/rel/undetected_analysis.csv`: Detailed log of undetected fault taps and bits.

### D. Phase 2: MIT-BIH Dataset & Fault Twin Pipeline
- `py/reliab_phase2/rel/model.py`: Phase 2 filter model.
- `py/reliab_phase2/rel/make_dataset.py`: Full dataset generation and fault-injected twin creation.
- `py/reliab_phase2/rel/check_dataset.py`: Dataset integrity and verification script.
- `py/reliab_phase2/rel/build_features.py`: SQI calculation and MC-Dropout uncertainty scoring.
- `py/reliab_phase2/rel/evaluate.py`: Baseline evaluation and fusion model training.
- `py/reliab_phase2/rel/bist_py.py`: Phase 2 signature verification script.
- `py/reliab_phase2/rel/compare_rtl_csv.py`: RTL vs Python CSV comparator.
- `py/reliab_phase2/rel/analyze_misses.py`: Miss analysis script.
- `py/reliab_phase2/rel/bist_py_coverage.csv`: Phase 2 BIST coverage log.
- `py/reliab_phase2/rel/undetected_analysis.csv`: Phase 2 undetected faults log.
- `py/reliab_phase2/rel/data/README.md`: Dataset and experiment overview.
- `py/reliab_phase2/rel/results/risk_coverage.png`: RQ2 risk vs coverage plot.
- `py/reliab_phase2/rel/results/rq1_heatmap.png`: RQ1 detection coverage heatmap.
- `py/reliab_phase2/rel/results/rq1_detection_heatmap.csv`: Coverage matrix.
- `py/reliab_phase2/rel/results/ucr_table.csv`: Unsafe-Confident Rate (UCR) benchmark table.

### E. Phase 3: Calibrated Fusion & Multi-Layer Evaluation
- `py/reliab_phase3/rel/model.py`: Phase 3 filter model.
- `py/reliab_phase3/rel/make_dataset.py`: Dataset script with held-out fault distributions.
- `py/reliab_phase3/rel/check_dataset.py`: Phase 3 dataset check script.
- `py/reliab_phase3/rel/build_features.py`: Feature builder with held-out classes.
- `py/reliab_phase3/rel/evaluate.py`: Final cross-layer fusion evaluation against B0-B4 baselines.
- `py/reliab_phase3/rel/bist_py.py`: BIST simulation script.
- `py/reliab_phase3/rel/compare_rtl_csv.py`: RTL vs Python CSV comparator.
- `py/reliab_phase3/rel/analyze_misses.py`: Miss analysis script.
- `py/reliab_phase3/rel/bist_py_coverage.csv`: BIST coverage log.
- `py/reliab_phase3/rel/undetected_analysis.csv`: Phase 3 undetected faults log.

---

## 5. Security & Sensitive Data Verification

Prior to pushing, an automated security audit verified:
- [x] No `.env` or configuration files containing passwords or secrets.
- [x] No AWS credentials, GCP service accounts, or Azure tokens.
- [x] No private SSH keys (`id_rsa`, `*.pem`) or GitHub personal access tokens (`ghp_*`).
- [x] All credential patterns strictly guarded in `.gitignore`.

---

## 6. Zero Code Modification Assurance

- [x] All Verilog and SystemVerilog files in `poster.srcs/` remain 100% unaltered.
- [x] Vivado project file `poster.xpr` remains 100% unaltered.
- [x] All Python scripts in `py/reliab_phase1/`, `py/reliab_phase2/`, and `py/reliab_phase3/` remain 100% unaltered.
- [x] All experimental CSV metrics, results, and PNG figures remain 100% unaltered.
