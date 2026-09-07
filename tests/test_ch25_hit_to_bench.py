"""Chapter 25: a docking score is not an affinity, and the assay is designed anyway.

Vina reports kcal/mol, which invites conversion to a Ki. The chapter converts
the three series members that way on purpose, shows the answers are wrong by
7x, 15x and 16x, and then designs the assay around a *stated guess* instead --
wide enough that being two decades out does not cost the experiment.
"""
import math

import pytest

from conftest import read_json, run_script


@pytest.fixture(scope="module")
def design():
    run_script("ch25_hit_to_bench/scripts/design_assay.py")
    return read_json("ch25_hit_to_bench/outputs/assay_design.json")


def test_converting_a_docking_score_to_a_ki_is_wrong_by_orders_of_magnitude(design):
    """7x, 15x, 16x -- all in the same direction, all far too potent."""
    errors = design["conversion_error_fold"]
    assert errors["STC"] == pytest.approx(6.7, abs=0.2)
    assert errors["18U"] == pytest.approx(15.3, abs=0.3)
    assert errors["1MU"] == pytest.approx(16.5, abs=0.3)
    for ligand, fold in errors.items():
        assert fold > 5, "%s converted to within a factor of five; that would " \
                         "weaken the chapter's claim rather than support it" % ligand


def test_every_conversion_is_too_potent_not_scattered(design):
    """A systematic offset, not noise. The scale is wrong, not the ranking."""
    for ligand, converted in design["naive_conversion"].items():
        assert converted < design["known_ki_uM"][ligand], \
            "%s converted to a weaker Ki than measured; the offset is supposed " \
            "to run the other way" % ligand


def test_the_conversion_is_the_textbook_one_and_still_fails(design):
    """Ki = exp(dG / RT). Recomputed, so the failure cannot be a coding slip.

    The point is that the arithmetic is right and the answer is still wrong:
    a Vina score is a ranking device on an energy-like scale, not a free
    energy, so there is nothing to fix in the conversion.
    """
    rt = 0.592424
    for ligand, score in design["docking_scores"].items():
        expected_uM = math.exp(score / rt) * 1e6
        assert design["naive_conversion"][ligand] == pytest.approx(expected_uM,
                                                                   rel=0.02), ligand


def test_the_potency_guess_is_labelled_a_guess(design):
    """10 uM, stated. The design is built on it rather than on the conversion."""
    assert design["guess_uM"] == pytest.approx(10.0, abs=1e-9)
    for ligand, converted in design["naive_conversion"].items():
        assert converted != design["guess_uM"], \
            "the guess must not be the converted number wearing a different name"


def test_the_range_is_wide_enough_to_survive_being_wrong(design):
    """The guess was two decades low and the design still worked.

    That is the argument for the width: an extra decade costs a few wells,
    and missing the curve costs the experiment.
    """
    series = design["concentration_series_uM"]
    assert design["points"] == len(series) == 13
    decades = math.log10(max(series) / min(series))
    assert decades >= 3.9, "the range spans %.1f decades; the chapter claims four" % decades
    assert all(design["range_covers_truth"][l] for l in design["known_ki_uM"]), \
        "the design must bracket every measured Ki, or it was not wide enough"
    for ligand, ki in design["known_ki_uM"].items():
        assert min(series) < ki < max(series), ligand


def test_the_guess_was_wrong_by_about_two_decades(design):
    """Stated in the chapter as the reason the width earns its keep."""
    for ligand, ki in design["known_ki_uM"].items():
        assert ki / design["guess_uM"] > 1.5, ligand


def test_the_compound_quantity_is_stated_with_its_assumptions(design):
    """5.25 mg, from 13 points, 3 replicates, 100 uL wells.

    Not a theoretical minimum -- enough to pipette, and enough left when the
    first plate goes wrong.
    """
    assert design["replicates"] == 3
    assert design["assay_volume_uL"] == 100
    assert design["compound_needed_mg"] == pytest.approx(5.25, abs=0.05)
    assert design["compound_needed_mg"] > 0
