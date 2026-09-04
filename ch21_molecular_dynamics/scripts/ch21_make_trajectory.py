"""
ch21_molecular_dynamics — the exact synthetic trajectory behind the book's
convergence demonstration.

Four Ornstein-Uhlenbeck relaxations at separated timescales, which is the
standard picture of how a protein relaxes: fast side chains, then loops, then
slower domain motion. The generator is consumed once per process, in the order
of `taus`, so that order is part of the specification.
"""
import numpy as np

SEED = 2101
T, DT = 3000.0, 0.01                     # ns total, ns per frame
TAUS = np.array([0.04, 1.2, 30.0, 700.0])
AMPS = np.array([0.50, 0.55, 0.65, 0.90])

def make_trajectory():
    n = int(T/DT); t = np.arange(n)*DT
    rng = np.random.default_rng(SEED)
    x = np.zeros(n)
    for tau, a in zip(TAUS, AMPS):
        lam = np.exp(-DT/tau); sig = np.sqrt(1 - lam**2)
        y = np.empty(n); y[0] = 0.0
        nz = rng.normal(size=n) * sig
        for i in range(1, n):
            y[i] = lam*y[i-1] + nz[i]
        x += a*(1 - np.exp(-t/tau)) + 0.22*a*y
    return t, np.abs(x) + 0.22

def window_stats(t, rmsd, w):
    """Mean over the window's second half, its slope, and the value at 10x."""
    k = int(w/DT); half = k//2
    seg, ts = rmsd[half:k], t[half:k]
    slope = np.polyfit(ts, seg, 1)[0]
    j = int(w*10/DT)
    later = rmsd[j-int(0.05*j):j].mean() if j < len(rmsd) else None
    return seg.mean(), slope, later

if __name__ == "__main__":
    t, rmsd = make_trajectory()
    expected = {1.0: 1.10, 10.0: 1.47, 100.0: 1.90, 1000.0: 2.34}
    for w in (1.0, 10.0, 100.0, 1000.0):
        m, s, l = window_stats(t, rmsd, w)
        print(f"{w:>6.0f} ns   mean {m:.2f}   slope {s:+.4f}   "
              f"at 10x {('%.2f' % l) if l else 'beyond run'}")
        assert abs(m - expected[w]) < 0.005, f"window {w}: got {m:.3f}"
    print("\nEvery window looks converged. The 10 ns answer is 37 per cent "
          "below the 1000 ns one.")
