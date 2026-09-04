"""Chapter 8: protonation and conformer generation.

The charges are asserted as a hard failure rather than printed. This series
spans -1 and -2, so a protonation change would corrupt the ranking rather than
shift it -- and a corrupted ranking still looks like a result. If a future
RDKit changes behaviour here, the build must break loudly.
"""
import pytest

from conftest import read_json, require_platform, run_script

# ETKDGv3, 300 attempts, pruneRmsThresh=0.5, on the DEPROTONATED forms --
# protonation comes before conformer generation, and the neutral forms give
# different counts. Counts do NOT track rotatable-bond count: 18U has more
# rotatable bonds than STC and yields fewer conformers. That is the teaching
# point of the chapter and must not be "fixed".
EXPECTED = {
    "STC": {"charge": -1, "rotatable_bonds": 4, "conformers": [15, 15, 16, 16, 16]},
    "18U": {"charge": -2, "rotatable_bonds": 6, "conformers": [9, 9, 12, 11, 8]},
    "1MU": {"charge": -2, "rotatable_bonds": 7, "conformers": [33, 35, 33, 28, 37]},
}
SEEDS = [1, 7, 42, 99, 2026]


@pytest.fixture(scope="module")
def prepared():
    run_script("ch08_ligand_prep/scripts/prepare_ligands.py")
    return read_json("ch08_ligand_prep/outputs/ligand_prep.json")


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_formal_charge_at_ph_74(prepared, name):
    assert prepared["ligands"][name]["formal_charge"] == EXPECTED[name]["charge"], \
        ("%s must carry charge %+d at pH 7.4. Docking the neutral form gets every "
         "member of this series wrong by a different amount."
         % (name, EXPECTED[name]["charge"]))


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_rotatable_bond_count(prepared, name):
    assert prepared["ligands"][name]["rotatable_bonds"] == EXPECTED[name]["rotatable_bonds"]


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_conformer_counts_by_seed(prepared, name):
    """The book's counts are from the DEPROTONATED form, exact on Linux.

    Off Linux the same RDKit version differs by one or two conformers, for the
    same reason the ch09 scores differ: the build, not the protocol.
    """
    require_platform("The conformer count")
    got = [prepared["ligands"][name]["conformers"][str(s)] for s in SEEDS]
    assert got == EXPECTED[name]["conformers"], \
        ("%s conformer counts %s, book says %s. Do not adjust the script until "
         "you know which side is wrong." % (name, got, EXPECTED[name]["conformers"]))


def test_conformer_count_does_not_track_rotatable_bonds(prepared):
    """The teaching point, asserted so nobody 'fixes' it later."""
    stc = prepared["ligands"]["STC"]
    u18 = prepared["ligands"]["18U"]
    assert u18["rotatable_bonds"] > stc["rotatable_bonds"]
    assert (sum(u18["conformers"].values()) < sum(stc["conformers"].values())), \
        "18U has more rotatable bonds and should still yield fewer conformers"


def test_stereochemistry_survives_the_round_trip(prepared):
    for name in EXPECTED:
        assert prepared["ligands"][name]["stereo_preserved"] is True
