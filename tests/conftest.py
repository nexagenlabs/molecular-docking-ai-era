"""Shared machinery for the chapter tests.

Every test here drives a chapter script **as a subprocess**, never by importing
it. An import-based test cannot even be collected before the code exists; a
subprocess call fails cleanly with a missing-file error, which is the failure
you want while a repository is being built.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def python_exe():
    """The pinned interpreter, if the repository's venv is present."""
    for candidate in (REPO / ".venv" / "Scripts" / "python.exe",
                      REPO / ".venv" / "bin" / "python"):
        if candidate.exists():
            return str(candidate)
    return sys.executable


def on_reference_platform():
    """True on Linux, where the book's three-decimal values were measured.

    Not a convenience. The same Vina 1.2.7, meeko 0.8.0 and RDKit 2026.3.5
    give -4.905/-4.911/-2.748 on Linux and -4.910/-4.903/-2.686 on Windows,
    for two measured reasons: the RDKit build's MMFF optimisation lands on a
    different conformer, and the Vina build scores differently on identical
    files. See PROGRESS.md.
    """
    return sys.platform.startswith("linux")


def platform_xfail(what):
    """Mark a value that is exact only on the reference platform.

    A decorator, not a call inside the test, and **non-strict on purpose**.
    An imperative `pytest.xfail()` aborts the test before its assertion runs,
    so a value that happens to match off Linux is never checked and never
    reported -- which is how ch08's STC row went on being marked platform-
    dependent after it had started matching the book exactly on Windows.

    Non-strict xfail runs the assertion either way: a mismatch is XFAIL, and a
    match is XPASS. The day a platform difference goes away, the suite says so
    instead of quietly continuing to expect it.
    """
    return pytest.mark.xfail(
        not on_reference_platform(),
        reason="%s is exact only on Linux; this is %s. The difference is "
               "measured and recorded in PROGRESS.md, not tuned away."
               % (what, sys.platform),
        strict=False,
    )


def run_script(relative, *args, timeout=1800):
    """Run a chapter script. Fails the test if it is missing or errors."""
    script = REPO / relative
    if not script.exists():
        pytest.fail("%s does not exist yet" % relative)
    result = subprocess.run([python_exe(), str(script), *args],
                            capture_output=True, text=True, timeout=timeout,
                            cwd=str(REPO))
    if result.returncode != 0:
        pytest.fail("%s exited %d\n--- stdout ---\n%s\n--- stderr ---\n%s"
                    % (relative, result.returncode, result.stdout, result.stderr))
    return result


def config_seeds():
    """Every `seed = N` in every chapter Vina config, parsed as an integer.

    Shared between the static guard in test_gotchas and the behavioural check
    in test_ch09, so that both are talking about the same number: the one in
    the file a reader re-executes from, not a literal in a script.
    """
    import re
    found = {}
    for config in sorted(REPO.glob("ch*/config/*.txt")):
        values = []
        for line in config.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*seed\s*=\s*(-?\d+)\s*$", line.partition("#")[0])
            if match:
                values.append(int(match.group(1)))
        found[config.relative_to(REPO).as_posix()] = values
    return found


def load_module(relative, name):
    """Import a chapter script by path, so its functions can be called directly.

    Most tests here drive a script as a subprocess and assert on what it wrote,
    which is the right shape for "does the chapter produce the book's number".
    It is the wrong shape for "does this function behave correctly on an input
    the chapter never sees" -- a deliberately displaced pose, a ligand whose
    file order and distance disagree. Those need the function itself.
    """
    import importlib.util
    path = REPO / relative
    if not path.exists():
        pytest.fail("%s does not exist" % relative)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script_raw(relative, *args, timeout=1800):
    """Run a chapter script and hand back the result, whatever it was.

    run_script() fails the test on a non-zero exit, which is right when the
    question is "does the chapter produce the book's number". It is wrong when
    the question is "does the chapter refuse clearly", and refusing clearly is
    a behaviour worth testing: several scripts here read another chapter's
    output, and the only thing worse than stopping is continuing.
    """
    script = REPO / relative
    if not script.exists():
        pytest.fail("%s does not exist yet" % relative)
    return subprocess.run([python_exe(), str(script), *args],
                          capture_output=True, text=True, timeout=timeout,
                          cwd=str(REPO))


