"""Chapter 5: what the QC report has to find before anyone docks.

Each assertion here is a specific way a structure quietly breaks a docking run.
"""
import pytest

from conftest import read_json, run_script


@pytest.fixture(scope="module")
def qc():
    run_script("ch05_receptor_prep/scripts/qc_report.py", "--quiet")
    return {entry: read_json("ch05_receptor_prep/outputs/qc_%s.json" % entry)
            for entry in ("1L2S", "4JXS", "4JXV", "1GA9")}


@pytest.mark.parametrize("entry,resolution,r_free", [
    ("1L2S", 1.94, 0.207),
    ("4JXS", 1.90, 0.212),
    ("4JXV", 1.76, 0.232),
    ("1GA9", 2.10, 0.249),
])
def test_resolution_and_r_free(qc, entry, resolution, r_free):
    """Read from the header, and the header has traps.

    FREE R VALUE TEST SET COUNT sits a few lines from FREE R VALUE and is an
    integer in the thousands; a prefix match reports 2647 as an R-free.
    """
    assert qc[entry]["resolution"] == pytest.approx(resolution, abs=0.005)
    assert qc[entry]["r_free"] == pytest.approx(r_free, abs=0.0005)


def test_1l2s_has_three_ligand_copies_at_the_right_distances(qc):
    copies = {"%s/%s" % (c["chain"], c["seq"]): c["distance_to_catalytic"]
              for c in qc["1L2S"]["ligand_copies"]}
    assert copies["A/1115"] == pytest.approx(2.70, abs=0.01)
    assert copies["B/2115"] == pytest.approx(2.70, abs=0.01)
    assert copies["B/3115"] == pytest.approx(22.72, abs=0.01)


def test_the_interface_copy_is_flagged_as_not_in_a_site(qc):
    """22.7 A from either active site. Nothing in the file marks it."""
    interface = [c for c in qc["1L2S"]["ligand_copies"] if c["seq"] == "3115"][0]
    assert interface["in_site"] is False


def test_1l2s_chain_a_is_missing_290_to_292(qc):
    gaps = qc["1L2S"]["missing_residues"]
    assert set(gaps) == {"A"}, "only chain A should have a break"
    assert gaps["A"] == ["LYS 290", "ILE 291", "ALA 292"]


def test_1l2s_sole_altloc_is_gln250(qc):
    assert list(qc["1L2S"]["altlocs"]) == ["GLN B250"]


def test_1l2s_chain_b_has_two_bridging_waters(qc):
    """HOH 403 and 481. Deleting them puts the crystal pose out of reach."""
    by_copy = qc["1L2S"]["bridging_waters_by_copy"]
    chain_b = by_copy["STC B/2115"]
    assert len(chain_b) == 2, \
        "expected two bridging waters in chain B, got %s" % [w["water"] for w in chain_b]
    waters = {w["water"]: w for w in chain_b}
    assert set(waters) == {"B/403", "B/481"}
    assert waters["B/403"]["distance_to_ligand"] == pytest.approx(2.68, abs=0.01)
    assert waters["B/481"]["distance_to_ligand"] == pytest.approx(2.70, abs=0.01)
    assert set(waters["B/403"]["contacts"]) == {"Asn346", "Arg349"}
    assert set(waters["B/481"]["contacts"]) == {"Thr316", "Lys315", "Tyr150"}


def test_1l2s_contains_no_phosphate(qc):
    """1L2S was not crystallised from phosphate.

    A phosphate reported here means the HETATM parsing has gone wrong, which
    means the ligand selection cannot be trusted either.
    """
    assert qc["1L2S"]["phosphorus_atoms"] == 0
    assert qc["1L2S"]["nearest_phosphorus_to_catalytic"] is None


def test_nearest_phosphate_across_the_other_three(qc):
    """7.83 A, in 4JXS -- the minimum across the three phosphate structures."""
    distances = {entry: qc[entry]["nearest_phosphorus_to_catalytic"]
                 for entry in ("4JXS", "4JXV", "1GA9")}
    assert min(distances.values()) == pytest.approx(7.83, abs=0.01)
    assert distances["4JXS"] == pytest.approx(7.83, abs=0.01)
    # All of them are surface artefacts, not site-bound.
    for entry, distance in distances.items():
        assert distance > 5.0, "%s has phosphorus in the site" % entry


def test_4jxs_ligand_is_in_chain_b_only(qc):
    copies = qc["4JXS"]["ligand_copies"]
    assert len(copies) == 1
    assert copies[0]["chain"] == "B"


def test_4jxv_ligand_is_in_both_chains(qc):
    """A/402 single, B/401 in two altlocs -- so a reference is two decisions."""
    copies = {"%s/%s" % (c["chain"], c["seq"]): c for c in qc["4JXV"]["ligand_copies"]}
    assert set(copies) == {"A/402", "B/401"}
    altloc_residues = qc["4JXV"]["altlocs"]
    assert any(key.startswith("1MU") for key in altloc_residues), \
        "the chain B ligand's two altlocs should be reported"


def test_1ga9_is_covalent_and_reported_as_such(qc):
    """ETP is bonded to Ser64 OG. Non-covalent docking cannot represent it."""
    links = qc["1GA9"]["covalent_to_catalytic"]
    assert len(links) == 2, "one LINK per chain"
    assert any("1.64" in l for l in links)
    assert any("1.62" in l for l in links)


def test_1ga9_potassium_is_reported(qc):
    """AmpC is a serine enzyme. A stray metal invites exactly the misreading
    this book warns about, so the report must name it."""
    additives = {a["res"] for a in qc["1GA9"]["additive_groups"]}
    assert "K" in additives
