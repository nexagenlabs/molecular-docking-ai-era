#!/usr/bin/env python3
"""Chapter 4 — what each file format destroys.

    python ch04_formats/scripts/roundtrip.py

Takes each charged ligand, writes it out to a format, reads it back, and
compares canonical SMILES, formal charge and atom order against the original.

The folklore is that PDB destroys chemistry. Open Babel re-perceives bond
orders and stereochemistry from the 3D coordinates, so that has been out of
date for years. The format that actually loses information is **PDBQT** — the
one docking uses.

Writes outputs/roundtrip.json and outputs/roundtrip.md.
"""
import json
import subprocess
import sys
from pathlib import Path

from rdkit import Chem, RDLogger

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
LIGANDS = REPO / "data" / "ligands"
WORK = OUT / "work"

sys.path.insert(0, str(REPO / "scripts"))
from docking_common import find_tool  # noqa: E402

FORMATS = ["pdb", "mol2", "pdbqt", "xyz"]
NAMES = ["STC", "18U", "1MU"]

RDLogger.DisableLog("rdApp.*")


def obabel_version(obabel):
    out = subprocess.run([obabel, "-V"], capture_output=True, text=True)
    return (out.stdout + out.stderr).strip().splitlines()[0]


def convert(obabel, src, dst):
    result = subprocess.run([obabel, str(src), "-O", str(dst)],
                            capture_output=True, text=True)
    # Open Babel reports conversion failures on stderr and still exits 0 often
    # enough that the output file is the thing to check, not the return code.
    if not dst.exists() or dst.stat().st_size == 0:
        print(result.stdout + result.stderr)
        sys.exit("obabel produced nothing for %s -> %s" % (src.name, dst.name))
    return result.stdout + result.stderr


def describe(mol):
    """Canonical SMILES, formal charge, and heavy-atom element sequence."""
    if mol is None:
        return None, None, None
    flat = Chem.RemoveHs(mol)
    return (Chem.MolToSmiles(flat, isomericSmiles=True),
            Chem.GetFormalCharge(flat),
            [a.GetSymbol() for a in flat.GetAtoms()])


def main():
    obabel = find_tool("obabel")
    version = obabel_version(obabel)
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    print("%s\n" % version)
    results = {"openbabel_version": version,
               "rdkit_version": Chem.rdBase.rdkitVersion,
               "formats": {f: {} for f in FORMATS}}

    for name in NAMES:
        source = LIGANDS / ("%s.sdf" % name)
        if not source.exists():
            sys.exit("%s missing -- run: python data/ligands/generate.py" % source)
        original = next(Chem.SDMolSupplier(str(source), removeHs=False))
        smiles_before, charge_before, order_before = describe(original)

        for fmt in FORMATS:
            intermediate = WORK / ("%s.%s" % (name, fmt))
            returned = WORK / ("%s_from_%s.sdf" % (name, fmt))
            convert(obabel, source, intermediate)
            convert(obabel, intermediate, returned)

            back = next(Chem.SDMolSupplier(str(returned), removeHs=False))
            if back is not None:
                # Re-perceive stereochemistry from coordinates, which is what
                # any downstream tool reading the file will do.
                Chem.AssignStereochemistryFrom3D(back)
            smiles_after, charge_after, order_after = describe(back)

            charge_lost = charge_after != charge_before
            order_changed = order_after != order_before
            smiles_changed = smiles_after != smiles_before
            results["formats"][fmt][name] = {
                "smiles_before": smiles_before,
                "smiles_after": smiles_after,
                "charge_before": charge_before,
                "charge_after": charge_after,
                "atom_order_preserved": not order_changed,
                "smiles_preserved": not smiles_changed,
                # Flagged means: something a downstream step would silently
                # get wrong. Charge loss corrupts the ranking; a reordering
                # breaks any RMSD computed against the original file.
                "flagged": charge_lost or order_changed or smiles_changed,
            }

    # -- report --------------------------------------------------------------
    lines = ["# Chapter 4 — format round-trips", "",
             "%s, RDKit %s." % (version, Chem.rdBase.rdkitVersion), "",
             "Each ligand written out to a format, read back, and compared with",
             "the original by canonical SMILES, formal charge and atom order.",
             "",
             "| Format | Ligand | Charge | Canonical SMILES | Atom order |",
             "|---|---|---|---|---|"]
    for fmt in FORMATS:
        for name in NAMES:
            r = results["formats"][fmt][name]
            lines.append("| %s | %s | %s | %s | %s |"
                         % (fmt.upper(), name,
                            "%+d → %+d" % (r["charge_before"], r["charge_after"]),
                            "preserved" if r["smiles_preserved"] else "**changed**",
                            "preserved" if r["atom_order_preserved"] else "**changed**"))

    pdb_ok = all(results["formats"]["pdb"][n]["smiles_preserved"] and
                 not results["formats"]["pdb"][n]["flagged"] for n in NAMES)
    mol2_ok = all(results["formats"]["mol2"][n]["smiles_preserved"] for n in NAMES)
    results["pdb_preserves_chemistry"] = pdb_ok
    results["mol2_preserves_chemistry"] = mol2_ok

    lines += [
        "",
        "## The folklore is out of date",
        "",
        "\"PDB destroys bond orders and stereochemistry\" was true of tools that",
        "read only the CONECT records. Open Babel re-perceives chemistry from the",
        "3D coordinates, and a PDB round trip here returns %s"
        % ("the same molecule, charge included." if pdb_ok
           else "a CHANGED molecule -- see the table."),
        "",
        "## PDBQT is the one that loses information",
        "",
    ]
    u18 = results["formats"]["pdbqt"]["18U"]
    lines += [
        "The 18U dianion goes in at %+d and comes back at %+d, and the atom order"
        % (u18["charge_before"], u18["charge_after"]),
        "%s." % ("changes" if not u18["atom_order_preserved"] else "is preserved"),
        "",
        "Both matter, and for different reasons:",
        "",
        "- **The charge loss** matters because the charges differ across this",
        "  series. Losing them is not a uniform shift, it is a different error",
        "  per ligand, which corrupts the ranking rather than moving it.",
        "- **The reordering** matters because it silently breaks any RMSD",
        "  computed against the original file. The numbers still come out; they",
        "  are just measuring the distance between mismatched atoms.",
        "",
        "So: keep an SDF as the reference copy, and convert outward only. Never",
        "read a PDBQT back in and treat it as the ligand you started with.",
        "",
        "## XYZ",
        "",
        "Coordinates and elements, nothing else. Charge %s."
        % ("lost" if results["formats"]["xyz"]["18U"]["charge_after"] != -2
           else "unexpectedly preserved"),
        "",
    ]

    (OUT / "roundtrip.json").write_text(json.dumps(results, indent=2) + "\n",
                                        encoding="utf-8")
    (OUT / "roundtrip.md").write_text("\n".join(lines), encoding="utf-8")

    print("%-7s %-5s %-12s %-10s %s" % ("format", "lig", "charge", "SMILES", "atom order"))
    for fmt in FORMATS:
        for name in NAMES:
            r = results["formats"][fmt][name]
            print("%-7s %-5s %+d -> %+d     %-10s %s"
                  % (fmt, name, r["charge_before"], r["charge_after"],
                     "same" if r["smiles_preserved"] else "CHANGED",
                     "same" if r["atom_order_preserved"] else "CHANGED"))
    print("\nwrote %s" % (OUT / "roundtrip.json"))


if __name__ == "__main__":
    main()
