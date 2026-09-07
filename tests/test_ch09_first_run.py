"""Chapter 9: the seed, and the box that fails silently.

The book's values here come from the synthetic system, not from AmpC. Asserting
them against AmpC would be asserting against a different experiment.
"""
import pytest

from conftest import platform_xfail, read_json, run_script

# The book prints three decimals, so three decimals is the tolerance.
TOLERANCE = 0.001

BOX_SCORES = {"20": -4.905, "12": -4.911, "8": -2.748}


@pytest.fixture(scope="module")
def sweep():
    run_script("ch09_first_run/scripts/box_sweep.py", "--system", "synthetic")
    return read_json("ch09_first_run/outputs/synthetic/box_sweep.json")


@pytest.fixture(scope="module")
def seeds():
    run_script("ch09_first_run/scripts/verify_run.py", "--system", "synthetic")
    return read_json("ch09_first_run/outputs/synthetic/verify_run.json")


def test_seed_42_is_reproducible(seeds):
    """Two runs at seed 42 must be byte-identical.

    If this fails, the seed does not control the search and nothing else in
    this repository can be trusted to repeat.
    """
    assert seeds["runs"]["seed42_run1"]["sha256"] == seeds["runs"]["seed42_run2"]["sha256"]
    assert seeds["seed42_reproducible"]


def test_the_configured_seed_actually_reproduces():
    """The seed in the config file has to be one that makes a run repeat.

    test_seed_42_is_reproducible proves that 42 works -- but it proves it about
    the literal 42 inside verify_run.py, not about the number in
    ch09_first_run/config/vina_config.txt, which is what a reader re-executes
    from. Changing that file's `seed = 42` to `seed = 0` left every
    reproducibility test in this suite green.

    So take the seed from the config, dock the synthetic system twice with it,
    and compare the bytes. At seed 0 the two poses differ and this fails, which
    is the whole point.
    """
    import hashlib
    import sys
    from pathlib import Path

    from conftest import REPO, config_seeds

    values = config_seeds().get("ch09_first_run/config/vina_config.txt", [])
    assert len(values) == 1, "expected exactly one seed in ch09's config"
    seed = values[0]

    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "ch09_first_run" / "scripts"))
    import systems
    from docking_common import dock

    receptor, ligand, centre = systems.get("synthetic")
    work = Path(receptor).parent
    digests = []
    for repeat in (1, 2):
        pose = work / ("config_seed_run%d.pdbqt" % repeat)
        dock(receptor, ligand, centre, (20, 20, 20), pose,
             seed=seed, exhaustiveness=8)
        digests.append(hashlib.sha256(pose.read_bytes()).hexdigest())

    assert digests[0] == digests[1], (
        "two runs at the configured seed (%d) gave different poses. Vina's "
        "default seed is 0 and it means 'choose one at random'; a config "
        "carrying it describes a run nobody can repeat." % seed)


def test_default_seed_is_not_reproducible(seeds):
    """Seed 0 means random, and two runs at it differ."""
    assert seeds["runs"]["seed0_run1"]["sha256"] != seeds["runs"]["seed0_run2"]["sha256"]
    assert not seeds["seed0_reproducible"]


def test_box_sweep_raises_no_error(sweep):
    """The chapter's real point: an undersized box is not an error.

    This holds on every platform, and it is the claim that matters. A reader
    who takes nothing else from Chapter 9 should take this.
    """
    assert set(sweep["scores"]) == {"20", "12", "8"}
    for size, score in sweep["scores"].items():
        assert score < 0, "box %s A returned a non-negative score" % size


def test_undersized_box_is_worse_than_both_larger_ones(sweep):
    """8 A cannot hold the ligand in every orientation; 20 and 12 can."""
    scores = sweep["scores"]
    assert scores["8"] > scores["20"]
    assert scores["8"] > scores["12"]


def test_large_and_medium_box_agree(sweep):
    """Once the box covers the pocket, making it larger buys nothing."""
    assert abs(sweep["scores"]["20"] - sweep["scores"]["12"]) < 0.05


@platform_xfail("The box-sweep score")
def test_box_scores_match_the_book(sweep):
    """Exact to three decimals -- on the platform the book was measured on.

    Non-strict, so if a future Windows build starts landing on the book's
    values the suite reports XPASS rather than going on expecting a difference
    that is no longer there.
    """
    for size, expected in BOX_SCORES.items():
        assert sweep["scores"][size] == pytest.approx(expected, abs=TOLERANCE), \
            ("box %s A: got %.3f, book says %.3f. Do not adjust the script; find "
             "out which side is wrong." % (size, sweep["scores"][size], expected))


def test_exhaustiveness_ratio_is_between_3_and_5():
    """Absolute timings are hardware-specific; only the ratio travels."""
    run_script("ch09_first_run/scripts/timing.py", "--system", "synthetic")
    timing = read_json("ch09_first_run/outputs/synthetic/timing.json")
    assert 3.0 <= timing["ratio"] <= 5.0, \
        "ratio %.2f outside the 3-5 band" % timing["ratio"]


def test_mode_one_rmsd_is_zero_by_construction():
    """0.000 0.000 is distance from mode 1, not a validation result."""
    run_script("ch09_first_run/scripts/modes.py", "--system", "synthetic")
    modes = read_json("ch09_first_run/outputs/synthetic/modes.json")
    assert modes["mode1_rmsd_is_zero"]
    assert modes["modes"][0]["rmsd_lb"] == 0.0
    assert modes["modes"][0]["rmsd_ub"] == 0.0
    # And the later modes are not zero, or the column would be meaningless.
    assert any(m["rmsd_lb"] > 0 for m in modes["modes"][1:])
