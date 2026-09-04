"""The three gotchas from CLAUDE.md section 5, asserted across the repository.

These are not chapter tests. They are standing guards: each one covers a
mistake that produces a plausible-looking wrong answer rather than an error,
which is the only kind worth a permanent test.
"""
import re

import pytest

from conftest import REPO, repo_text_files, run_script, read_json

# Prose may quote the forbidden flag -- explaining why it is forbidden is half
# the point of this repository. Code may not use it. So Python is checked with
# the comments and string literals removed, rather than by grepping the file,
# and documentation is checked only for shell command lines.
DOC_SUFFIXES = {".md", ".txt", ".yml"}

# The API form is the more dangerous one: no flag appears anywhere, the
# parameter is easy to pass by accident, and the result looks like a validation
# that passed.
FORBIDDEN_IN_CODE = ("--minimize", "minimize=True", "minimize = True")


def code_only(path):
    """A Python file's source with comments and string literals removed."""
    import io
    import tokenize
    pieces = []
    with open(path, "rb") as handle:
        try:
            for token in tokenize.tokenize(handle.readline):
                if token.type in (tokenize.COMMENT, tokenize.STRING):
                    continue
                pieces.append(token.string)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # Unparseable file: fall back to the whole text, which can only
            # make the guard stricter.
            return path.read_text(encoding="utf-8", errors="replace")
    return " ".join(pieces)


def test_no_script_uses_minimize():
    """--minimize superimposes before measuring, and makes every redock pass.

    A pose displaced 3.0 A returns 3.00000 without the flag and 0.00000 with
    it. There is no legitimate use of it in this repository -- in code. Prose
    that explains the trap is exactly what should exist.
    """
    offenders = []
    for path in repo_text_files():
        relative = path.relative_to(REPO).as_posix()
        if path.suffix == ".py":
            haystack = code_only(path)
            needles = FORBIDDEN_IN_CODE
        elif path.suffix == ".sh":
            haystack = path.read_text(encoding="utf-8", errors="replace")
            needles = ("--minimize",)
        else:
            continue
        for needle in needles:
            if needle in haystack:
                offenders.append("%s (%s)" % (relative, needle))
    assert not offenders,         "--minimize or minimize=True used in: %s" % ", ".join(offenders)


def test_the_rmsd_call_passes_minimize_false_explicitly():
    """Not passing it is not enough; the record has to be able to say so.

    spyrmsd defaults to minimize=False, so an implicit call would be correct
    today and silently wrong if that default ever changed.
    """
    validate = REPO / "ch17_validation" / "scripts" / "validate.py"
    if not validate.exists():
        pytest.skip("ch17 not built yet")
    assert "minimize=False" in validate.read_text(encoding="utf-8")


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
    """The same rule for command lines, not only config files.

    A file satisfies it either by putting --seed on the command line itself, or
    by going through scripts/docking_common.dock(), which always does and whose
    callers name the seed as `seed=`. What matters is that no Vina run anywhere
    in this repository is left on the default.
    """
    offenders = []
    for path in REPO.glob("**/*.py"):
        if any(part in {".git", ".venv", ".tools"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "--exhaustiveness" not in text and "exhaustiveness=" not in text:
            continue
        if "--seed" in text or "seed=" in text:
            continue
        offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, \
        "these run Vina with no seed: %s" % ", ".join(offenders)


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
