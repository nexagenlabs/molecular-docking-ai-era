"""Chapter 27: a methods section generated from the record rather than remembered.

Every number in the paragraph is traceable to
ch20_protocol_record/outputs/filled_record.json. **That is a cross-chapter
dependency**, and the fixture builds the chain ch09 -> ch20 -> ch27 rather
than assuming it.

The claim worth guarding is the last one: the two fields a tool cannot fill
are left as visible [TODO] markers inside the paragraph. A methods section with
a hole in it is one somebody will fix; one with a plausible sentence covering
the hole is one nobody will ever check.
"""
import re

import pytest

from conftest import REPO, run_script

METHODS = REPO / "ch27_methods" / "outputs" / "methods.md"


@pytest.fixture(scope="module")
def methods(ch20_outputs):
    """ch20_outputs is the dependency, and it builds ch09's AmpC run in turn."""
    run_script("ch27_methods/scripts/write_methods.py")
    return METHODS.read_text(encoding="utf-8"), ch20_outputs


def test_the_gaps_are_visible_in_the_paragraph_not_only_in_a_table(methods):
    """[TODO] in the running text, where a reader cannot skip it."""
    text, record = methods
    for field in record["todo"]:
        if field == "Cross-docking or enrichment result":
            continue        # a different experiment; it has its own record
        assert "[TODO: %s" % field in text, \
            "%s is missing from the paragraph as a visible gap" % field


def test_no_gap_was_filled_with_a_plausible_sentence(methods):
    """The two fields no tool can fill must not have acquired values."""
    _, record = methods
    for field in ("Stereochemistry as docked", "Exclusions and deviations"):
        assert record["fields"][field]["value"] is None, \
            "%s was filled in; a tool can record what happened, not what you " \
            "decided" % field


def test_the_numbers_in_the_prose_come_from_the_record(methods):
    """Spot-checked against the record itself, field by field.

    The point of generating this text is that nothing in it is typed twice.
    """
    text, record = methods
    structure = record["structure"]
    assert structure["pdb_id"] in text
    assert "%.2f" % structure["resolution"] in text
    assert "%.3f" % structure["r_free"] in text
    assert "chain %s" % structure["chain"] in text.lower() or \
        "Chain %s" % structure["chain"] in text
    assert str(structure["disordered_side_chain_count"]) in text
    assert record["fields"]["Random seed"]["value"] in text


def test_the_ligand_copy_and_its_distance_are_both_stated(methods):
    """Selected by distance, and the discarded copy is named.

    A methods section that says "the ligand" when the entry holds three copies
    is not reproducible, however precise the rest of it is.
    """
    text, record = methods
    structure = record["structure"]
    assert structure["chosen_copy"] in text
    assert "%.2f" % structure["chosen_distance"] in text
    assert str(len(structure["ligand_copies"])) in text
    assert "order of appearance" in text or "file order" in text, \
        "the text does not say that file order was NOT how the copy was chosen"


def test_the_absence_of_a_metal_is_stated_rather_than_omitted(methods):
    """AmpC is a class C serine hydrolase. Silence invites the other reading."""
    text, _ = methods
    assert "serine hydrolase" in text
    assert "no metal" in text.lower()


def test_superposition_is_named_as_omitted_and_why(methods):
    """The gotcha, carried into the prose a reader will actually publish."""
    text, _ = methods
    assert "without superposition" in text.lower()
    assert "minimize=False" in text
    assert re.search(r"0\.000|returns 0", text), \
        "the text does not say what enabling superposition would return, " \
        "which is the only part that makes the omission checkable"


def test_it_refuses_when_ch20_has_not_been_run(tmp_path):
    """The dependency, declared by failing rather than by degrading."""
    from conftest import run_script_raw

    record = REPO / "ch20_protocol_record" / "outputs" / "filled_record.json"
    if not record.exists():
        pytest.skip("ch20 has not been run in this tree yet")
    stashed = tmp_path / "filled_record.json"
    record.replace(stashed)
    try:
        result = run_script_raw("ch27_methods/scripts/write_methods.py")
        message = result.stdout + result.stderr
        assert result.returncode != 0, \
            "write_methods.py produced a methods section with no record to " \
            "read; every number in it would be invented"
        assert "Traceback" not in message
        assert "ch20" in message
    finally:
        stashed.replace(record)
