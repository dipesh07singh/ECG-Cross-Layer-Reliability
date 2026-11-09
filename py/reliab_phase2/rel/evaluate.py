"""Phase 3b: SQI model, baselines B0-B4, calibrated fusion F, RQ1 heatmap, RQ2 risk-coverage, root cause.
Run: python evaluate.py      (needs data/features.npz)
"""
import numpy as np, pandas as pd, os, itertools
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, confusion_matrix
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
os.makedirs("results", exist_ok=True); rng = np.random.default_rng(0)
f = np.load("data/features.npz"); CL = list(f["classes"]); N = len(f["y"])
cls = np.array(CL)[f["cls"]]; split = f["split"]; y = f["y"]; p = f["p"]
HELD = ["S5", "C2"]                                   # held-out fault classes (never seen by SQI / fusion training)
pred = (p >= 0.5).astype(int); twin = pred[f["base_idx"]]
harm = ((twin == y) & (pred != y)).astype(int)        # fault-free twin right, faulty output wrong
print("harm rate overall %.3f | per class:" % harm.mean()); print(pd.Series(harm).groupby(cls).mean().round(3).to_string())

hwflag = np.maximum(f["bist"], (f["shadow"] > 0).astype(int)).astype(float)
X = np.c_[f["sqi"], p, f["ent"], f["var"], f["shadow"], f["bist"], f["t_since"]]
seen = ~np.isin(cls, HELD); is_tr, is_va, is_te = split == "train", split == "val", split == "test"

# SQI model: signal-quality only -> trained to flag sensor/signal corruption (S*, C*), never sees hardware-only faults as "bad"
sig_bad = np.array([c[0] in "SC" for c in cls]).astype(int)
sqi_m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced"))
sqi_m.fit(f["sqi"][is_tr & seen], sig_bad[is_tr & seen]); sqi_score = sqi_m.predict_proba(f["sqi"])[:, 1]

# Fusion F: gradient-boosted P(harm), isotonic calibration on validation patients
gb = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=0).fit(
    np.c_[X, sqi_score][is_tr & seen], harm[is_tr & seen])
raw_va = gb.predict_proba(np.c_[X, sqi_score][is_va & seen])[:, 1]
iso = IsotonicRegression(out_of_bounds="clip").fit(raw_va, harm[is_va & seen])
F_score = iso.predict(gb.predict_proba(np.c_[X, sqi_score])[:, 1])

# B4: naive weighted score, weights tuned on validation (strong baseline)
def rc_area(score, h, grid=np.linspace(0.5, 1, 11)):
    o = np.argsort(score + 1e-9*rng.random(len(score))); hs = h[o]; cs = np.cumsum(hs)
    return np.mean([cs[int(c*len(h))-1]/int(c*len(h)) for c in grid])
ent_n = f["ent"]/ (np.log(2)+1e-9); best = (9, None)
for w in itertools.product(np.linspace(0, 1, 6), repeat=3):
    if abs(sum(w)-1) > 1e-6: continue
    s = w[0]*sqi_score + w[1]*hwflag + w[2]*ent_n; a = rc_area(s[is_va & seen], harm[is_va & seen])
    if a < best[0]: best = (a, w)
print("B4 weights (sqi, hw, uncertainty):", best[1]); B4 = best[1][0]*sqi_score+best[1][1]*hwflag+best[1][2]*ent_n
SYS = {"B0 raw CNN": np.zeros(N), "B1 SQI gate": sqi_score, "B2 hardware gate": hwflag, "B3 CNN uncertainty": ent_n,
       "B4 weighted score": B4, "F fusion": F_score}

def ucr(score, h, cov):
    o = np.argsort(score + 1e-9*rng.random(len(score))); k = max(int(cov*len(h)), 1); return h[o][:k].mean()
def cluster_ci(score, h, recs, cov, B=200):
    ur = np.unique(recs); idx = {r: np.flatnonzero(recs == r) for r in ur}; v = []
    for _ in range(B):
        s = np.concatenate([idx[r] for r in rng.choice(ur, len(ur))]); v.append(ucr(score[s], h[s], cov))
    return np.percentile(v, [2.5, 97.5])

rows = []
sets = {"in-distribution (seen fault classes + clean)": is_te & seen,
        "held-out fault classes (S5, C2) + clean": is_te & (~seen | (cls == "clean"))}
