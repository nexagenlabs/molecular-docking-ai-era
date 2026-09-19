"""Chapter 16: EF = 1.0 is chance, and Vina's LIT-PCBA median is below it.

CLAUDE.md section 6: "GNINA LIT-PCBA median EF1% 1.88-2.58 against Vina 0.90.
**EF = 1.0 is chance**, so Vina is below it. Preserve that framing."

The framing is the assertion. "GNINA 2.58 against Vina 0.90" reads as one
method being three times better than another method that works; keeping the
1.0 in the sentence is what makes it read as one method working and the other
not. So the tests below check the ordering against chance rather than only the
numbers, because the numbers alone cannot go wrong in the way the sentence can.
"""
import pytest


def test_the_published_medians_are_carried_unchanged(ch16_outputs):
    methods = ch16_outputs["methods"]
    assert methods["Vina"]["ef1"] == pytest.approx(0.90, abs=1e-9)
    assert methods["GNINA (low)"]["ef1"] == pytest.approx(1.88, abs=1e-9)
    assert methods["GNINA (high)"]["ef1"] == pytest.approx(2.58, abs=1e-9)


def test_chance_is_stated_as_one_and_random_is_pinned_to_it(ch16_outputs):
    """An enrichment factor is a ratio against the library's own hit rate.

    Making the random row explicit is the point: without it, 0.90 and 2.58 are
    just two numbers and nothing marks where the origin is.
    """
    assert ch16_outputs["chance_ef"] == pytest.approx(1.0, abs=1e-9)
    assert ch16_outputs["methods"]["random"]["ef1"] == pytest.approx(1.0, abs=1e-9)


def test_vina_is_below_chance_and_the_output_says_so(ch16_outputs):
    assert ch16_outputs["methods"]["Vina"]["ef1"] < ch16_outputs["chance_ef"]
    assert ch16_outputs["vina_is_below_chance"] is True
    assert ch16_outputs["methods"]["Vina"]["better_than_chance"] is False
    assert ch16_outputs["methods"]["random"]["better_than_chance"] is False


def test_below_chance_costs_more_than_picking_at_random(ch16_outputs):
    """The arithmetic that makes "below chance" concrete rather than rhetorical.

    Ranking by Vina and testing the top slice needs more compounds tested than
    testing the same number picked with your eyes shut.
    """
    methods = ch16_outputs["methods"]
    assert methods["Vina"]["compounds_to_test"] > methods["random"]["compounds_to_test"]
    assert methods["Vina"]["cost"] > methods["random"]["cost"]
    for name in ("GNINA (low)", "GNINA (high)"):
        assert methods[name]["compounds_to_test"] < methods["random"]["compounds_to_test"]
        assert methods[name]["better_than_chance"] is True


def test_the_compound_count_follows_from_the_stated_library(ch16_outputs):
    """Recomputed here, so the table cannot drift away from its own inputs."""
    wanted = ch16_outputs["wanted_actives"]
    rate = ch16_outputs["hit_rate"]
    for name, entry in ch16_outputs["methods"].items():
        expected = wanted / (rate * entry["ef1"])
        assert entry["compounds_to_test"] == pytest.approx(expected, rel=0.001), name
        assert entry["cost"] == pytest.approx(
            entry["compounds_to_test"] * ch16_outputs["cost_per_compound"],
            rel=0.001), name


def test_gninas_gain_is_real_and_modest(ch16_outputs):
    """2.58 takes 10,000 compounds to 3,876. Useful; not a solved problem."""
    methods = ch16_outputs["methods"]
    ratio = (methods["random"]["compounds_to_test"]
             / methods["GNINA (high)"]["compounds_to_test"])
    assert 2.0 < ratio < 3.0, \
        "the best published rescoring is a factor of about 2.6, not an order " \
        "of magnitude; a ratio outside 2-3 means the framing has moved"


def test_run_sh_propagates_the_gnina_pipelines_exit_code(ch16_outputs):
    """The arithmetic ran; the rescoring did not. Exit 0 for both puts a thing
    that happened and a thing that did not on the same footing.

    Asserted as equality rather than as "non-zero", so this still holds on a
    machine that does have GNINA installed.
    """
    import subprocess

    from conftest import REPO, bash_exe

    pipeline = subprocess.run([bash_exe(), "ch16_rescoring/scripts/rescore_with_gnina.sh"],
                              capture_output=True, text=True, cwd=str(REPO),
                              timeout=900)
    wrapper = subprocess.run([bash_exe(), "ch16_rescoring/run.sh"],
                             capture_output=True, text=True, cwd=str(REPO),
                             timeout=1800)
    assert wrapper.returncode == pipeline.returncode, (
        "rescore_with_gnina.sh exited %d and run.sh exited %d"
        % (pipeline.returncode, wrapper.returncode))
    assert "rescoring.md" in wrapper.stdout, \
        "the footer must still print; the arithmetic did run"


def test_the_gnina_pipeline_refuses_rather_than_pretending(ch16_outputs):
    """GNINA is not installed here, and the chapter must not simulate it.

    ch16_rescoring/scripts/rescore_with_gnina.sh prints the command it would
    run and exits non-zero. The arithmetic above is published numbers, and the
    chapter's honesty depends on those two never being confused.
    """
    import subprocess

    from conftest import REPO, bash_exe

    result = subprocess.run([bash_exe(), "ch16_rescoring/scripts/rescore_with_gnina.sh"],
                            capture_output=True, text=True, cwd=str(REPO),
                            timeout=300)
    message = result.stdout + result.stderr
    assert result.returncode != 0, \
        "the GNINA pipeline exited 0 without GNINA installed"
    assert "gnina" in message.lower()
    assert "not simulated" in message.lower() or "nothing here is simulated" in message.lower()
