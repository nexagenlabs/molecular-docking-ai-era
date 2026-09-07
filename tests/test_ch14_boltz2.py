"""Chapter 14: the squaring step, which reverses the conclusion.

The chapter's whole argument is one keystroke. Boltz-2 reports r = 0.62 and
FEP+ reports R2 = 0.52; quoted side by side the newer method looks ahead.
Squared, 0.62 becomes 0.38 and FEP+ is fourteen points in front instead of ten
points behind.

CLAUDE.md section 6 states it as "r = 0.62; squared = 0.38 against FEP+ 0.52.
The notebook must show the squaring; the book's argument depends on it." So the
squaring is what is asserted here, not just the number it produces -- 0.38 is
the kind of value that could be typed in and look right.
"""
import math

import pytest


def test_the_reported_correlation_is_squared_before_comparison(ch14_outputs):
    r = ch14_outputs["boltz2_r"]
    assert r == pytest.approx(0.62, abs=1e-9)
    assert ch14_outputs["boltz2_r_squared"] == pytest.approx(r * r, abs=1e-12), \
        "r_squared is not r * r; the value was not computed from the input"
    assert ch14_outputs["boltz2_r_squared_rounded"] == pytest.approx(0.38, abs=1e-9)


def test_squaring_reverses_which_method_is_ahead(ch14_outputs):
    """Before: 0.62 against 0.52. After: 0.38 against 0.52."""
    r = ch14_outputs["boltz2_r"]
    fep = ch14_outputs["fep_plus_r_squared"]
    assert r > fep, "the unsquared comparison must still favour Boltz-2"
    assert ch14_outputs["boltz2_r_squared"] < fep, \
        "squaring must put FEP+ ahead, or the chapter's argument does not hold"
    assert ch14_outputs["variance_gap"] == pytest.approx(
        fep - ch14_outputs["boltz2_r_squared"], abs=1e-12)


def test_r_and_r_squared_are_not_the_same_quantity(ch14_outputs):
    """The failure the chapter is about, stated as an inequality."""
    assert ch14_outputs["boltz2_r"] != ch14_outputs["boltz2_r_squared"]


def test_what_r_062_buys_on_a_series_this_tight(ch14_outputs):
    """0.32 kcal/mol apart, ordered correctly 54.8% of the time.

    4.8 points better than a coin flip, which is the number the book prints.
    """
    row = next(p for p in ch14_outputs["pairwise"]
               if p["true_gap_kcal"] == pytest.approx(0.32))
    assert row["accuracy"] == pytest.approx(0.548, abs=0.002)
    assert row["accuracy"] > 0.5, "worse than guessing would be a different claim"
    assert row["accuracy"] - 0.5 < 0.06, \
        "at this separation the advantage over a coin flip is single digits"


def test_the_simulation_agrees_with_the_closed_form(ch14_outputs):
    """Two routes to the same number, which is why both are computed.

    Phi(r*delta / sqrt(2(1-r^2))). A simulation that agreed with nothing would
    be a random number generator with a plausible mean.
    """
    r = ch14_outputs["boltz2_r"]
    sigma = ch14_outputs["series_sigma_kcal"]
    for row in ch14_outputs["pairwise"]:
        assert row["accuracy"] == pytest.approx(row["accuracy_analytic"], abs=0.002), \
            ("simulated and analytic disagree at %.2f kcal/mol"
             % row["true_gap_kcal"])
        # And recomputed here from r alone, so the script cannot satisfy this
        # by writing the same wrong number into both fields.
        z = r * (row["true_gap_kcal"] / sigma) / math.sqrt(2 * (1 - r * r))
        expected = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        assert row["accuracy_analytic"] == pytest.approx(expected, abs=1e-6)


def test_accuracy_rises_with_separation(ch14_outputs):
    gaps = [p["true_gap_kcal"] for p in ch14_outputs["pairwise"]]
    accuracies = [p["accuracy"] for p in ch14_outputs["pairwise"]]
    assert gaps == sorted(gaps)
    assert accuracies == sorted(accuracies), \
        "a wider true difference must be easier to order, not harder"
