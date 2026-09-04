#!/usr/bin/env python3
"""Re-measure the structural facts the rest of this repository depends on.

Every claim in data/structures/README.md is printed here from the coordinates,
so a reader can check the documentation against the files rather than trusting
it. Standard library only, deliberately: this runs before the conda environment
exists.

    python scripts/audit_structures.py
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STRUCT = HERE / "data" / "structures"
ENTRIES = ("1L2S", "4JXS", "4JXV", "1GA9")

# The ligand of interest in each entry. Waters, ions and crystallisation
# additives are NOT listed here on purpose -- the audit prints every HETATM
# group it found so that nothing is dropped silently.
LIGAND = {"1L2S": "STC", "4JXS": "18U", "4JXV": "1MU", "1GA9": "ETP"}


def read_pdb(path):
    atoms, missing, links = [], [], []
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            atoms.append({
                "rec": line[:6].strip(),
                "name": line[12:16].strip(),
                "alt": line[16],
                "res": line[17:20].strip(),
                "chain": line[21],
                "seq": line[22:26].strip(),
                "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
            })
        elif line.startswith("REMARK 465"):
            # The record is preceded by free-text header lines with the same
            # prefix, so match the column layout rather than the prefix:
            # residue name, one-character chain, integer sequence number.
            fields = line[10:].split()
            if len(fields) == 3 and len(fields[0]) == 3 and len(fields[1]) == 1                     and fields[2].lstrip("-").isdigit():
                missing.append(f"{fields[0]} {fields[1]}{fields[2]}")
        elif line.startswith("LINK"):
            links.append(line.rstrip())
    return atoms, missing, links


def ser64_og(atoms):
    return [a for a in atoms if a["res"] == "SER" and a["seq"] == "64" and a["name"] == "OG"]


def dist(a, b):
    return math.dist(a, b)


def audit(pdb_id):
    path = STRUCT / f"{pdb_id}.pdb"
    if not path.exists():
        sys.exit(f"{path} missing -- run: bash data/structures/fetch.sh")
    atoms, missing, links = read_pdb(path)
    print(f"\n=== {pdb_id} " + "=" * (60 - len(pdb_id)))

    catalytic = ser64_og(atoms)
    print(f"Ser64 OG present in chains: {', '.join(a['chain'] for a in catalytic)}")

    # Ligand copies, ranked by distance to the catalytic serine. A copy far from
    # every Ser64 OG is at a crystal contact, not in an active site. Selecting
    # the ligand by file order instead of by this distance is the failure mode
    # this audit exists to make visible.
    lig = LIGAND[pdb_id]
    copies = {}
    for a in atoms:
        if a["res"] == lig:
            copies.setdefault((a["chain"], a["seq"]), []).append(a["xyz"])
    print(f"{lig} copies: {len(copies)}")
    for (chain, seq), xyz in sorted(copies.items()):
        per_chain = "  ".join(
            f"{s['chain']}={min(dist(x, s['xyz']) for x in xyz):6.2f}" for s in catalytic
        )
        nearest = min(min(dist(x, s["xyz"]) for x in xyz) for s in catalytic)
        verdict = "catalytic" if nearest < 5.0 else "NOT in an active site -- discard"
        print(f"  {chain}/{seq:<5} {len(xyz):2d} atoms   min dist to Ser64 OG: {per_chain}   {verdict}")

    # Everything else that is a HETATM. Printed in full: silent ligand
    # mis-picking is the failure guarded against here.
    others = sorted({a["res"] for a in atoms if a["rec"] == "HETATM"} - {lig})
    print(f"other HETATM groups: {', '.join(others) if others else '(none)'}")

    phosphorus = [a for a in atoms if a["rec"] == "HETATM" and a["name"] == "P"]
    if phosphorus and catalytic:
        near = min(dist(p["xyz"], s["xyz"]) for p in phosphorus for s in catalytic)
        print(f"nearest P to any Ser64 OG: {near:.2f} A ({len(phosphorus)} P atoms) "
              f"-- {'surface artefact, delete' if near > 5.0 else 'IN THE SITE, look again'}")

    altlocs = sorted({(a["res"], a["chain"], a["seq"]) for a in atoms if a["alt"] != " "})
    print("altlocs: " + (", ".join(f"{r} {c}{s}" for r, c, s in altlocs) if altlocs else "(none)"))

    print("missing residues (REMARK 465): " + (", ".join(missing) if missing else "(none)"))

    # A LINK from Ser64 OG is a covalent complex. Non-covalent docking cannot
    # represent it, whatever the score says.
    covalent = [l for l in links if "SER" in l and " 64 " in l and "OG" in l]
    if covalent:
        print("COVALENT to Ser64 -- exclude from non-covalent docking:")
        for l in covalent:
            print("  " + l)


if __name__ == "__main__":
    for entry in ENTRIES:
        audit(entry)
    print("\nUniProt number = PDB number + 16. Ser64 here is Ser80 in P00811.")
