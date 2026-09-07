"""The three gotchas from CLAUDE.md section 5, asserted across the repository.

These are not chapter tests. They are standing guards: each one covers a
mistake that produces a plausible-looking wrong answer rather than an error,
which is the only kind worth a permanent test.
"""
import re
from pathlib import Path

import pytest

from conftest import (REPO, config_seeds, load_module, repo_text_files,
                      run_script, read_json)

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


def test_the_rmsd_function_measures_displacement_rather_than_shape():
    """The gotcha, run rather than read.

    CLAUDE.md section 5 states the experiment: a pose displaced 3.0 Å returns
    3.00000 without --minimize and 0.00000 with it. So displace a pose by
    exactly 3.0 Å, hand it to ch17's own symmetry_rmsd, and see which number
    comes back.

    This replaces a test that searched validate.py for the string
    "minimize=False". That test passed while the code was calling
    minimize=True, because the file also contains three paragraphs of prose
    explaining why minimize=False is required, and substring-matching prose is
    not a test. Calling the function cannot be fooled that way.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem
    from rdkit.Geometry import Point3D

    validate = load_module("ch17_validation/scripts/validate.py", "ch17_validate")

    mol = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1C(=O)NC"))
    assert AllChem.EmbedMolecule(mol, randomSeed=11) == 0
    AllChem.MMFFOptimizeMolecule(mol)

    displaced = Chem.Mol(mol)
    conf = displaced.GetConformer()
    for i in range(displaced.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        conf.SetAtomPosition(i, Point3D(p.x + 3.0, p.y, p.z))

    measured = validate.symmetry_rmsd(mol, displaced)
    assert measured == pytest.approx(3.0, abs=1e-4), (
        "a rigid 3.0 A translation measured as %.5f A. 0.0 means the two "
        "structures were superimposed before measuring -- which is what "
        "--minimize and minimize=True do, and what makes every redock pass."
        % measured)


def test_the_rmsd_of_a_pose_against_itself_is_zero():
    """The other half of the pair, so the measurement is not simply broken.

    A symmetry_rmsd that returned 3.0 for everything would satisfy the test
    above. This one fails if it does.
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

    validate = load_module("ch17_validation/scripts/validate.py", "ch17_validate")
    mol = Chem.AddHs(Chem.MolFromSmiles("c1ccccc1C(=O)NC"))
    assert AllChem.EmbedMolecule(mol, randomSeed=11) == 0
    AllChem.MMFFOptimizeMolecule(mol)
    assert validate.symmetry_rmsd(mol, Chem.Mol(mol)) == pytest.approx(0.0, abs=1e-6)


def test_no_vina_config_leaves_the_seed_at_the_random_default():
    """Vina's default seed is 0, and 0 does not mean "seed zero". It means
    "choose one at random".

    The previous version of this test asked whether a seed line was *present*.
    `seed = 0` is present and parses, and is exactly the condition the test
    exists to prevent -- so changing 42 to 0 in ch09's config left it green.
    The value is parsed and checked now, not matched.

    That 0 is unusable is not taken from the manual here: ch09's
    test_default_seed_is_not_reproducible docks twice at seed 0 and gets two
    different poses, and test_the_configured_seed_actually_reproduces docks
    twice at whatever this config says. This is the cheap static guard that
    still runs when no tools are installed.
    """
    seeds = config_seeds()
    assert seeds, "no Vina config files found to check"
    for name, values in seeds.items():
        assert values, "%s does not set a seed" % name
        for value in values:
            assert value != 0, (
                "%s sets seed = 0. That is Vina's default and it means 'choose "
                "one at random': two runs at it differ, and nothing in the log "
                "tells them apart." % name)
            assert value > 0, \
                "%s sets seed = %d; Vina wants a positive integer" % (name, value)


