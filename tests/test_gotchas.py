"""The three gotchas from CLAUDE.md section 5, asserted across the repository.

These are not chapter tests. They are standing guards: each one covers a
mistake that produces a plausible-looking wrong answer rather than an error,
which is the only kind worth a permanent test.
"""
import re

import pytest

from conftest import REPO, repo_text_files, run_script, read_json

# This file necessarily contains the string it forbids, and so does the
# documentation that explains why. Both are exempt by name rather than by
# pattern, so a new file cannot quietly inherit the exemption.
MINIMIZE_EXEMPT = {
    "tests/test_gotchas.py",
    "CLAUDE.md",
    "README.md",
    "PROGRESS.md",
    "BUILD_REPORT.md",
    "protocols/reproducibility_record.md",
    "ch17_validation/README.md",
    "ch09_first_run/README.md",
    "ch09_first_run/outputs/expected/results.md",
    "SESSION_PLAN.md",
    "tests/test_ch17_validation.py",
    "requirements.txt",
    "environment/environment.yml",
    "environment/README.md",
}


def test_no_script_uses_minimize():
    """--minimize superimposes before measuring, and makes every redock pass.

    A pose displaced 3.0 A returns 3.00000 without the flag and 0.00000 with
    it. There is no legitimate use of it in this repository.
    """
    offenders = []
    for path in repo_text_files():
        relative = path.relative_to(REPO).as_posix()
        if relative in MINIMIZE_EXEMPT:
            continue
        if "--minimize" in path.read_text(encoding="utf-8", errors="replace"):
            offenders.append(relative)
    assert not offenders, \
        "--minimize appears in: %s" % ", ".join(offenders)


def test_no_vina_config_leaves_the_seed_unset():
    """Vina's default seed is 0, which means random.

    Two runs at the default differ and nothing in the log says so, so a config
    without a seed is a config that cannot be re-executed.
    """
    configs = list(REPO.glob("ch*/config/*.txt"))
    assert configs, "no Vina config files found to check"
    for config in configs:
        text = config.read_text(encoding="utf-8")
        assert re.search(r"^\s*seed\s*=\s*\d+", text, re.MULTILINE), \
            "%s does not set a seed" % config.relative_to(REPO)


def test_every_vina_invocation_passes_a_seed():
    """The same rule for command lines, not only config files."""
    offenders = []
    for path in REPO.glob("**/*.py"):
        if any(part in {".git", ".venv", ".tools"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "--exhaustiveness" in text and "--seed" not in text:
            offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, \
        "these build a Vina command line with no seed: %s" % ", ".join(offenders)


def test_every_run_script_is_strict():
    """set -euo pipefail, so a failed step stops the chapter."""
    scripts = list(REPO.glob("ch*/run.sh"))
    assert len(scripts) == 25, "expected 25 chapter run.sh files, found %d" % len(scripts)
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "set -euo pipefail" in text, \
            "%s does not set -euo pipefail" % script.relative_to(REPO)


def test_format_checker_flags_pdbqt_charge_loss():
    """The third gotcha, checked through the chapter that measures it."""
    run_script("ch04_formats/scripts/roundtrip.py")
    result = read_json("ch04_formats/outputs/roundtrip.json")
    assert result["formats"]["pdbqt"]["18U"]["charge_after"] == 0
    assert result["formats"]["pdbqt"]["18U"]["flagged"] is True


def test_no_fabricated_values_remain():
    """TODO(value) marks a gap. A plausible placeholder would survive review."""
    outstanding = []
    for path in repo_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if "TODO(value)" in text and path.name not in ("BUILD_REPORT.md",
                                                       "PROGRESS.md",
                                                       "SESSION_PLAN.md",
                                                       "test_gotchas.py"):
            outstanding.append(path.relative_to(REPO).as_posix())
    if outstanding:
        pytest.fail("unresolved TODO(value) in: %s" % ", ".join(outstanding))
