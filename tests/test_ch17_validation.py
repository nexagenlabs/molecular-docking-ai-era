"""Chapter 17: the redock, and the two ways it can be faked.

The first is picking the wrong ligand copy. The second is measuring RMSD with
superposition, which discards exactly what a redock tests.
"""
import pytest

from conftest import REPO, read_json, run_script


@pytest.fixture(scope="module")
def validation(ch17_outputs):
    """The shared session run. ch02, ch16 and ch23 all read this file."""
    return ch17_outputs


def test_selects_the_catalytic_copy_not_the_interface_one(validation):
    """1L2S holds a copy 22.7 A from any active site. File order does not say so."""
    selection = validation["1L2S"]["ligand_selection"]
    assert selection["chosen"]["distance_to_ser64_og"] == pytest.approx(2.70, abs=0.01)
    discarded = [c for c in selection["candidates"]
                 if c["copy"] != selection["chosen"]["copy"]]
    assert any(c["distance_to_ser64_og"] > 20 for c in discarded), \
        "the interface copy at 22.7 A must appear among the candidates"
    assert selection["selected_by"] == "minimum distance to Ser64 OG"


def test_reports_every_unused_hetatm_group(validation):
    """Silent ligand mis-picking is the failure this script exists to prevent."""
    for entry in ("1L2S", "4JXS", "4JXV"):
        assert validation[entry]["unused_hetatm_groups"], \
            "%s reported no unused HETATM groups, which cannot be right" % entry


def test_rmsd_is_computed_without_superposition(validation):
    """--minimize makes every validation pass. It must never be used."""
    method = validation["rmsd_method"]
    assert method["superposition"] is False
    assert method["symmetry_corrected"] is True
    assert method["heavy_atoms_only"] is True
    assert "--minimize" not in method.get("command", "")


def test_rmsd_values_are_reported_for_all_three_entries(validation):
    for entry in ("1L2S", "4JXS", "4JXV"):
        rmsd = validation[entry]["rmsd"]
        assert rmsd is not None and rmsd > 0, \
            ("%s produced RMSD %r. A redock RMSD of exactly zero means "
             "superposition crept in." % (entry, rmsd))


def test_seed_is_recorded(validation):
    assert validation["docking"]["seed"] == 42
    assert validation["docking"]["exhaustiveness"] == 32


def test_validation_record_is_emitted():
    record = REPO / "ch17_validation" / "outputs" / "validation_record.md"
    assert record.exists(), "validation_record.md was not written"
    text = record.read_text(encoding="utf-8")
    # The tier-one fields of Chapter 20's record: without these the run cannot
    # be repeated, however complete the rest of the document is.
    for field in ("Receptor source", "Ligand source", "Box centre",
                  "Box dimensions", "seed", "Vina"):
        assert field.lower() in text.lower(), "record is missing %r" % field
