#!/usr/bin/env python3
"""Quality-control report for a crystal structure, before you dock into it.

    python ch05_receptor_prep/scripts/qc_report.py [PDBID ...]

Defaults to the four AmpC entries. For each one it reports resolution and
R-free, chain breaks, missing side chains, alternate locations, every HETATM
group with its distance to the catalytic serine, and the waters that bridge
ligand to protein.

The report answers one question: **what in this file will change my answer, and
have I decided about it?** Every line is something a reader has to rule in or
out before docking, and every one of them has been the cause of a published
result that could not be reproduced.

Writes outputs/qc_<PDBID>.json and outputs/qc_<PDBID>.md.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"

DEFAULT_ENTRIES = ["1L2S", "4JXS", "4JXV", "1GA9"]

# AmpC's catalytic nucleophile, in PDB numbering.
#
# NUMBERING TRAP: UniProt number = PDB number + 16. Ser64 here is Ser80 in
# UniProt P00811 and in the AlphaFold model. A script that mixes UniProt
# annotations with PDB numbering picks the wrong residue and says nothing.
CATALYTIC = ("SER", "64", "OG")

# A HETATM group this far from the catalytic serine is not in the active site,
# whatever the file's atom order suggests.
SITE_CUTOFF = 5.0

# Hydrogen-bond distance. A water within this of both ligand and protein is
# bridging them, and deleting it changes what docking can reach.
BRIDGE_CUTOFF = 3.5

# Anything that is not a ligand: solvent, ions, and crystallisation additives.
NOT_A_LIGAND = {"HOH", "WAT", "PO4", "SO4", "GOL", "EDO", "MPD", "PEG", "ACT",
                "CL", "NA", "K", "MG", "CA", "ZN", "MN", "NO3", "TRS", "DMS"}


def parse(path):
    atoms, missing_res, missing_atoms, links = [], [], [], []
    resolution = r_free = None
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            atoms.append({
                "rec": line[:6].strip(),
                "name": line[12:16].strip(),
                "altloc": line[16],
                "res": line[17:20].strip(),
                "chain": line[21],
                "seq": line[22:26].strip(),
                "element": line[76:78].strip() or line[12:16].strip()[:1],
                "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
            })
        elif line.startswith("REMARK   2 RESOLUTION."):
            # "REMARK   2 RESOLUTION.    1.94 ANGSTROMS." -- take the token
            # after the label, not the first float on the line, which is the
            # remark number itself.
            tail = line.split("RESOLUTION.", 1)[1].split()
            if tail:
                try:
                    resolution = float(tail[0])
                except ValueError:
                    pass
        elif re.match(r"^REMARK   3   FREE R VALUE\s+:", line):
            # Anchored, because the same file carries FREE R VALUE TEST SET
            # COUNT (an integer in the thousands) and BIN FREE R VALUE. A
            # prefix match picks up whichever comes first and reports 2647 as
            # an R-free without blinking.
            tail = line.split(":", 1)[1].strip()
            try:
                r_free = float(tail)
            except ValueError:
                pass
        elif line.startswith("REMARK 465"):
            # Free-text header lines share the prefix, so match the column
            # layout instead: residue name, one-character chain, integer.
            fields = line[10:].split()
            if (len(fields) == 3 and len(fields[0]) == 3 and len(fields[1]) == 1
                    and fields[2].lstrip("-").isdigit()):
                missing_res.append({"res": fields[0], "chain": fields[1],
                                    "seq": fields[2]})
        elif line.startswith("REMARK 470"):
            fields = line[10:].split()
            if (len(fields) >= 4 and len(fields[0]) == 3 and len(fields[1]) == 1
                    and fields[2].lstrip("-").isdigit()):
                missing_atoms.append({"res": fields[0], "chain": fields[1],
                                      "seq": fields[2], "atoms": fields[3:]})
        elif line.startswith("LINK"):
            links.append(line.rstrip())
    return {"atoms": atoms, "missing_residues": missing_res,
            "missing_atoms": missing_atoms, "links": links,
            "resolution": resolution, "r_free": r_free}


def dist(a, b):
    return math.dist(a, b)


def report(pdb_id):
    path = STRUCTURES / ("%s.pdb" % pdb_id)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    data = parse(path)
    atoms = data["atoms"]
    protein = [a for a in atoms if a["rec"] == "ATOM"]
    catalytic = [a for a in protein if (a["res"], a["seq"], a["name"]) == CATALYTIC]

    out = {"pdb_id": pdb_id,
           "resolution": data["resolution"],
           "r_free": data["r_free"],
           "catalytic_serine_chains": [a["chain"] for a in catalytic]}

    lines = ["# %s -- receptor QC" % pdb_id, ""]
    lines.append("Resolution %.2f A, R-free %.3f."
                 % (data["resolution"], data["r_free"]))
    lines.append("")
    lines.append("Catalytic %s%s OG present in chains: %s"
                 % (CATALYTIC[0].title(), CATALYTIC[1],
                    ", ".join(a["chain"] for a in catalytic)))
    lines.append("")
    lines.append("> Numbering trap: UniProt number = PDB number + 16. Ser64 here")
    lines.append("> is Ser80 in UniProt P00811 and in the AlphaFold model.")
    lines.append("")

    # -- chain breaks --------------------------------------------------------
    gaps = {}
    for m in data["missing_residues"]:
        gaps.setdefault(m["chain"], []).append("%s %s" % (m["res"], m["seq"]))
    out["missing_residues"] = gaps
    lines.append("## Chain breaks (REMARK 465)")
    lines.append("")
    if gaps:
        for chain, residues in sorted(gaps.items()):
            lines.append("- chain %s: %s" % (chain, ", ".join(residues)))
        lines.append("")
        lines.append("A gap near the site is a reason to use the other chain, not")
        lines.append("something to model over quietly.")
    else:
        lines.append("None. Every modelled residue is present.")
    lines.append("")

    # -- missing side chains -------------------------------------------------
    side = {}
    for m in data["missing_atoms"]:
        side.setdefault(m["chain"], []).append(
            {"residue": "%s %s" % (m["res"], m["seq"]), "atoms": m["atoms"]})
    out["missing_side_chain_atoms"] = side
    lines.append("## Disordered side chains (REMARK 470)")
    lines.append("")
    if side:
        for chain, entries in sorted(side.items()):
            lines.append("- chain %s: %d residues" % (chain, len(entries)))
            for entry in entries:
                lines.append("  - %s missing %s"
                             % (entry["residue"], " ".join(entry["atoms"])))
        lines.append("")
        lines.append("Two defensible treatments, and they are not equivalent:")
        lines.append("")
        lines.append("- **Type the residue down to what is present.** A lysine")
        lines.append("  missing CG, CD, CE and NZ holds exactly alanine's heavy")
        lines.append("  atoms, so alanine is an honest description of the file.")
        lines.append("  Cheap, and it changes the chemistry of that position.")
        lines.append("- **Rebuild the missing atoms** with PDBFixer or a similar")
        lines.append("  tool. Keeps the residue identity, at the cost of atoms")
        lines.append("  that are modelled rather than observed.")
        lines.append("")
        lines.append("Deleting the whole residue is the option to avoid near the")
        lines.append("site: it removes backbone as well, and leaves a hole that")
        lines.append("nothing in the output mentions.")
    else:
        lines.append("None.")
    lines.append("")

    # -- altlocs -------------------------------------------------------------
    altlocs = {}
    for a in atoms:
        if a["altloc"] != " ":
            altlocs.setdefault("%s %s%s" % (a["res"], a["chain"], a["seq"]),
                               set()).add(a["altloc"])
    out["altlocs"] = {k: sorted(v) for k, v in sorted(altlocs.items())}
    lines.append("## Alternate locations")
    lines.append("")
    if altlocs:
        for where, which in sorted(altlocs.items()):
            lines.append("- %s: altlocs %s" % (where, ", ".join(sorted(which))))
        lines.append("")
        lines.append("Pick one and record which. The choice is arbitrary; leaving")
        lines.append("it unrecorded is what makes it irreproducible.")
    else:
        lines.append("None.")
    lines.append("")

    # -- HETATM groups -------------------------------------------------------
    groups = {}
    for a in atoms:
        if a["rec"] == "HETATM":
            groups.setdefault((a["res"], a["chain"], a["seq"]), []).append(a)

    het = []
    for (res, chain, seq), group_atoms in sorted(groups.items()):
        if catalytic:
            near = min(dist(a["xyz"], s["xyz"]) for a in group_atoms for s in catalytic)
        else:
            near = None
        het.append({"res": res, "chain": chain, "seq": seq,
                    "atoms": len(group_atoms),
                    "distance_to_catalytic": round(near, 2) if near is not None else None,
                    "in_site": near is not None and near < SITE_CUTOFF,
                    "is_ligand_candidate": res not in NOT_A_LIGAND})
    out["hetatm_groups"] = het

    ligands = [h for h in het if h["is_ligand_candidate"]]
    out["ligand_copies"] = ligands
    lines.append("## Ligand copies")
    lines.append("")
    if ligands:
        lines.append("| Group | Atoms | Distance to Ser64 OG | Verdict |")
        lines.append("|---|---|---|---|")
        for h in ligands:
            verdict = "catalytic" if h["in_site"] else "**NOT in an active site**"
            lines.append("| %s %s/%s | %d | %.2f A | %s |"
                         % (h["res"], h["chain"], h["seq"], h["atoms"],
                            h["distance_to_catalytic"], verdict))
        lines.append("")
        lines.append("Select by this distance, never by file order. Nothing in the")
        lines.append("file marks which copy is the one you meant.")
    else:
        lines.append("No ligand-like HETATM group found.")
    lines.append("")

    # -- solvent and additives -----------------------------------------------
    additives = [h for h in het if not h["is_ligand_candidate"] and h["res"] != "HOH"]
    waters = [h for h in het if h["res"] == "HOH"]
    out["additive_groups"] = additives
    out["water_count"] = len(waters)
    lines.append("## Solvent, ions and additives")
    lines.append("")
    lines.append("%d waters." % len(waters))
    if additives:
        lines.append("")
        for h in additives:
            lines.append("- %s %s/%s, %.2f A from Ser64 OG -- %s"
                         % (h["res"], h["chain"], h["seq"], h["distance_to_catalytic"],
                            "IN THE SITE, look again" if h["in_site"]
                            else "surface artefact, delete"))
    lines.append("")

    # -- phosphate -----------------------------------------------------------
    # 4JXS, 4JXV and 1GA9 were crystallised from 1.7 M potassium phosphate.
    # 1L2S was not, and a phosphate reported there means the parsing is wrong.
    phosphorus = [a for a in atoms if a["rec"] == "HETATM" and a["element"] == "P"]
    nearest_p = (min(dist(p["xyz"], s["xyz"]) for p in phosphorus for s in catalytic)
                 if phosphorus and catalytic else None)
    out["phosphorus_atoms"] = len(phosphorus)
    out["nearest_phosphorus_to_catalytic"] = (round(nearest_p, 2)
                                              if nearest_p is not None else None)
    lines.append("## Phosphate")
    lines.append("")
    if phosphorus:
        lines.append("%d phosphorus atoms; nearest to Ser64 OG %.2f A."
                     % (len(phosphorus), nearest_p))
        lines.append("From the 1.7 M potassium phosphate crystallisation. Surface")
        lines.append("artefacts -- delete them. Measured here, not assumed.")
    else:
        lines.append("None. (1L2S was not crystallised from phosphate; a phosphate")
        lines.append("reported here would mean the HETATM parsing is wrong.)")
    lines.append("")

    # -- bridging waters -----------------------------------------------------
    # A water within hydrogen-bonding distance of both the ligand and the
    # protein is part of the binding site as observed. Delete it and the
    # crystallographic pose may no longer be reachable by docking -- and the
    # redock then fails for a reason invisible in the output.
    # Reported per ligand copy. Doing it only for the closest copy answers the
    # question for one chain and silently says nothing about the other, which
    # is exactly the kind of half-answer this report exists to prevent.
    site_ligands = [h for h in ligands if h["in_site"]]
    by_copy = {}
    for chosen in site_ligands:
        lig_atoms = groups[(chosen["res"], chosen["chain"], chosen["seq"])]
        found = []
        for h in waters:
            water_atoms = groups[(h["res"], h["chain"], h["seq"])]
            to_lig = min(dist(w["xyz"], l["xyz"])
                         for w in water_atoms for l in lig_atoms)
            if to_lig > BRIDGE_CUTOFF:
                continue
            contacts = sorted({"%s%s" % (p["res"].title(), p["seq"])
                               for p in protein for w in water_atoms
                               if p["name"] not in ("C", "N", "O", "CA")
                               and dist(w["xyz"], p["xyz"]) <= BRIDGE_CUTOFF})
            if contacts:
                found.append({"water": "%s/%s" % (h["chain"], h["seq"]),
                              "distance_to_ligand": round(to_lig, 2),
                              "contacts": contacts})
        found.sort(key=lambda b: b["distance_to_ligand"])
        by_copy["%s %s/%s" % (chosen["res"], chosen["chain"], chosen["seq"])] = found
    out["bridging_waters_by_copy"] = by_copy
    bridges = [b for found in by_copy.values() for b in found]
    out["bridging_waters"] = bridges
    lines.append("## Bridging waters")
    lines.append("")
    if bridges:
        lines.append("Within %.1f A of both a ligand copy and a protein side chain:"
                     % BRIDGE_CUTOFF)
        lines.append("")
        for copy, found in sorted(by_copy.items()):
            lines.append("- **%s**" % copy)
            for b in found:
                lines.append("  - HOH %s, %.2f A from the ligand, contacts %s"
                             % (b["water"], b["distance_to_ligand"],
                                ", ".join(b["contacts"])))
            if not found:
                lines.append("  - none")
        lines.append("")
        lines.append("**Deleting these makes the crystallographic pose unreachable**")
        lines.append("by docking. Keeping them fixes a water where a ligand atom")
        lines.append("might belong. Neither is the safe default; the decision has to")
        lines.append("be made and recorded.")
    else:
        lines.append("None found.")
    lines.append("")

    # -- covalent links ------------------------------------------------------
    covalent = [l for l in data["links"]
                if CATALYTIC[0] in l and (" %s " % CATALYTIC[1]) in l
                and CATALYTIC[2] in l]
    out["covalent_to_catalytic"] = covalent
    if covalent:
        lines.append("## Covalent link to the catalytic serine")
        lines.append("")
        for l in covalent:
            lines.append("    " + l)
        lines.append("")
        lines.append("**Exclude from non-covalent docking.** No score from a")
        lines.append("non-covalent run means anything against a covalent complex,")
        lines.append("and the exclusion is a modelling decision that has to be")
        lines.append("written down as one.")
        lines.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("qc_%s.json" % pdb_id)).write_text(json.dumps(out, indent=2) + "\n")
    (OUT / ("qc_%s.md" % pdb_id)).write_text("\n".join(lines))
    return out, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("entries", nargs="*", default=DEFAULT_ENTRIES,
                    help="PDB IDs (default: the four AmpC entries)")
    ap.add_argument("--quiet", action="store_true", help="write files, print a summary")
    args = ap.parse_args()

    for pdb_id in (args.entries or DEFAULT_ENTRIES):
        out, lines = report(pdb_id)
        if args.quiet:
            print("%s  %.2f A  R-free %.3f  %d ligand copies  %d bridging waters"
                  % (pdb_id, out["resolution"], out["r_free"],
                     len(out["ligand_copies"]), len(out["bridging_waters"])))
        else:
            print("\n".join(lines))
            print("\n" + "-" * 70)
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
