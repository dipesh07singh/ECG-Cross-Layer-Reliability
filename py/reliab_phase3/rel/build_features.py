"""Phase 3a: train 1D-CNN (clean data), MC-Dropout predictions, SQI features, hardware evidence.
Run: python build_features.py          (CPU, ~10-25 min on real data)
     python build_features.py --quick  (tiny test run)
"""
import numpy as np, torch, torch.nn as nn, sys, time
from scipy.signal import find_peaks
from scipy.stats import kurtosis
from model import fir
QUICK = "--quick" in sys.argv
EPOCHS = 2 if QUICK else 12
T_MC = 5 if QUICK else 20
torch.manual_seed(0); np.random.seed(0)
d = np.load("data/dataset.npz"); FS = 360
CLASSES = list(d["classes"]) + ["clean"]
base_out, base_y = d["base_out"].astype(np.float32), d["base_y"]
base_rec, base_split = d["base_rec"], d["base_split"]
f_out, f_raw = d["f_out"], d["f_raw"]; f_base = d["f_base"]; f_fault = d["f_fault"]
Nb, Nf = len(base_out), len(f_out)

class Net(nn.Module):
    def __init__(s):
        super().__init__()
        def blk(i, o, k): return nn.Sequential(nn.Conv1d(i, o, k, stride=2, padding=k//2), nn.BatchNorm1d(o), nn.ReLU())
        s.f = nn.Sequential(blk(1, 16, 9), blk(16, 32, 7), blk(32, 64, 5), blk(64, 64, 5))
        s.h = nn.Sequential(nn.Dropout(0.3), nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3), nn.Linear(64, 2))
    def forward(s, x):
        z = s.f(x); return s.h(torch.cat([z.mean(2), z.amax(2)], 1))

def tens(X): return torch.from_numpy(np.asarray(X, dtype=np.float32)/512.0).unsqueeze(1)

def fit(Xtr, ytr, Xva, yva):
    m = Net(); opt = torch.optim.Adam(m.parameters(), 1e-3)
    w = torch.tensor([1.0, (ytr == 0).sum()/max((ytr == 1).sum(), 1)], dtype=torch.float32)
    lossf = nn.CrossEntropyLoss(weight=w); Xt, yt = tens(Xtr), torch.from_numpy(ytr).long()
    best, state = 1e9, None
    for ep in range(EPOCHS):
        m.train(); perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), 128):
            idx = perm[i:i+128]; opt.zero_grad(); lossf(m(Xt[idx]), yt[idx]).backward(); opt.step()
        m.eval()
        with torch.no_grad(): vl = lossf(m(tens(Xva)), torch.from_numpy(yva).long()).item()
        print(f"  epoch {ep+1}/{EPOCHS} val loss {vl:.4f}", flush=True)
        if vl < best: best, state = vl, {k: v.clone() for k, v in m.state_dict().items()}
    m.load_state_dict(state); return m

def mc_predict(m, X, T=T_MC):
    m.eval()
    for mod in m.modules():
        if isinstance(mod, nn.Dropout): mod.train()
    out = np.zeros((len(X), 3), dtype=np.float32)
    with torch.no_grad():
        for i in range(0, len(X), 512):
            xb = tens(X[i:i+512]); P = torch.stack([torch.softmax(m(xb), 1)[:, 1] for _ in range(T)])
            p = P.mean(0); ent = -(p*torch.log(p+1e-8)+(1-p)*torch.log(1-p+1e-8))
            out[i:i+512] = torch.stack([p, ent, P.var(0)], 1).numpy()
    return out

# ---- train: full model (train patients) + 2-fold cross-fit models (so fusion sees honest CNN outputs)
tr = base_split == "train"; va = base_split == "val"
t0 = time.time(); print("training full CNN"); full = fit(base_out[tr], base_y[tr], base_out[va], base_y[va])
recs = np.unique(base_rec[tr]); grp = {r: i % 2 for i, r in enumerate(recs)}
fold = [None, None]
for k in range(2):
    print(f"training cross-fit model {k+1}/2 (trained on the other half of the train patients)")
    a = tr & np.array([grp.get(r, -1) != k for r in base_rec]); b = tr & np.array([grp.get(r, -1) == k for r in base_rec])
    fold[k] = fit(base_out[a], base_y[a], base_out[va], base_y[va])
print("CNN training done in %.1f min" % ((time.time()-t0)/60))

def model_for_base(i):  # which CNN scores a window derived from base window i
    return fold[grp[base_rec[i]]] if base_split[i] == "train" else full
