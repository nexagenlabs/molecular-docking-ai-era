"""Chapter 12: a small screen, and the two things it refuses to report.

The screen runs and ranks. What it will not do is quote an enrichment factor,
because the top 1% of 19 compounds is 0.19 compounds and any number reported
for it would be an artefact of rounding -- and it will not drop the compound
that failed preparation, because a screen that quietly loses part of its
library reports enrichment over a set nobody can reconstruct.

Both refusals are asserted here. The ranking is docking output, so what is
asserted about it is that the known actives are found near the top, not their
exact positions.
"""
import pytest


def test_the_library_size_and_the_failure_are_both_reported(ch12_outputs):
    """One compound failed preparation, and it is named rather than skipped.

    The dropped rows are rarely a random sample of the library.
    """
    assert ch12_outputs["library_size"] == 19
    assert len(ch12_outputs["failures"]) == 1
    failure = ch12_outputs["failures"][0]
    assert failure["name"] == "sodium_chloride"
    assert failure["reason"].strip(), "a failure with no reason is a silent drop"
    names = {r["name"] for r in ch12_outputs["results"]}
    assert failure["name"] not in names, \
        "the failed compound is also in the results; it was scored somehow"


def test_enrichment_is_refused_at_this_library_size(ch12_outputs):
    """The top 1% of 19 compounds is 0.19 compounds.

    ch18 measures enrichment properly, on 10,000. Reporting a number here
    would be reporting a rounding artefact with three decimal places.
    """
    assert ch12_outputs["ef1_is_defined"] is False
    assert "ef1" not in ch12_outputs, \
        "an EF1% value was reported for a 19-compound library"


def test_the_known_actives_rank_near_the_top(ch12_outputs):
    """Ranks 1, 2 and 7 of 19 on this platform.

    Asserted as "in the top half, and two of them in the top three" rather
    than as the exact ranks: the ordering comes from docking scores that are
    separated by hundredths of a kcal/mol.
    """
    ranks = ch12_outputs["active_ranks"]
    assert len(ranks) == 3, "three known actives are in the library"
    assert min(ranks) == 1, "no active reached rank 1"
    assert sorted(ranks)[1] <= 3, "only one active is in the top three"
    assert max(ranks) <= 10, \
        "an active ranked %d of %d; the chapter's point is that they rank " \
        "well, not perfectly" % (max(ranks), ch12_outputs["library_size"])


def test_the_ranking_is_by_affinity_and_all_scores_are_negative(ch12_outputs):
    scores = [r["affinity"] for r in ch12_outputs["results"]]
    assert scores == sorted(scores), "the results are not sorted by affinity"
    assert all(s < 0 for s in scores), \
        "a non-negative affinity means the box missed the receptor entirely"


def test_the_decoys_are_named_so_the_screen_can_be_criticised(ch12_outputs):
    """Common drugs, not property-matched actives.

    Stated in the chapter as a weakness: a screen whose decoys are lighter and
    less charged than its actives measures molecular weight. Asserting the
    weight difference keeps that sentence honest.
    """
    results = {r["name"]: r for r in ch12_outputs["results"]}
    actives = {"STC", "18U", "1MU"}
    assert actives <= set(results)
    active_mw = [results[a]["mw"] for a in actives]
    decoy_mw = [r["mw"] for n, r in results.items() if n not in actives]
    assert min(active_mw) > sum(decoy_mw) / len(decoy_mw), \
        "the lightest active is no longer heavier than the average decoy, so " \
        "the chapter's caveat about property matching needs rewriting"
    assert min(active_mw) > min(decoy_mw) * 1.5, \
        "the decoys are supposed to be conspicuously lighter; that is the " \
        "weakness the chapter names, and a screen over them measures " \
        "molecular weight as much as it measures binding"


def test_the_cost_extrapolation_is_linear_and_says_so(ch12_outputs):
    """Straight-line, which assumes every compound costs what these did.

    Recomputed from the measured per-compound time, so the table cannot drift
    away from the run that produced it.
    """
    per_compound = ch12_outputs["seconds_per_compound"]
    cores = ch12_outputs["docking"]["cores"]
    assert per_compound > 0 and cores > 0
    for size, entry in ch12_outputs["extrapolation"].items():
        # Core-hours, not wall-hours: the measured seconds were wall time on
        # `cores` cores, so the cost of the work is that times the core count.
        expected = int(size) * per_compound * cores / 3600.0
        assert entry["core_hours"] == pytest.approx(expected, rel=0.01), size
        assert entry["days_on_100_cores"] == pytest.approx(
            entry["core_hours"] / 100.0 / 24.0, abs=0.01), size
    million = ch12_outputs["extrapolation"]["1000000"]["core_hours"]
    assert 3000 < million < 8000, \
        "a million compounds came to %.0f core-hours; the chapter's " \
        "conclusion is that a screen is affordable" % million


def test_the_run_is_recorded_the_same_way_as_every_other(ch12_outputs):
    docking = ch12_outputs["docking"]
    assert docking["seed"] == 42
    assert docking["exhaustiveness"] == 8
    assert "1.2.7" in docking["program"]
