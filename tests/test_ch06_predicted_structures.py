"""Chapter 6: a near-perfect backbone that does not buy a near-crystal pose.

Two claims, and the second is the one the chapter exists for.

The numbering trap first: UniProt number = PDB number + 16. Ask the AlphaFold
model for residue 64 -- the number the crystal structure uses -- and you get
isoleucine, not the catalytic serine, and no error is raised.

Then the test that settles it. pLDDT 98.5 at the site and a backbone 0.216 A
from the crystal, and the pose docked into the model still lands further from
the crystallographic one than the pose docked into the crystal. No confidence
metric predicted that gap, which is the point: the metrics do not measure the
thing docking uses.

RMSD values are docking output, so the assertions are on the comparison rather
than on the third decimal -- the same rule test_ch17_validation follows.
"""
import pytest


def test_the_numbering_offset_is_recovered_rather_than_assumed(ch06_outputs):
    """+16 across the whole chain, established from the sequences at 100%."""
    numbering = ch06_outputs["numbering"]
    assert numbering["offset_uniprot_minus_pdb"] == 16
    assert numbering["residue_identity"] == pytest.approx(1.0, abs=1e-9), \
        "the offset is only meaningful if the sequences match; identity is %.3f" \
        % numbering["residue_identity"]


def test_looking_up_the_pdb_number_in_the_model_gives_the_wrong_residue(ch06_outputs):
    """The trap, as a fact about residue 64 rather than as a warning.

    This is what makes it dangerous: it is a silent substitution, not an error.
    """
    site = {row["pdb"]: row for row in ch06_outputs["numbering"]["site"]}
    catalytic = site["64"]
    assert catalytic["crystal_residue"] == "SER"
    assert catalytic["model_residue"] == "SER", \
        "at the correct UniProt number the model does have the serine"
    assert catalytic["model_residue_at_pdb_number"] != "SER", \
        "residue 64 of the model must NOT be the catalytic serine, or the " \
        "chapter's central example has gone away"
    wrong = [r for r in ch06_outputs["numbering"]["site"]
             if r["model_residue_at_pdb_number"] != r["crystal_residue"]]
    assert len(wrong) >= 12, \
        "only %d of the 14 site residues are wrong under naive numbering; the " \
        "trap is supposed to be near-total" % len(wrong)


def test_confidence_is_reported_where_docking_uses_it(ch06_outputs):
    """A whole-chain pLDDT average hides the only part that matters."""
    confidence = ch06_outputs["confidence"]
    assert confidence["site_mean_plddt"] == pytest.approx(98.5, abs=0.2)
    assert confidence["whole_chain_plddt"] == pytest.approx(96.4, abs=0.2)
    assert confidence["site_mean_plddt"] > 90, \
        "the site is very high confidence, which is what makes the result " \
        "below worth reporting"
    assert len(confidence["site_plddt"]) == 14


def test_the_backbone_agreement_is_excellent(ch06_outputs):
    """0.216 A over 358 CA atoms. By any structural criterion this is a good model."""
    geometry = ch06_outputs["geometry"]
    assert geometry["matched_ca_atoms"] == 358
    assert geometry["backbone_rmsd"] < 0.5
    assert geometry["site_ca_rmsd"] < 0.5


def test_the_docked_pose_is_still_worse_than_the_crystals(ch06_outputs):
    """The chapter's conclusion, and the only assertion that decides it.

    Same ligand, same box, same seed, same exhaustiveness; the receptor is the
    only difference. Asserted as a comparison rather than as 3.140 against
    1.114, because both are docking output.
    """
    docking = ch06_outputs["docking"]
    af = docking["rmsd_to_crystal_pose"]
    crystal = docking["crystal_structure_reference_rmsd"]
    assert af > crystal, \
        ("docking into the AlphaFold model gave %.3f A and into the crystal "
         "%.3f A. The chapter's conclusion is that the prediction is worse."
         % (af, crystal))
    assert af > 2.0, \
        "the AlphaFold pose is supposed to miss the usual 2 A criterion"
    assert crystal < 2.0, \
        "the crystal-structure redock is supposed to meet it"


def test_no_confidence_metric_predicted_the_gap(ch06_outputs):
    """Stated in the chapter and checkable: every metric said the model was good.

    If a future model had a poor site pLDDT or a poor backbone, the chapter's
    argument would be the ordinary one about bad models rather than the
    surprising one about good ones.
    """
    assert ch06_outputs["confidence"]["site_mean_plddt"] > 95
    assert ch06_outputs["geometry"]["backbone_rmsd"] < 0.3
    assert ch06_outputs["geometry"]["site_side_chain_mean"] < 1.0
    assert ch06_outputs["docking"]["rmsd_to_crystal_pose"] > 2.0


def test_the_run_is_recorded_the_same_way_as_every_other(ch06_outputs):
    docking = ch06_outputs["docking"]
    assert docking["seed"] == 42
    assert docking["exhaustiveness"] == 32
    assert "1.2.7" in docking["program"]
