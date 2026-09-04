"""Chapter 20: the filled AmpC record has to match the book's example.

These are the values SESSION_PLAN 3 names explicitly, and they are the ones a
reader will check the example against.
"""
import pytest

from conftest import REPO, read_json, run_script


@pytest.fixture(scope="module")
def record():
    run_script("ch20_protocol_record/scripts/fill_record.py")
    return read_json("ch20_protocol_record/outputs/filled_record.json")


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
    """Three copies in the entry; the one used is 2.70 Å from Ser64 OG."""
    copies = record["structure"]["ligand_copies"]
    assert len(copies) == 3
    assert record["structure"]["chosen_distance"] == pytest.approx(2.70, abs=0.01)
    assert any(c["distance_to_ser64_og"] > 20 for c in copies), \
        "the interface copy must still appear, so the choice can be checked"


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


def test_blank_template_marks_the_tier_one_fields():
    blank = REPO / "ch20_protocol_record" / "templates" / "blank_record.md"
    assert blank.exists()
    text = blank.read_text(encoding="utf-8")
    assert text.count("★") >= 7
    for field in ("Receptor source", "Ligand source", "Box centre",
                  "Box dimensions", "Random seed", "Docking program"):
        assert field in text
