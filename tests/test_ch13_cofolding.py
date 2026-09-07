"""Chapter 13: the input file, which can be checked without a GPU.

Boltz-2 needs a CUDA GPU and several gigabytes of weights, and this is not
that machine. The chapter writes the input anyway, because the input is half
the protocol and three things in it are easy to get wrong and impossible to
notice afterwards: the signal peptide, the numbering, and the charge.

Those three are what these tests hold. The chapter also must not simulate the
prediction it cannot run -- STRESS_REPORT.md B13 notes the exit code was the
one thing its run.sh obscured, so the script's own exit status is asserted
here rather than run.sh's.
"""
import re

import pytest

from conftest import REPO, run_script_raw

YAML = REPO / "ch13_cofolding" / "outputs" / "ampc_stc.yaml"


@pytest.fixture(scope="module")
def cofold():
    """The script refuses to fabricate a prediction, so a non-zero exit is right.

    It still writes the input file first, which is the part that can be
    checked here.
    """
    result = run_script_raw("ch13_cofolding/scripts/cofold.py")
    assert YAML.exists(), "no input file was written"
    return result, YAML.read_text(encoding="utf-8")


def test_it_refuses_rather_than_simulating_a_prediction(cofold):
    result, _ = cofold
    message = result.stdout + result.stderr
    assert result.returncode != 0, \
        "the script exited 0 without a GPU; a machine reading exit codes " \
        "cannot then tell a real run from a skipped one"
    assert "Nothing is simulated" in message
    assert "Traceback" not in message


def test_the_sequence_is_the_mature_protein(cofold):
    """UniProt P00811 residues 20-377. The first 19 are a signal peptide.

    Folding them with the complex hands the model 19 residues of something
    that is not in the crystal structure.
    """
    _, text = cofold
    sequence = re.search(r"sequence:\s*([A-Z]+)", text).group(1)
    assert len(sequence) == 358, \
        "expected the 358-residue mature protein, got %d residues" % len(sequence)
    assert sequence.startswith("APQQ"), \
        "the mature protein starts at Ala20; a sequence starting elsewhere " \
        "means the signal peptide boundary moved"


def test_the_catalytic_serine_is_where_the_mature_numbering_puts_it(cofold):
    """Ser64 in the crystal is Ser80 in UniProt: PDB + 16.

    The script checks this itself and stops if it fails. Checked again here
    against the file it wrote, because this is the one assertion that catches
    an off-by-one in the signal-peptide boundary.
    """
    _, text = cofold
    sequence = re.search(r"sequence:\s*([A-Z]+)", text).group(1)
    # Mature residue 1 is UniProt 20, so UniProt 80 is mature index 61 (0-based).
    assert sequence[80 - 20] == "S", \
        "residue 80 of the mature sequence is %r, not the catalytic serine" \
        % sequence[80 - 20]


def test_this_file_carries_the_same_numbering_trap_ch06_demonstrates(cofold):
    """Asking this sequence for residue 64 gives isoleucine, not the serine.

    ch06 finds this in the AlphaFold model. It is a property of the numbering,
    not of AlphaFold, so it is here too -- which is what makes the renumbering
    step in the follow-up list load-bearing rather than pedantic. Asserted as
    the residue rather than as the warning: the warning is prose and would
    still read correctly over a sequence that had quietly shifted.
    """
    _, text = cofold
    sequence = re.search(r"sequence:\s*([A-Z]+)", text).group(1)
    assert sequence[64 - 20] != "S", \
        "UniProt 64 of this sequence is a serine, so the trap this file warns " \
        "about is not present in it and the warning has become decoration"
    assert sequence[64 - 20] == "I", \
        "expected isoleucine at UniProt 64, got %r" % sequence[64 - 20]
    assert "UniProt numbering" in text and "Ser64" in text and "Ser80" in text, \
        "the file must name both numbers, or a reader has to work out which " \
        "convention it is in"


def test_the_ligand_carries_its_formal_charge(cofold):
    """STC is -1 at pH 7.4, and co-folding models take SMILES.

    Their handling of formal charge is not always documented, which is the
    reason to write it explicitly and say so.
    """
    _, text = cofold
    smiles = re.search(r'smiles:\s*"([^"]+)"', text).group(1)
    assert "[O-]" in smiles, "the ligand SMILES is the neutral acid: %s" % smiles
    assert smiles.count("[O-]") == 1, \
        "STC carries a single negative charge; 18U and 1MU are the dianions"


def test_the_command_it_would_run_carries_a_seed(cofold):
    """The same rule as everywhere else here, in the place it applies.

    Boltz-2 takes the seed on the command line, not in the input YAML, so this
    checks the command the chapter prints rather than the file it writes. A
    co-folding run left on a default seed is as unrepeatable as a Vina one.
    """
    result, _ = cofold
    message = result.stdout + result.stderr
    seed = re.search(r"--seed\s+(\d+)", message)
    assert seed, "the printed command sets no seed"
    assert int(seed.group(1)) != 0, "--seed 0 is the random default"
    assert int(seed.group(1)) == 42, \
        "this repository docks at seed 42 throughout; a different one here " \
        "would be a decision, and it is not recorded as one"


def test_it_says_what_would_have_to_be_checked_afterwards(cofold):
    """Superimpose on the receptor, then measure the ligand RMSD with no fitting.

    Superimposing on the ligand is the --minimize mistake wearing a different
    hat, and it is the mistake a co-folded complex invites, because the
    prediction arrives in its own frame.
    """
    result, _ = cofold
    message = result.stdout + result.stderr
    assert "RECEPTOR" in message
    assert "minimize" in message.lower(), \
        "the chapter must connect this to the ch17 gotcha, not restate it loosely"
