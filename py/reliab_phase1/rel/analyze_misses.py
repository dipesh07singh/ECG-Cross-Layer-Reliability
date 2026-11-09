import numpy as np, pandas as pd
from model import fir
c = pd.read_csv("bist_py_coverage.csv")
rng = np.random.default_rng(0)
x = rng.integers(-2048, 2048, 300000)          # full-range random input
# ECG-like range: MIT-BIH 11-bit, centred -> roughly +-1024
xe = rng.integers(-1024, 1024, 300000)
ref, refe = fir(x), fir(xe)
rows=[]
for r in c[c.detected==0].itertuples():
    f=(r.kind,r.tap,r.bit,r.val)
    rows.append((r.kind,r.tap,r.bit,r.val,
                 not np.array_equal(fir(x,f),ref), not np.array_equal(fir(xe,f),refe)))
m = pd.DataFrame(rows, columns="kind tap bit val changes_fullrange changes_ecgrange".split())
m.to_csv("undetected_analysis.csv", index=False)
print("total", len(c), "detected", c.detected.sum(), "undetected", len(m))
print("undetected: output never changes (redundant, full 12-bit range):", (~m.changes_fullrange).sum())
print("undetected: output changes on full-range inputs (real BIST misses):", m.changes_fullrange.sum())
print("  of which never change on ECG-range inputs:", (m.changes_fullrange & ~m.changes_ecgrange).sum())
print(m.groupby("kind")[["changes_fullrange"]].agg(["sum","count"]))
red = (~m.changes_fullrange).sum(); det = c.detected.sum()
print("raw coverage %.1f%%, coverage of non-redundant faults %.1f%%" % (100*det/len(c), 100*det/(len(c)-red)))
print(m[m.changes_fullrange].groupby(["kind","bit"]).size())
