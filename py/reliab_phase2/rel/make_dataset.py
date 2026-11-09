"""Phase 2: MIT-BIH -> windows -> injected faults with fault-free twins.
Run:  python make_dataset.py            (real data, needs internet, ~10-20 min first time)
      python make_dataset.py --synthetic   (quick self-test, no internet)
"""
import numpy as np, pandas as pd, argparse, os
from model import fir

FS, WIN = 360, 1800                      # 5 s windows
DS1 = [101,106,108,109,112,114,115,116,118,119,122,124,201,203,205,207,208,209,215,220,223,230]
DS2 = [100,103,105,111,113,117,121,123,200,202,210,212,213,214,219,221,222,228,231,232,233,234]
VAL = [106,118,205,230]                  # validation patients, taken out of DS1
NORMAL = set("NLRej"); ABN = set("AaJSVEFfQ/")
CLASSES = ["S1","S2","S3","S4","S5","S6","H1","H2","C1","C2"]
SNR = [12, 6, 0]

def clip12(v): return np.clip(np.rint(v), -2048, 2047).astype(np.int64)
def pw(x): return float(np.var(x)) + 1e-9

# ---------------- data loading ----------------
def load_real(rec, cache):
    f = os.path.join(cache, f"{rec}.npz")
    if os.path.exists(f):
        d = np.load(f); return d["x"], d["s"], d["a"]
    import wfdb
    rd = wfdb.rdrecord(str(rec), pn_dir="mitdb", physical=False)
    if "MLII" not in rd.sig_name: return None
    ch = rd.sig_name.index("MLII")
    x = (rd.d_signal[:, ch] - rd.baseline[ch]).astype(np.int64)
    ann = wfdb.rdann(str(rec), "atr", pn_dir="mitdb")
    s, a = [], []
    for smp, sym in zip(ann.sample, ann.symbol):
        if sym in NORMAL: s.append(smp); a.append(0)
        elif sym in ABN:  s.append(smp); a.append(1)
    s, a = np.array(s), np.array(a)
    np.savez(f, x=x, s=s, a=a); return x, s, a

def load_noise(cache):
    f = os.path.join(cache, "nstdb.npz")
    if os.path.exists(f):
        d = np.load(f); return {k: d[k] for k in d.files}
    import wfdb
    pool = {}
    for n in ["bw", "em", "ma"]:
        r = wfdb.rdrecord(n, pn_dir="nstdb", physical=True)
        pool[n] = r.p_signal[:, 0].astype(float)
    np.savez(f, **pool); return pool

def synthetic(seed):
    rng = np.random.default_rng(seed); n = FS*60*3
    x = rng.normal(0, 8, n); s, a = [], []
    t = 200
    while t < n-200:
        ab = int(rng.random() < 0.25); amp = 700 if not ab else 1000
        w = 6 if not ab else 14
        k = np.arange(-40, 40); x[t-40:t+40] += amp*np.exp(-(k/w)**2)
        s.append(t); a.append(ab); t += int(rng.integers(220, 380))
    return np.clip(np.rint(x), -2048, 2047).astype(np.int64), np.array(s), np.array(a)

# ---------------- injectors ----------------
def s1(x, sev, rng, _):
    d = int([0.5, 1, 2][sev]*FS); st = int(rng.integers(0, WIN-d)); y = x.copy(); y[st:st+d] = y[st]; return y
def s2(x, sev, rng, _):
    p = np.abs(x).max()*[0.8, 0.6, 0.4][sev]; return np.clip(x, -p, p)
def s3(x, sev, rng, _):
    return clip12(x + rng.normal(0, np.sqrt(pw(x)/10**(SNR[sev]/10)), len(x)))
def s4(x, sev, rng, noise):
    k = list(noise)[int(rng.integers(len(noise)))]; z = noise[k]
    st = int(rng.integers(0, len(z)-WIN)); seg = z[st:st+WIN] - z[st:st+WIN].mean()
    seg = seg/(seg.std()+1e-9)*np.sqrt(pw(x)/10**(SNR[sev]/10)); return clip12(x + seg)
def s5(x, sev, rng, _):
    return clip12(x*(1 + rng.choice([-1, 1])*[0.2, 0.4, 0.6][sev]))
def s6(x, sev, rng, _):
    return clip12(x + rng.choice([-1, 1])*[0.1, 0.3, 0.6][sev]*np.abs(x).max())
