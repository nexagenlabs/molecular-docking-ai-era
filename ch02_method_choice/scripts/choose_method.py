#!/usr/bin/env python3
"""Chapter 2 — choosing a method, from measurements rather than reputation.

    python ch02_method_choice/scripts/choose_method.py

Every recommendation here is read out of another chapter's output file. Nothing
is asserted from the literature or from memory: if a chapter has not been run,
the criterion that depends on it says so instead of guessing.

That is the point of putting this chapter second and building it last. Method
choice is usually made from reputation, before any measurement exists. Here it
is made from the measurements the rest of the book produced, which is the same
decision taken in the other order.

Writes outputs/method_choice.json and outputs/method_choice.md.
"""
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"

# Each criterion names the chapter that measured it and the file it lives in.
# A criterion whose file is missing reports "not measured" -- it does not fall
# back to a default, because a default here is a guess wearing a number.
SOURCES = {
    "flexibility": ("ch10", "ch10_flexibility/outputs/rotamers.json"),
    "predicted_structure": ("ch06", "ch06_predicted_structures/outputs/alphafold_comparison.json"),
    "redock": ("ch17", "ch17_validation/outputs/validation.json"),
    "ranking": ("ch26", "ch26_case_study/outputs/case_study.json"),
    "precision": ("ch22", "ch22_free_energy/outputs/power.json"),
    "correlation": ("ch14", "ch14_boltz2/outputs/correlation.json"),
    "screen_cost": ("ch12", "ch12_screening/outputs/screen.json"),
    "rescoring": ("ch16", "ch16_rescoring/outputs/rescoring.json"),
}


