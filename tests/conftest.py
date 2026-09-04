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


def read_json(relative):
    path = REPO / relative
    if not path.exists():
        pytest.fail("%s was not produced" % relative)
    return json.loads(path.read_text())


def repo_text_files(suffixes=(".py", ".sh", ".txt", ".md", ".yml", ".ipynb")):
    """Every text file in the repository, skipping git and local toolchains."""
    skip = {".git", ".venv", ".tools", "outputs", "__pycache__"}
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in skip for part in path.parts):
            continue
        yield path
