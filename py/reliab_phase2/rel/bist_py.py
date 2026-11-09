import numpy as np
from model import fir
def lfsr_seq(n, step=12, seed=0xACE1):
    s = seed; out = []
    for _ in range(n):
        out.append(s)
        for _ in range(step):
            s = ((s << 1) & 0xFFFF) | (((s>>15)^(s>>14)^(s>>12)^(s>>3)) & 1)
    return out
def to_s12(v): v &= 0xFFF; return v-4096 if v>=2048 else v
def signature(fault, N=8192, WARM=12, step=12):
    L = lfsr_seq(WARM+N, step)
    x = np.array([to_s12(v) for v in L])
    y = fir(x, fault)                       # y_comb[j] = FIR output using x up to j
    m = 0
    for k in range(WARM, WARM+N):
        yk = int(y[k-2]) & 0xFFFF           # registered output, 2-cycle alignment
        fb = ((m>>15)^(m>>14)^(m>>12)^(m>>3)) & 1
        m = (((m<<1)&0xFFFF)|fb) ^ yk
    return m
if __name__ == "__main__":
    import sys, pandas as pd
    N = int(sys.argv[1]) if len(sys.argv)>1 else 8192
    step = int(sys.argv[2]) if len(sys.argv)>2 else 12
    g = signature(None, N, step=step); print("golden = %04x" % g)
    rows=[]
    for kind in range(3):
        for tap in range(1 if kind==0 else 8):
            for b in range(27 if kind==0 else (24 if kind==1 else 12)):
                for v in (0,1):
                    s = signature((kind,tap,b,v), N, step=step)
                    rows.append((kind,tap,b,v,int(s!=g),'%04x'%s))
    df = pd.DataFrame(rows, columns="kind tap bit val detected sig".split())
    df.to_csv("bist_py_coverage.csv", index=False)
    print("detected", df.detected.sum(), "/", len(df))
