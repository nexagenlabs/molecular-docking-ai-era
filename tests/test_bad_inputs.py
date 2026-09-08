"""Adversarial inputs: every script must refuse with a sentence, not a traceback.

build-record/STRESS_TEST.md section 3 fed six bad inputs to this repository. Four were
refused cleanly -- a nonexistent PDB entry, a structure with no ligand, an
unparseable SMILES, and a run.sh invoked from a foreign working directory.
The fifth, an empty SDF, produced a raw OSError traceback out of
Chem.SDMolSupplier, and the idiom that produced it appeared unguarded at
eleven call sites across nine chapters.

A traceback is not a refusal. It tells a reader that the program broke, not
that their file is empty, and it is indistinguishable from a bug in the
repository. These tests hold the line at the shared reader in scripts/molfile.py
and then at one chapter end to end, so the contract is checked both where it
is implemented and where a reader would meet it.
"""
import shutil
import sys

import pytest

from conftest import REPO, run_script_raw

sys.path.insert(0, str(REPO / "scripts"))
import molfile  # noqa: E402

# The four ways next(Chem.SDMolSupplier(path)) goes wrong, measured on RDKit
# 2026.03.5. Each is a different exception at a different point, which is why
# a single try/except at the call site was never going to cover them.
CASES = {
    "absent": None,
    "empty": b"",
    "not an SDF": b"garbage\nnot a molfile at all\n",
    "truncated": (b"\n     RDKit          3D\n\n"
                  b"  2  1  0  0  0  0  0  0  0  0999 V2000\n"),
}


@pytest.fixture(params=sorted(CASES))
def bad_sdf(request, tmp_path):
    path = tmp_path / ("%s.sdf" % request.param.replace(" ", "_"))
    content = CASES[request.param]
    if content is not None:
        path.write_bytes(content)
    return request.param, path


def test_read_one_refuses_every_broken_sdf_by_name(bad_sdf):
    kind, path = bad_sdf
    with pytest.raises(SystemExit) as excinfo:
        molfile.read_one(path, what="the STC reference copy")
    message = str(excinfo.value)
    assert "the STC reference copy" in message, \
        "%s: the refusal did not name what was being read" % kind
    assert path.name in message, \
        "%s: the refusal did not name the file" % kind


def test_read_all_refuses_every_broken_sdf_by_name(bad_sdf):
    kind, path = bad_sdf
    with pytest.raises(SystemExit) as excinfo:
        molfile.read_all(path, what="the docked poses")
    assert path.name in str(excinfo.value), \
        "%s: the refusal did not name the file" % kind


def test_the_tolerant_readers_return_nothing_rather_than_raising(bad_sdf):
    """ch04, ch08 and generate.py --check measure whether a file reads back.

    For them an unreadable file is the result, so try_read_one and try_read_all
    have to survive all four cases without raising -- including SystemExit,
    which would end the chapter mid-measurement.
    """
    kind, path = bad_sdf
    assert molfile.try_read_one(path) is None, kind
    assert molfile.try_read_all(path) == [], kind


def test_a_good_sdf_still_reads(tmp_path):
    """The guards must not have made every file unreadable."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1C(=O)NC"))
    assert AllChem.EmbedMolecule(mol, randomSeed=11) == 0
    path = tmp_path / "good.sdf"
    writer = Chem.SDWriter(str(path))
    writer.write(mol)
    writer.close()

    assert molfile.read_one(path).GetNumAtoms() == mol.GetNumAtoms()
    assert len(molfile.read_all(path)) == 1


def test_an_empty_reference_sdf_stops_ch04_with_a_message():
    """The report's own case, end to end.

    An empty data/ligands/STC.sdf used to kill ch04_formats/scripts/roundtrip.py
    with a raw OSError traceback from Chem.SDMolSupplier. This swaps the tracked
    reference copy for an empty file, runs the chapter, and puts it back --
    which is why the restore is in a finally and the test asserts afterwards
    that the file came back byte-for-byte.
    """
    reference = REPO / "data" / "ligands" / "STC.sdf"
    original = reference.read_bytes()
    backup = reference.with_suffix(".sdf.testbackup")
    shutil.copy2(reference, backup)
    try:
        reference.write_bytes(b"")
        result = run_script_raw("ch04_formats/scripts/roundtrip.py")
    finally:
        reference.write_bytes(original)
        backup.unlink(missing_ok=True)

    assert reference.read_bytes() == original, "the reference copy was not restored"
    assert result.returncode != 0, "an empty reference SDF produced exit 0"
    message = result.stdout + result.stderr
    assert "Traceback" not in message, \
        "refused with a traceback rather than a message:\n%s" % message[-2000:]
    assert "STC.sdf" in message, "the refusal did not name the file"
    assert "empty" in message.lower(), "the refusal did not say what was wrong"
