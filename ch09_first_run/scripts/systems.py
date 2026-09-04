#!/usr/bin/env python3
"""The two systems Chapter 9 uses, and the difference between them.

Chapter 9 runs two things that must never be confused:

  synthetic  A ten-heavy-atom ligand in a shell of carbon atoms. The book's
             timing and box-size numbers are these. They are cheap to repeat
             and mean nothing about protein binding.

  ampc       1L2S chain B and STC. What a reader actually docks. It has no
             published expected score in the book.

Conflating them is how a reader ends up expecting 14 seconds on a real protein.
"""
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
sys.path.insert(0, str(REPO / "scripts"))

from docking_common import find_tool  # noqa: E402
import subprocess  # noqa: E402

SYNTHETIC = CH / "outputs" / "synthetic"
AMPC = CH / "outputs" / "ampc"


def synthetic(build_if_missing=True):
    """Return (receptor, ligand, centre) for the synthetic system."""
    lig_sdf = SYNTHETIC / "lig.sdf"
    lig_pdbqt = SYNTHETIC / "lig.pdbqt"
    rec = SYNTHETIC / "rec.pdbqt"
    if build_if_missing and not (lig_sdf.exists() and rec.exists()):
        subprocess.run([sys.executable, str(CH / "scripts" / "make_test_system.py")],
                       check=True)
    if not lig_pdbqt.exists() or lig_pdbqt.stat().st_mtime < lig_sdf.stat().st_mtime:
        result = subprocess.run([find_tool("mk_prepare_ligand"),
                                 "-i", str(lig_sdf), "-o", str(lig_pdbqt)],
                                capture_output=True, text=True)
        # Meeko reports ligand errors and still exits 0, so the output file is
        # checked rather than the return code. Without explicit hydrogens it
        # writes nothing and a pipeline that trusts the exit status silently
        # docks whatever was left over from the previous run.
        if not lig_pdbqt.exists():
            print(result.stdout + result.stderr)
            sys.exit("mk_prepare_ligand wrote no PDBQT for the synthetic ligand")
    if not rec.exists():
        sys.exit("%s missing -- run scripts/make_test_system.py" % rec)
    return rec, lig_pdbqt, (0.0, 0.0, 0.0)


def ampc(build_if_missing=True):
    """Return (receptor, ligand, centre) for the AmpC system."""
    inputs = AMPC / "inputs.json"
    if build_if_missing and not inputs.exists():
        subprocess.run([sys.executable, str(CH / "scripts" / "prepare_ampc.py")],
                       check=True)
    if not inputs.exists():
        sys.exit("%s missing -- run scripts/prepare_ampc.py" % inputs)
    centre = tuple(json.loads(inputs.read_text())["box"]["centre"])
    return AMPC / "receptor.pdbqt", AMPC / "ligand.pdbqt", centre


def get(name, build_if_missing=True):
    if name == "synthetic":
        return synthetic(build_if_missing)
    if name == "ampc":
        return ampc(build_if_missing)
    sys.exit("unknown system %r -- use 'synthetic' or 'ampc'" % name)


def add_argument(parser):
    parser.add_argument("--system", choices=("synthetic", "ampc"),
                        default="synthetic",
                        help="synthetic (the book's numbers) or ampc (the real run)")
