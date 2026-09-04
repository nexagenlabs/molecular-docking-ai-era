"""Chapter 4: what each file format destroys.

The folklore is that PDB destroys chemistry. Open Babel re-perceives bond
orders and stereochemistry from the 3D coordinates, so that has been out of
date for years. The format that actually loses information is PDBQT -- the one
docking uses.
"""
import pytest

from conftest import read_json, run_script


@pytest.fixture(scope="module")
def roundtrip():
    run_script("ch04_formats/scripts/roundtrip.py")
    return read_json("ch04_formats/outputs/roundtrip.json")


def test_pdbqt_loses_formal_charge(roundtrip):
    """The 18U dianion comes back neutral."""
    result = roundtrip["formats"]["pdbqt"]["18U"]
    assert result["charge_before"] == -2
    assert result["charge_after"] == 0, \
        "PDBQT is supposed to return the dianion neutral; got %s" % result["charge_after"]


def test_pdbqt_reorders_atoms(roundtrip):
    """The reordering is why an RMSD against the original silently breaks."""
    assert roundtrip["formats"]["pdbqt"]["18U"]["atom_order_preserved"] is False


@pytest.mark.parametrize("fmt", ["pdb", "mol2"])
@pytest.mark.parametrize("name", ["STC", "18U", "1MU"])
def test_pdb_and_mol2_preserve_canonical_smiles(roundtrip, fmt, name):
    """Charge, bond orders and stereochemistry all survive."""
    result = roundtrip["formats"][fmt][name]
    assert result["smiles_after"] == result["smiles_before"], \
        ("%s round-trip through %s changed the molecule:\n  before %s\n  after  %s"
         % (name, fmt.upper(), result["smiles_before"], result["smiles_after"]))
    assert result["charge_after"] == result["charge_before"]


def test_xyz_loses_charge(roundtrip):
    assert roundtrip["formats"]["xyz"]["18U"]["charge_after"] != -2


def test_the_folklore_is_recorded_as_wrong(roundtrip):
    """The README has to correct it explicitly, so the result asserts it too."""
    assert roundtrip["pdb_preserves_chemistry"] is True
