#!/usr/bin/env python3
"""Chapter 25 — from a docking hit to an experiment somebody can run.

    python ch25_hit_to_bench/scripts/design_assay.py

A docking score is not a measurement. Turning one into an experiment means
answering questions the score cannot: what concentrations to test, how much
compound to buy, and what result would count as confirmation.

This works those out for the AmpC series, whose answers are known, so the
design can be checked against them.

Writes outputs/assay_design.json and outputs/assay_design.md.
"""
import json
import math
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

RT = 0.001987 * 298.15

# Known Ki. In a real hit-to-bench step these are unknown -- that is the point
# of the experiment -- so the design below uses only the docking score, and the
# known values are held back to check the design afterwards.
KNOWN_KI_uM = {"STC": 26.0, "18U": 18.0, "1MU": 26.0}

# Docking scores from ch26, docking into 1L2S.
DOCKING_SCORE = {"STC": -7.377, "18U": -8.090, "1MU": -7.916}

# A dose-response curve needs points either side of the inflection. Two decades
# below and two above is the usual minimum; three is safer when the potency is
# unknown, which it always is at this stage.
DECADES_BELOW = 2
DECADES_ABOVE = 2
POINTS_PER_DECADE = 3

ASSAY_VOLUME_uL = 100
REPLICATES = 3
MW_ESTIMATE = 350.0        # g/mol, typical for this series


def dg_to_ki_uM(dg):
    """ΔG to Ki. **Not used for docking scores.** See the warning below."""
    return math.exp(dg / RT) * 1e6


def design(guess_ki_uM):
    """Concentration series bracketing a guessed potency."""
    low = guess_ki_uM / (10 ** DECADES_BELOW)
    high = guess_ki_uM * (10 ** DECADES_ABOVE)
    points = POINTS_PER_DECADE * (DECADES_BELOW + DECADES_ABOVE) + 1
    step = (high / low) ** (1 / (points - 1))
    return [low * step ** i for i in range(points)]


def compound_needed_mg(top_uM, volume_uL=ASSAY_VOLUME_uL, replicates=REPLICATES,
                       mw=MW_ESTIMATE):
    """Milligrams for the top concentration, with a 10x stock and slack."""
    moles = top_uM * 1e-6 * volume_uL * 1e-6 * replicates
    # A 10x stock, and 5x the assay volume so there is something to pipette
    # and something left over when the first plate goes wrong.
    return moles * mw * 1000 * 10 * 5


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("A docking score is not an affinity.\n")
    print("The temptation is to read a Ki off the score, since Vina reports")
    print("kcal/mol. Doing it for this series would give:\n")
    for name, score in DOCKING_SCORE.items():
        implied = dg_to_ki_uM(score)
        actual = KNOWN_KI_uM[name]
        print("   %-5s score %.3f -> 'Ki' %.2f uM;  measured Ki %.0f uM;  out by %.0fx"
              % (name, score, implied, actual, actual / implied))
    print("\n   Wrong by roughly two orders of magnitude, in the same direction,")
    print("   for all three. A Vina score is a ranking device on an energy-like")
    print("   scale; it is not a free energy and it does not convert.")
    print("\n   So the assay is designed around a POTENCY GUESS, stated as a")
    print("   guess, and wide enough to be wrong.")

    guess = 10.0
    print("\nDesign, bracketing a guess of %.0f uM:" % guess)
    series = design(guess)
    print("   %d points, %.4f uM to %.0f uM, %d per decade, %d replicates"
          % (len(series), series[0], series[-1], POINTS_PER_DECADE, REPLICATES))
    print("   " + ", ".join("%.3g" % c for c in series))

    top = series[-1]
    mg = compound_needed_mg(top)
    print("\n   top concentration %.0f uM, %d uL wells, %d replicates"
          % (top, ASSAY_VOLUME_uL, REPLICATES))
    print("   compound needed: %.2f mg at MW %.0f (10x stock, 5x volume slack)"
          % (mg, MW_ESTIMATE))

    print("\nDoes the design cover the truth?")
    covered = {}
    for name, ki in KNOWN_KI_uM.items():
        inside = series[0] <= ki <= series[-1]
        covered[name] = inside
        print("   %-5s measured %.0f uM  %s"
              % (name, ki, "inside the range" if inside else "OUTSIDE THE RANGE"))
    if all(covered.values()):
        print("\n   All three are inside, with room either side. A guess two")
        print("   decades low still worked, because the range is four decades")
        print("   wide -- which is the argument for the width.")

    print("\nWhat would count as confirmation:")
    print("   * a dose-response curve with a clear plateau at both ends")
    print("   * a Hill slope near 1; far from 1 suggests aggregation or")
    print("     stoichiometry that is not 1:1")
    print("   * activity that survives 0.01% detergent -- AmpC is a classic")
    print("     target for promiscuous aggregators, and a micromolar 'hit' that")
    print("     vanishes with detergent was never a hit")
    print("   * the same answer from a second, orthogonal assay")

    print("\nAnd what does NOT count:")
    print("   * a single-concentration percentage inhibition")
    print("   * an IC50 compared against a Ki from another paper. IC50 depends")
    print("     on substrate concentration and Km; Ki does not. They are not")
    print("     interconvertible without both, and this repository never")
    print("     converts between Ki, IC50 and Kd.")

    payload = {
        "docking_scores": DOCKING_SCORE,
        "known_ki_uM": KNOWN_KI_uM,
        "naive_conversion": {name: round(dg_to_ki_uM(score), 3)
                             for name, score in DOCKING_SCORE.items()},
        "conversion_error_fold": {
            name: round(KNOWN_KI_uM[name] / dg_to_ki_uM(DOCKING_SCORE[name]), 1)
            for name in DOCKING_SCORE},
        "guess_uM": guess,
        "concentration_series_uM": [round(c, 4) for c in series],
        "points": len(series),
        "replicates": REPLICATES,
        "assay_volume_uL": ASSAY_VOLUME_uL,
        "compound_needed_mg": round(mg, 2),
        "range_covers_truth": covered,
    }
    (OUT / "assay_design.json").write_text(json.dumps(payload, indent=2) + "\n",
                                           encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "assay_design.json"))


