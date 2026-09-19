"""Chapter 25: a docking score is not an affinity, and the assay is designed anyway.

Vina reports kcal/mol, which invites conversion to a Ki. The chapter converts
the three series members that way on purpose, shows the answers are wrong by
7x, 15x and 17x, and then designs the assay around a *stated guess* instead --
wide enough to survive an error that nothing available at design time bounds.
"""
import math

import pytest

from conftest import REPO, read_json, run_script


@pytest.fixture(scope="module")
def design():
    run_script("ch25_hit_to_bench/scripts/design_assay.py")
    return read_json("ch25_hit_to_bench/outputs/assay_design.json")


def test_converting_a_docking_score_to_a_ki_is_wrong_by_orders_of_magnitude(design):
    """7x, 15x, 17x -- all in the same direction, all far too potent."""
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

    The tolerance is 1e-9, where it used to be 0.02. This test recomputes the
    identical expression, so anything short of float agreement means the
    constant moved -- and a constant can move a long way inside 2%. The
    chapter README carried a table built at T = 297.8 K against the script's
    298.15 K, 1.25% out, for long enough to be published: `rel=0.02` could not
    see it. A check has to be tight enough to detect the thing it is named for.
    """
    rt = 0.001987 * 298.15
    for ligand, score in design["docking_scores"].items():
        expected_uM = math.exp(score / rt) * 1e6
        assert design["naive_conversion"][ligand] == pytest.approx(expected_uM,
                                                                   rel=1e-9), ligand


def test_the_potency_guess_is_labelled_a_guess(design):
    """10 uM, stated. The design is built on it rather than on the conversion."""
    assert design["guess_uM"] == pytest.approx(10.0, abs=1e-9)
    for ligand, converted in design["naive_conversion"].items():
        assert converted != design["guess_uM"], \
            "the guess must not be the converted number wearing a different name"


def test_the_range_is_wide_enough_to_survive_being_wrong(design):
    """Four decades, spanning every measured Ki with room either side.

    The width is fixed while the error is still unknowable: an extra decade
    costs a few wells, and missing the curve costs the experiment.
    """
    series = design["concentration_series_uM"]
    assert design["points"] == len(series) == 13
    decades = math.log10(max(series) / min(series))
    assert decades >= 3.9, "the range spans %.1f decades; the chapter claims four" % decades
    assert all(design["range_covers_truth"][l] for l in design["known_ki_uM"]), \
        "the design must bracket every measured Ki, or it was not wide enough"
    for ligand, ki in design["known_ki_uM"].items():
        assert min(series) < ki < max(series), ligand


def test_the_guess_was_low_by_under_half_a_decade(design):
    """0.26 to 0.41 decades -- not the two decades the chapter used to claim.

    This test was `test_the_guess_was_wrong_by_about_two_decades` and asserted
    only `ki / guess > 1.5`, which 1.8x satisfies. A check that passes at 1.8x
    is not evidence for two decades: it is the same shape as the --minimize
    guard that substring-matched prose. Assert the figure, and recompute it
    here so the payload cannot define its own correctness.
    """
    errors = design["guess_error_decades"]
    assert set(errors) == set(design["known_ki_uM"])
    for ligand, ki in design["known_ki_uM"].items():
        assert errors[ligand] == pytest.approx(
            math.log10(ki / design["guess_uM"]), abs=1e-3), ligand
        assert 0 < errors[ligand] < 0.5, (
            "%s sits %.2f decades from the guess; the chapter says under half "
            "a decade" % (ligand, errors[ligand]))
    assert min(errors.values()) == pytest.approx(0.26, abs=0.01)
    assert max(errors.values()) == pytest.approx(0.41, abs=0.01)


def test_the_width_is_chosen_before_the_error_can_be_known(design):
    """The argument for four decades, which the observed error cannot supply.

    The width is two constants, fixed at design time. What was available then
    was the naive conversion -- itself wrong by 7x to 17x -- and the docking
    score, which bounds nothing. So the width is not a response to the error.
    """
    assert design["decades_below"] == 2
    assert design["decades_above"] == 2
    low, high = design["naive_conversion_span_uM"]
    assert low == pytest.approx(1.17, abs=0.02)
    assert high == pytest.approx(3.91, abs=0.02)
    assert min(design["conversion_error_fold"].values()) > 5

    # The margin the design used is a fraction of the margin it provided, and
    # nothing at design time could have predicted which fraction.
    width = design["decades_below"] + design["decades_above"]
    assert max(design["guess_error_decades"].values()) < width / 4


def _conversion_table(text):
    """The three rows under the `Ki if converted` header, minus sign normalised."""
    lines = text.splitlines()
    head = next(i for i, l in enumerate(lines)
                if l.startswith("| Ligand | Docking score"))
    assert lines[head + 1].startswith("|---"), lines[head + 1]
    return [l.replace("−", "-").strip() for l in lines[head + 2:head + 5]]


def test_the_readme_table_is_the_generated_one(design):
    """The README's conversion table, against the report the script wrote.

    This is the table that carried T = 297.8 K while the script used 298.15,
    because it was copied by hand once and then never recomputed. Nothing in
    the suite compared the two, so the drift was free. Now it is not.
    """
    readme = _conversion_table(
        (REPO / "ch25_hit_to_bench" / "README.md").read_text(encoding="utf-8"))
    report = _conversion_table(
        (REPO / "ch25_hit_to_bench" / "outputs" / "assay_design.md")
        .read_text(encoding="utf-8"))
    assert len(readme) == 3
    assert readme == report, (
        "the chapter README's conversion table no longer matches the one the "
        "script writes; regenerate it rather than editing either by hand")


def test_one_rounding_point_per_quantity(design):
    """A run may not publish two roundings of the same number.

    The payload carries raw floats and every display rounds them once. Storing
    `round(x, 1)` and then formatting it `%.0f` is what let 16.52 reach the
    reader as 16x in the report and 17x on stdout.
    """
    for ligand, fold in design["conversion_error_fold"].items():
        raw = design["known_ki_uM"][ligand] / design["naive_conversion"][ligand]
        assert fold == pytest.approx(raw, rel=1e-12), (
            "%s's error fold was stored as %r where the raw quotient is %r; "
            "the payload carries raw values and display rounds them once"
            % (ligand, fold, raw))
    row = next(r for r in _conversion_table(
        (REPO / "ch25_hit_to_bench" / "outputs" / "assay_design.md")
        .read_text(encoding="utf-8")) if r.startswith("| 1MU"))
    assert row.endswith("| 17× |"), row


def test_the_compound_quantity_is_stated_with_its_assumptions(design):
    """5.25 mg, from 13 points, 3 replicates, 100 uL wells.

    Not a theoretical minimum -- enough to pipette, and enough left when the
    first plate goes wrong.
    """
    assert design["replicates"] == 3
    assert design["assay_volume_uL"] == 100
    assert design["compound_needed_mg"] == pytest.approx(5.25, abs=0.05)
    assert design["compound_needed_mg"] > 0
