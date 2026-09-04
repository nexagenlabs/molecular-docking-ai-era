#!/usr/bin/env python3
"""Chapter 15 — the co-folding field, and what the headline numbers mean.

    python ch15_cofolding_field/scripts/compare_methods.py

A table of what these methods report, with the arithmetic that makes the
figures comparable. Every entry carries the *form* of its metric, because the
central failure in reading this literature is comparing an r against an R² —
which Chapter 14 shows reverses the ranking of two specific methods.

The numbers here are as published. The columns this script adds are the
comparable ones: variance explained, and what that correlation is worth when
ranking two compounds a given distance apart.

Writes outputs/field_comparison.json and .md.
"""
import json
import math
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# As published. `metric` is the FORM of the reported number, which is the
# column that actually matters -- see below.
METHODS = [
    {"name": "Boltz-2", "metric": "r", "value": 0.62,
     "benchmark": "FEP+ benchmark",
     "note": "affinity prediction alongside structure"},
    {"name": "FEP+", "metric": "R2", "value": 0.52,
     "benchmark": "FEP+ benchmark",
     "note": "alchemical free energy, not a folding model"},
    {"name": "Vina (docking)", "metric": "EF1%", "value": 0.90,
     "benchmark": "LIT-PCBA",
     "note": "below chance; EF = 1.0 is chance"},
    {"name": "GNINA (rescoring)", "metric": "EF1%", "value": 2.58,
     "benchmark": "LIT-PCBA",
     "note": "CNN rescoring of Vina poses, top of the reported range"},
]

# The spread of the series in this repository, for the ranking column.
SERIES_SPREAD_KCAL = 0.32
TYPICAL_SPREAD_KCAL = 1.5


def variance_explained(entry):
    """Put every correlation on the same footing: r squared."""
    if entry["metric"] == "r":
        return entry["value"] ** 2
    if entry["metric"] == "R2":
        return entry["value"]
    return None


def pairwise_accuracy(r, gap_kcal, sigma=TYPICAL_SPREAD_KCAL):
    """P(two compounds ordered correctly), closed form."""
    if r is None or r <= 0 or r >= 1:
        return None
    z = r * (gap_kcal / sigma) / math.sqrt(2 * (1 - r * r))
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("%-20s %-8s %-8s %-12s %-10s %s"
          % ("method", "metric", "value", "r-squared", "P(rank)", "benchmark"))
    rows = []
    for entry in METHODS:
        r2 = variance_explained(entry)
        r = math.sqrt(r2) if r2 is not None else None
        accuracy = pairwise_accuracy(r, SERIES_SPREAD_KCAL)
        rows.append({**entry, "variance_explained": r2,
                     "implied_r": round(r, 3) if r is not None else None,
                     "pairwise_accuracy_series": accuracy})
        print("%-20s %-8s %-8.2f %-12s %-10s %s"
              % (entry["name"], entry["metric"], entry["value"],
                 "%.3f" % r2 if r2 is not None else "n/a",
                 "%.3f" % accuracy if accuracy is not None else "n/a",
                 entry["benchmark"]))

    boltz = next(r for r in rows if r["name"] == "Boltz-2")
    fep = next(r for r in rows if r["name"] == "FEP+")
    print("\nThe comparison that goes wrong:")
    print("   Boltz-2 r = %.2f against FEP+ R-squared = %.2f reads as +%.2f."
          % (boltz["value"], fep["value"], boltz["value"] - fep["value"]))
    print("   Squared, it is %.2f against %.2f: %.2f the OTHER way."
          % (boltz["variance_explained"], fep["variance_explained"],
             fep["variance_explained"] - boltz["variance_explained"]))
    print("   Same two numbers, opposite conclusion, one keystroke apart.")

    print("\nThe comparison that also goes wrong:")
    vina = next(r for r in rows if r["name"].startswith("Vina"))
    gnina = next(r for r in rows if r["name"].startswith("GNINA"))
    print("   GNINA %.2f against Vina %.2f reads as about 3x better."
          % (gnina["value"], vina["value"]))
    print("   Chance is 1.0. Vina is BELOW it, so one of those two methods is")
    print("   not working and the ratio hides which.")

    print("\nAnd on this series specifically (%.2f kcal/mol spread):"
          % SERIES_SPREAD_KCAL)
    for row in rows:
        if row["pairwise_accuracy_series"] is not None:
            print("   %-20s orders two compounds correctly %.1f%% of the time"
                  % (row["name"], 100 * row["pairwise_accuracy_series"]))
    print("   A coin flip is 50%.")

    payload = {"methods": rows,
               "series_spread_kcal": SERIES_SPREAD_KCAL,
               "assumed_population_spread_kcal": TYPICAL_SPREAD_KCAL}
    (OUT / "field_comparison.json").write_text(json.dumps(payload, indent=2) + "\n",
                                               encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "field_comparison.json"))


def write_report(payload):
    lines = [
        "# Chapter 15 — the co-folding field", "",
        "Published figures, with the columns that make them comparable.",
        "",
        "| Method | Reported | Form | Variance explained | P(correct order) | Benchmark |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["methods"]:
        lines.append("| %s | %.2f | %s | %s | %s | %s |"
                     % (row["name"], row["value"], row["metric"],
                        "%.3f" % row["variance_explained"]
                        if row["variance_explained"] is not None else "—",
                        "%.3f" % row["pairwise_accuracy_series"]
                        if row["pairwise_accuracy_series"] is not None else "—",
                        row["benchmark"]))
    lines += [
        "",
        "The **Form** column is the one that matters. The central failure in",
        "reading this literature is comparing an r against an R².",
        "",
        "## Two comparisons that go wrong",
        "",
        "**Boltz-2 against FEP+.** *r = 0.62 against R² = 0.52* reads as ten",
        "points ahead. Squared, it is **0.38 against 0.52** — fourteen points the",
        "other way. Same two numbers, opposite conclusion, one keystroke apart.",
        "",
        "**GNINA against Vina.** *2.58 against 0.90* reads as about three times",
        "better. **Chance is 1.0**, so Vina is below it: one of those two methods",
        "is not working, and the ratio hides which one.",
        "",
        "## On this series",
        "",
        "The AmpC series spans %.2f kcal/mol. At the correlations above, ordering"
        % payload["series_spread_kcal"],
        "two of its members correctly is a coin flip with a small thumb on it —",
        "the last column, against 0.500 for guessing.",
        "",
        "This is not a ranking of methods. It is a demonstration that the",
        "headline numbers do not compare unless you put them in the same form",
        "first, and that once you do, the differences between them are smaller",
        "than the gap between all of them and the question being asked.",
        "",
        "## Assumption stated",
        "",
        "P(correct order) assumes the population of compounds has a spread of",
        "%.1f kcal/mol, which is typical for a congeneric series and is *wider*"
        % payload["assumed_population_spread_kcal"],
        "than this one. A narrower population would make every figure worse.",
        "",
    ]
    (OUT / "field_comparison.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
