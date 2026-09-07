"""Chapter 26: three reproduction tests with published answers.

CLAUDE.md section 6: "redock 1L2S (original authors reported 1.75 and 1.87 A
against crystal), cross-dock into 4JXS and 4JXV, and rank the series against
26, 18 and 31 uM."

Test 3's answer is that there is no reliable ranking here to reproduce, and
that is a result rather than a failure of the test. It is asserted as such --
a future version that started producing a confident ranking of a series
spanning 0.32 kcal/mol would be reporting its own noise, and this file should
fail rather than record the improvement.

Affinities and RMSDs are docking output. What is asserted is what the chapter
concludes from them.
"""
import pytest

PUBLISHED_REDOCK_RMSD = [1.75, 1.87]


def test_test1_the_redock_reproduces_the_published_conclusion(ch26_outputs):
    """Under 2 A either way, which is the criterion that matters.

    Reproducing a published number to two decimals would be surprising.
    Reproducing the conclusion is what a reproduction test is for.
    """
    test1 = ch26_outputs["test1_redock_1l2s"]
    assert test1["published"] == PUBLISHED_REDOCK_RMSD, \
        "the published values must be carried literally; they are the thing " \
        "being reproduced against"
    assert all(v < 2.0 for v in test1["published"]), \
        "the original authors' own values are under 2 A"
    assert test1["rmsd"] < 2.0, \
        "this run gave %.3f A; the published values are 1.75 and 1.87" % test1["rmsd"]
    assert test1["under_2A"] is True


def test_test2_one_ligand_does_not_prefer_its_own_structure(ch26_outputs):
    """The finding cross-docking exists to produce.

    A ligand that does not score best in the structure it was crystallised in
    is telling you the receptor conformations differ more than the ligands do
    -- which is why a redock alone does not validate a protocol.
    """
    cross = ch26_outputs["test2_cross_docking"]
    assert set(cross) == {"STC", "18U", "1MU"}
    for ligand, entry in cross.items():
        assert set(entry["scores"]) == {"1L2S", "4JXS", "4JXV"}, ligand
        best = min(entry["scores"], key=lambda k: entry["scores"][k])
        assert entry["best_receptor"] == best, \
            "%s: best_receptor is %s but the lowest score is in %s" % (
                ligand, entry["best_receptor"], best)
        assert entry["prefers_native"] == (best == entry["native_receptor"]), ligand

    failures = [l for l, e in cross.items() if not e["prefers_native"]]
    assert failures, \
        "every ligand now prefers its native receptor. That would make " \
        "cross-docking look easy here, and the chapter says it is not -- " \
        "check the receptors before believing it"


def test_the_matrix_is_complete_and_only_the_diagonal_carries_an_rmsd(ch26_outputs):
    """An RMSD off the diagonal would be a comparison against another ligand."""
    matrix = ch26_outputs["matrix"]
    assert set(matrix) == {"1L2S", "4JXS", "4JXV"}
    diagonal = 0
    for receptor, row in matrix.items():
        assert set(row) == {"STC", "18U", "1MU"}, receptor
        for ligand, cell in row.items():
            assert cell["affinity"] < 0, "%s/%s" % (receptor, ligand)
            if cell["native"]:
                diagonal += 1
                assert cell["rmsd"] is not None, "%s/%s" % (receptor, ligand)
            else:
                assert cell["rmsd"] is None, \
                    "%s/%s is not a redock and cannot have an RMSD against a " \
                    "crystal pose of a different ligand" % (receptor, ligand)
    assert diagonal == 3


def test_test3_the_two_affinity_sources_disagree_and_both_are_kept(ch26_outputs):
    """1MU is 26 uM in ChEMBL and 31 uM in PDBbind. Neither is picked."""
    ligands = ch26_outputs["test3_ranking"]["ligands"]
    assert ligands["1MU"]["ki_chembl_um"] == pytest.approx(26.0)
    assert ligands["1MU"]["ki_pdbbind_um"] == pytest.approx(31.0)
    assert ligands["STC"]["ki_chembl_um"] == pytest.approx(26.0)
    assert ligands["18U"]["ki_chembl_um"] == pytest.approx(18.0)


def test_test3_chembl_does_not_order_two_of_the_three(ch26_outputs):
    """STC and 1MU are both 26 uM, so ChEMBL contains no ordering between them.

    A sort function will still return one before the other, and the result
    reads as a ranking the data does not contain. Recording the tie as a tie
    is the only way to stop that.
    """
    ranking = ch26_outputs["test3_ranking"]
    assert ranking["chembl_has_a_tie"] is True
    tied = [group for group in ranking["by_ki_chembl"] if len(group) > 1]
    assert tied == [["1MU", "STC"]] or tied == [["STC", "1MU"]], \
        "expected STC and 1MU tied at 26 uM, got %r" % tied


def test_test3_the_two_sources_rank_the_series_differently(ch26_outputs):
    """PDBbind orders STC before 1MU; ChEMBL cannot order them at all.

    The disagreement between the sources is larger than the gap a method would
    have to resolve, which is the chapter's conclusion.
    """
    ranking = ch26_outputs["test3_ranking"]
    assert ranking["by_ki_chembl"] != ranking["by_ki_pdbbind"]
    assert ranking["series_spread_kcal"] == pytest.approx(0.32, abs=0.005)


def test_test3_there_is_no_ranking_here_to_reproduce(ch26_outputs):
    """The result, asserted as a result.

    The series spans 0.32 kcal/mol -- a factor of 1.7 in Ki -- and no scoring
    function resolves that. If the docking order ever matched both experimental
    orders, that would be a coincidence worth investigating rather than a
    success worth recording.
    """
    ranking = ch26_outputs["test3_ranking"]
    docking_order = [g[0] for g in ranking["by_docking_score"]]
    pdbbind_order = [g[0] for g in ranking["by_ki_pdbbind"]]
    assert docking_order != pdbbind_order, \
        ("docking reproduced PDBbind's order exactly (%s). Over a 0.32 "
         "kcal/mol spread that is not a method working; check it before "
         "reporting it." % docking_order)
    assert ranking["series_spread_kcal"] < 0.5


def test_the_run_is_recorded_the_same_way_as_every_other(ch26_outputs):
    docking = ch26_outputs["docking"]
    assert docking["seed"] == 42
    assert docking["exhaustiveness"] == 32
    assert "1.2.7" in docking["program"]
