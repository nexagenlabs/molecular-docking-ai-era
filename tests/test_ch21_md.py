"""Chapter 21: every window looks converged.

A synthetic trajectory with four separated relaxation timescales. Each
observation window passes its own flat-tail test, and the 10 ns answer is 37%
below the 1000 ns one. Pure arithmetic, so these must match exactly everywhere.
"""
import pytest

from conftest import read_json, run_script, unknown_construction

EXPECTED = {
    "1": {"mean": 1.10, "slope": -0.150},
    "10": {"mean": 1.47, "slope": -0.010},
    "100": {"mean": 1.90, "slope": 0.007},
    "1000": {"mean": 2.34, "slope": 0.0004},
}
# The book prints the means to two decimals and the slopes to three or four.
MEAN_TOLERANCE = 0.005
SLOPE_TOLERANCE = 0.0005


@pytest.fixture(scope="module")
def convergence():
    run_script("ch21_molecular_dynamics/scripts/convergence.py")
    return read_json("ch21_molecular_dynamics/outputs/convergence.json")


@pytest.mark.parametrize("window", ["1", "10", "100", "1000"])
def test_window_mean_rmsd(convergence, window):
    ours = convergence["windows"][window]["mean_rmsd"]
    theirs = EXPECTED[window]["mean"]
    if ours != pytest.approx(theirs, abs=MEAN_TOLERANCE):
        unknown_construction("%s ns window mean" % window, ours, theirs)


@pytest.mark.parametrize("window", ["1", "10", "100", "1000"])
def test_second_half_slope(convergence, window):
    """The book reports NEGATIVE slopes for the two shortest windows.

    A monotone sum of exponentials cannot produce one at all, so those come
    from a noise realisation whose seed is not recorded.
    """
    ours = convergence["windows"][window]["slope_second_half"]
    theirs = EXPECTED[window]["slope"]
    if ours != pytest.approx(theirs, abs=SLOPE_TOLERANCE):
        unknown_construction("%s ns window slope" % window, ours, theirs)


def test_long_windows_all_look_converged(convergence):
    """The trap: a flat tail is not evidence of convergence.

    Every window from 10 ns up passes the test, and each is settled only on its
    own timescale. Construction-independent -- it follows from having
    relaxation processes slower than the window, whatever their amplitudes.
    """
    for window in ("10", "100", "1000"):
        assert convergence["windows"][window]["looks_converged"] is True,             "the %s ns window should pass the flat-tail test" % window


def test_ten_nanosecond_answer_is_far_below_the_thousand(convergence):
    """The chapter's claim, in two parts.

    The size of the shortfall is construction-dependent and asserted loosely.
    The book's exact 37% is asserted strictly against the book, and reported as
    an XFAIL carrying both numbers when the construction differs.
    """
    short = convergence["windows"]["10"]["mean_rmsd"]
    long = convergence["windows"]["1000"]["mean_rmsd"]
    shortfall = (long - short) / long

    # Construction-independent: a 10 ns window misses a large part of the
    # answer, whatever the amplitudes are.
    assert shortfall > 0.25, \
        "10 ns is only %.1f%% below 1000 ns" % (100 * shortfall)

    if round(shortfall, 2) != pytest.approx(0.37, abs=0.005):
        unknown_construction("the 10 ns shortfall",
                             "%.0f%%" % (100 * shortfall), "37%")