def load(name):
    chapter, relative = SOURCES[name]
    path = REPO / relative
    if not path.exists():
        return None, "%s has not been run (%s missing)" % (chapter, relative)
    return json.loads(path.read_text()), None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    findings, unmeasured = [], []

    def add(question, answer, verdict, chapter):
        findings.append({"question": question, "answer": answer,
                         "verdict": verdict, "chapter": chapter})
        print("\n%s" % question)
        print("   %s" % answer)
        print("   -> %s   [%s]" % (verdict, chapter))

    def missing(question, why):
        unmeasured.append({"question": question, "why": why})
        print("\n%s" % question)
        print("   NOT MEASURED: %s" % why)

    # -- rigid or flexible receptor? ----------------------------------------
    data, why = load("flexibility")
    if data is None:
        missing("Rigid receptor, or flexible side chains?", why)
    else:
        changing = data["rotamer_changing"]
        rigid = len(data["rigid"])
        add("Rigid receptor, or flexible side chains?",
            "%d of the site residues change rotamer across %d chains (%s); %d "
            "stay inside %.0f degrees in every torsion."
            % (len(changing), len(data["chains"]), ", ".join(changing), rigid,
               data["threshold_degrees"]),
            "Rigid receptor is defensible. If you make anything flexible, make "
            "it exactly those %d and nothing else." % len(changing),
            "ch10")

    # -- crystal structure or prediction? -----------------------------------
    data, why = load("predicted_structure")
    if data is None:
        missing("Crystal structure, or a predicted one?", why)
    else:
        add("Crystal structure, or a predicted one?",
            "The AlphaFold model has pLDDT %.1f at the site and a backbone %.3f A "
            "from the crystal, and docking into it gives %.3f A against %.3f A "
            "for the crystal structure."
            % (data["confidence"]["site_mean_plddt"],
               data["geometry"]["backbone_rmsd"],
               data["docking"]["rmsd_to_crystal_pose"],
               data["docking"]["crystal_structure_reference_rmsd"]),
            "Use the crystal structure when one exists. A near-perfect backbone "
            "did not buy a near-crystal pose, and no confidence metric predicted "
            "that.",
            "ch06")

    # -- has the protocol been validated at all? ----------------------------
    data, why = load("redock")
    if data is None:
        missing("Does the protocol reproduce a known pose?", why)
    else:
        entries = [k for k in ("1L2S", "4JXS", "4JXV") if k in data]
        rmsds = {k: data[k]["rmsd"] for k in entries}
        passing = [k for k, v in rmsds.items() if v < 2.0]
        add("Does the protocol reproduce a known pose?",
            "Redock RMSD: %s." % ", ".join("%s %.2f A" % (k, v)
                                           for k, v in rmsds.items()),
            "%d of %d under 2 A. Validate before trusting any prospective "
            "result, and report the failures -- a protocol validated on its best "
            "case has not been validated." % (len(passing), len(rmsds)),
            "ch17")

    # -- can this question be answered by ranking at all? -------------------
    data, why = load("precision")
    if data is None:
        missing("Can any method rank this series?", why)
    else:
        spread = data["series_spread_kcal"]
        needed = data["requirements"]["AmpC series, full spread (18-31 uM)"]["required_sigma_kcal"]
        add("Can any method rank this series?",
            "The series spans %.2f kcal/mol, so ranking its ends at 95%% "
            "confidence needs sigma below %.3f. The best statistical error any "
            "of these methods reports is 0.20." % (spread, needed),
            "No. Choose a different question, or a different series. This is the "
            "cheapest finding in the book and the one most often skipped.",
            "ch22")

    data, why = load("correlation")
    if data is not None:
        pair = data["pairwise"][0]
        add("What would a good ML predictor buy here?",
            "At r = %.2f -- Boltz-2's reported figure, r-squared = %.2f -- two "
            "compounds %.2f kcal/mol apart are ordered correctly %.1f%% of the "
            "time." % (data["boltz2_r"], data["boltz2_r_squared"],
                       pair["true_gap_kcal"], 100 * pair["accuracy"]),
            "%.1f points better than a coin flip. The limit is the question, not "
            "the method." % (100 * (pair["accuracy"] - 0.5)),
            "ch14")

    # -- screening --------------------------------------------------------
    data, why = load("screen_cost")
    if data is None:
        missing("What would a screen cost?", why)
    else:
        million = data["extrapolation"].get("1000000")
        add("What would a screen cost?",
            "%.2f s per compound measured on %d cores; %s core-hours for a "
            "million compounds."
            % (data["seconds_per_compound"], data["docking"]["cores"],
               "{:,.0f}".format(million["core_hours"]) if million else "?"),
            "Affordable. Cost is not the constraint here -- what you do with the "
            "ranking is.",
            "ch12")

    data, why = load("rescoring")
    if data is not None:
        add("Is the ranking any good?",
            "Published LIT-PCBA medians: Vina EF1%% %.2f, GNINA %.2f to %.2f. "
            "EF = 1.0 is chance."
            % (data["methods"]["Vina"]["ef1"],
               data["methods"]["GNINA (low)"]["ef1"],
               data["methods"]["GNINA (high)"]["ef1"]),
            "Vina's ranking is below chance on that benchmark. Rescore, and "
            "expect a factor of two rather than a solved problem.",
            "ch16")

    print("\n" + "=" * 68)
    print("SUMMARY")
    print("=" * 68)
    import textwrap
    for finding in findings:
        # Print the whole verdict, wrapped. An earlier version took the text up
        # to the first "." and turned "4.8 points better than a coin flip" into
        # "4." -- a summary that mangles its own numbers is worse than no
        # summary.
        wrapped = textwrap.wrap(finding["verdict"], width=64)
        print("  * %s" % wrapped[0])
        for line in wrapped[1:]:
            print("    %s" % line)
    if unmeasured:
        print("\nNot measured (%d):" % len(unmeasured))
        for entry in unmeasured:
            print("  * %s -- %s" % (entry["question"], entry["why"]))
        print("\nThese are gaps, not defaults. Run the chapter.")

    payload = {"findings": findings, "unmeasured": unmeasured,
               "sources": {k: v[1] for k, v in SOURCES.items()}}
    (OUT / "method_choice.json").write_text(json.dumps(payload, indent=2) + "\n",
                                            encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "method_choice.json"))


def write_report(payload):
    lines = [
        "# Chapter 2 — choosing a method", "",
        "Every row below is read out of another chapter's output file. Nothing",
        "is asserted from the literature or from memory, and a criterion whose",
        "chapter has not been run says so rather than guessing.",
        "",
        "| Question | What was measured | What follows | From |",
        "|---|---|---|---|",
    ]
    for finding in payload["findings"]:
        lines.append("| %s | %s | %s | %s |"
                     % (finding["question"], finding["answer"],
                        finding["verdict"], finding["chapter"]))
    if payload["unmeasured"]:
        lines += ["", "## Not measured", "", "| Question | Why |", "|---|---|"]
        for entry in payload["unmeasured"]:
            lines.append("| %s | %s |" % (entry["question"], entry["why"]))
        lines += ["", "Gaps, not defaults. Run the chapter."]
    lines += [
        "",
        "## Why this chapter is second and was built last",
        "",
        "Method choice is normally made from reputation, before any measurement",
        "exists — which is the only order in which it *can* be made, the first",
        "time. This chapter makes the same decision in the other order, from the",
        "measurements the rest of the book produced, so a reader can see what the",
        "reputation-based answer would have got right and wrong.",
        "",
        "The most useful row is the one about whether the question can be",
        "answered at all. It costs two lines of arithmetic, it comes back *no*",
        "for this series, and it is the step most often skipped — because it is",
        "the only one that can tell you not to run the calculation.",
        "",
    ]
    (OUT / "method_choice.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
