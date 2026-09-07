"""Chapter 24: the refusal, and what the background does to a p-value.

STRESS_REPORT.md B6: this chapter's refusal was asserted by nothing. There was
no test file at all, so removing the refusal -- the one behaviour the chapter
exists to demonstrate -- would have gone unnoticed. That is what these are for.

The same twelve genes give p = 0.0993 or p = 4.8e-11 depending only on what
was counted as "could have been a hit", and nothing in a tool's output tells
you which universe it used. So the script will not choose one.
"""
import subprocess

import pytest

from conftest import REPO, read_json, python_exe, run_script, run_script_raw

SCRIPT = "ch24_network_pharmacology/scripts/enrichment.py"


@pytest.fixture(scope="module")
def enrichment():
    run_script(SCRIPT, "--compare")
    return read_json("ch24_network_pharmacology/outputs/enrichment.json")


def test_it_refuses_to_run_without_a_background():
    """Exit 2, no result. Not a warning, not a default with a note in the log.

    This is the only script in the repository that refuses to do the thing it
    is for, and it is the chapter.
    """
    result = run_script_raw(SCRIPT)
    message = result.stdout + result.stderr
    assert result.returncode == 2, \
        "expected exit 2, got %d:\n%s" % (result.returncode, message)
    assert "REFUSING TO RUN" in message
    assert "no background gene list given" in message
    assert "Traceback" not in message


def test_the_refusal_produces_no_result(tmp_path):
    """"Exit code 2, no result" -- the second half, checked as a file.

    The refusal's prose does contain the words "p-value", because it is
    explaining why it will not compute one; grepping the text for them would
    be testing the explanation rather than the behaviour. What matters is that
    nothing was written. So the output file is moved aside first, and the
    refusal must leave it absent.
    """
    output = REPO / "ch24_network_pharmacology" / "outputs" / "enrichment.json"
    stashed = None
    if output.exists():
        stashed = tmp_path / "enrichment.json"
        output.replace(stashed)
    try:
        result = run_script_raw(SCRIPT)
        assert result.returncode == 2
        assert not output.exists(), \
            "the refusal wrote %s anyway" % output.name
    finally:
        if stashed is not None:
            stashed.replace(output)


def test_the_refusal_names_the_choices_rather_than_just_declining():
    """A refusal that does not say what to do instead is an obstacle."""
    result = run_script_raw(SCRIPT)
    message = result.stdout + result.stderr
    for background in ("assayed", "expressed", "genome"):
        assert "--background %s" % background in message, \
            "the refusal did not offer --background %s" % background
    assert "1500" in message and "12000" in message and "20000" in message, \
        "the refusal did not say how big each universe is"


@pytest.mark.parametrize("background", ["assayed", "expressed", "genome"])
def test_naming_a_background_lets_it_run(background):
    result = run_script_raw(SCRIPT, "--background", background)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_same_overlap_spans_nine_orders_of_magnitude(enrichment):
    """0.0993 against 4.78e-11. One experiment, three defensible universes."""
    results = {r["background"]: r for r in enrichment["results"]}
    assert results["assayed"]["p_value"] == pytest.approx(0.0993, abs=0.0005)
    assert results["expressed"]["p_value"] == pytest.approx(6.25e-09, rel=0.01)
    assert results["genome"]["p_value"] == pytest.approx(4.78e-11, rel=0.01)
    assert results["assayed"]["p_value"] / results["genome"]["p_value"] > 1e8


def test_the_verdict_flips_with_the_background(enrichment):
    """Not a difference of degree. Significant or not, on the same twelve genes."""
    results = {r["background"]: r for r in enrichment["results"]}
    assert results["assayed"]["significant_at_0.05"] is False
    assert results["expressed"]["significant_at_0.05"] is True
    assert results["genome"]["significant_at_0.05"] is True


def test_fold_enrichment_follows_from_the_background_size(enrichment):
    """Recomputed here from hits, pathway and overlap, so the table cannot drift."""
    hits, pathway, overlap = (enrichment["hits"], enrichment["pathway"],
                              enrichment["overlap"])
    for row in enrichment["results"]:
        expected_overlap = hits * pathway / row["size"]
        assert row["expected_overlap"] == pytest.approx(expected_overlap, abs=0.01), \
            row["background"]
        assert row["fold_enrichment"] == pytest.approx(overlap / expected_overlap,
                                                       rel=0.01), row["background"]


def test_the_p_value_is_cross_checked_against_scipy(enrichment):
    """Two routes to the same hypergeometric tail.

    A p-value computed one way and never checked is a p-value nobody has read.
    """
    for row in enrichment["results"]:
        assert row["agrees_with_scipy"] is True, row["background"]
        assert row["p_value"] == pytest.approx(row["p_value_scipy"], rel=1e-9), \
            row["background"]


def test_every_background_says_what_it_means(enrichment):
    """A universe named but not defined is the same problem one step later."""
    for row in enrichment["results"]:
        assert row["what"].strip(), row["background"]
        assert row["why"].strip(), row["background"]
