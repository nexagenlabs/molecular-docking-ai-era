#!/usr/bin/env python3
"""Chapter 22 — can a free-energy calculation resolve this series at all?

    python ch22_free_energy/scripts/power.py

Before running an alchemical calculation, ask what precision the question
needs. It is a two-line calculation and it is almost never done.

Two independent estimates each with standard error σ give a *difference* with
standard error σ√2. To be 95% confident that a difference of Δ is not zero you
need

    Δ > 1.96 · σ√2      i.e.      σ < Δ / 2.77

This script runs that for the AmpC series and for a few sizes of effect worth
caring about, against the statistical errors free-energy methods actually
report.

**No MD or FEP software is required, and none is used.** The point is upstream
of the calculation: whether the calculation could answer the question even if
it ran perfectly.

Writes outputs/power.json and outputs/power.md.
"""
import json
import math
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

RT = 0.001987 * 298.15          # kcal/mol at 25 C
CONFIDENCE_Z = 1.96             # two-sided 95%

# Statistical errors that alchemical methods report. These are the *statistical*
# error only -- the uncertainty from finite sampling of a given force field.
# Force-field error is separate, larger, and does not shrink with more sampling.
REPORTED_ERRORS = {
    "well-converged FEP, one edge": 0.20,
    "typical production FEP": 0.35,
    "short FEP or small lambda ladder": 0.50,
    "MM-GBSA (no formal error bar; typical spread)": 1.50,
}

# The series in this repository, and some differences worth resolving.
QUESTIONS = {
    "AmpC series, full spread (18-31 µM)": None,      # computed below
    "a 2-fold difference in Ki": None,
    "a 10-fold difference in Ki": None,
    "a 100-fold difference in Ki": None,
}

KI = {"STC": 26.0, "18U": 18.0, "1MU_chembl": 26.0, "1MU_pdbbind": 31.0}


def dg(ki_micromolar):
    """Ki in µM to ΔG in kcal/mol. This direction only."""
    return RT * math.log(ki_micromolar * 1e-6)


def required_sigma(delta, z=CONFIDENCE_Z):
    """Largest per-estimate σ that still resolves a difference of `delta`."""
    return delta / (z * math.sqrt(2))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    series_spread = abs(dg(max(KI.values())) - dg(min(KI.values())))
    deltas = {
        "AmpC series, full spread (18-31 uM)": series_spread,
        "a 2-fold difference in Ki": abs(RT * math.log(2)),
        "a 10-fold difference in Ki": abs(RT * math.log(10)),
        "a 100-fold difference in Ki": abs(RT * math.log(100)),
    }

    print("Ki to free energy (this direction only -- no conversion between Ki,")
    print("IC50 and Kd happens anywhere in this repository):\n")
    for name, ki in KI.items():
        print("   %-16s %5.1f uM -> %.2f kcal/mol" % (name, ki, dg(ki)))
    print("\n   full spread of the series: %.2f kcal/mol" % series_spread)

    print("\nWhat precision each question needs, at 95%% confidence:\n")
    print("   %-38s %-10s %s" % ("question", "delta", "sigma must be below"))
    requirements = {}
    for name, delta in deltas.items():
        sigma = required_sigma(delta)
        requirements[name] = {"delta_kcal": round(delta, 3),
                              "required_sigma_kcal": round(sigma, 3)}
        print("   %-38s %-10.2f %.3f kcal/mol" % (name, delta, sigma))

    print("\nAgainst the statistical errors these methods report:\n")
    print("   %-46s %s" % ("method", "can it resolve..."))
    verdicts = {}
    for method, sigma in REPORTED_ERRORS.items():
        resolvable = [name for name, req in requirements.items()
                      if sigma <= req["required_sigma_kcal"]]
        verdicts[method] = {"sigma_kcal": sigma, "can_resolve": resolvable}
        if resolvable:
            print("   %-46s %s" % (method, "; ".join(resolvable)))
        else:
            print("   %-46s %s" % (method, "none of the above"))

    best = min(REPORTED_ERRORS.values())
    needed = requirements["AmpC series, full spread (18-31 uM)"]["required_sigma_kcal"]
    print("\nThe AmpC series spans %.2f kcal/mol, so resolving its two ends needs"
          % series_spread)
    print("sigma below %.3f kcal/mol. The best statistical error in the table is"
          % needed)
    print("%.2f -- %.0fx too large." % (best, best / needed))
    print("\nAnd that comparison flatters the method twice over:")
    print("  * it is the statistical error only. Force-field error is separate,")
    print("    larger, and does not shrink with more sampling.")
    print("  * ChEMBL and PDBbind disagree about 1MU by %.2f kcal/mol, which is"
          % abs(dg(KI["1MU_chembl"]) - dg(KI["1MU_pdbbind"])))
    print("    %.0f%% of the whole spread being resolved. The experimental answer"
          % (100 * abs(dg(KI["1MU_chembl"]) - dg(KI["1MU_pdbbind"])) / series_spread))
    print("    is not known to the precision the calculation is being asked for.")
    print("\nThe useful conclusion is not 'FEP is bad'. It is that this series is")
    print("the wrong experiment, and two lines of arithmetic said so before any")
    print("compute was spent.")

    payload = {
        "rt_kcal": round(RT, 6),
        "confidence_z": CONFIDENCE_Z,
        "ki_uM": KI,
        "dg_kcal": {k: round(dg(v), 3) for k, v in KI.items()},
        "series_spread_kcal": round(series_spread, 3),
        "requirements": requirements,
        "reported_errors": verdicts,
        "experimental_disagreement_kcal":
            round(abs(dg(KI["1MU_chembl"]) - dg(KI["1MU_pdbbind"])), 3),
    }
    (OUT / "power.json").write_text(json.dumps(payload, indent=2) + "\n",
                                    encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "power.json"))


