#!/usr/bin/env python3
"""Chapter 21 — every window looks converged.

    python ch21_molecular_dynamics/scripts/convergence.py

A synthetic RMSD trajectory built from four relaxation processes a decade
apart. It is then observed through four windows, also a decade apart, and each
one is subjected to the test everyone actually applies: *has the second half
stopped rising?*

Every window long enough that anyone would trust it passes. The 10 ns
answer is nearly 40% below the 1000 ns one.

No MD software is needed: the trajectory is generated, not simulated. That is
deliberate — the point is about how trajectories are *read*, and a synthetic
one lets the true answer be known.

Writes outputs/convergence.json, outputs/convergence.md and
outputs/convergence.png.
"""
import json
import sys
from pathlib import Path

import numpy as np

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# Four relaxation processes, a decade apart: a side chain settling, a loop, a
# domain, and whatever the slowest thing in the system is. Real proteins have
# this structure; the separation here is clean so the arithmetic is legible.
TAUS = [0.1, 1.0, 10.0, 100.0]          # ns

# Amplitudes chosen so the four window means land as near the book's values as
# a monotone four-exponential model can reach: 1.10, 1.47, 1.90, 2.34 Å. The
# residual is about 0.08 Å and it does not go away by fitting harder -- see the
# note at the end of this file.
BASELINE = 0.000
AMPLITUDES = [1.112, 0.270, 0.101, 0.910]

# Thermal noise. Without it the trajectory is monotone and no window would ever
# show a falling tail -- which is exactly what makes the shortest windows look
# settled.
NOISE_SIGMA = 0.05                      # Å
SEED = 42
SAMPLE_INTERVAL = 0.01                  # ns between frames
TOTAL_TIME = 1000.0                     # ns

WINDOWS = [1, 10, 100, 1000]            # ns

# The test as it is actually applied: the second half of the run is not rising.
# Not a good test. It is the one in use.
CONVERGED_SLOPE = 0.02                  # Å/ns


def trajectory():
    """RMSD against time: four saturating exponentials plus noise."""
    rng = np.random.default_rng(SEED)
    t = np.arange(0.0, TOTAL_TIME + SAMPLE_INTERVAL, SAMPLE_INTERVAL)
    signal = np.full_like(t, BASELINE)
    for amplitude, tau in zip(AMPLITUDES, TAUS):
        signal = signal + amplitude * (1.0 - np.exp(-t / tau))
    return t, signal + rng.normal(0.0, NOISE_SIGMA, size=t.shape)


def analyse(t, rmsd, window):
    """Mean, second-half slope, and the verdict the naive test returns."""
    inside = t <= window
    times, values = t[inside], rmsd[inside]
    half = times >= window / 2.0
    # Least squares on the second half only. This is the standard eyeball test
    # written down: fit the tail, see whether it is still climbing.
    slope, _ = np.polyfit(times[half], values[half], 1)
    return {
        "window_ns": window,
        "mean_rmsd": round(float(values.mean()), 3),
        "slope_second_half": round(float(slope), 4),
        "looks_converged": bool(slope <= CONVERGED_SLOPE),
        "final_value": round(float(values[-1]), 3),
    }


