#!/usr/bin/env python3
"""Build the reference SDF copies of the ligand series, and check them.

    python data/ligands/generate.py            # write the SDFs
    python data/ligands/generate.py --check    # regenerate and compare, write nothing

The SDFs in this directory are committed, so every reader measures RMSD against
a byte-identical reference rather than against whatever their RDKit produced.
This script is how they were made and how their provenance stays auditable:
`--check` rebuilds them in memory and compares against what is on disk.

`--check` requires the pinned environment (see environment/README.md). A
mismatch under a different RDKit is expected and is not an error in the data --
it is the reason the SDFs are committed in the first place.

PDBQT is written outward only, never read back: it drops formal charge and
reorders atoms, so a PDBQT round-trip would silently return the 18U dianion as
the neutral diacid with an atom order that breaks any RMSD computed against it.
"""
import argparse
import sys
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    sys.exit("RDKit not available. See environment/README.md -- the reference "
             "copies must be built under the pinned environment, not whatever "
             "RDKit happens to be installed.")

HERE = Path(__file__).resolve().parent

# Conformer-generation settings. Fixed so the reference copies are reproducible;
# recorded here because a seed that is not written down is a seed that is lost.
EMBED_SEED = 42
FORCE_FIELD = "MMFF94s"

# Neutral SMILES are the forms drawn in the book. The docked forms are the
# neutral ones with every carboxylic acid deprotonated -- the aryl sulfonamide
# N-H has a pKa near 10 and stays neutral at pH 7.4. `charge` is the expected
# total formal charge and is asserted, not assumed: it is the check that the
# deprotonation below actually did what the table says.
LIGANDS = {
    "STC": {
        "neutral": "c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)O)Cl",
        "docked":  "c1cc(ccc1NS(=O)(=O)c2ccsc2C(=O)[O-])Cl",
        "charge": -1,
        "ki": "26 uM",
        "entry": "1L2S",
    },
    "18U": {
        "neutral": "c1cc(ccc1CNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O",
        "docked":  "c1cc(ccc1CNS(=O)(=O)c2ccsc2C(=O)[O-])C(=O)[O-]",
        "charge": -2,
        "ki": "18 uM",
        "entry": "4JXS",
    },
    "1MU": {
        "neutral": "c1cc(ccc1CCNS(=O)(=O)c2ccsc2C(=O)O)C(=O)O",
        "docked":  "c1cc(ccc1CCNS(=O)(=O)c2ccsc2C(=O)[O-])C(=O)[O-]",
        "charge": -2,
        # The two sources disagree. Both are recorded; neither is chosen.
        "ki": "26 uM (ChEMBL) / 31 uM (PDBbind)",
        "entry": "4JXV",
    },
}


def build(name, spec):
    """Return an embedded, optimised molecule for one ligand."""
    mol = Chem.MolFromSmiles(spec["docked"])
    if mol is None:
        sys.exit(f"{name}: SMILES did not parse")

    charge = Chem.GetFormalCharge(mol)
    if charge != spec["charge"]:
        sys.exit(f"{name}: formal charge is {charge:+d}, table says "
                 f"{spec['charge']:+d}. The charges differ across this series, "
                 f"so docking the wrong one corrupts the ranking rather than "
                 f"shifting it. Fix the SMILES, not the table.")

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = EMBED_SEED
    if AllChem.EmbedMolecule(mol, params) != 0:
        sys.exit(f"{name}: embedding failed")
    AllChem.MMFFOptimizeMolecule(mol, mmffVariant=FORCE_FIELD)

    mol.SetProp("_Name", name)
    mol.SetProp("smiles_neutral", spec["neutral"])
    mol.SetProp("smiles_docked", spec["docked"])
    mol.SetProp("formal_charge", str(spec["charge"]))
    mol.SetProp("ki", spec["ki"])
    mol.SetProp("pdb_entry", spec["entry"])
    mol.SetProp("embed_seed", str(EMBED_SEED))
    mol.SetProp("force_field", FORCE_FIELD)
    mol.SetProp("rdkit_version", Chem.rdBase.rdkitVersion)
    return mol


def canonical(mol):
    return Chem.MolToSmiles(Chem.RemoveHs(mol))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and compare against the committed SDFs")
    args = ap.parse_args()

    failures = 0
    for name, spec in LIGANDS.items():
        path = HERE / f"{name}.sdf"
        fresh = build(name, spec)

        if not args.check:
            writer = Chem.SDWriter(str(path))
            writer.write(fresh)
            writer.close()
            print(f"wrote {path.name}  charge {spec['charge']:+d}  "
                  f"{fresh.GetNumHeavyAtoms()} heavy atoms")
            continue

        if not path.exists():
            print(f"FAIL {name}: {path.name} missing -- run without --check")
            failures += 1
            continue

        committed = next(Chem.SDMolSupplier(str(path), removeHs=False))
        if committed is None:
            print(f"FAIL {name}: {path.name} did not parse")
            failures += 1
            continue

        problems = []
        if canonical(committed) != canonical(fresh):
            problems.append(f"canonical SMILES differ:\n"
                            f"      on disk: {canonical(committed)}\n"
                            f"      rebuilt: {canonical(fresh)}")
        if Chem.GetFormalCharge(committed) != spec["charge"]:
            problems.append(f"charge on disk is "
                            f"{Chem.GetFormalCharge(committed):+d}, "
                            f"expected {spec['charge']:+d}")
        if committed.GetNumAtoms() == fresh.GetNumAtoms():
            a = committed.GetConformer()
            b = fresh.GetConformer()
            worst = max((a.GetAtomPosition(i) - b.GetAtomPosition(i)).Length()
                        for i in range(committed.GetNumAtoms()))
            if worst > 1e-3:
                problems.append(f"coordinates differ, worst atom {worst:.4f} A "
                                f"-- expected under a different RDKit than "
                                f"{Chem.rdBase.rdkitVersion}, see "
                                f"environment/README.md")
        else:
            problems.append(f"atom count differs: {committed.GetNumAtoms()} "
                            f"on disk, {fresh.GetNumAtoms()} rebuilt")

        if problems:
            failures += 1
            print(f"FAIL {name}")
            for p in problems:
                print(f"  - {p}")
        else:
            print(f"ok   {name}  charge {spec['charge']:+d}  "
                  f"{committed.GetNumHeavyAtoms()} heavy atoms")

    if args.check:
        print(f"\n{'FAILED' if failures else 'all reference copies match'}"
              + (f" ({failures})" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
