"""Chapter 22: whether the question can be answered before it is asked.

Two independent estimates with standard error sigma give a difference with
standard error sigma*sqrt(2), so resolving a difference of Delta at 95%
confidence needs sigma < Delta / 2.77.

The chapter's claim is not that free-energy methods are bad. It is that *this*
series is the wrong experiment for them, and that two lines of arithmetic
establish it before any compute is spent. Both halves are asserted: the
arithmetic, and the conclusion it forces.
"""
import math

import pytest


def test_the_series_spread_is_the_one_the_book_prints(ch22_outputs):
    """0.32 kcal/mol across 18-31 uM. Every other chapter quotes this number."""
    assert ch22_outputs["series_spread_kcal"] == pytest.approx(0.32, abs=0.005)


def test_delta_g_follows_from_ki_and_nothing_else(ch22_outputs):
    """dG = RT ln(Ki). Recomputed here from the Ki table in the same file.

    Ki, IC50 and Kd are never interconverted anywhere in this repository; this
    is the one conversion that is done, and it is done from Ki alone.
    """
    rt = ch22_outputs["rt_kcal"]
    for name, ki_um in ch22_outputs["ki_uM"].items():
        expected = rt * math.log(ki_um * 1e-6)
        assert ch22_outputs["dg_kcal"][name] == pytest.approx(expected, abs=0.005), name


def test_resolving_the_series_needs_sigma_below_0116(ch22_outputs):
    requirement = ch22_outputs["requirements"]["AmpC series, full spread (18-31 uM)"]
    assert requirement["required_sigma_kcal"] == pytest.approx(0.116, abs=0.002)
    # And it is Delta / (1.96 * sqrt(2)), not a number that was typed in.
    z = ch22_outputs["confidence_z"]
    expected = ch22_outputs["series_spread_kcal"] / (z * math.sqrt(2))
    assert requirement["required_sigma_kcal"] == pytest.approx(expected, abs=0.002)


def test_no_reported_method_error_is_small_enough(ch22_outputs):
    """The best statistical error in the table is 0.20, and 0.116 is needed.

    This is the chapter's answer: no. If a future edition adds a method that
    clears it, this test fails and the conclusion has to be rewritten -- which
    is the right thing for it to do.
    """
    needed = ch22_outputs["requirements"][
        "AmpC series, full spread (18-31 uM)"]["required_sigma_kcal"]
    best = min(e["sigma_kcal"] for e in ch22_outputs["reported_errors"].values())
    assert best == pytest.approx(0.20, abs=0.005)
    assert best > needed, \
        "some method now reports an error small enough to rank this series"
    assert best / needed > 1.5, "the shortfall is roughly a factor of two"


def test_larger_differences_are_within_reach(ch22_outputs):
    """Not a claim that the methods do not work. A ten-fold difference is fine."""
    requirements = ch22_outputs["requirements"]
    tenfold = requirements["a 10-fold difference in Ki"]
    assert tenfold["required_sigma_kcal"] > 0.20, \
        "a well-converged FEP edge must be able to resolve a 10-fold difference"
    assert "a 10-fold difference in Ki" in \
        ch22_outputs["reported_errors"]["well-converged FEP, one edge"]["can_resolve"]


def test_the_experimental_answer_is_not_known_that_precisely(ch22_outputs):
    """ChEMBL and PDBbind disagree about 1MU by more than a third of the spread.

    This is the second reason the comparison flatters the method: even a
    perfect calculation would be aiming at a target whose position is disputed.
    """
    disagreement = ch22_outputs["experimental_disagreement_kcal"]
    assert disagreement == pytest.approx(0.104, abs=0.005)
    fraction = disagreement / ch22_outputs["series_spread_kcal"]
    assert fraction > 0.3, \
        "the source disagreement is a third of the effect being resolved"
    assert ch22_outputs["ki_uM"]["1MU_chembl"] != ch22_outputs["ki_uM"]["1MU_pdbbind"], \
        "both 1MU values must be carried; picking one would hide this"
