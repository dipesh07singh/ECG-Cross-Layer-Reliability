import numpy as np, pandas as pd
from model import fir
d = np.load("data/dataset.npz")
print("clean windows per split:\n", pd.Series(d["base_split"]).value_counts().to_string())
print("abnormal fraction per split:\n", pd.Series(d["base_y"]).groupby(d["base_split"]).mean().round(2).to_string())
cls = d["classes"][d["f_cls"]]; sp = d["base_split"][d["f_base"]]
print("fault windows (class x severity):\n", pd.crosstab(cls, d["f_sev"]).to_string())
# integrity: clean twin == fault-free FIR of its raw window; faulty out == FIR(raw_in, fault)
bad = 0
for j in np.random.default_rng(1).choice(len(d["f_raw"]), 200, replace=False):
    f = tuple(int(v) for v in d["f_fault"][j]); f = None if f[0] < 0 else f
    bad += not np.array_equal(fir(d["f_raw"][j].astype(np.int64), f), d["f_out"][j])
    b = d["f_base"][j]; bad += not np.array_equal(fir(d["base_raw"][b].astype(np.int64)), d["base_out"][b])
print("integrity check mismatches (must be 0):", bad)
# does the fault actually change the output?
chg = pd.Series([not np.array_equal(d["f_out"][j], d["base_out"][d["f_base"][j]]) for j in range(len(d["f_out"]))]).groupby(cls).mean().round(2)
print("fraction of windows whose output differs from the twin:\n", chg.to_string())
