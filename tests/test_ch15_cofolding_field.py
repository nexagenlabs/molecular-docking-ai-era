"""Chapter 15: the headline numbers do not compare until you put them in one form.

Four published figures in three different units. The chapter's claim is that
the Form column is the load-bearing one -- an r against an R2, and an EF1%
against a chance value of 1.0 -- and that once every number is in the same
form the differences between the methods are smaller than the gap between all
of them and the question being asked.
"""
import pytest

from conftest import read_json, run_script


@pytest.fixture(scope="module")
def field():
    run_script("ch15_cofolding_field/scripts/compare_methods.py")
    return read_json("ch15_cofolding_field/outputs/field_comparison.json")


def by_name(field):
    return {m["name"]: m for m in field["methods"]}


def test_every_method_states_which_form_its_number_is_in(field):
    """The column the chapter is about. A row without it is the failure itself."""
    forms = {m["metric"] for m in field["methods"]}
    assert forms <= {"r", "R2", "EF1%"}, "an unrecognised metric appeared: %s" % forms
    for method in field["methods"]:
        assert method["metric"], "%s reports a number with no form" % method["name"]
        assert method["benchmark"], "%s reports a number with no benchmark" % method["name"]


def test_the_two_correlation_methods_are_compared_as_variance(field):
    """0.384 against 0.520, not 0.62 against 0.52."""
    methods = by_name(field)
    boltz, fep = methods["Boltz-2"], methods["FEP+"]
    assert boltz["metric"] == "r" and boltz["value"] == pytest.approx(0.62)
    assert fep["metric"] == "R2" and fep["value"] == pytest.approx(0.52)
    assert boltz["variance_explained"] == pytest.approx(0.62 * 0.62, abs=1e-9)
    assert fep["variance_explained"] == pytest.approx(0.52, abs=1e-9), \
        "an R2 is already a variance; squaring it again would be the same error twice"
    assert boltz["variance_explained"] < fep["variance_explained"]


def test_the_two_screening_methods_are_compared_against_chance(field):
    """2.58 against 0.90 hides that 1.0 is chance and one of them is below it."""
    methods = by_name(field)
    assert methods["Vina (docking)"]["value"] == pytest.approx(0.90)
    assert methods["GNINA (rescoring)"]["value"] == pytest.approx(2.58)
    assert methods["Vina (docking)"]["value"] < 1.0, "EF = 1.0 is chance"
    assert "chance" in methods["Vina (docking)"]["note"].lower(), \
        "the Vina row must carry the chance value, or the table repeats the error"


def test_an_ef_is_not_given_a_variance_or_a_correlation(field):
    """Enrichment and correlation are not interconvertible.

    Filling those columns for the EF rows would be inventing a comparison, so
    they have to stay null rather than be estimated into something tidier.
    """
    for method in field["methods"]:
        if method["metric"] == "EF1%":
            assert method["variance_explained"] is None, method["name"]
            assert method["implied_r"] is None, method["name"]
            assert method["pairwise_accuracy_series"] is None, method["name"]


def test_on_this_series_both_correlation_methods_are_near_a_coin_flip(field):
    """The last column, against 0.500 for guessing."""
    assert field["series_spread_kcal"] == pytest.approx(0.32, abs=0.005)
    for name in ("Boltz-2", "FEP+"):
        accuracy = by_name(field)[name]["pairwise_accuracy_series"]
        assert 0.5 < accuracy < 0.60, \
            ("%s orders two members of this series correctly %.3f of the time; "
             "anything outside 0.50-0.60 changes the chapter's conclusion"
             % (name, accuracy))


def test_the_population_spread_assumption_is_stated(field):
    """P(correct order) depends on it, so it cannot be left implicit.

    1.5 kcal/mol is typical for a congeneric series and is *wider* than this
    one, which means every figure above flatters the methods rather than the
    reverse.
    """
    assumed = field["assumed_population_spread_kcal"]
    assert assumed == pytest.approx(1.5, abs=1e-9)
    assert assumed > field["series_spread_kcal"]