def write_report(payload):
    lines = [
        "# Chapter 22 — free energy: can the question be answered?", "",
        "Two independent estimates with standard error σ give a difference with",
        "standard error σ√2, so resolving a difference Δ at 95% confidence needs",
        "",
        "    σ < Δ / 2.77",
        "",
        "## The series", "",
        "| | Ki | ΔG |",
        "|---|---|---|",
    ]
    for name, ki in payload["ki_uM"].items():
        lines.append("| %s | %.1f µM | %.2f kcal/mol |"
                     % (name, ki, payload["dg_kcal"][name]))
    lines += [
        "",
        "Full spread: **%.2f kcal/mol**." % payload["series_spread_kcal"],
        "",
        "## What each question needs", "",
        "| Question | Δ | σ must be below |",
        "|---|---|---|",
    ]
    for name, req in payload["requirements"].items():
        lines.append("| %s | %.2f kcal/mol | **%.3f kcal/mol** |"
                     % (name, req["delta_kcal"], req["required_sigma_kcal"]))
    lines += [
        "",
        "## Against what methods actually report", "",
        "| Method | Statistical σ | Can resolve |",
        "|---|---|---|",
    ]
    for method, entry in payload["reported_errors"].items():
        lines.append("| %s | %.2f | %s |"
                     % (method, entry["sigma_kcal"],
                        "; ".join(entry["can_resolve"]) or "**nothing above**"))
    needed = payload["requirements"]["AmpC series, full spread (18-31 uM)"]["required_sigma_kcal"]
    lines += [
        "",
        "Resolving the two ends of the AmpC series needs σ below **%.3f**." % needed,
        "The best statistical error in the table is 0.20 — **%.0f× too large**."
        % (0.20 / needed),
        "",
        "And that comparison flatters the method twice:",
        "",
        "- It is the **statistical** error only: the uncertainty from finite",
        "  sampling of a given force field. Force-field error is separate,",
        "  larger, and does not shrink with more sampling.",
        "- ChEMBL and PDBbind disagree about 1MU by **%.2f kcal/mol** — %.0f%% of"
        % (payload["experimental_disagreement_kcal"],
           100 * payload["experimental_disagreement_kcal"] / payload["series_spread_kcal"]),
        "  the entire spread being resolved. **The experimental answer is not",
        "  known to the precision the calculation is being asked for.**",
        "",
        "## The point",
        "",
        "Not that free-energy methods are bad. They resolve a 10-fold difference",
        "in Ki comfortably, and that is a question worth asking. The point is",
        "that *this* series is the wrong experiment for them, and two lines of",
        "arithmetic establish it before any compute is spent.",
        "",
        "Chapter 14 reaches the same conclusion for a correlation-based method,",
        "and Chapter 26 reaches it by trying the ranking and failing.",
        "",
        "## No software was needed",
        "",
        "No MD or FEP package is used here, and that is not a limitation of this",
        "environment — the question is upstream of the calculation. Whether the",
        "calculation *could* answer the question, if it ran perfectly, is decided",
        "by the size of the effect and the precision of the method, both of which",
        "are known before anything is submitted.",
        "",
    ]
    (OUT / "power.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
