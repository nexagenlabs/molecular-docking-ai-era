"""Chapter 18: two screens with identical AUC and opposite usefulness.

Nothing here touches docking software, so these values are pure arithmetic and
must match exactly on every platform.
"""
import pytest

from conftest import read_json, run_script

# 10,000 compounds, 100 actives, tuned to equal AUC.
EXPECTED = {
    "A": {"auc": 0.758, "ef1": 56.0, "ef5": 11.6, "bedroc": 0.574},
    "B": {"auc": 0.758, "ef1": 0.0, "ef5": 0.6, "bedroc": 0.058},
}
TOLERANCE = 0.001


@pytest.fixture(scope="module")
def metrics():
    run_script("ch18_enrichment/scripts/enrichment.py")
    return read_json("ch18_enrichment/outputs/metrics.json")


@pytest.mark.parametrize("screen", ["A", "B"])
def test_auc(metrics, screen):
    assert metrics["screens"][screen]["auc"] == pytest.approx(
        EXPECTED[screen]["auc"], abs=TOLERANCE)


def test_the_two_screens_have_the_same_auc(metrics):
    """The whole argument of the chapter is that this is not enough."""
    assert metrics["screens"]["A"]["auc"] == pytest.approx(
        metrics["screens"]["B"]["auc"], abs=TOLERANCE)


@pytest.mark.parametrize("screen", ["A", "B"])
@pytest.mark.parametrize("metric", ["ef1", "ef5", "bedroc"])
def test_early_enrichment_metrics(metrics, screen, metric):
    assert metrics["screens"][screen][metric] == pytest.approx(
        EXPECTED[screen][metric], abs=TOLERANCE)


def test_screen_b_finds_nothing_early(metrics):
    """Equal AUC, and EF1% of zero. That is the point."""
    assert metrics["screens"]["B"]["ef1"] == pytest.approx(0.0, abs=TOLERANCE)
    assert metrics["screens"]["A"]["ef1"] > 50


def test_bedroc_agrees_with_rdkit(metrics):
    """Computed twice by different routes; they agreed to six decimals."""
    for screen in ("A", "B"):
        ours = metrics["screens"][screen]["bedroc_full_precision"]
        theirs = metrics["screens"][screen]["bedroc_rdkit"]
        assert round(ours, 6) == round(theirs, 6), \
            ("BEDROC for screen %s: ours %.8f, RDKit %.8f" % (screen, ours, theirs))


def test_bedroc_weight_concentration(metrics):
    """At alpha=20, 79.8% of the weight falls in the top 8% of the list."""
    assert metrics["alpha"] == 20
    assert metrics["weight_in_top_8_percent"] == pytest.approx(0.798, abs=TOLERANCE)
