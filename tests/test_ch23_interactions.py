"""Chapter 23: an RMSD is one number for a whole molecule.

It says the pose is 1.114 A away. It does not say which contacts survived that
distance -- and the two measurements can disagree in both directions: a pose
can sit close and miss the interaction the chemistry depends on, or sit
further away and make every one of them.

**This chapter reads ch17's output.** The fixture builds it, rather than
hoping an earlier run left it behind.
"""
import pytest

from conftest import REPO, read_json, run_script, run_script_raw


@pytest.fixture(scope="module")
def prints(ch17_outputs):
    """ch17_outputs is the dependency: the crystal and docked SDFs come from it."""
    run_script("ch23_interactions/scripts/fingerprint.py")
    return read_json("ch23_interactions/outputs/fingerprint.json")


def test_it_refuses_when_ch17_has_not_been_run(tmp_path):
    """The pattern ch20 did not follow and this chapter does.

    ch17's work directory is moved aside, and the script must name the missing
    file and the chapter that makes it rather than tracebacking or producing a
    fingerprint of nothing.
    """
    work = REPO / "ch17_validation" / "outputs" / "work"
    if not work.exists():
        pytest.skip("ch17 has not been run in this tree yet")
    stashed = tmp_path / "work"
    work.replace(stashed)
    try:
        result = run_script_raw("ch23_interactions/scripts/fingerprint.py")
        message = result.stdout + result.stderr
        assert result.returncode != 0
        assert "ch17_validation/run.sh" in message, \
            "the refusal did not say which chapter produces the missing file"
        assert "Traceback" not in message
    finally:
        stashed.replace(work)


def test_the_two_fingerprints_are_of_the_same_ligand_and_site(prints):
    assert prints["crystal"] == "1L2S"
    assert prints["chain"] == "B"
    assert prints["ligand"] == "STC"
    assert prints["rmsd_for_context"] == pytest.approx(1.114, abs=0.01), \
        "the RMSD carried through from ch17 no longer matches; the two " \
        "chapters are describing different poses"


def test_most_of_the_crystallographic_contacts_survive(prints):
    """93% recovered. Computed here from the three lists, not read from a field."""
    shared, missed = len(prints["shared"]), len(prints["missed"])
    assert shared + missed > 0
    assert prints["recovery"] == pytest.approx(shared / (shared + missed), abs=0.001)
    assert prints["recovery"] > 0.85, \
        "recovery fell to %.3f; a 1.1 A pose is supposed to keep most of its " \
        "contacts" % prints["recovery"]


def test_the_disagreement_runs_in_both_directions(prints):
    """A contact missed, and three the docked pose makes that the crystal does not.

    This is the chapter's point. A fingerprint that only ever lost contacts
    would just be a noisier RMSD.
    """
    assert prints["missed"], "no crystallographic contact was missed at all"
    assert prints["docked_only"], \
        "the docked pose made no contact the crystal pose does not; the " \
        "comparison would then be one-directional"


def test_the_catalytic_serine_contact_is_kept_but_not_completely(prints):
    """Ser64 keeps its hydrogen bond and loses the hydrophobic contact.

    Which is exactly the kind of thing an RMSD of 1.114 A cannot tell you.
    """
    assert "Ser64:hbond" in prints["shared"]
    assert "Ser64:hydrophobic" in prints["missed"]


def test_every_cutoff_is_stated(prints):
    """Every one is a threshold on a continuum.

    A contact at 3.6 A is not absent from a 3.5 A criterion -- it is just
    outside it, and a fingerprint that renders that as a clean 0 has invented
    precision the geometry does not have. Stating the cutoffs is what lets a
    reader see that.
    """
    cutoffs = prints["cutoffs"]
    for name in ("hydrophobic", "hbond", "salt_bridge", "stacking",
                 "stacking_angle"):
        assert name in cutoffs, "no cutoff recorded for %s" % name
        assert cutoffs[name] > 0
    assert cutoffs["hbond"] < cutoffs["hydrophobic"], \
        "a hydrogen bond criterion looser than the hydrophobic one would make " \
        "every hydrophobic contact a hydrogen bond as well"


def test_detection_is_distance_only_and_the_cutoff_is_the_whole_rule(prints):
    """No pharmacophore model and no scoring function: nothing to tune.

    Driven rather than read. Two atoms are placed either side of the hydrogen
    bond cutoff and the detector is asked about each. If anything but the
    distance were involved, one of these two answers would not follow from the
    cutoff alone -- and grepping the source for the word "pharmacophore" would
    not have found that out, since the file's own prose contains it.
    """
    from conftest import load_module

    fp = load_module("ch23_interactions/scripts/fingerprint.py", "ch23_fingerprint")
    cutoff = fp.HBOND

    def contacts_at(distance):
        protein = [{"res": "ASN", "chain": "B", "seq": "152", "name": "ND2",
                    "xyz": (0.0, 0.0, 0.0)}]
        ligand = [{"symbol": "O", "charge": 0, "xyz": (distance, 0.0, 0.0)}]
        return fp.fingerprint(protein, ligand, [])

    inside = contacts_at(cutoff - 0.05)
    outside = contacts_at(cutoff + 0.05)
    assert any("hbond" in kinds for kinds in inside.values()), \
        "a heteroatom pair at %.2f A was not called a hydrogen bond" % (cutoff - 0.05)
    assert not any("hbond" in kinds for kinds in outside.values()), \
        "a heteroatom pair at %.2f A was called a hydrogen bond; the cutoff " \
        "is not what decides" % (cutoff + 0.05)