for name, m in sets.items():
    for s, sc in SYS.items():
        for cov in [0.8, 0.9]:
            lo, hi = cluster_ci(sc[m], harm[m], f["rec"][m], cov)
            rows.append(dict(setting=name, system=s, coverage=cov, UCR=round(ucr(sc[m], harm[m], cov), 4),
                             CI_lo=round(lo, 4), CI_hi=round(hi, 4),
                             AUROC=round(roc_auc_score(harm[m], sc[m]), 3) if s != "B0 raw CNN" else np.nan))
R = pd.DataFrame(rows); R.to_csv("results/ucr_table.csv", index=False)
print("\nUnsafe-confident rate (lower is better), patient-level bootstrap 95% CI:"); print(R.to_string(index=False))

# calibration of F on test (equal-mass bins)
m = is_te & seen; q = np.array_split(np.argsort(F_score[m]), 10)
ece = sum(len(b)/m.sum()*abs(F_score[m][b].mean()-harm[m][b].mean()) for b in q)
print("\nECE of fused P(harm), in-distribution test: %.4f" % ece)

# risk-coverage curves
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for a, (name, m) in zip(ax, sets.items()):
    for s, sc in SYS.items():
        cv = np.linspace(0.3, 1, 36); a.plot(cv, [ucr(sc[m], harm[m], c) for c in cv], label=s, lw=2.2 if s.startswith("F") else 1.2)
    a.set_title(name, fontsize=9); a.set_xlabel("coverage (fraction served)"); a.set_ylabel("unsafe-confident rate")
ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig("results/risk_coverage.png", dpi=200); plt.close()

# RQ1: detector x fault-class detection rate (harmful windows flagged; continuous detectors set to flag 5% of clean test windows)
clean_te = is_te & (cls == "clean"); dets = {"BIST": f["bist"].astype(float), "Shadow path": (f["shadow"] > 0).astype(float),
        "SQI": sqi_score, "CNN uncertainty": ent_n}
H = {}
for dn, sc in dets.items():
    thr = np.quantile(sc[clean_te], 0.95) if len(np.unique(sc[clean_te])) > 1 else 0.5
    flag = sc > thr if len(np.unique(sc[clean_te])) > 1 else sc > 0
    H[dn] = {c: flag[is_te & (cls == c) & (harm == 1)].mean() if (is_te & (cls == c) & (harm == 1)).sum() > 0 else np.nan
             for c in CL if c != "clean"}
HM = pd.DataFrame(H).round(2); HM.to_csv("results/rq1_detection_heatmap.csv"); print("\nRQ1 detection rate on harmful test windows:"); print(HM.to_string())
print("(harmful windows per class:", {c: int((is_te & (cls == c) & (harm == 1)).sum()) for c in CL if c != "clean"}, ")")
fig, a = plt.subplots(figsize=(6.5, 4.5)); im = a.imshow(HM.values, vmin=0, vmax=1, cmap="viridis")
a.set_xticks(range(HM.shape[1])); a.set_xticklabels(HM.columns, rotation=30, ha="right"); a.set_yticks(range(HM.shape[0])); a.set_yticklabels(HM.index)
for i in range(HM.shape[0]):
    for j in range(HM.shape[1]): a.text(j, i, "" if np.isnan(HM.values[i, j]) else f"{HM.values[i, j]:.2f}", ha="center", va="center", color="w", fontsize=8)
plt.colorbar(im, label="detection rate"); plt.tight_layout(); plt.savefig("results/rq1_heatmap.png", dpi=200); plt.close()

# root cause: Sensor / Hardware / Multiple / None
cause = np.array(["None" if c == "clean" else "Sensor" if c[0] == "S" else "Hardware" if c == "H1" or c == "H2" else "Multiple" for c in cls])
rc = HistGradientBoostingClassifier(max_iter=150, random_state=0).fit(np.c_[X, sqi_score][is_tr & seen], cause[is_tr & seen])
mt = is_te & seen; pc = rc.predict(np.c_[X, sqi_score][mt]); lab = ["None", "Sensor", "Hardware", "Multiple"]
print("\nRoot-cause accuracy (in-distribution test): %.3f" % (pc == cause[mt]).mean())
print(pd.DataFrame(confusion_matrix(cause[mt], pc, labels=lab), index=lab, columns=lab).to_string())
print("\nsaved results/ucr_table.csv, risk_coverage.png, rq1_detection_heatmap.csv, rq1_heatmap.png")
