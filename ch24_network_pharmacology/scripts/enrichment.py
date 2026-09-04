#!/usr/bin/env python3
"""Chapter 24 — enrichment analysis refuses to run without a background.

    python ch24_network_pharmacology/scripts/enrichment.py --background genome
    python ch24_network_pharmacology/scripts/enrichment.py --compare

**Running this without --background is an error, not a default.** That refusal
is the chapter's argument, so it is implemented rather than described.

A pathway-enrichment p-value is a statement about a hit list *relative to a
universe of genes that could have been hits*. Change the universe and the
p-value changes, often by orders of magnitude, with nothing in the output
indicating that anything was assumed. Most tools pick a background silently —
usually the whole annotated genome — and that choice is almost always wrong for
a screen, because a screen could only ever have hit what it assayed.

Writes outputs/enrichment.json and outputs/enrichment.md.
"""
import argparse
import json
import sys
from fractions import Fraction
from math import comb
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# A worked example with round numbers, so the arithmetic can be checked by
# hand. The shape is what matters, not these particular genes.
#
# The overlap is chosen so that the three backgrounds DISAGREE about
# significance at p < 0.05, because that is the decision rule people actually
# apply. At an overlap of 11 or more all three call it significant and the
# demonstration is only about effect size; at 10 or fewer the narrowest
# background says no while the other two say yes. That choice is a teaching
# decision and is stated here rather than left to look like data.
HITS = 120              # genes coming out of the screen
PATHWAY = 80            # genes annotated to the pathway being tested
OVERLAP = 10            # hits that are in the pathway

# Three defensible universes for the same experiment. Every one of them is a
# real choice somebody makes; none of them is the obvious right answer, which
# is exactly why it has to be stated.
BACKGROUNDS = {
    "genome": {
        "size": 20000,
        "what": "every annotated protein-coding gene",
        "why": "the default in most tools, and the one nobody chose on purpose",
    },
    "expressed": {
        "size": 12000,
        "what": "genes expressed in the tissue the screen was run in",
        "why": "a gene not expressed here could never have been a hit",
    },
    "assayed": {
        "size": 1500,
        "what": "genes the assay could actually detect",
        "why": "a targeted panel; the screen could only ever have hit these",
    },
}


def hypergeometric_sf(overlap, background, pathway, hits):
    """P(X >= overlap) for a hypergeometric draw. Exact, no approximation.

    Summed as integers and divided as a Fraction. comb(20000, 120) has some
    four hundred digits, so dividing in floating point raises OverflowError --
    which is the good outcome. The bad one is a library that quietly returns
    inf or 0.0 and lets a p-value of zero into a figure.
    """
    denominator = comb(background, hits)
    upper = min(pathway, hits)
    total = sum(comb(pathway, k) * comb(background - pathway, hits - k)
                for k in range(overlap, upper + 1))
    return float(Fraction(total, denominator))


def hypergeometric_sf_scipy(overlap, background, pathway, hits):
    """The same quantity from scipy, as a second opinion."""
    try:
        from scipy.stats import hypergeom
    except ImportError:
        return None
    return float(hypergeom.sf(overlap - 1, background, pathway, hits))


def fold_enrichment(overlap, background, pathway, hits):
    expected = hits * pathway / background
    return overlap / expected


