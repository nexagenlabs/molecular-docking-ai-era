"""
ch18_enrichment — the exact construction behind the book's two screens.

The single generator is consumed sequentially across the whole search loop, so
the loop bounds and their order are part of the specification. Re-seeding inside
the loop, or changing the ranges, gives different screens.
"""
import numpy as np
from math import exp, sinh, cosh

N, n = 10_000, 100          # library size, number of actives
SEED = 2024

def auc(labels):
    l = np.asarray(labels); N_ = len(l); n_ = l.sum(); m = N_ - n_
    return 1 - ((np.where(l == 1)[0] + 1).sum() - n_*(n_+1)/2) / (n_*m)

def ef(labels, frac):
    l = np.asarray(labels); N_ = len(l); n_ = l.sum(); k = int(round(N_*frac))
    return (l[:k].sum()/k) / (n_/N_)

def bedroc(labels, alpha=20.0):
    """Truchon & Bayly 2007. Labels ordered best-scoring first, 1 = active."""
    l = np.asarray(labels); N_ = len(l); n_ = int(l.sum()); Ra = n_/N_
    r = np.where(l == 1)[0] + 1
    rie = (np.exp(-alpha*r/N_).sum()/n_) / ((1-exp(-alpha))/(N_*(exp(alpha/N_)-1)))
    return (rie * Ra * sinh(alpha/2) / (cosh(alpha/2) - cosh(alpha/2 - alpha*Ra))
            + 1/(1 - exp(alpha*(1-Ra))))

def make_screens():
    rng = np.random.default_rng(SEED)
    best = None
    for hi in range(40, 70):                    # actives placed in the top 1%
        for lo in range(2000, 7000, 100):       # upper bound of B's spread
            A = np.zeros(N, int)
            A[rng.choice(100, hi, replace=False)] = 1
            A[rng.choice(np.arange(100, N), n - hi, replace=False)] = 1
            B = np.zeros(N, int)
            B[rng.choice(np.arange(400, lo), n, replace=False)] = 1
            d = abs(auc(A) - auc(B))
            if best is None or d < best[0]:
                best = (d, hi, lo, A.copy(), B.copy())
    return best

if __name__ == "__main__":
    d, hi, lo, A, B = make_screens()
    assert (hi, lo) == (56, 4800), f"expected hi=56 lo=4800, got {hi} {lo}"
    for name, s in (("A", A), ("B", B)):
        print(f"Screen {name}: AUC {auc(s):.3f}  EF1% {ef(s,0.01):.1f}  "
              f"EF5% {ef(s,0.05):.1f}  BEDROC {bedroc(s):.3f}")
    # cross-check against RDKit
    try:
        from rdkit.ML.Scoring import Scoring
        for name, s in (("A", A), ("B", B)):
            rd = Scoring.CalcBEDROC([[int(v)] for v in s], 0, 20.0)
            assert abs(rd - bedroc(s)) < 1e-6, f"BEDROC mismatch for {name}"
        print("BEDROC agrees with RDKit to 1e-6")
    except ImportError:
        print("RDKit unavailable; cross-check skipped")
