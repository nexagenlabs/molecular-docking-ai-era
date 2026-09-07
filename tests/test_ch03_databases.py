"""Chapter 3: two independent sources for every number, and one disagreement kept.

Resolution and R-free come from the RCSB REST API and from the header of the
coordinate file this repository downloaded. Agreement between them is the
check; where the sources disagree -- 1MU's Ki, 26 uM in ChEMBL and 31 uM in
PDBbind -- both values are carried rather than one being chosen.

This chapter reaches the network. The header half of every check works
offline, so the tests are split: the file-header values are asserted always,
and the API agreement only when the run actually reached RCSB.
"""
import pytest

from conftest import read_json, run_script

# From the coordinate file headers. These are facts about four fixed PDB
# entries and do not depend on the platform, the network or the run.
HEADER = {
    "1L2S": (1.94, 0.207),
    "4JXS": (1.90, 0.212),
    "4JXV": (1.76, 0.232),
    "1GA9": (2.10, 0.249),
}


@pytest.fixture(scope="module")
def cross_check():
    run_script("ch03_databases/scripts/cross_check.py", timeout=900)
    return read_json("ch03_databases/outputs/cross_check.json")


@pytest.mark.parametrize("entry", sorted(HEADER))
def test_the_file_header_says_what_the_book_says(cross_check, entry):
    resolution, r_free = HEADER[entry]
    record = cross_check["entries"][entry]
    assert record["header_resolution"] == pytest.approx(resolution, abs=0.005)
    assert record["header_r_free"] == pytest.approx(r_free, abs=0.0005)


@pytest.mark.parametrize("entry", sorted(HEADER))
def test_the_api_and_the_file_agree(cross_check, entry):
    """The check itself. Skipped, not faked, when the network was unavailable."""
    if cross_check["offline"]:
        pytest.skip("cross_check.py ran offline; there is no API value to compare")
    record = cross_check["entries"][entry]
    assert record["resolution_agrees"] is True, \
        "%s: API %s, file %s" % (entry, record["api_resolution"],
                                 record["header_resolution"])
    assert record["r_free_agrees"] is True, \
        "%s: API %s, file %s" % (entry, record["api_r_free"],
                                 record["header_r_free"])


def test_the_ligand_skeletons_match_the_pdb_component_dictionary(cross_check):
    """Compared as the NEUTRAL skeleton, on purpose.

    The PDB component describes the molecule as modelled in the crystal, which
    carries no protonation state for pH 7.4. This repository docks STC at -1
    and 18U and 1MU at -2. Those are different molecules; the check is that
    the skeleton matches and the charge is expected to differ.
    """
    if cross_check["offline"]:
        pytest.skip("no chemical component data was fetched")
    for name in ("STC", "18U", "1MU"):
        ligand = cross_check["ligands"][name]
        assert ligand["same_neutral_skeleton"] is True, \
            "%s: ours %s, PDB %s" % (name, ligand["our_smiles"],
                                     ligand["pdb_smiles"])


def test_our_smiles_carry_the_charge_the_pdb_component_does_not(cross_check):
    """The difference that makes the neutral-skeleton comparison necessary."""
    if cross_check["offline"]:
        pytest.skip("no chemical component data was fetched")
    charges = {"STC": 1, "18U": 2, "1MU": 2}
    for name, expected in charges.items():
        ours = cross_check["ligands"][name]["our_smiles"]
        assert ours.count("[O-]") == expected, \
            "%s should carry %d deprotonated oxygens: %s" % (name, expected, ours)
        assert "[O-]" not in cross_check["ligands"][name]["pdb_smiles"], \
            "%s: the PDB component is supposed to be the neutral form" % name


def test_the_two_affinity_sources_agree_except_about_1mu(cross_check):
    """26 against 31 uM. Reported, not resolved.

    ch22 and ch26 both depend on this staying a disagreement: it is 32% of the
    entire spread the series is being asked to resolve.
    """
    affinity = cross_check["affinity"]
    for name in ("STC", "18U"):
        assert affinity[name]["chembl_uM"] == affinity[name]["pdbbind_uM"], name
    assert affinity["1MU"]["chembl_uM"] == pytest.approx(26.0)
    assert affinity["1MU"]["pdbbind_uM"] == pytest.approx(31.0)
    assert affinity["1MU"]["chembl_uM"] != affinity["1MU"]["pdbbind_uM"], \
        "the sources now agree about 1MU; if that is real it changes ch22 " \
        "and ch26, so find out which value moved before updating anything"


def test_etp_is_carried_but_never_converted(cross_check):
    """83 nM, measured with a different substrate and buffer.

    Not comparable to the micromolar values above. No conversion between Ki,
    IC50 and Kd happens anywhere in this repository, and this is the entry
    that most invites one.
    """
    etp = cross_check["affinity"]["ETP"]
    assert "chembl_uM" not in etp and "pdbbind_uM" not in etp, \
        "ETP was given a micromolar value, which would put it on the same " \
        "axis as the series"
    assert "not comparable" in etp["note"].lower()
    assert "not converted" in etp["note"].lower()


def test_1ga9_is_flagged_as_the_excluded_entry(cross_check):
    """A covalent boronic acid with a potassium ion, in a serine enzyme.

    The exclusion is a modelling decision and has to be visible as one.
    """
    groups = cross_check["entries"]["1GA9"]["hetatm_groups"]
    assert "ETP" in groups
    assert "K" in groups, \
        "the potassium is supposed to be named explicitly; a stray metal in a " \
        "serine enzyme invites exactly the misreading this book warns about"


def test_the_phosphate_entries_are_visible_as_such(cross_check):
    """4JXS, 4JXV and 1GA9 carry crystallisation phosphate; 1L2S does not."""
    assert "PO4" not in cross_check["entries"]["1L2S"]["hetatm_groups"]
    for entry in ("4JXS", "4JXV", "1GA9"):
        assert "PO4" in cross_check["entries"][entry]["hetatm_groups"], entry