SENSOR = {"S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6}

def hw_table():
    c = pd.read_csv("bist_py_coverage.csv"); c = c[c.detected == 1]   # output-observable faults only
    def sev(r):
        if r.kind == 0: return 0 if r.bit <= 14 else (1 if r.bit <= 19 else 2)
        if r.kind == 1: return 0 if r.bit <= 12 else (1 if r.bit <= 17 else 2)
        return 0 if r.bit <= 3 else (1 if r.bit <= 6 else 2)
    c = c.assign(sev=c.apply(sev, axis=1)); return c
def pick_hw(tab, group, sev, rng):
    t = tab[(tab.kind.isin([0, 1]) if group == "H1" else tab.kind == 2) & (tab.sev == sev)]
    r = t.iloc[int(rng.integers(len(t)))]; return (int(r.kind), int(r.tap), int(r.bit), int(r.val))

def make_variant(x, cls, sev, rng, noise, tab):
    fault = None
    if cls in SENSOR: x = SENSOR[cls](x, sev, rng, noise)
    elif cls == "H1": fault = pick_hw(tab, "H1", sev, rng)
    elif cls == "H2": fault = pick_hw(tab, "H2", sev, rng)
    elif cls == "C1": x = s3(x, sev, rng, noise); fault = pick_hw(tab, "H1", sev, rng)
    elif cls == "C2": x = s4(x, sev, rng, noise); fault = pick_hw(tab, "H2", sev, rng)
    return x, fault

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--n_var", type=int, default=2)      # fault variants per clean window
    ap.add_argument("--frac", type=float, default=1.0)   # use this fraction of windows
    ap.add_argument("--out", default="data/dataset.npz")
    a = ap.parse_args(); rng = np.random.default_rng(0)
    os.makedirs("data/cache", exist_ok=True); tab = hw_table()
    if a.synthetic:
        recs = {100: DS2, 101: DS1, 106: DS1, 102: DS1}  # fake ids to exercise the splits
        data = {r: synthetic(r) for r in recs}
        noise = {k: np.cumsum(np.random.default_rng(i).normal(size=100000)) for i, k in enumerate(["bw", "em", "ma"])}
        split_of = {100: "test", 101: "train", 106: "val", 102: "train"}
    else:
        data = {}
        for r in DS1+DS2:
            print("loading", r, flush=True); d = load_real(r, "data/cache")
            if d is not None: data[r] = d
        noise = load_noise("data/cache")
        split_of = {r: ("test" if r in DS2 else "val" if r in VAL else "train") for r in data}
    B = dict(raw=[], out=[], y=[], rec=[], split=[])
    for r, (x, s, ab) in data.items():
        for st in range(0, len(x)-WIN+1, WIN):
            m = (s >= st) & (s < st+WIN)
            if m.sum() == 0 or rng.random() > a.frac: continue
            B["raw"].append(x[st:st+WIN]); B["y"].append(int(ab[m].max()))
            B["rec"].append(r); B["split"].append(split_of[r])
    raw = np.array(B["raw"]); out = np.array([fir(w) for w in raw])
    print("base windows:", len(raw), "abnormal fraction: %.2f" % np.mean(B["y"]))
    F = dict(raw=[], out=[], base=[], cls=[], sev=[], fault=[])
    for i in range(len(raw)):
        for _ in range(a.n_var):
            cls = CLASSES[int(rng.integers(len(CLASSES)))]; sev = int(rng.integers(3))
            xr, fault = make_variant(raw[i], cls, sev, rng, noise, tab)
            F["raw"].append(xr); F["out"].append(fir(xr, fault)); F["base"].append(i)
            F["cls"].append(CLASSES.index(cls)); F["sev"].append(sev); F["fault"].append(fault or (-1, -1, -1, -1))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    np.savez(a.out, base_raw=raw.astype(np.int16), base_out=out.astype(np.int16),
             base_y=np.array(B["y"]), base_rec=np.array(B["rec"]), base_split=np.array(B["split"]),
             f_raw=np.array(F["raw"]).astype(np.int16), f_out=np.array(F["out"]).astype(np.int16),
             f_base=np.array(F["base"]), f_cls=np.array(F["cls"]), f_sev=np.array(F["sev"]),
             f_fault=np.array(F["fault"]), classes=np.array(CLASSES))
    print("saved", a.out, "| fault windows:", len(F["raw"]))
main()
