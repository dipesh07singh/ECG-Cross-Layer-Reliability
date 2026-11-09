import numpy as np, pandas as pd
from model import fir

CSV = r"E:/poster/bist_coverage.csv"   # <-- apni CSV ka asli path daalo

c = pd.read_csv(CSV)
print("Coverage by kind (0=acc, 1=product, 2=coef):")
print(c.groupby("kind").detected.agg(["sum", "count"]))

rng = np.random.default_rng(0)
x = rng.integers(-2048, 2048, 200000)
ref = fir(x)

miss = c[c.detected == 0]
real, redundant = 0, 0
for r in miss.itertuples():
    out = fir(x, (int(r.kind), int(r.tap), int(r.bit), int(r.val)))
    if np.array_equal(out, ref): redundant += 1
    else: real += 1

det = int(c.detected.sum()); tot = len(c)
print(f"\nDetected: {det}/{tot} = {100*det/tot:.1f}%")
print(f"Undetected but redundant (output kabhi nahi badalta): {redundant}")
print(f"Undetected and real misses: {real}")
testable = tot - redundant
print(f"Adjusted coverage: {det}/{testable} = {100*det/testable:.1f}%")