def analyse(name, spec):
    background = spec["size"]
    if PATHWAY > background or HITS > background:
        sys.exit("background %s (%d) is smaller than the hit list or the pathway"
                 % (name, background))
    p = hypergeometric_sf(OVERLAP, background, PATHWAY, HITS)
    p_scipy = hypergeometric_sf_scipy(OVERLAP, background, PATHWAY, HITS)
    fold = fold_enrichment(OVERLAP, background, PATHWAY, HITS)
    return {"background": name, "size": background, "what": spec["what"],
            "why": spec["why"], "p_value": p, "p_value_scipy": p_scipy,
            "agrees_with_scipy": (p_scipy is not None
                                  and abs(p - p_scipy) < 1e-12 * max(p, 1e-300)
                                  or p_scipy is not None
                                  and abs(p - p_scipy) <= 1e-15),
            "fold_enrichment": round(fold, 2),
            "expected_overlap": round(HITS * PATHWAY / background, 2),
            "significant_at_0.05": bool(p < 0.05)}


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--background", choices=sorted(BACKGROUNDS),
                    help="REQUIRED. Which universe of genes could have been hits.")
    ap.add_argument("--compare", action="store_true",
                    help="run all three backgrounds side by side")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if not args.background and not args.compare:
        # The refusal. Not a warning, not a default with a note in the log --
        # a non-zero exit, because a p-value computed against an unstated
        # background is not a weaker result, it is not a result.
        print("REFUSING TO RUN: no background gene list given.\n", file=sys.stderr)
        print("An enrichment p-value is a statement about a hit list relative to",
              file=sys.stderr)
        print("a universe of genes that could have been hits. Without that", file=sys.stderr)
        print("universe the number means nothing -- and it will still look like",
              file=sys.stderr)
        print("a p-value, print to three decimals, and go into a figure.\n", file=sys.stderr)
        print("Choose one and say so:\n", file=sys.stderr)
        for name, spec in sorted(BACKGROUNDS.items()):
            print("  --background %-10s %d genes: %s"
                  % (name, spec["size"], spec["what"]), file=sys.stderr)
        print("\nOr --compare to see what the choice is worth.", file=sys.stderr)
        sys.exit(2)

    names = sorted(BACKGROUNDS) if args.compare else [args.background]
    results = [analyse(name, BACKGROUNDS[name]) for name in names]

    print("Hit list %d genes, pathway %d genes, overlap %d.\n"
          % (HITS, PATHWAY, OVERLAP))
    print("%-11s %-8s %-10s %-12s %-12s %s"
          % ("background", "size", "expected", "fold", "p-value", "significant?"))
    for r in results:
        print("%-11s %-8d %-10.2f %-12.2f %-12.3g %s"
              % (r["background"], r["size"], r["expected_overlap"],
                 r["fold_enrichment"], r["p_value"],
                 "yes" if r["significant_at_0.05"] else "no"))

    if len(results) > 1:
        strongest = min(results, key=lambda r: r["p_value"])
        weakest = max(results, key=lambda r: r["p_value"])
        ratio = weakest["p_value"] / strongest["p_value"]
        print("\nSame hits, same pathway, same overlap.")
        print("The p-value moves by a factor of %.3g between the widest and the"
              % ratio)
        print("narrowest background: %.3g against %.3g."
              % (weakest["p_value"], strongest["p_value"]))
        disagree = len({r["significant_at_0.05"] for r in results}) > 1
        if disagree:
            print("\nThey do not even agree on significance at p < 0.05. The")
            print("conclusion is a property of the background, and the background")
            print("is the one thing most tools choose for you silently.")
        else:
            print("\nHere they happen to agree on significance -- but the effect")
            print("size differs by %.1fx, which is what goes in the abstract."
                  % (max(r["fold_enrichment"] for r in results)
                     / min(r["fold_enrichment"] for r in results)))

    agree = [r for r in results if r["p_value_scipy"] is not None]
    if agree:
        worst = max(abs(r["p_value"] - r["p_value_scipy"]) for r in agree)
        print("\nExact integer arithmetic against scipy.stats.hypergeom:")
        print("largest difference %.3g -- computed twice by different routes."
              % worst)

    payload = {"hits": HITS, "pathway": PATHWAY, "overlap": OVERLAP,
               "results": results,
               "backgrounds_available": BACKGROUNDS}
    (OUT / "enrichment.json").write_text(json.dumps(payload, indent=2) + "\n",
                                         encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "enrichment.json"))


def write_report(payload):
    results = payload["results"]
    lines = [
        "# Chapter 24 — network pharmacology", "",
        "Hit list %d genes, pathway %d genes, overlap %d. One experiment, three"
        % (payload["hits"], payload["pathway"], payload["overlap"]),
        "defensible backgrounds.", "",
        "| Background | Size | Expected overlap | Fold enrichment | p-value | Significant? |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append("| **%s** | %d | %.2f | %.2f | %.3g | %s |"
                     % (r["background"], r["size"], r["expected_overlap"],
                        r["fold_enrichment"], r["p_value"],
                        "yes" if r["significant_at_0.05"] else "**no**"))
    lines += ["", "What each background means:", ""]
    for r in results:
        lines.append("- **%s** (%d) — %s. %s"
                     % (r["background"], r["size"], r["what"], r["why"]))
    if len(results) > 1:
        strongest = min(results, key=lambda r: r["p_value"])
        weakest = max(results, key=lambda r: r["p_value"])
        lines += [
            "",
            "The same twelve genes are %.3g against %.3g depending only on what"
            % (weakest["p_value"], strongest["p_value"]),
            "you counted as *could have been a hit*. Nothing in a tool's output",
            "tells you which universe it used.",
            "",
        ]
    lines += [
        "## The refusal",
        "",
        "```",
        "$ python ch24_network_pharmacology/scripts/enrichment.py",
        "REFUSING TO RUN: no background gene list given.",
        "```",
        "",
        "Exit code 2, no result. Not a warning, not a default with a note in the",
        "log. A p-value computed against an unstated background is not a weaker",
        "result — it is not a result — and it will still print to three decimals",
        "and go into a figure.",
        "",
        "This is the only script in the repository that refuses to do the thing",
        "it is for. That is the chapter.",
        "",
    ]
    (OUT / "enrichment.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
