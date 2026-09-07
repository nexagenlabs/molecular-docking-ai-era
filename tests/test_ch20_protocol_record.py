"""Chapter 20: the filled AmpC record has to match the book's example.

These are the values SESSION_PLAN 3 names explicitly, and they are the ones a
reader will check the example against.

**This chapter reads ch09's AmpC run.** Two of its inputs:

    ch09_first_run/config/vina_config.txt              committed
    ch09_first_run/outputs/ampc/logs/modes.log         gitignored

The second is produced only by PART 2 of ch09_first_run/run.sh. In this
author's working tree it had been left behind by an earlier manual run, so the
suite passed here and failed in a clean clone: without the log the record
carries five TODOs instead of three and tier_one_complete is False. The
dependency was real, silent and undeclared.

So the fixture below builds it rather than hoping for it. It is a fixture and
not a comment because a declared dependency that nothing executes is the same
undeclared dependency with better documentation.
"""
import pytest

from conftest import REPO, read_json, run_script, run_script_raw


@pytest.fixture(scope="module")
def record(ch20_outputs):
    """The shared session run, which builds ch09's AmpC branch first.

    That fixture lives in conftest because ch27 reads this chapter's output in
    turn, so the chain ch09 -> ch20 -> ch27 is built once for the whole suite.
    """
    return ch20_outputs


def test_the_worked_example_matches_the_book(record):
    structure = record["structure"]
    assert structure["pdb_id"] == "1L2S"
    assert structure["chain"] == "B"
    assert structure["r_free"] == pytest.approx(0.207, abs=0.0005)
    assert structure["chosen_copy"] == "B/2115"
    assert structure["altlocs"] == ["GLN B250"]


def test_no_metal_is_stated_rather_than_omitted(record):
    """AmpC is a class C serine hydrolase.

    A record that simply says nothing about metals leaves a reader to wonder
    whether one was quietly deleted, so 'none' has to be asserted rather than
    implied by absence.
    """
    assert record["structure"]["metals"] == []
    waters_field = record["fields"]["Waters and ions"]["value"]
    assert "none" in waters_field.lower()
    assert "serine hydrolase" in waters_field


def test_the_ligand_copy_was_chosen_by_distance(record):
    """Three copies in the entry; the one used is B/2115, 2.70 Å from Ser64 OG.

    The distance alone does not establish the choice, and this test used to
    assert only the distance. 1L2S's first STC copy in file order, A/1115, is
    *also* 2.70 Å from a Ser64 OG, so selecting by file order passed here while
    picking the wrong chain -- chain A, the one missing Lys290-Ala292. The
    copy's identity is what distinguishes the two, so it is asserted here, and
    the rule itself is tested on a case where order and distance disagree in
    test_gotchas.test_the_ligand_copy_is_chosen_by_distance_and_not_by_file_order.
    """
    copies = record["structure"]["ligand_copies"]
    assert len(copies) == 3
    assert record["structure"]["chosen_copy"] == "B/2115"
    assert record["structure"]["chosen_distance"] == pytest.approx(2.70, abs=0.01)
    assert any(c["distance_to_ser64_og"] > 20 for c in copies), \
        "the interface copy must still appear, so the choice can be checked"
    # The decoy: another copy at the same distance, in the chain not used.
    decoys = [c for c in copies
              if c["chain"] != "B" and c["distance_to_ser64_og"] < 5.0]
    assert decoys, ("1L2S must still hold a catalytic copy outside chain B. "
                    "If it does not, this test no longer distinguishes "
                    "selection by distance from selection by file order.")


def test_every_tier_one_field_is_filled(record):
    """The seven fields without which the run cannot be re-executed."""
    assert record["tier_one_complete"] is True


def test_the_fields_a_tool_cannot_fill_are_left_visible(record):
    """Three gaps, marked, not papered over with plausible filler."""
    assert set(record["todo"]) == {
        "Stereochemistry as docked",
        "Cross-docking or enrichment result",
        "Exclusions and deviations",
    }


def test_seed_is_cross_checked_between_config_and_log(record):
    """A config edited after the run describes a protocol that never ran."""
    assert record["seed_mismatch"] is None
    assert record["fields"]["Random seed"]["value"] == "42"


@pytest.mark.parametrize("flag, missing", [
    ("--config", "ch09_first_run/config/no_such_config.txt"),
    ("--log", "ch09_first_run/outputs/ampc/logs/no_such.log"),
])
def test_a_missing_upstream_file_stops_the_run_and_names_it(flag, missing,
                                                            tmp_path):
    """Both inputs, refused the same way.

    The config used to get a clear sentence and the log used to degrade to an
    empty dict. The asymmetry is what let a record be produced that named no
    docking program, reported no redocking result, and said so only by leaving
    two more TODOs than usual -- which looks like a finding, not a missing
    file. ch02 and ch23 name their missing upstream artefacts; this is the same
    contract, asserted.
    """
    result = run_script_raw("ch20_protocol_record/scripts/fill_record.py",
                            flag, missing,
                            "--out", str(tmp_path / "record.md"))
    assert result.returncode != 0, \
        "a missing %s produced exit 0:\n%s" % (flag, result.stdout)
    message = result.stdout + result.stderr
    assert "no_such" in message, "the refusal did not name the missing file"
    assert "ch09_first_run/run.sh" in message, \
        "the refusal did not say which chapter produces it"
    assert "Traceback" not in message, "refused with a traceback, not a message"


def test_blank_template_marks_the_tier_one_fields():
    blank = REPO / "ch20_protocol_record" / "templates" / "blank_record.md"
    assert blank.exists()
    text = blank.read_text(encoding="utf-8")
    assert text.count("★") >= 7
    for field in ("Receptor source", "Ligand source", "Box centre",
                  "Box dimensions", "Random seed", "Docking program"):
        assert field in text