def write_pdb(path, records):
    """A minimal PDB from (record, name, res, chain, seq, xyz, element) rows."""
    lines = []
    for serial, (rec, name, res, chain, seq, xyz, element) in enumerate(records, 1):
        lines.append("%-6s%5d %-4s %3s %s%4s    %8.3f%8.3f%8.3f  1.00  0.00"
                     "          %2s"
                     % (rec, serial, name, res, chain, seq,
                        xyz[0], xyz[1], xyz[2], element))
    path.write_text("\n".join(lines) + "\nEND\n", encoding="utf-8")
    return path


def test_the_ligand_copy_is_chosen_by_distance_and_not_by_file_order(tmp_path):
    """Seven chapters select a ligand copy. All seven go through one rule.

    The rule cannot be tested on 1L2S, which is why the previous test did not
    catch replacing the distance search with `copies[0]`: 1L2S's first STC copy
    in file order happens to sit 2.70 Å from Ser64 OG, so the distance
    assertion held while the code was picking the wrong chain -- chain A, the
    one missing Lys290-Ala292.

    So this builds a case where file order and distance disagree, which no
    entry in this repository does:

        A/100   2.60 Å   in the site, but the WRONG CHAIN -- and first in file
        B/899   4.00 Å   in the site, right chain, but not the nearest
        B/901   2.70 Å   the answer

    Selecting by file order returns A/100. Taking the first qualifying copy in
    the chain returns B/899. Only distance returns B/901.
    """
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    import receptor_prep

    pdb = write_pdb(tmp_path / "synthetic.pdb", [
        ("ATOM", " OG ", "SER", "A", "64", (0.0, 0.0, 0.0), " O"),
        ("ATOM", " OG ", "SER", "B", "64", (100.0, 0.0, 0.0), " O"),
        ("HETATM", " C1 ", "LIG", "A", "100", (2.60, 0.0, 0.0), " C"),
        ("HETATM", " C1 ", "LIG", "B", "899", (104.0, 0.0, 0.0), " C"),
        ("HETATM", " C1 ", "LIG", "B", "901", (102.70, 0.0, 0.0), " C"),
    ])
    atoms, _, _ = receptor_prep.parse(pdb)

    copies = receptor_prep.ligand_copies(atoms, "LIG")
    assert [c["seq"] for c in copies] == ["100", "899", "901"], \
        "file order must be what it is, or the test proves nothing"

    chosen, reported = receptor_prep.select_copy(atoms, "LIG", "B")
    assert chosen is not None
    assert (chosen["chain"], chosen["seq"]) == ("B", "901"), \
        ("selected %s/%s. B/901 is the nearest copy in chain B; A/100 is what "
         "file order gives and B/899 is what 'first one in the chain that "
         "qualifies' gives." % (chosen["chain"], chosen["seq"]))
    assert chosen["distance_to_ser64_og"] == pytest.approx(2.70, abs=0.01)
    assert len(reported) == 3, \
        "the discarded copies must come back too, so the choice can be checked"


def test_no_catalytic_copy_in_the_chain_returns_nothing_rather_than_the_nearest():
    """A chain with no copy inside the site must not fall back to a far one.

    22.7 Å from any active site is where 1L2S's third STC copy sits. Returning
    it because it was the closest thing available is the failure mode this
    whole rule exists to prevent.
    """
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    import receptor_prep
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        pdb = write_pdb(Path(tmp) / "synthetic.pdb", [
            ("ATOM", " OG ", "SER", "A", "64", (0.0, 0.0, 0.0), " O"),
            ("HETATM", " C1 ", "LIG", "B", "900", (22.7, 0.0, 0.0), " C"),
        ])
        atoms, _, _ = receptor_prep.parse(pdb)
        chosen, copies = receptor_prep.select_copy(atoms, "LIG", "B")
    assert chosen is None
    assert len(copies) == 1 and copies[0]["in_site"] is False


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


