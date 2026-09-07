#!/usr/bin/env python3
"""Reading molecules out of an SDF, with the four failure modes named.

`next(Chem.SDMolSupplier(path))` is the idiom this repository reached for
eleven times, and it has four distinct ways of going wrong. Measured, not
assumed -- RDKit 2026.03.5:

    file absent     OSError at construction    "File error: Bad input file ..."
    file empty      OSError at construction    "File error: Invalid input ..."
    not an SDF      StopIteration at next()    "End of supplier hit"
    record broken   next() returns None, and the caller carries on with None

The first two reach the reader as a raw traceback, which is the one thing
every other adversarial input in this repository does not do: a nonexistent
PDB entry, a structure with no ligand and an unparseable SMILES all stop with
a sentence. The third is a traceback with a message about suppliers. The
fourth is worse than any of them, because nothing stops at all -- the None
travels on until something downstream fails for an unrelated-looking reason.

So every SDF read goes through here. The rule is the same one the rest of the
repository follows: name the file, say what was wrong with it, and stop.
"""
import sys
from pathlib import Path


def _refuse(what, path, detail):
    sys.exit("%s: %s\n  %s" % (what, detail, path))


def _describe(path, what):
    return what or Path(path).name


def read_one(path, removeHs=False, what=None):
    """The single molecule in an SDF. Stops with a message if there isn't one.

    `what` names the thing for the error message -- "the STC reference copy"
    reads better than "STC.sdf" when the reader has three SDFs open.
    """
    from rdkit import Chem

    path = Path(path)
    label = _describe(path, what)
    if not path.exists():
        _refuse(label, path, "no such file")
    if path.stat().st_size == 0:
        _refuse(label, path, "the file is empty; an SDF with no records is "
                             "not a molecule")
    try:
        supplier = Chem.SDMolSupplier(str(path), removeHs=removeHs)
    except OSError as exc:
        _refuse(label, path, "RDKit could not open it (%s)" % exc)
    try:
        mol = next(iter(supplier))
    except StopIteration:
        _refuse(label, path, "RDKit read no records from it; the file exists "
                             "but is not an SDF")
    if mol is None:
        _refuse(label, path, "RDKit read a record but could not parse it; the "
                             "file is truncated or malformed")
    return mol


def try_read_one(path, removeHs=False):
    """The single molecule in an SDF, or None. Never raises, never exits.

    For the two places where failing to read the file is the *measurement*
    rather than an error: ch04 round-trips a charged ligand through four
    formats to find out which of them destroy it, and ch08 writes a conformer
    out and reads it back to see whether the stereochemistry survived. A hard
    refusal there would refuse to record the result the chapter exists to
    record. Everywhere else, use read_one.
    """
    from rdkit import Chem

    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        supplier = Chem.SDMolSupplier(str(path), removeHs=removeHs)
        return next(iter(supplier))
    except (OSError, StopIteration):
        return None


def try_read_all(path, removeHs=True):
    """Every parseable molecule in an SDF, or []. Never raises, never exits.

    Same rule as try_read_one: for the callers that already treat "no poses"
    as an outcome they report rather than an error they stop on.
    """
    from rdkit import Chem

    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        supplier = Chem.SDMolSupplier(str(path), removeHs=removeHs)
        return [m for m in supplier if m is not None]
    except OSError:
        return []


def read_all(path, removeHs=True, what=None):
    """Every parseable molecule in an SDF, refusing rather than returning [].

    Pose files go through here. `[m for m in SDMolSupplier(p) if m]` silently
    turns "the docking wrote nothing" into an empty list, and an empty list is
    a result shape rather than an error -- so the caller reports zero poses and
    a reader has no way to tell that from a run that genuinely found none.
    """
    from rdkit import Chem

    path = Path(path)
    label = _describe(path, what)
    if not path.exists():
        _refuse(label, path, "no such file")
    if path.stat().st_size == 0:
        _refuse(label, path, "the file is empty; an SDF with no records is "
                             "not a set of poses")
    try:
        supplier = Chem.SDMolSupplier(str(path), removeHs=removeHs)
    except OSError as exc:
        _refuse(label, path, "RDKit could not open it (%s)" % exc)
    mols = [m for m in supplier if m is not None]
    if not mols:
        _refuse(label, path, "RDKit parsed no molecule from it; the file "
                             "exists but holds no usable record")
    return mols
