#!/usr/bin/env python3
"""Chapter 14 — Boltz-2 against FEP+, and what r = 0.62 actually buys.

    python ch14_boltz2/scripts/correlation.py

Boltz-2 reports **r = 0.62** on the FEP+ benchmark. FEP+ itself reports
**R² = 0.52**. Those are not the same quantity, and the comparison that matters
is between like and like:

    r  = 0.62
    r² = 0.62² = 0.38

**0.38 against 0.52.** The squaring is shown rather than asserted, because the
whole argument turns on it and because a correlation coefficient quoted next to
an R² is the single most effective way to make a method look better than it is.

The second half asks what an r of 0.62 is worth at the bench: given two
compounds whose true affinities differ by a known amount, how often does the
method put them in the right order?

Writes outputs/correlation.json, outputs/correlation.md and
outputs/correlation.png.
"""
import json
import math
from pathlib import Path

import numpy as np

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

BOLTZ2_R = 0.62          # as reported
FEP_R2 = 0.52            # as reported

# Typical spread of a congeneric series in kcal/mol. The AmpC series in this
# repository spans 0.32 kcal/mol, which is far tighter than this.
SERIES_SIGMA = 1.5


def pairwise_accuracy(r, true_gap, sigma=SERIES_SIGMA, samples=400000, seed=42):
    """P(the method orders two compounds correctly), by simulation.

    Model: predicted = r * true + sqrt(1 - r^2) * noise, both standardised.
    Two compounds whose true values differ by `true_gap` kcal/mol are ranked
    correctly when the predicted difference has the same sign.
    """
    rng = np.random.default_rng(seed)
    gap = true_gap / sigma                       # in standard deviations
    noise = rng.standard_normal(samples) - rng.standard_normal(samples)
    predicted_gap = r * gap + math.sqrt(1 - r * r) * noise
    return float((predicted_gap > 0).mean())


def analytic_pairwise_accuracy(r, true_gap, sigma=SERIES_SIGMA):
    """The same probability in closed form, as a check on the simulation.

    The predicted difference is normal with mean r*gap and variance
    2*(1 - r^2), so the probability is Phi(r*gap / sqrt(2*(1 - r^2))).
    """
    from math import erf, sqrt
    gap = true_gap / sigma
    z = r * gap / sqrt(2 * (1 - r * r))
    return 0.5 * (1 + erf(z / sqrt(2)))


def plot(rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.2))

    left.bar(["Boltz-2\nr", "Boltz-2\nr²", "FEP+\nR²"],
             [BOLTZ2_R, BOLTZ2_R ** 2, FEP_R2],
             color=["#9aa5b1", "#2f6f8f", "#7a4f9a"])
    left.set_ylim(0, 0.75)
    left.set_ylabel("value")
    left.set_title("Comparing like with like")
    for i, v in enumerate([BOLTZ2_R, BOLTZ2_R ** 2, FEP_R2]):
        left.text(i, v + 0.015, "%.2f" % v, ha="center")

    gaps = [row["true_gap_kcal"] for row in rows]
    right.plot(gaps, [row["accuracy"] for row in rows], marker="o")
    right.axhline(0.5, color="k", linestyle="--", linewidth=0.8,
                  label="coin flip")
    right.set_xlabel("true difference between two compounds (kcal/mol)")
    right.set_ylabel("P(ranked correctly)")
    right.set_ylim(0.4, 1.0)
    right.set_title("What r = 0.62 buys at the bench")
    right.legend()
    fig.tight_layout()
    path = OUT / "correlation.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    r_squared = BOLTZ2_R ** 2
    print("Boltz-2 on the FEP+ benchmark")
    print("  reported r          = %.2f" % BOLTZ2_R)
    print("  r squared           = %.2f x %.2f = %.4f" % (BOLTZ2_R, BOLTZ2_R, r_squared))
    print("  rounded             = %.2f" % round(r_squared, 2))
    print("\nFEP+ on the same benchmark")
    print("  reported R squared  = %.2f" % FEP_R2)
    print("\n  %.2f against %.2f." % (round(r_squared, 2), FEP_R2))
    print("  Boltz-2 explains %.0f%% of the variance; FEP+ explains %.0f%%."
          % (100 * r_squared, 100 * FEP_R2))
    print("  The gap is %.0f percentage points of variance, not the %.0f points"
          % (100 * (FEP_R2 - r_squared), 100 * abs(BOLTZ2_R - FEP_R2)))
    print("  that r against R squared appears to show.")

    print("\nWhat r = %.2f is worth when ranking two compounds" % BOLTZ2_R)
    print("(series spread %.1f kcal/mol):\n" % SERIES_SIGMA)
    print("  %-22s %-14s %-14s %s"
          % ("true difference", "simulated", "analytic", "vs coin flip"))
    rows = []
    for gap in (0.32, 0.5, 1.0, 1.5, 2.0, 3.0):
        simulated = pairwise_accuracy(BOLTZ2_R, gap)
        analytic = analytic_pairwise_accuracy(BOLTZ2_R, gap)
        rows.append({"true_gap_kcal": gap, "accuracy": simulated,
                     "accuracy_analytic": analytic})
        print("  %-22s %-14.3f %-14.3f %+.1f points"
              % ("%.2f kcal/mol" % gap, simulated, analytic,
                 100 * (simulated - 0.5)))

    worst = rows[0]
    print("\n  The AmpC series in this repository spans %.2f kcal/mol."
          % worst["true_gap_kcal"])
    print("  At that separation a method with r = %.2f orders two compounds"
          % BOLTZ2_R)
    print("  correctly %.1f%% of the time -- %.1f points better than guessing."
          % (100 * worst["accuracy"], 100 * (worst["accuracy"] - 0.5)))
    print("\n  That is not a criticism of Boltz-2. It is a statement about what")
    print("  any method with that correlation can do, and about how tight a")
    print("  series has to be before no method can help you.")

    figure = plot(rows)
    payload = {
        "boltz2_r": BOLTZ2_R,
        "boltz2_r_squared": r_squared,
        "boltz2_r_squared_rounded": round(r_squared, 2),
        "fep_plus_r_squared": FEP_R2,
        "variance_gap": round(FEP_R2 - r_squared, 4),
        "series_sigma_kcal": SERIES_SIGMA,
        "pairwise": rows,
    }
    (OUT / "correlation.json").write_text(json.dumps(payload, indent=2) + "\n",
                                          encoding="utf-8")
    write_report(payload)
    if figure:
        print("\nwrote %s" % figure)
    print("wrote %s" % (OUT / "correlation.json"))


