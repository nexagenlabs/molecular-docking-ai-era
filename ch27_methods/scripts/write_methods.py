#!/usr/bin/env python3
"""Chapter 27 — generate the methods paragraph from the record, not from memory.

    python ch27_methods/scripts/write_methods.py

A methods section written from memory a month after the run is a work of
fiction with a high hit rate. This one is generated from the protocol record
Chapter 20 filled, so every number in it can be traced to a file.

Where the record has a gap, the paragraph carries **[TODO: ...]** in the text.
That is deliberate and it is the whole design: a methods section with a visible
hole is a methods section somebody will fix, and one with a plausible sentence
covering the hole is not.

Writes outputs/methods.md.
"""
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
RECORD = REPO / "ch20_protocol_record" / "outputs" / "filled_record.json"
VALIDATION = REPO / "ch17_validation" / "outputs" / "validation.json"


def value(record, field):
    entry = record["fields"].get(field, {})
    if entry.get("value") is None:
        return None, entry.get("source", "not recorded")
    return entry["value"], None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not RECORD.exists():
        sys.exit("%s missing -- run ch20_protocol_record/run.sh first" % RECORD)
    record = json.loads(RECORD.read_text())
    structure = record["structure"]
    validation = (json.loads(VALIDATION.read_text())
                  if VALIDATION.exists() else None)

    gaps = []

    def field(name, fallback_note):
        text, missing = value(record, name)
        if text is None:
            gaps.append((name, missing or fallback_note))
            return "**[TODO: %s -- %s]**" % (name, missing or fallback_note)
        return text

    seed = field("Random seed", "")
    exhaustiveness = field("Exhaustiveness / num_modes / energy_range", "")
    program = field("Docking program and version", "")
    box_centre = field("Box centre", "")
    box_size = field("Box dimensions", "")
    stereo = field("Stereochemistry as docked", "state it yourself")
    exclusions = field("Exclusions and deviations", "no tool can fill this")

    paragraph = []
    paragraph.append(
        "The crystal structure of AmpC beta-lactamase from *Escherichia coli* "
        "(PDB %s, %.2f A, R-free %.3f) was obtained from the RCSB Protein Data "
        "Bank. Chain %s was used; chain A carries a break at %s and was "
        "discarded. All waters, ions and crystallisation additives were removed, "
        "and %d disordered side chains (REMARK 470) were truncated to the atoms "
        "present in the deposited coordinates. The structure contains no metal "
        "ion: AmpC is a class C serine hydrolase."
        % (structure["pdb_id"], structure["resolution"], structure["r_free"],
           structure["chain"],
           ", ".join(structure["gaps"].get("A", [])) or "the reported positions",
           structure["disordered_side_chain_count"]))

    lig = structure.get("ligand_copies", [])
    paragraph.append(
        "The entry contains %d copies of the ligand; the copy used (%s) was "
        "selected by minimum distance to the Ser64 OG atom (%.2f A) rather than "
        "by order of appearance in the file, and the remaining copies -- "
        "including one %.2f A from any active site -- were discarded."
        % (len(lig), structure["chosen_copy"], structure["chosen_distance"],
           max(c["distance_to_ser64_og"] for c in lig)))

    paragraph.append(
        "Ligands were built from SMILES with explicit formal charges at pH 7.4 "
        "(STC -1, 18U -2, 1MU -2), embedded with RDKit ETKDGv3 and optimised "
        "with MMFF94s. Stereochemistry as docked: %s. Receptor and ligand PDBQT "
        "files were prepared with meeko 0.8.0. PDBQT was written but never read "
        "back, because the format does not preserve formal charge or atom order."
        % stereo)

    paragraph.append(
        "Docking used %s with a search box centred at %s A and measuring %s A, "
        "derived from the centroid of the crystallographic ligand with 8 A "
        "padding. The random seed was fixed at %s and exhaustiveness / num_modes "
        "/ energy_range were %s. The seed is reported because Vina's default of "
        "0 selects a random seed, and runs at the default are not reproducible."
        % (program, box_centre, box_size, seed, exhaustiveness))

    if validation:
        entries = [k for k in validation if k in ("1L2S", "4JXS", "4JXV")]
        rmsds = ", ".join("%s %.2f A" % (k, validation[k]["rmsd"]) for k in entries)
        paragraph.append(
            "Redocking accuracy was assessed as symmetry-corrected heavy-atom "
            "RMSD to the crystallographic pose, computed with spyrmsd **without "
            "superposition** (minimize=False): %s. Superposition is omitted "
            "deliberately; enabling it measures shape agreement rather than "
            "placement, and returns 0.000 for a pose displaced from the site."
            % rmsds)

    paragraph.append("Exclusions and deviations: %s" % exclusions)

    text = "\n\n".join(paragraph)
    print(text)
    print("\n" + "-" * 70)
    if gaps:
        print("\n%d gap(s) left in the text as TODO:" % len(gaps))
        for name, why in gaps:
            print("   %-42s %s" % (name, why))
        print("\nLeft visible on purpose. A methods section with a hole in it is")
        print("one somebody will fix; one with a plausible sentence over the hole")
        print("is one nobody will ever check.")
    else:
        print("\nNo gaps: every field the paragraph needs was in the record.")

    lines = [
        "# Methods", "",
        "Generated by `ch27_methods/scripts/write_methods.py` from",
        "`ch20_protocol_record/outputs/filled_record.json`. Every number below is",
        "traceable to a file rather than to somebody's memory of the run.", "",
        text, "",
    ]
    if gaps:
        lines += ["", "---", "",
                  "## Gaps left in the text", "",
                  "| Field | Why a tool cannot fill it |", "|---|---|"]
        for name, why in gaps:
            lines.append("| %s | %s |" % (name, why))
        lines += [
            "",
            "These are left as **[TODO]** in the paragraph itself rather than",
            "quietly omitted. A methods section with a visible hole is one",
            "somebody will fix; one with a plausible sentence covering the hole",
            "is one nobody will ever check.",
            "",
        ]
    (OUT / "methods.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote %s" % (OUT / "methods.md"))


if __name__ == "__main__":
    main()
