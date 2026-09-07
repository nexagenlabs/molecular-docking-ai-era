"""Chapter 10: which side chains actually move.

Thirteen binding-site residues, four structures, eight chains. Eight of the
thirteen vary by 20 degrees or less in every torsion, so making them flexible
buys search cost and nothing else.
"""
import pytest

from conftest import read_json, run_script

ROTAMER_CHANGING = {"Gln120", "Leu293", "Thr316"}
THRESHOLD = 20.0     # degrees; below this a residue is not moving


@pytest.fixture(scope="module")
def torsions(ch10_outputs):
    """The shared session run. Chapter 2 reads this file too."""
    return ch10_outputs


def test_eight_chains_were_analysed(torsions):
    assert len(torsions["chains"]) == 8, \
        "expected eight chains across 1L2S, 4JXS, 4JXV and 1GA9; got %d" % len(
            torsions["chains"])


def test_rotamer_changing_residues(torsions):
    """Exactly three, and these three."""
    assert set(torsions["rotamer_changing"]) == ROTAMER_CHANGING, \
        ("got %s, book says %s"
         % (sorted(torsions["rotamer_changing"]), sorted(ROTAMER_CHANGING)))


def test_the_rest_are_rigid(torsions):
    """Eight of the thirteen vary by 20 degrees or less in every torsion."""
    rigid = [r for r, spread in torsions["max_spread"].items()
             if spread <= THRESHOLD]
    assert len(rigid) >= 8, \
        "expected at least eight residues varying by <= %.0f deg; got %d" % (
            THRESHOLD, len(rigid))
    for residue in ROTAMER_CHANGING:
        assert residue not in rigid


def test_catalytic_serine_does_not_move(torsions):
    """Ser64 is the nucleophile. If it were rotameric the site would not exist."""
    assert torsions["max_spread"]["Ser64"] <= THRESHOLD