def write_report(payload):
    lines = [
        "# Chapter 14 — Boltz-2 and the squaring step", "",
        "## Comparing like with like", "",
        "| | Value |",
        "|---|---|",
        "| Boltz-2, reported **r** | %.2f |" % payload["boltz2_r"],
        "| Boltz-2, **r²** = %.2f × %.2f | **%.4f** |"
        % (payload["boltz2_r"], payload["boltz2_r"], payload["boltz2_r_squared"]),
        "| FEP+, reported **R²** | %.2f |" % payload["fep_plus_r_squared"],
        "",
        "**%.2f against %.2f.** Boltz-2 explains %.0f%% of the variance in the"
        % (payload["boltz2_r_squared_rounded"], payload["fep_plus_r_squared"],
           100 * payload["boltz2_r_squared"]),
        "benchmark; FEP+ explains %.0f%%."
        % (100 * payload["fep_plus_r_squared"]),
        "",
        "Quoted as *r = 0.62 against R² = 0.52*, the newer method looks ahead. It",
        "is not. An r and an R² are different quantities and a comparison between",
        "them is not a comparison. The squaring is one keystroke and it reverses",
        "the conclusion.",
        "",
        "## What r = 0.62 buys",
        "",
        "Two compounds whose true affinities differ by a known amount: how often",
        "does a method with this correlation put them in the right order?",
        "",
        "| True difference | P(correct order) | Better than a coin flip by |",
        "|---|---|---|",
    ]
    for row in payload["pairwise"]:
        lines.append("| %.2f kcal/mol | %.3f | %.1f points |"
                     % (row["true_gap_kcal"], row["accuracy"],
                        100 * (row["accuracy"] - 0.5)))
    worst = payload["pairwise"][0]
    lines += [
        "",
        "Simulated over 400,000 pairs and checked against the closed form",
        "Φ(r·Δ / √(2(1−r²))); the two agree to three decimals.",
        "",
        "**The AmpC series in this repository spans %.2f kcal/mol.** At that"
        % worst["true_gap_kcal"],
        "separation a method with r = %.2f gets the order right %.1f%% of the"
        % (payload["boltz2_r"], 100 * worst["accuracy"]),
        "time — %.1f points better than guessing."
        % (100 * (worst["accuracy"] - 0.5)),
        "",
        "That is not a criticism of Boltz-2. It is a statement about what *any*",
        "method with that correlation can do, and about how tight a congeneric",
        "series has to be before no method can help you. Chapter 26 reaches the",
        "same conclusion from the other end, by trying to rank the series and",
        "finding there is no reliable ranking there to reproduce.",
        "",
    ]
    (OUT / "correlation.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
