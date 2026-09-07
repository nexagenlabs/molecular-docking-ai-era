"""Chapter 2: every recommendation read out of another chapter's output file.

**This chapter reads seven other chapters.** The fixture builds all seven,
because a test that asserts the seven verdicts while the source files happen
to be lying around from an earlier run is asserting a state the suite never
creates -- STRESS_REPORT.md B1, in the chapter with the most exposure to it.

The chapter's other claim is what it does when a source is absent: it reports
NOT MEASURED and counts the gap, rather than falling back to a default. A
default here is a guess wearing a number, and that is tested by taking a
source away.
"""
import json

import pytest

from conftest import REPO, load_module, read_json, run_script, run_script_raw

# Every chapter ch02 reads, and what a reader would look up in each. Seven
# sources for seven criteria: an eighth entry that no criterion loads is a
# dependency the chapter advertises and does not have, and ch26 was one until
# the parametrized test below removed each source in turn and found that
# removing ch26's changed nothing.
SOURCES = {
    "flexibility": "ch10",
    "predicted_structure": "ch06",
    "redock": "ch17",
    "precision": "ch22",
    "correlation": "ch14",
    "screen_cost": "ch12",
    "rescoring": "ch16",
}


@pytest.fixture(scope="module")
def choice(ch06_outputs, ch10_outputs, ch12_outputs, ch14_outputs,
           ch16_outputs, ch17_outputs, ch22_outputs):
    """All seven upstream chapters, then ch02 itself.

    Every argument is a dependency. Listing them is what makes the dependency
    executable rather than a sentence in a README.
    """
    run_script("ch02_method_choice/scripts/choose_method.py")
    return read_json("ch02_method_choice/outputs/method_choice.json")


def test_every_declared_source_is_a_source_the_chapter_actually_reads(choice):
    """Not that the paths exist -- that each one is load-bearing.

    An entry nobody loads is a dependency the chapter advertises and does not
    have, and `sources` in the output then reads as a claim about provenance
    rather than a record of it. ch26 was such an entry. The parametrized test
    below is what establishes "load-bearing" by removing each in turn; this
    one holds the list to the seven criteria so a ninth cannot be added
    without a row to go with it.
    """
    assert set(choice["sources"]) == set(SOURCES)
    assert len(choice["sources"]) == len(choice["findings"]), \
        "%d sources declared for %d criteria" % (len(choice["sources"]),
                                                 len(choice["findings"]))
    for name, chapter in SOURCES.items():
        path = choice["sources"][name]
        assert path.startswith(chapter + "_"), \
            "%s should come from %s, but the path is %s" % (name, chapter, path)


def test_all_seven_questions_are_answered_when_every_source_is_present(choice):
    assert len(choice["findings"]) == 7, \
        "expected seven criteria, got %d" % len(choice["findings"])
    assert choice["unmeasured"] == [], \
        "with all seven sources present nothing should be unmeasured: %s" % (
            choice["unmeasured"],)
    for finding in choice["findings"]:
        assert finding["question"].strip()
        assert finding["answer"].strip()
        assert finding["verdict"].strip()
        assert finding["chapter"] in set(SOURCES.values()), finding["chapter"]


def test_the_answers_carry_the_numbers_their_sources_produced(choice):
    """Spot-checked against the upstream files, so the summary cannot drift.

    Three of the seven, chosen because each would be easy to leave stale: the
    rotamer count, the redock verdict and the series spread.
    """
    findings = {f["chapter"]: f for f in choice["findings"]}

    rotamers = read_json("ch10_flexibility/outputs/rotamers.json")
    for residue in rotamers["rotamer_changing"]:
        assert residue in findings["ch10"]["answer"], \
            "%s changes rotamer but is not named in ch02's answer" % residue

    validation = read_json("ch17_validation/outputs/validation.json")
    for entry in ("1L2S", "4JXS", "4JXV"):
        assert "%.2f" % validation[entry]["rmsd"] in findings["ch17"]["answer"], \
            "ch02 does not carry %s's redock RMSD" % entry

    power = read_json("ch22_free_energy/outputs/power.json")
    assert "%.2f" % power["series_spread_kcal"] in findings["ch22"]["answer"]


def test_the_ranking_verdict_is_no(choice):
    """The cheapest finding in the book and the one most often skipped.

    If this ever became yes, the rest of the book would need rewriting -- so
    the test says which answer it expects rather than merely that there is one.
    """
    finding = next(f for f in choice["findings"] if f["chapter"] == "ch22")
    assert finding["verdict"].lower().lstrip().startswith("no"), \
        "the ranking verdict is %r" % finding["verdict"]


@pytest.mark.parametrize("name", sorted(SOURCES))
def test_a_missing_source_reports_not_measured_rather_than_a_default(name, choice,
                                                                     tmp_path):
    """The behaviour, driven rather than described, for every one of the seven.

    One source file is moved aside and the chapter re-run. Its row must move
    from findings to unmeasured, naming the file, and the two counts must still
    add to seven -- a criterion that quietly disappeared would be worse than
    one reported as a gap, because the report would then look complete.

    Parametrized over all of them because two were not doing this. The
    `correlation` and `rescoring` branches read `if data is not None:` with no
    else, so with ch14 or ch16 unrun their rows vanished from the report
    entirely: six findings, zero gaps, and nothing saying a question had been
    dropped. Testing only the one source that happened to be handled correctly
    is how that survived.
    """
    source = REPO / choice["sources"][name]
    if not source.exists():
        pytest.skip("%s has not been run in this tree yet" % name)

    output = REPO / "ch02_method_choice" / "outputs" / "method_choice.json"
    stashed = tmp_path / source.name
    source.replace(stashed)
    try:
        result = run_script_raw("ch02_method_choice/scripts/choose_method.py")
        assert result.returncode == 0, \
            "a missing source must degrade to NOT MEASURED, not stop the chapter"
        degraded = json.loads(output.read_text())
        assert len(degraded["findings"]) + len(degraded["unmeasured"]) == 7, \
            ("removing %s left %d findings and %d gaps. A criterion vanished "
             "instead of being reported as one."
             % (name, len(degraded["findings"]), len(degraded["unmeasured"])))
        assert len(degraded["unmeasured"]) == 1
        gap = degraded["unmeasured"][0]
        assert source.name in gap["why"], \
            "the gap does not name the missing file: %r" % gap["why"]
        assert "NOT MEASURED" in result.stdout
        assert "These are gaps, not defaults" in result.stdout
    finally:
        stashed.replace(source)
        run_script("ch02_method_choice/scripts/choose_method.py")


def test_no_default_value_is_available_to_fall_back_on(tmp_path):
    """The absence of a fallback, checked directly on the loader.

    load() returns (None, why) and there is no third branch that supplies a
    number. A default here would be indistinguishable from a measurement in
    the report, which is what makes this worth a test of its own.
    """
    module = load_module("ch02_method_choice/scripts/choose_method.py", "ch02_choose")
    original = dict(module.SOURCES)
    module.SOURCES["correlation"] = ("ch14", "ch14_boltz2/outputs/no_such_file.json")
    try:
        data, why = module.load("correlation")
    finally:
        module.SOURCES.clear()
        module.SOURCES.update(original)
    assert data is None
    assert "ch14" in why and "no_such_file.json" in why
