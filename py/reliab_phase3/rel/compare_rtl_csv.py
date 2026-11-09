# usage: python compare_rtl_csv.py "E:/poster/.../bist_coverage.csv"   (the CSV written by Vivado, 8192-pattern run)
import sys, pandas as pd
r = pd.read_csv(sys.argv[1]); r["sig"] = r["sig"].astype(str).str.lower().str.zfill(4)
p = pd.read_csv("bist_py_coverage.csv"); p["sig"] = p["sig"].astype(str).str.lower().str.zfill(4)
m = r.merge(p, on=["kind","tap","bit","val"], suffixes=("_rtl","_py"))
bad = m[m.sig_rtl != m.sig_py]
print(len(m), "faults compared,", len(bad), "signature mismatches")
