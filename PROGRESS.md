# PROGRESS

Session memory for the autonomous build. Updated after every completed task.

## Phase 0 — foundation

- [x] directory skeleton (25 chapter directories, stub READMEs, outputs/expected)
- [x] `.gitignore`, `.gitattributes`
- [x] `LICENSE` — MIT, Suryaprakash Tripathy
- [x] `errata.md`
- [x] `README.md` placeholder (rewritten properly in Phase 4)
- [x] `PROGRESS.md`
- [x] `environment/environment.yml`, `requirements.txt`, `environment/README.md`
- [x] environment created and `environment/resolved.txt` written
- [x] `data/structures/fetch.sh` — run, checksums recorded
- [x] `data/ligands/` — SDFs generated and committed, `generate.py --check` passes
- [x] `scripts/audit_structures.py` — every structural claim re-measured
- [x] `protocols/reproducibility_record.md` — Chapter 20's seventeen fields
- [ ] `tests/` — pytest harness

## Phase 1 — the pattern chapter

- [x] `ch09_first_run` — AmpC run, four demonstrations, gate accepted
- [ ] `ch09_first_run` — synthetic system, config, plan-named scripts

## Phase 2 — chapters with hard expected values

- [ ] 2.1 `ch05_receptor_prep`
- [ ] 2.2 `ch08_ligand_prep`
- [ ] 2.3 `ch04_formats`
- [ ] 2.4 `ch17_validation`
- [ ] 2.5 `ch18_enrichment`
- [ ] 2.6 `ch10_flexibility`
- [ ] 2.7 `ch21_molecular_dynamics`

## Phase 3 — remaining chapters

Not started.

## Phase 4 — integration

Not started.

---

## Blocked / needs a decision

### Three-decimal values do not reproduce on Windows

**Status: diagnosed, not blocking. The book is right; the platform is the
variable.**

Chapter 9's synthetic box sweep, same Vina 1.2.7, meeko 0.8.0, RDKit 2026.3.5:

| Where | 20 Å | 12 Å | 8 Å |
|---|---|---|---|
| Book | −4.905 | −4.911 | −2.748 |
| Native Linux (WSL, this machine) | **−4.905** | **−4.911** | **−2.748** |
| Native Windows | −4.910 | −4.903 | −2.686 |
| Linux Vina, Windows-built ligand | −4.904 | −4.896 | −2.728 |

Two independent causes, both measured:

1. **The RDKit build.** Windows and Linux RDKit 2026.3.5 give different MMFF
   optimised coordinates from the same `EmbedMolecule(randomSeed=11)`. The
   receptor, built with numpy's PCG64, is byte-identical across the two — so
   the divergence is the force field's convergence, not the RNG.
2. **The Vina build.** Handed the identical Windows-built ligand and receptor,
   Linux and Windows Vina return different scores (−4.904 vs −4.910 at 20 Å).

**Consequence for the repository:** seed 42 gives byte-identical results within
a build, not across builds, and nothing in the log distinguishes the two
situations. Exact-value tests assert three decimals on Linux and behaviour
elsewhere. `scripts/docking_common.py` carries the measurements and
`is_reference_platform()`.

### Open Babel is 3.1.0, not the pinned 3.2.1

`openbabel-wheel` ships a cp312 Windows wheel built from Open Babel 3.1.0; no
3.2.1 Windows wheel exists. ch04's round-trip results are Open Babel's output,
so this could move a published value. ch04 is run and compared anyway, with the
version difference recorded next to the result.

## Deviations from CLAUDE.md

- **`make_test_system.py` wrote the ligand without hydrogens.** The file as
  supplied called `Chem.MolToMolFile(Chem.RemoveHs(m), "lig.sdf")`, but the
  recipe in `CLAUDE.md` §6 says `Chem.MolToMolFile(m, "lig.sdf")` with the
  comment "explicit Hs — meeko requires them". Meeko does require them: on the
  stripped file it writes no PDBQT and reports an error. Corrected to match the
  recipe, which then reproduces the book's numbers exactly on Linux.
- **`make_test_system.py` location.** `CLAUDE.md` §6 says
  `scripts/make_test_system.py`; `SESSION_PLAN.md` §1.2 says it belongs to
  ch09. It lives at `ch09_first_run/scripts/make_test_system.py`.
- **Vina on Windows** is the official `vina_1.2.7_win.exe` binary, because
  `pip install vina==1.2.7` needs Boost and PyPI ships no Windows wheel. Same
  upstream release, driven through the same command line.
- **Python is 3.12.10**, not the book's 3.12.3.
- **Ten disordered chain B side chains are typed as alanine** in ch09's AmpC
  receptor rather than deleted. REMARK 470 says they are missing their distal
  atoms, so the file holds exactly alanine's heavy atoms; deleting the residues
  would remove backbone, and Lys290's centre of mass is 1.1 Å outside the 20 Å
  box face. Chapter 5 describes rebuilding with PDBFixer as the alternative.

## Timings for the book's hardware note

Chapter 9, AmpC system, 4 cores, Windows 11, seed 42:

| Exhaustiveness | Wall time |
|---|---|
| 8 | 6.8–7.3 s |
| 32 | 27.0 s |

Ratio 3.7, inside the 3–5 band. The book's 3.4 s and 14.2 s were a different
machine and a much smaller ligand — the synthetic system, not AmpC.