Pb = np.zeros((Nb, 3), dtype=np.float32); Pf = np.zeros((Nf, 3), dtype=np.float32)
for key, mdl in [("full", full), ("f0", fold[0]), ("f1", fold[1])]:
    pick = lambda i: (model_for_base(i) is mdl)
    mb = np.array([pick(i) for i in range(Nb)])
    if mb.any(): Pb[mb] = mc_predict(mdl, base_out[mb])
    mf = mb[f_base]
    if mf.any(): Pf[mf] = mc_predict(mdl, f_out[mf])
    print("scored with", key, int(mb.sum()), "clean +", int(mf.sum()), "fault windows", flush=True)

# ---- clean CNN quality (test patients, no faults) = table stakes
te = base_split == "test"; pr = (Pb[te, 0] >= 0.5).astype(int); y = base_y[te]
tp = ((pr == 1) & (y == 1)).sum(); fp = ((pr == 1) & (y == 0)).sum(); fn = ((pr == 0) & (y == 1)).sum()
print("CLEAN TEST: acc %.3f  F1(abnormal) %.3f  confusion [[TN,FP],[FN,TP]] = [[%d,%d],[%d,%d]]" % (
      (pr == y).mean(), 2*tp/max(2*tp+fp+fn, 1), ((pr == 0) & (y == 0)).sum(), fp, fn, tp))

# ---- SQI features (computed on the signal the CNN sees)
def sqi(x):
    x = x.astype(np.float64); n = len(x); a = np.abs(x).max()+1e-9; dx = np.diff(x)
    z = np.r_[0, (dx == 0).astype(int), 0]; edges = np.flatnonzero(np.diff(z)); runs = edges[1::2]-edges[::2]
    F = np.abs(np.fft.rfft(x-x.mean()))**2; fr = np.fft.rfftfreq(n, 1/FS); tot = F.sum()+1e-9
    pk, _ = find_peaks(x, height=0.5*x.max() if x.max() > 0 else 1e9, distance=int(0.25*FS))
    rr = np.diff(pk)/FS
    return [np.ptp(x)/1024, x.std()/512, (runs.max() if len(runs) else 0)/n, np.mean(np.abs(x) >= 0.995*a),
            dx.std()/(x.std()+1e-6), F[fr < 0.7].sum()/tot, F[fr > 20].sum()/tot, len(pk),
            (rr.std()/rr.mean()) if len(rr) > 1 else 0.0, kurtosis(x), abs(x.mean())/(x.std()+1.0)]
SQI_NAMES = "ptp std flat_run clip_frac hf_ratio bw_pow emg_pow n_peaks rr_cv kurt offset".split()
print("computing SQI features ..."); Sb = np.array([sqi(w) for w in base_out]); Sf = np.array([sqi(w) for w in f_out])

# ---- hardware evidence: shadow divergence (bit-exact fault-free filter on the same raw input) + periodic BIST
print("computing shadow-path divergence ...")
shadow = np.array([np.mean(fir(f_raw[j].astype(np.int64)) != f_out[j]) for j in range(Nf)])
rng = np.random.default_rng(0); K = 4                     # BIST runs every K windows
t_since = rng.integers(0, K, Nf + Nb); age = rng.integers(0, 2*K, Nf)   # windows since last test / since fault onset
hw = f_fault[:, 0] >= 0; bist_f = (hw & (age >= t_since[Nb:])).astype(int)

cls_b = np.full(Nb, len(CLASSES)-1); is_f = np.r_[np.zeros(Nb, int), np.ones(Nf, int)]
np.savez("data/features.npz", classes=np.array(CLASSES), sqi_names=np.array(SQI_NAMES),
         rec=np.r_[base_rec, base_rec[f_base]], split=np.r_[base_split, base_split[f_base]],
         cls=np.r_[cls_b, d["f_cls"]], sev=np.r_[np.zeros(Nb, int), d["f_sev"]], y=np.r_[base_y, base_y[f_base]],
         base_idx=np.r_[np.arange(Nb), f_base], is_fault=is_f,
         p=np.r_[Pb[:, 0], Pf[:, 0]], ent=np.r_[Pb[:, 1], Pf[:, 1]], var=np.r_[Pb[:, 2], Pf[:, 2]],
         sqi=np.r_[Sb, Sf], shadow=np.r_[np.zeros(Nb), shadow], bist=np.r_[np.zeros(Nb, int), bist_f],
         t_since=t_since, hw=np.r_[np.zeros(Nb, int), hw.astype(int)])
print("saved data/features.npz")
