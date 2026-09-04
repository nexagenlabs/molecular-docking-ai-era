"""Chapter 21: every window looks converged.

A synthetic trajectory with four separated relaxation timescales. Each
observation window passes its own flat-tail test, and the 10 ns answer is 37%
below the 1000 ns one. Pure arithmetic, so these must match exactly everywhere.
"""
import pytest

from conftest import read_json, run_script

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
    assert convergence["windows"][window]["mean_rmsd"] == pytest.approx(
        EXPECTED[window]["mean"], abs=MEAN_TOLERANCE)


@pytest.mark.parametrize("window", ["1", "10", "100", "1000"])
def test_second_half_slope(convergence, window):
    assert convergence["windows"][window]["slope_second_half"] == pytest.approx(
        EXPECTED[window]["slope"], abs=SLOPE_TOLERANCE)


def test_every_window_looks_converged(convergence):
    """That is the trap: a flat tail is not evidence of convergence."""
    for window in EXPECTED:
        assert convergence["windows"][window]["looks_converged"] is True


def test_ten_nanosecond_answer_is_far_below_the_thousand(convergence):
    short = convergence["windows"]["10"]["mean_rmsd"]
    long = convergence["windows"]["1000"]["mean_rmsd"]
    shortfall = (long - short) / long
    assert shortfall == pytest.approx(0.37, abs=0.01), \
        "10 ns is %.1f%% below 1000 ns; the book says 37%%" % (100 * shortfall)
