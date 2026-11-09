# Cross-Layer Reliability Closure for AI-Assisted ECG Edge Systems

A closed-loop reliability framework integrating **Hardware (BIST/Shadow)**, **Signal Quality Index (SQI)**, and **AI Uncertainty (MC-Dropout)** to eliminate unsafe overconfident predictions and verify signal recovery under injected hardware and sensor faults.

---

## 📌 Project Overview
* **Hardware Layer:** RTL simulation of fixed-point FIR filter with internal saboteur stuck-at fault injection (630 faults) verified via LFSR/MISR BIST (8,192 patterns).
* **AI/ML Layer:** 1D-CNN trained on MIT-BIH Arrhythmia Database (inter-patient split) with MC-Dropout uncertainty estimation.
* **Control Layer:** Gradient-boosted fusion model predicting P(harm) and root causes (Sensor, Hardware, Physiological) paired with an independent verifier.

---

## 📊 Key Results
- **BIST Hardware Coverage:** 492 / 630 stuck-at faults (78.1%) detected in Vivado RTL simulation.
- **Fusion Safety (RQ2):** Fused reliability model achieves lowest Unsafe-Confident Rate (UCR) with an AUROC of **0.834** and ECE of **0.0092**.
- **Complementary Evidence (RQ1):** Hardware paths catch stuck-at faults (80–100%), while SQI/Uncertainty cover sensor dropouts and noise artifacts.

---

## 🛠️ Repository Structure
```text
├── model.py                # Bit-exact Python filter & BIST logic
├── bist_py.py              # RTL vs Python signature validation
├── make_dataset.py         # MIT-BIH dataset loading & ground-truth fault injection
├── check_dataset.py        # Dataset integrity & fault verification script
├── build_features.py       # SQI feature calculation & MC-Dropout uncertainty scoring
└── evaluate.py             # Baseline evaluation, fusion training, and metrics logger
## 🚀 How to Run

1. **Install Dependencies:**
   ```bash
   pip install numpy pandas torch xgboost scikit-learn wfdb matplotlib
   python make_dataset.py
python check_dataset.py
python build_features.py
python evaluate.py