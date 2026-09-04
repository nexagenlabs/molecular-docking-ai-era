"""Chapter 21: every window looks converged.

A synthetic trajectory with four separated relaxation timescales. Each
observation window passes its own flat-tail test, and the 10 ns answer is 37%
below the 1000 ns one. Pure arithmetic on a fixed construction, so these must
match exactly everywhere.
"""
import pytest

from conftest import read_json, run_script

EXPECTED = {
    "1": {"mean": 1.10, "slope": -0.150, "at10x": 1.45},
    "10": {"mean": 1.47, "slope": -0.010, "at10x": 1.99},
    "100": {"mean": 1.90, "slope": 0.007, "at10x": 2.37},
    "1000": {"mean": 2.34, "slope": 0.0004, "at10x": None},
}
# The book prints the means and the 10x values to two decimals and the slopes
# to three or four; the tolerances follow the printed precision.
MEAN_TOLERANCE = 0.005
SLOPE_TOLERANCE = 0.0005


@pytest.fixture(scope="module")
def convergence():
    run_script("ch21_molecular_dynamics/scripts/convergence.py")
    return read_json("ch21_molecular_dynamics/outputs/convergence.json")


def test_the_construction_asserts_its_own_window_means():
    """`ch21_make_trajectory.py` checks all four means against the book.

    Run as a subprocess so its own assertions are the test. The generator is
    consumed once per process in the order of `taus`, so that order is part of
    the specification.
    """
    run_script("ch21_molecular_dynamics/scripts/ch21_make_trajectory.py")


@pytest.mark.parametrize("window", ["1", "10", "100", "1000"])
def test_window_mean_rmsd(convergence, window):
    assert convergence["windows"][window]["mean_rmsd"] == pytest.approx(
        EXPECTED[window]["mean"], abs=MEAN_TOLERANCE)


@pytest.mark.parametrize("window", ["1", "10", "100", "1000"])
def test_second_half_slope(convergence, window):
    """Two of these are NEGATIVE, and that is the whole point.

    A monotone sum of exponentials cannot produce a negative slope at all. The
    trajectory's four relaxations are Ornstein-Uhlenbeck processes, so a
    window's tail can fall while the trajectory as a whole is still climbing --
    which is the strongest form of the trap the chapter is about.
    """
    assert convergence["windows"][window]["slope_second_half"] == pytest.approx(
        EXPECTED[window]["slope"], abs=SLOPE_TOLERANCE)


@pytest.mark.parametrize("window", ["1", "10", "100"])
def test_value_at_ten_times_the_window(convergence, window):
    """What you would have seen had you run ten times longer."""
    assert convergence["windows"][window]["value_at_10x_window"] == pytest.approx(
        EXPECTED[window]["at10x"], abs=MEAN_TOLERANCE)


def test_the_thousand_nanosecond_window_has_no_ten_times_value(convergence):
    """The run is 3000 ns, so 10x the longest window is beyond it. Say so."""
    assert convergence["windows"]["1000"]["value_at_10x_window"] is None


def test_all_eleven_published_values_reproduce(convergence):
    """The script counts its own agreement with the book; assert the count."""
    assert convergence["book_values_matched"] == "11/11"


def test_every_window_looks_converged(convergence):
    """The trap: a flat tail is not evidence of convergence.

    All four windows pass, and each is settled only on its own timescale.
    """
    assert convergence["windows_passing_flat_tail_test"] == 4
    for window in ("1", "10", "100", "1000"):
        assert convergence["windows"][window]["looks_converged"] is True, \
            "the %s ns window should pass the flat-tail test" % window


def test_ten_nanosecond_answer_is_far_below_the_thousand(convergence):
    """The chapter's claim: 1.47 A against 2.34 A, a 37% shortfall.

    Asserted against the two-decimal means the chapter reports, which is what
    the book's 37% is a statement about. From the unrounded means it is 37.5%,
    close enough to the boundary that a formatter can print either -- so the
    script records both and this checks both are present and consistent.
    """
    short = round(convergence["windows"]["10"]["mean_rmsd"], 2)
    long = round(convergence["windows"]["1000"]["mean_rmsd"], 2)
    assert (short, long) == (1.47, 2.34)

    shortfall = convergence["shortfall_10ns_vs_1000ns"]
    assert shortfall == pytest.approx((long - short) / long, abs=0.0005)
    assert round(shortfall, 2) == pytest.approx(0.37, abs=0.005), \
        "10 ns is %.1f%% below 1000 ns, book says 37%%" % (100 * shortfall)
    assert convergence["shortfall_from_unrounded_means"] == pytest.approx(
        0.375, abs=0.0005)
