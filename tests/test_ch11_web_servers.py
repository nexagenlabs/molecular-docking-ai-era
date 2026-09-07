"""Chapter 11: what a docking web server lets you record, and what it does not.

The chapter's conclusion is that a web-server run cannot be repeated -- not by
you and not by the server -- because almost none of them lets you set a seed
and almost none reports the one it used. That is asserted against Chapter 20's
seventeen fields rather than argued.

The upload set carries its own claim: the ligand goes up as SDF and not PDBQT,
because PDBQT loses the formal charge and this series cannot afford to.
"""
import pytest

from conftest import REPO, read_json, run_script

UPLOAD = REPO / "ch11_web_servers" / "outputs" / "upload"


@pytest.fixture(scope="module")
def audit():
    run_script("ch11_web_servers/scripts/prepare_upload.py")
    return read_json("ch11_web_servers/outputs/server_audit.json")


def test_the_ligand_goes_up_as_sdf_and_not_pdbqt(audit):
    """The server makes its own PDBQT. Sending one is a second chance to lose
    the charge, and the charge is the thing this series turns on."""
    names = set(audit["upload_files"])
    assert "STC.sdf" in names
    assert not [n for n in names if n.endswith(".pdbqt")], \
        "a PDBQT is in the upload set: %s" % sorted(names)
    assert (UPLOAD / "STC.sdf").exists()
    assert not list(UPLOAD.glob("*.pdbqt"))


def test_the_uploaded_ligand_still_carries_its_charge():
    """Written out and read back, because that is the round trip ch04 measures."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    import molfile
    from rdkit import Chem

    mol = molfile.read_one(UPLOAD / "STC.sdf", what="the uploaded STC copy")
    assert Chem.GetFormalCharge(mol) == -1, \
        "the upload set's STC is neutral; the formal charge was lost before it " \
        "ever reached a server"


def test_the_receptor_is_one_chain_with_no_solvent(audit):
    assert audit["receptor_atoms"] == 2761
    text = (UPLOAD / "1L2S_chainB_clean.pdb").read_text(encoding="utf-8")
    chains = {line[21] for line in text.splitlines() if line.startswith("ATOM")}
    assert chains == {"B"}, "expected chain B only, found %s" % chains
    assert "HOH" not in text, "waters were uploaded"


def test_the_box_is_computed_and_written_down(audit):
    """One of the few fields a server lets you control, so arrive with the number."""
    box = (UPLOAD / "box.txt").read_text(encoding="utf-8")
    for key in ("center_x", "center_y", "center_z", "size_x", "size_y", "size_z"):
        assert key in box, "box.txt does not give %s" % key
    assert audit["box"]["centre"] and audit["box"]["size"]
    assert box.lstrip().startswith("#"), \
        "box.txt must say where the numbers came from, or it is six numbers " \
        "a reader has to take on trust"


def test_the_audit_covers_all_seventeen_protocol_fields(audit):
    assert len(audit["audit"]) == 17, \
        "Chapter 20 defines seventeen fields; the audit covers %d" % len(audit["audit"])
    for row in audit["audit"]:
        assert isinstance(row["settable"], bool), row["field"]
        assert isinstance(row["recordable"], bool), row["field"]


def test_the_counts_follow_from_the_rows(audit):
    """Recomputed, so the summary cannot drift away from the table above it."""
    assert audit["settable"] == sum(1 for r in audit["audit"] if r["settable"])
    assert audit["recordable"] == sum(1 for r in audit["audit"] if r["recordable"])
    assert audit["settable"] == 11
    assert audit["recordable"] == 9


def test_three_tier_one_fields_cannot_be_recorded(audit):
    """And the seed is one of them, which is what decides the chapter."""
    assert set(audit["tier_one_not_recordable"]) == {
        "Receptor preparation tool and version",
        "Docking program and version",
        "Random seed",
    }
    seed_row = next(r for r in audit["audit"] if r["field"] == "Random seed")
    assert seed_row["settable"] is False
    assert seed_row["recordable"] is False


def test_nothing_is_submitted_anywhere():
    """Submitting to a third-party service is the user's decision, not a script's.

    Asserted statically because the alternative is a test that finds out by
    submitting something.
    """
    source = (REPO / "ch11_web_servers" / "scripts"
              / "prepare_upload.py").read_text(encoding="utf-8")
    for forbidden in ("requests.post", "urllib.request.urlopen", "urlopen(",
                      "http.client", "webbrowser."):
        assert forbidden not in source, \
            "prepare_upload.py contains %r; this chapter contacts no server" % forbidden
