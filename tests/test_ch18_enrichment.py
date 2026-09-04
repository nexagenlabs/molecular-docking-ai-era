"""Chapter 18: two screens with identical AUC and opposite usefulness.

Nothing here touches docking software, so these values are pure arithmetic on a
fixed construction and must match exactly on every platform.
"""
import pytest

from conftest import read_json, run_script

# 10,000 compounds, 100 actives, searched for the pair with equal AUC.
EXPECTED = {
    "A": {"auc": 0.758, "ef1": 56.0, "ef5": 11.6, "bedroc": 0.574},
    "B": {"auc": 0.758, "ef1": 0.0, "ef5": 0.6, "bedroc": 0.058},
}
TOLERANCE = 0.001


@pytest.fixture(scope="module")
def metrics():
    run_script("ch18_enrichment/scripts/enrichment.py")
    return read_json("ch18_enrichment/outputs/metrics.json")


def test_the_construction_asserts_its_own_search_result():
    """`ch18_make_screens.py` checks that the search lands on hi=56, lo=4800.

    Run as a subprocess so its own assertions are the test. The single
    generator is consumed sequentially across the nested loop, so the bounds
    and their order are part of the specification -- re-seeding inside the loop
    or changing a range gives different screens.
    """
    run_script("ch18_enrichment/scripts/ch18_make_screens.py")


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
    """Everything downstream of AUC, which is where the two screens diverge."""
    assert metrics["screens"][screen][metric] == pytest.approx(
        EXPECTED[screen][metric], abs=TOLERANCE), \
        ("screen %s %s: %s here, book says %s"
         % (screen, metric, metrics["screens"][screen][metric],
            EXPECTED[screen][metric]))


def test_all_eight_published_values_reproduce(metrics):
    """The script counts its own agreement with the book; assert the count.

    A per-metric assertion can pass while the comparison itself has rotted --
    this checks that the script is still doing the comparison it reports.
    """
    assert metrics["book_values_matched"] == "8/8"


def test_screen_b_finds_nothing_early(metrics):
    """Equal AUC, and EF1% of zero. That is the point."""
    assert metrics["screens"]["B"]["ef1"] == pytest.approx(0.0, abs=TOLERANCE)
    assert metrics["screens"]["B"]["actives_in_top_1_percent"] == 0
    assert metrics["screens"]["A"]["actives_in_top_1_percent"] == 56


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
