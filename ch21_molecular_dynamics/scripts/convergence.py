#!/usr/bin/env python3
"""Chapter 21 — every window looks converged.

    python ch21_molecular_dynamics/scripts/convergence.py

A synthetic RMSD trajectory built from four Ornstein-Uhlenbeck relaxations at
separated timescales. It is then observed through four windows, also a decade
apart, and each one is subjected to the test everyone actually applies: *has
the second half stopped rising?*

Every window passes. The 10 ns answer is 37% below the 1000 ns one.

No MD software is needed: the trajectory is generated, not simulated. That is
deliberate — the point is about how trajectories are *read*, and a synthetic
one lets the true answer be known.

The construction lives in `ch21_make_trajectory.py` and is imported rather than
copied, so there is exactly one definition of the trajectory. This script
analyses it and writes the report.

Writes outputs/convergence.json, outputs/convergence.md and
outputs/convergence.png.
"""
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# One definition of the trajectory, imported. A chapter about how sensitive a
# conclusion is to what you sampled cannot afford two copies of its own data.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ch21_make_trajectory import (AMPS, DT, SEED, T, TAUS,  # noqa: E402
                                  make_trajectory, window_stats)

WINDOWS = [1.0, 10.0, 100.0, 1000.0]    # ns

# The test as it is actually applied: the second half of the run is not rising.
# Not a good test. It is the one in use.
CONVERGED_SLOPE = 0.02                  # A/ns