# [a-z0-9_] rather than [a-z_]: ch14_boltz2 has a digit in its name, and a
# pattern that skipped it would have reported ch02 as depending on six chapters
# instead of seven -- silently, which is the shape of failure this whole file
# is about. Caught by the companion test below asserting the exact set.
CHAPTER_PATH = re.compile(r"\b(ch\d\d_[a-z0-9_]+)/(?:outputs|config)/")

# The same dependency written the other way. ch27 reads ch17 as
# `REPO / "ch17_validation" / "outputs" / "validation.json"`, which the pattern
# above cannot see -- there is no slash between the chapter and "outputs".
# A scan that under-reports is worse than no scan, because it says "no
# undeclared dependencies" when it means "none in the form I looked for".
CHAPTER_SEGMENT = re.compile(r"""["'](ch\d\d_[a-z0-9_]+)["']""")


def cross_chapter_reads():
    """Which chapters read another chapter's generated files. Returns {ch: {ch}}."""
    found = {}
    for chapter in sorted(REPO.glob("ch[0-9][0-9]_*")):
        if not chapter.is_dir():
            continue
        sources = [chapter / "run.sh"] + sorted(
            list((chapter / "scripts").glob("*.py"))
            + list((chapter / "scripts").glob("*.sh")))
        upstream = set()
        for path in sources:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in (CHAPTER_PATH, CHAPTER_SEGMENT):
                for match in pattern.finditer(text):
                    if match.group(1) != chapter.name:
                        upstream.add(match.group(1))
        if upstream:
            found[chapter.name] = upstream
    return found


def test_every_cross_chapter_dependency_is_declared_in_the_readme():
    """A chapter that reads another chapter's output has to say so.

    Ten such edges were undeclared. Low severity while the scripts announce it
    at runtime -- ch02 names every missing file and ch23 exits with the chapter
    to run -- but ch20 did not announce it, and a reader who runs chapters in
    the order the book presents them has no way to discover the order they
    actually need.

    Derived from the code rather than from a list, so adding a new dependency
    fails this until the README catches up. Naming either the directory
    (`ch17_validation/...`) or the chapter (`Chapter 17`) counts.
    """
    undeclared = []
    for chapter, upstream in cross_chapter_reads().items():
        readme = (REPO / chapter / "README.md").read_text(encoding="utf-8")
        for other in sorted(upstream):
            number = int(other[2:4])
            if other in readme or "Chapter %d" % number in readme:
                continue
            undeclared.append("%s reads %s" % (chapter, other))
    assert not undeclared, \
        "undeclared cross-chapter dependencies:\n  " + "\n  ".join(undeclared)


def test_the_declared_dependencies_are_the_ones_that_exist():
    """The mirror: a README must not claim an upstream the code never reads.

    ch02 listed ch26_case_study/outputs/case_study.json among its sources and
    no criterion ever loaded it, so the chapter advertised a dependency it did
    not have and its own `sources` field was a claim rather than a record.
    Only the five chapters that genuinely read upstream files are checked here,
    because a README may of course mention another chapter for any other
    reason.
    """
    reads = cross_chapter_reads()
    assert set(reads) == {"ch02_method_choice", "ch16_rescoring",
                          "ch20_protocol_record", "ch23_interactions",
                          "ch27_methods"}, \
        ("the set of chapters reading other chapters' output changed: %s. "
         "That is fine, but the new one needs its README updated and this "
         "list with it." % sorted(reads))
    assert reads["ch02_method_choice"] == {
        "ch06_predicted_structures", "ch10_flexibility", "ch12_screening",
        "ch14_boltz2", "ch16_rescoring", "ch17_validation", "ch22_free_energy",
    }, "ch02's upstream set is %s" % sorted(reads["ch02_method_choice"])
    assert reads["ch27_methods"] == {"ch20_protocol_record", "ch17_validation"}, \
        "ch27's upstream set is %s" % sorted(reads["ch27_methods"])
    # Twelve edges across five chapters. Ten of them were undeclared.
    assert sum(len(v) for v in reads.values()) == 12


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