def read_json(relative):
    path = REPO / relative
    if not path.exists():
        pytest.fail("%s was not produced" % relative)
    return json.loads(path.read_text())


# -- shared chapter runs ----------------------------------------------------
#
# Several chapters read another chapter's output. Chapter 2 reads eight of
# them; ch23 and ch16 read ch17's; ch27 reads ch20's, which reads ch09's AmpC
# branch. A test for any of those has to build what it depends on -- asserting
# a state the suite never creates is exactly the defect STRESS_REPORT.md B1
# describes, and it passed here for a session only because an earlier manual
# run had left the files lying about.
#
# Session scope, so a chapter that four test modules depend on is run once and
# not four times. The docking chapters are the reason: ch26 alone is nine Vina
# runs at exhaustiveness 32.

@pytest.fixture(scope="session")
def ch06_outputs():
    run_script("ch06_predicted_structures/scripts/compare_alphafold.py", timeout=3600)
    return read_json("ch06_predicted_structures/outputs/alphafold_comparison.json")


@pytest.fixture(scope="session")
def ch07_outputs():
    run_script("ch07_pocket/scripts/define_pocket.py", timeout=3600)
    return read_json("ch07_pocket/outputs/pocket.json")


@pytest.fixture(scope="session")
def ch10_outputs():
    run_script("ch10_flexibility/scripts/torsion_analysis.py")
    return read_json("ch10_flexibility/outputs/rotamers.json")


@pytest.fixture(scope="session")
def ch12_outputs():
    run_script("ch12_screening/scripts/screen.py", timeout=3600)
    return read_json("ch12_screening/outputs/screen.json")


@pytest.fixture(scope="session")
def ch14_outputs():
    run_script("ch14_boltz2/scripts/correlation.py")
    return read_json("ch14_boltz2/outputs/correlation.json")


@pytest.fixture(scope="session")
def ch16_outputs():
    run_script("ch16_rescoring/scripts/enrichment_arithmetic.py")
    return read_json("ch16_rescoring/outputs/rescoring.json")


@pytest.fixture(scope="session")
def ch17_outputs():
    run_script("ch17_validation/scripts/validate.py", timeout=3600)
    return read_json("ch17_validation/outputs/validation.json")


@pytest.fixture(scope="session")
def ch22_outputs():
    run_script("ch22_free_energy/scripts/power.py")
    return read_json("ch22_free_energy/outputs/power.json")


@pytest.fixture(scope="session")
def ch26_outputs():
    run_script("ch26_case_study/scripts/case_study.py", timeout=7200)
    return read_json("ch26_case_study/outputs/case_study.json")


@pytest.fixture(scope="session")
def ch09_ampc_run():
    """ch09's AmpC branch: the receptor, the ligand and the run log.

    derive_box.py is deliberately not run -- it regenerates the committed
    config, whose only diff would be its embedded timestamp, and a suite that
    dirties a tracked file leaves `git status` unable to distinguish an edit
    from a run.
    """
    run_script("ch09_first_run/scripts/prepare_ampc.py", timeout=1800)
    run_script("ch09_first_run/scripts/modes.py", "--system", "ampc", timeout=1800)
    log = REPO / "ch09_first_run" / "outputs" / "ampc" / "logs" / "modes.log"
    assert log.exists(), "ch09's AmpC branch did not write %s" % log
    return log


@pytest.fixture(scope="session")
def ch20_outputs(ch09_ampc_run):
    run_script("ch20_protocol_record/scripts/fill_record.py")
    return read_json("ch20_protocol_record/outputs/filled_record.json")


def repo_text_files(suffixes=(".py", ".sh", ".txt", ".md", ".yml", ".ipynb")):
    """Every text file in the repository, skipping git and local toolchains."""
    skip = {".git", ".venv", ".tools", "outputs", "__pycache__"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in skip for part in path.parts):
            continue
        yield path