def analyse(t, rmsd, window):
    """Mean, second-half slope, value at 10x, and the naive test's verdict.

    The statistics come from `window_stats` in the construction module, so the
    definitions here and there cannot drift: the mean is over the window's
    second half, and the value at 10x is averaged over the last 5% before that
    point rather than read off a single frame.
    """
    mean, slope, later = window_stats(t, rmsd, window)
    return {
        "window_ns": window,
        "mean_rmsd": round(float(mean), 3),
        "slope_second_half": round(float(slope), 4),
        "looks_converged": bool(slope <= CONVERGED_SLOPE),
        "value_at_10x_window": None if later is None else round(float(later), 3),
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
        entry = results[str(int(window))]
        axis.axhline(entry["mean_rmsd"], color="C1", linestyle="--", linewidth=1,
                     label="mean %.2f A" % entry["mean_rmsd"])
        axis.set_title("%d ns window\nslope %+.3f A/ns"
                       % (window, entry["slope_second_half"]))
        axis.set_xlabel("time (ns)")
        axis.set_ylim(0, 3)
        axis.legend(loc="lower right", fontsize=8)
    axes[0].set_ylabel("RMSD (A)")
    fig.suptitle("Each window that looks settled is settled only on its own "
                 "timescale.", y=1.02)
    fig.tight_layout()
    path = OUT / "convergence.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t, rmsd = make_trajectory()

    results = {str(int(w)): analyse(t, rmsd, w) for w in WINDOWS}

    print("%d Ornstein-Uhlenbeck relaxations at tau = %s ns, seed %d, %.0f ns "
          "sampled every %.2f ns\n"
          % (len(TAUS), ", ".join(str(x) for x in TAUS), SEED, T, DT))
    print("%-10s %-10s %-14s %-14s %s"
          % ("window", "mean RMSD", "slope 2nd half", "at 10x window", "verdict"))
    for window in WINDOWS:
        entry = results[str(int(window))]
        at10 = ("%.2f A" % entry["value_at_10x_window"]
                if entry["value_at_10x_window"] is not None else "beyond run")
        print("%-10s %-10.2f %-+14.4f %-14s %s"
              % ("%d ns" % window, entry["mean_rmsd"], entry["slope_second_half"],
                 at10, "looks converged" if entry["looks_converged"] else "still rising"))

    # The book's 37% is a statement about the numbers in its own table, so it
    # is computed from the means at the precision the table prints them. From
    # the unrounded means it is 37.5%, which rounds either way depending on the
    # formatter -- both are recorded rather than one being chosen.
    short = round(results["10"]["mean_rmsd"], 2)
    long = round(results["1000"]["mean_rmsd"], 2)
    shortfall = (long - short) / long
    shortfall_unrounded = ((results["1000"]["mean_rmsd"] - results["10"]["mean_rmsd"])
                           / results["1000"]["mean_rmsd"])
    # Counted, not asserted. An earlier version of this script printed "every
    # window passes" unconditionally while a window was visibly still rising.
    # A claim in a print statement is not a result.
    passing = [w for w in WINDOWS if results[str(int(w))]["looks_converged"]]
    print("\n%d of the %d windows pass the flat-tail test: %s."
          % (len(passing), len(WINDOWS), ", ".join("%d ns" % w for w in passing)))
    print("The 10 ns answer is %.0f%% below the 1000 ns one." % (100 * shortfall))
    print("Nothing inside a 10 ns run says so.")

    book = {"1": {"mean": 1.10, "slope": -0.150, "at10x": 1.45},
            "10": {"mean": 1.47, "slope": -0.010, "at10x": 1.99},
            "100": {"mean": 1.90, "slope": 0.007, "at10x": 2.37},
            "1000": {"mean": 2.34, "slope": 0.0004, "at10x": None}}

    # Compared at the precision the book prints, and counted rather than
    # claimed. The slopes are given to three or four places, the means to two.
    checked, mismatched = 0, []
    for window in WINDOWS:
        key = str(int(window))
        entry, ref = results[key], book[key]
        for field, value, expected, places in (
                ("mean", entry["mean_rmsd"], ref["mean"], 2),
                ("slope", entry["slope_second_half"], ref["slope"],
                 len(str(ref["slope"]).split(".")[1])),
                ("at 10x", entry["value_at_10x_window"], ref["at10x"], 2)):
            if expected is None:
                continue
            checked += 1
            if round(value, places) != round(expected, places):
                mismatched.append("%s ns %s: %s here, %s in the book"
                                  % (key, field, round(value, places), expected))
    print("\n%d of the %d published values reproduce exactly."
          % (checked - len(mismatched), checked))
    for line in mismatched:
        print("  " + line)

    payload = {
        "taus_ns": [float(x) for x in TAUS],
        "amplitudes": [float(x) for x in AMPS],
        "seed": SEED,
        "sample_interval_ns": DT,
        "total_time_ns": T,
        "converged_slope_threshold": CONVERGED_SLOPE,
        "windows": results,
        "windows_passing_flat_tail_test": len(passing),
        "shortfall_10ns_vs_1000ns": round(float(shortfall), 3),
        "shortfall_from_unrounded_means": round(float(shortfall_unrounded), 3),
        "book": book,
        "book_values_matched": "%d/%d" % (checked - len(mismatched), checked),
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
        "A synthetic RMSD trajectory: four Ornstein-Uhlenbeck relaxations at",
        "τ = %s ns with amplitudes %s, seed %d, %.0f ns sampled every %.2f ns."
        % (", ".join(str(x) for x in payload["taus_ns"]),
           ", ".join(str(x) for x in payload["amplitudes"]),
           payload["seed"], payload["total_time_ns"], payload["sample_interval_ns"]),
        "",
        "| Window | Mean RMSD | Slope over 2nd half | Value at 10× window | Verdict |",
        "|---|---|---|---|---|",
    ]
    for window in WINDOWS:
        entry = results[str(int(window))]
        at10 = ("%.2f Å" % entry["value_at_10x_window"]
                if entry["value_at_10x_window"] is not None else "—")
        lines.append("| %d ns | %.2f Å | %+.4f Å/ns | %s | %s |"
                     % (window, entry["mean_rmsd"], entry["slope_second_half"],
                        at10, "looks converged" if entry["looks_converged"]
                        else "still rising"))
    lines += [
        "",
        "**%d of the %d windows pass the flat-tail test.** The 10 ns answer is"
        % (payload["windows_passing_flat_tail_test"], len(WINDOWS)),
        "%.0f%% below the 1000 ns one, and nothing available inside a 10 ns run"
        % (100 * payload["shortfall_10ns_vs_1000ns"]),
        "says so. (That figure is taken from the means at the precision this",
        "table prints them, which is what the book's 37% is. From the unrounded",
        "means it is %.1f%% — a difference of half a point that changes nothing"
        % (100 * payload["shortfall_from_unrounded_means"]),
        "about the argument, and is recorded rather than resolved.)",
        "",
        "The test being applied — *has the second half stopped rising?* — is the",
        "one in general use. It is not a bad test because it is naive; it is a bad",
        "test because a process slower than the window is invisible to it **by",
        "construction**. A trajectory relaxing on a 700 ns timescale looks",
        "perfectly flat over any 10 ns stretch of itself. Two of the four windows",
        "here report a *falling* tail, which is the strongest possible version of",
        "the trap: the run is not merely flat, it looks as though it has settled",
        "and started to come back down.",
        "",
        "## Against the book",
        "",
        "| Window | Mean, book | Mean, here | Slope, book | Slope, here |",
        "|---|---|---|---|---|",
    ]
    for window in WINDOWS:
        entry, ref = results[str(int(window))], book[str(int(window))]
        lines.append("| %d ns | %.2f Å | %.2f Å | %+.4f | %+.4f |"
                     % (window, ref["mean"], entry["mean_rmsd"],
                        ref["slope"], entry["slope_second_half"]))
    lines += [
        "",
        "**%s of the published values reproduce exactly**, at the precision the"
        % payload["book_values_matched"],
        "book prints them — the four means, the four second-half slopes and the",
        "three values at ten times the window.",
        "",
        "The negative slopes are the part worth naming. A monotone sum of",
        "exponentials cannot produce one at all, so they are evidence that the",
        "trajectory is stochastic rather than a smooth saturating curve: each",
        "relaxation is an OU process, and the noise is what lets a window's tail",
        "fall while the trajectory as a whole is still climbing. That is not a",
        "detail of the demonstration. It **is** the demonstration.",
        "",
    ]
    (OUT / "convergence.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
