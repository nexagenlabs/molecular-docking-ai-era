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


# The synthetic receptor, byte for byte. numpy's PCG64 stream is portable and
# make_test_system.py writes with newline="\n" explicitly, so this file is
# identical on every platform. Verified: Windows 11 / Python 3.12.10 and Ubuntu
# 24.04 / Python 3.12.3 both produce this digest.
SYNTHETIC_RECEPTOR_SHA256 = \
    "6fc7bcb24bc4036face0d3f95215b57fb7a3ec2702e53d9fb674b7e0887fa471"


def test_the_synthetic_receptor_is_the_one_the_book_describes(tmp_path):
    """CLAUDE.md section 6: 140 carbons on a shell, radius 9.0-10.5 A.

    Every number Chapter 9 prints depends on this file and nothing asserted it.
    The constants live in make_test_system.py as SHELL_ATOMS, SHELL_MIN and
    SHELL_SPAN, and a named constant is not a checked one -- editing 140 to 150
    would change every box-sweep score in the chapter and no test would notice.

    Built into tmp_path, so this does not disturb the chapter's own outputs.
    """
    import hashlib
    import math

    from conftest import run_script

    run_script("ch09_first_run/scripts/make_test_system.py", str(tmp_path))
    receptor = tmp_path / "rec.pdbqt"
    lines = [l for l in receptor.read_text().splitlines() if l.startswith("ATOM")]

    assert len(lines) == 140, \
        "the shell has %d atoms; the book says 140" % len(lines)

    radii = []
    for line in lines:
        x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
        radii.append(math.sqrt(x * x + y * y + z * z))
        assert line[76:78].strip() == "C" or line.rstrip().endswith("C"), \
            "the shell is carbon: %r" % line
    assert min(radii) >= 9.0 - 1e-6, "an atom lies inside the 9.0 A inner radius"
    assert max(radii) <= 10.5 + 1e-6, "an atom lies outside the 10.5 A outer radius"
    # And the shell is actually populated across the band rather than sitting
    # on one surface, which is what "radius 9.0-10.5" means.
    assert max(radii) - min(radii) > 1.0


def test_the_synthetic_receptor_is_byte_identical_across_platforms(tmp_path):
    """The property that makes it usable as a control.

    When a score differs between two machines, this file is what establishes
    that the *input* was the same -- so its portability is load-bearing, not a
    nicety. It rests on two things a future edit could break without any other
    test noticing: numpy's PCG64 stream, and the explicit newline="\\n" that
    stops Python's text mode writing CRLF on Windows.
    """
    import hashlib

    from conftest import run_script

    run_script("ch09_first_run/scripts/make_test_system.py", str(tmp_path))
    digest = hashlib.sha256((tmp_path / "rec.pdbqt").read_bytes()).hexdigest()
    assert digest == SYNTHETIC_RECEPTOR_SHA256, (
        "the synthetic receptor changed: %s\nIf this was deliberate, every "
        "number in Chapter 9 moves with it." % digest)


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


@pytest.mark.xfail(
    reason="OPEN DISAGREEMENT WITH THE BOOK, not a platform difference. "
           "CLAUDE.md section 6 says to assert only that the ratio is 3-5. "
           "Measured best-of-3 on an idle machine: Linux (the reference "
           "platform) 2.80, Windows 3.34; the book's own 3.4 s and 14.2 s give "
           "4.18. The band does not hold where the book says its numbers come "
           "from. See PROGRESS.md -- this is awaiting an author decision and "
           "must not be tuned away.",
    strict=False,
)
def test_exhaustiveness_ratio_is_between_3_and_5():
    """Absolute timings are hardware-specific; only the ratio travels.

    Except that it does not travel as far as the book claims. timing.py's own
    docstring gives the mechanism: the grid is computed once whatever the
    search does, so the fixed cost is a larger share of the exhaustiveness-8
    run on a fast machine, and the ratio falls. The book measured 3.4 s at
    exhaustiveness 8; this machine measures 1.47 s. It is roughly twice as
    fast, and the ratio drops out of the band accordingly.

    Left as a non-strict xfail rather than a widened band, because widening it
    would be tuning the test to the observation -- which is the one thing
    CLAUDE.md section 6 forbids. If the band is wrong it is the book that needs
    the correction, and that is not a decision a test file gets to make.
    """
    run_script("ch09_first_run/scripts/timing.py", "--system", "synthetic")
    timing = read_json("ch09_first_run/outputs/synthetic/timing.json")
    assert 3.0 <= timing["ratio"] <= 5.0, \
        "ratio %.2f outside the 3-5 band" % timing["ratio"]


def test_exhaustiveness_costs_more_than_it_saves_but_not_four_times_more():
    """The claim underneath the band, which does hold on both platforms.

    Whatever the exact ratio, two things are true everywhere it has been
    measured: quadrupling exhaustiveness costs meaningfully more time, and it
    costs *less* than four times more, because the grid is a fixed cost. That
    is the teaching point; 3-5 was an attempt to put a number on it.
    """
    run_script("ch09_first_run/scripts/timing.py", "--system", "synthetic")
    timing = read_json("ch09_first_run/outputs/synthetic/timing.json")
    assert timing["ratio"] > 1.5, \
        ("ratio %.2f: quadrupling exhaustiveness barely cost anything, which "
         "would mean the search is not doing what the flag says"
         % timing["ratio"])
    assert timing["ratio"] < 4.0, \
        ("ratio %.2f: at or above 4x there is no fixed cost being amortised, "
         "which contradicts the chapter's explanation" % timing["ratio"])


def test_mode_one_rmsd_is_zero_by_construction():
    """0.000 0.000 is distance from mode 1, not a validation result."""
    run_script("ch09_first_run/scripts/modes.py", "--system", "synthetic")
    modes = read_json("ch09_first_run/outputs/synthetic/modes.json")
    assert modes["mode1_rmsd_is_zero"]
    assert modes["modes"][0]["rmsd_lb"] == 0.0
    assert modes["modes"][0]["rmsd_ub"] == 0.0
    # And the later modes are not zero, or the column would be meaningless.
    assert any(m["rmsd_lb"] > 0 for m in modes["modes"][1:])