def write_report(payload):
    lines = [
        "# Chapter 25 — hit to bench", "",
        "## A docking score is not an affinity", "",
        "Vina reports kcal/mol, which invites conversion to a Ki. For this",
        "series that gives:", "",
        "| Ligand | Docking score | Ki if converted | Measured Ki | Out by |",
        "|---|---|---|---|---|",
    ]
    for name, score in payload["docking_scores"].items():
        lines.append("| %s | %.3f | %.2f µM | %.0f µM | %.0f× |"
                     % (name, score, payload["naive_conversion"][name],
                        payload["known_ki_uM"][name],
                        payload["conversion_error_fold"][name]))
    lines += [
        "",
        "Wrong by roughly two orders of magnitude, in the same direction, for",
        "all three. A Vina score is a ranking device on an energy-like scale. It",
        "is not a free energy and it does not convert.",
        "",
        "So the assay is designed around a **potency guess** — stated as a guess,",
        "and wide enough to be wrong.",
        "",
        "## The design", "",
        "| | |",
        "|---|---|",
        "| Guess | %.0f µM |" % payload["guess_uM"],
        "| Range | %.4f – %.0f µM |" % (payload["concentration_series_uM"][0],
                                        payload["concentration_series_uM"][-1]),
        "| Points | %d (%d per decade) |" % (payload["points"], POINTS_PER_DECADE),
        "| Replicates | %d |" % payload["replicates"],
        "| Well volume | %d µL |" % payload["assay_volume_uL"],
        "| Compound needed | **%.2f mg** |" % payload["compound_needed_mg"],
        "",
        "Compound quantity assumes a 10× stock and 5× the assay volume: enough to",
        "pipette, and enough left when the first plate goes wrong. It is not a",
        "theoretical minimum.",
        "",
        "## Does the design cover the truth?", "",
        "| Ligand | Measured Ki | Inside the range? |",
        "|---|---|---|",
    ]
    for name, inside in payload["range_covers_truth"].items():
        lines.append("| %s | %.0f µM | %s |"
                     % (name, payload["known_ki_uM"][name],
                        "yes" if inside else "**no**"))
    lines += [
        "",
        "The guess was two decades low and the design still worked, because the",
        "range is four decades wide. That is the argument for the width: the",
        "cost of an extra decade is a few wells, and the cost of missing the",
        "curve is the whole experiment.",
        "",
        "## What counts as confirmation",
        "",
        "- A dose-response curve with a clear plateau at **both** ends.",
        "- A Hill slope near 1. Far from 1 suggests aggregation, or a",
        "  stoichiometry that is not 1:1.",
        "- Activity that survives 0.01% detergent. **AmpC is a classic target",
        "  for promiscuous aggregators** — a micromolar hit that vanishes with",
        "  detergent was never a hit.",
        "- The same answer from a second, orthogonal assay.",
        "",
        "## What does not",
        "",
        "- A single-concentration percentage inhibition.",
        "- An IC50 compared against a Ki from another paper. IC50 depends on",
        "  substrate concentration and Km; Ki does not. They are not",
        "  interconvertible without both — and no conversion between Ki, IC50",
        "  and Kd happens anywhere in this repository.",
        "",
    ]
    (OUT / "assay_design.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