def plot(t, rmsd, results):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available; skipping the figure")
        return None

    fig, axes = plt.subplots(1, 4, figsize=(15, 3.6))
    for axis, window in zip(axes, WINDOWS):
        inside = t <= window
        axis.plot(t[inside], rmsd[inside], linewidth=0.7)
        entry = results[str(window)]
        axis.axhline(entry["mean_rmsd"], color="C1", linestyle="--", linewidth=1,
                     label="mean %.2f Å" % entry["mean_rmsd"])
        axis.set_title("%d ns window\nslope %+.3f Å/ns"
                       % (window, entry["slope_second_half"]))
        axis.set_xlabel("time (ns)")
        axis.set_ylim(0, 3)
        axis.legend(loc="lower right", fontsize=8)
    axes[0].set_ylabel("RMSD (Å)")
    fig.suptitle("Each window that looks settled is settled only on its own "
                 "timescale.", y=1.02)
    fig.tight_layout()
    path = OUT / "convergence.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t, rmsd = trajectory()

    results = {}
    for window in WINDOWS:
        entry = analyse(t, rmsd, window)
        # What you would have seen had you run ten times longer.
        if window * 10 <= TOTAL_TIME:
            index = int(round(window * 10 / SAMPLE_INTERVAL))
            entry["value_at_10x_window"] = round(float(rmsd[index]), 3)
        else:
            entry["value_at_10x_window"] = None
        results[str(window)] = entry

    print("%d relaxation processes at tau = %s ns, noise sigma %.2f A, seed %d\n"
          % (len(TAUS), ", ".join(str(x) for x in TAUS), NOISE_SIGMA, SEED))
    print("%-10s %-10s %-14s %-14s %s"
          % ("window", "mean RMSD", "slope 2nd half", "at 10x window", "verdict"))
    for window in WINDOWS:
        entry = results[str(window)]
        at10 = ("%.2f A" % entry["value_at_10x_window"]
                if entry["value_at_10x_window"] is not None else "-")
        print("%-10s %-10.2f %-+14.4f %-14s %s"
              % ("%d ns" % window, entry["mean_rmsd"], entry["slope_second_half"],
                 at10, "looks converged" if entry["looks_converged"] else "still rising"))

    short = results["10"]["mean_rmsd"]
    long = results["1000"]["mean_rmsd"]
    shortfall = (long - short) / long
    # Counted, not asserted. An earlier version of this script printed "every
    # window passes" unconditionally while the 1 ns window was visibly still
    # rising. A claim in a print statement is not a result.
    passing = [w for w in WINDOWS if results[str(w)]["looks_converged"]]
    print("\n%d of the %d windows pass the flat-tail test: %s."
          % (len(passing), len(WINDOWS), ", ".join("%d ns" % w for w in passing)))
    print("The 10 ns answer is %.0f%% below the 1000 ns one." % (100 * shortfall))
    print("Nothing inside a 10 ns run says so.")

    book = {"1": {"mean": 1.10, "slope": -0.150, "at10x": 1.45},
            "10": {"mean": 1.47, "slope": -0.010, "at10x": 1.99},
            "100": {"mean": 1.90, "slope": 0.007, "at10x": 2.37},
            "1000": {"mean": 2.34, "slope": 0.0004, "at10x": None}}
    payload = {
        "taus_ns": TAUS,
        "baseline": BASELINE,
        "amplitudes": AMPLITUDES,
        "noise_sigma": NOISE_SIGMA,
        "seed": SEED,
        "sample_interval_ns": SAMPLE_INTERVAL,
        "converged_slope_threshold": CONVERGED_SLOPE,
        "windows": results,
        "shortfall_10ns_vs_1000ns": round(float(shortfall), 3),
        "book": book,
    }
    (OUT / "convergence.json").write_text(json.dumps(payload, indent=2) + "\n",
                                          encoding="utf-8")

    figure = plot(t, rmsd, results)
    if figure:
        print("wrote %s" % figure)

    write_report(payload)
    print("wrote %s" % (OUT / "convergence.json"))


def write_report(payload):
    results, book = payload["windows"], payload["book"]
    lines = [
        "# Chapter 21 — every window looks converged", "",
        "A synthetic RMSD trajectory: four relaxation processes at τ = %s ns,"
        % ", ".join(str(x) for x in payload["taus_ns"]),
        "plus Gaussian noise (σ = %.2f Å, seed %d)."
        % (payload["noise_sigma"], payload["seed"]),
        "",
        "| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |",
        "|---|---|---|---|---|",
    ]
    for window in WINDOWS:
        entry = results[str(window)]
        at10 = ("%.2f Å" % entry["value_at_10x_window"]
                if entry["value_at_10x_window"] is not None else "—")
        lines.append("| %d ns | %.2f Å | %+.4f Å/ns | %s | %s |"
                     % (window, entry["mean_rmsd"], entry["slope_second_half"],
                        at10, "looks converged" if entry["looks_converged"]
                        else "still rising"))
    lines += [
        "",
        "**%d of the %d windows pass the flat-tail test**, including every window"
        % (sum(1 for w in WINDOWS if results[str(w)]["looks_converged"]), len(WINDOWS)),
        "long enough that anyone would trust it. The 10 ns answer is %.0f%% below"
        % (100 * payload["shortfall_10ns_vs_1000ns"]),
        "the 1000 ns one, and nothing available inside a 10 ns run says so.",
        "",
        "The test being applied — *has the second half stopped rising?* — is the",
        "one in general use. It is not a bad test because it is naive; it is a bad",
        "test because a process slower than the window is invisible to it **by",
        "construction**. A trajectory relaxing on a 300 ns timescale looks",
        "perfectly flat over any 10 ns stretch of itself.",
        "",
        "## Against the book",
        "",
        "| Window | Mean, book | Mean, here | Slope, book | Slope, here |",
        "|---|---|---|---|---|",
    ]
    for window in WINDOWS:
        entry, ref = results[str(window)], book[str(window)]
        lines.append("| %d ns | %.2f Å | %.2f Å | %+.4f | %+.4f |"
                     % (window, ref["mean"], entry["mean_rmsd"],
                        ref["slope"], entry["slope_second_half"]))
    lines += [
        "",
        "The book's construction is not recorded — `CLAUDE.md` gives the results",
        "and says the trajectory has four separated relaxation timescales. Fitting",
        "amplitudes *and* timescales to the book's seven published numbers leaves",
        "a residual of about 0.08 Å that will not reduce, which is itself",
        "informative: a monotone sum of exponentials cannot produce the reported",
        "**negative** slopes at all. Those need noise, and the noise realisation",
        "is a seed nobody wrote down.",
        "",
        "So the deterministic half is reconstructed and the stochastic half is",
        "not. What reproduces is every qualitative claim, including the one the",
        "chapter is about: the shortfall between the 10 ns and 1000 ns answers is",
        "%.0f%% here against the book's 37%%." % (100 * payload["shortfall_10ns_vs_1000ns"]),
        "",
    ]
    (OUT / "convergence.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
