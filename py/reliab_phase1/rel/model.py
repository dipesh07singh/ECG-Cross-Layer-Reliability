import numpy as np
COEF = [60,170,300,494,494,300,170,60]

def force(v, b, val, width):
    m = (1 << width) - 1
    u = np.asarray(v, dtype=np.int64) & m
    u = (u | (1 << b)) if val else (u & ~(1 << b))
    u = u & m
    return np.where(u >= (1 << (width-1)), u - (1 << width), u)

def fir(x, fault=None):          # fault = (kind, tap, bit, val) or None; kind 0=acc 1=product 2=coef
    x = np.asarray(x, dtype=np.int64); n = len(x); acc = np.zeros(n, dtype=np.int64)
    for k in range(8):
        xs = np.concatenate([np.zeros(k, dtype=np.int64), x[:n-k]])
        c = COEF[k]
        if fault and fault[0] == 2 and fault[1] == k:
            c = int(force(c, fault[2], fault[3], 12))
        p = xs * c
        if fault and fault[0] == 1 and fault[1] == k:
            p = force(p, fault[2], fault[3], 24)
        acc = acc + p
    if fault and fault[0] == 0:
        acc = force(acc, fault[2], fault[3], 27)
    return acc >> 11
