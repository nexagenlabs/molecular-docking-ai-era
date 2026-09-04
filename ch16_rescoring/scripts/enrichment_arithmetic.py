#!/usr/bin/env python3
"""Chapter 16 — what a rescoring enrichment factor is worth.

    python ch16_rescoring/scripts/enrichment_arithmetic.py

The published LIT-PCBA result: **GNINA median EF1% of 1.88–2.58 against Vina's
0.90.**

**EF = 1.0 is chance.** Vina is *below* it — a screen ranked by Vina score puts
fewer actives in its top 1% than picking compounds at random would. That
framing is the chapter, and it disappears the moment the two numbers are quoted
as "2.58 versus 0.90", which reads as a method that is roughly three times
better than a method that works.

This script does the arithmetic that turns those figures into decisions: how
many compounds you have to buy and test to find a given number of actives.

Writes outputs/rescoring.json and outputs/rescoring.md.
"""
import json
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
OUT = CH / "outputs"

# LIT-PCBA, as published.
METHODS = {
    "random": {"ef1": 1.00, "what": "picking compounds with your eyes shut"},
    "Vina": {"ef1": 0.90, "what": "docking score, no rescoring"},
    "GNINA (low)": {"ef1": 1.88, "what": "CNN rescoring, low end of the range"},
    "GNINA (high)": {"ef1": 2.58, "what": "CNN rescoring, high end of the range"},
}

LIBRARY = 1_000_000        # compounds in the screening library
HIT_RATE = 0.001           # 0.1% of the library is genuinely active
WANTED = 10                # actives you need in hand to start a project
COST_PER_COMPOUND = 50.0   # currency units to buy and assay one compound


def compounds_needed(ef, hit_rate=HIT_RATE, wanted=WANTED):
    """How many top-ranked compounds you must test to find `wanted` actives."""
    effective_rate = hit_rate * ef
    if effective_rate <= 0:
        return None
    return wanted / effective_rate


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    print("LIT-PCBA median EF1%%, and what it costs to find %d actives" % WANTED)
    print("(library %s compounds, %.1f%% genuinely active)\n"
          % ("{:,}".format(LIBRARY), 100 * HIT_RATE))
    print("%-14s %-8s %-14s %-16s %s"
          % ("method", "EF1%", "vs chance", "compounds tested", "cost"))

    results = {}
    for name, spec in METHODS.items():
        ef = spec["ef1"]
        needed = compounds_needed(ef)
        results[name] = {
            "ef1": ef,
            "what": spec["what"],
            "compounds_to_test": round(needed),
            "cost": round(needed * COST_PER_COMPOUND),
            "better_than_chance": ef > 1.0,
        }
        print("%-14s %-8.2f %-14s %-16s %s"
              % (name, ef,
                 "better" if ef > 1.0 else ("chance" if ef == 1.0 else "WORSE"),
                 "{:,}".format(round(needed)),
                 "{:,}".format(round(needed * COST_PER_COMPOUND))))

    random_cost = results["random"]["cost"]
    vina = results["Vina"]
    print("\nVina's EF1%% of %.2f is below 1.0, so ranking a library by Vina score"
          % vina["ef1"])
    print("and testing the top slice is worse than not ranking it at all:")
    print("%s compounds against %s, costing %s more."
          % ("{:,}".format(vina["compounds_to_test"]),
             "{:,}".format(results["random"]["compounds_to_test"]),
             "{:,}".format(vina["cost"] - random_cost)))

    best = results["GNINA (high)"]
    print("\nGNINA at the top of its range gets you to %d actives for %s"
          % (WANTED, "{:,}".format(best["compounds_to_test"])))
    print("compounds -- %.1fx fewer than random, %.1fx fewer than Vina."
          % (results["random"]["compounds_to_test"] / best["compounds_to_test"],
             vina["compounds_to_test"] / best["compounds_to_test"]))
    print("\nReal, and modest. An EF of 2.58 means the top 1% of your ranked")
    print("library is 2.58 times richer in actives than the library -- not that")
    print("2.58 out of 3 hits are real, which is how the number tends to be read.")

    payload = {"library": LIBRARY, "hit_rate": HIT_RATE, "wanted_actives": WANTED,
               "cost_per_compound": COST_PER_COMPOUND,
               "chance_ef": 1.0, "methods": results,
               "vina_is_below_chance": not vina["better_than_chance"]}
    (OUT / "rescoring.json").write_text(json.dumps(payload, indent=2) + "\n",
                                        encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "rescoring.json"))


def write_report(payload):
    results = payload["methods"]
    lines = [
        "# Chapter 16 — rescoring", "",
        "LIT-PCBA median EF1%, and what each is worth in compounds bought.",
        "",
        "Library of %s, %.1f%% genuinely active, %d actives wanted in hand."
        % ("{:,}".format(payload["library"]), 100 * payload["hit_rate"],
           payload["wanted_actives"]),
        "",
        "| Method | EF1% | Against chance | Compounds to test | Cost |",
        "|---|---|---|---|---|",
    ]
    for name, entry in results.items():
        verdict = ("better" if entry["ef1"] > 1.0
                   else "**chance**" if entry["ef1"] == 1.0 else "**worse**")
        lines.append("| %s | %.2f | %s | %s | %s |"
                     % (name, entry["ef1"], verdict,
                        "{:,}".format(entry["compounds_to_test"]),
                        "{:,}".format(entry["cost"])))
    vina = results["Vina"]
    lines += [
        "",
        "## EF = 1.0 is chance",
        "",
        "**Vina's 0.90 is below it.** Ranking a library by Vina score and testing",
        "the top slice finds fewer actives than testing the same number of",
        "compounds picked at random — %s tested against %s, for %s more spent."
        % ("{:,}".format(vina["compounds_to_test"]),
           "{:,}".format(results["random"]["compounds_to_test"]),
           "{:,}".format(vina["cost"] - results["random"]["cost"])),
        "",
        "Quoted as *\"GNINA 2.58 against Vina 0.90\"*, this reads as one method",
        "being about three times better than another method that works. One of",
        "them does not work. Keep the 1.0 in the sentence.",
        "",
        "## And GNINA's improvement is real, and modest",
        "",
        "An EF1% of 2.58 means the top 1% of the ranked library is 2.58 times",
        "richer in actives than the library as a whole. It does not mean that",
        "2.58 out of every 3 hits are real, which is how the number tends to get",
        "read. On the arithmetic above it takes you from %s compounds to %s."
        % ("{:,}".format(results["random"]["compounds_to_test"]),
           "{:,}".format(results["GNINA (high)"]["compounds_to_test"])),
        "",
        "That is a genuine and useful gain. It is not a solved problem.",
        "",
    ]
    (OUT / "rescoring.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
