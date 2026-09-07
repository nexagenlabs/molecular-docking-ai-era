# Chapter 16 — rescoring

## Run

```bash
bash ch16_rescoring/run.sh
```

The arithmetic runs anywhere. The GNINA pipeline does not run here — see below.

## Depends on Chapter 17

The arithmetic depends on nothing. The GNINA pipeline rescores a pose that
Chapter 17 produced:

| Reads | Produced by |
|---|---|
| `ch17_validation/outputs/work/1L2S_receptor.pdbqt` | `bash ch17_validation/run.sh` |
| `ch17_validation/outputs/work/1L2S_pose.pdbqt` | `bash ch17_validation/run.sh` |

Both are gitignored, so a fresh clone does not have them. `scripts/rescore_with_gnina.sh`
prints the command it would run and stops; it does not rescore a pose it
invented.

## EF = 1.0 is chance

The published LIT-PCBA result: **GNINA median EF1% of 1.88–2.58 against Vina's
0.90.**

**Vina is below chance.** A library ranked by Vina score, with the top slice
tested, yields fewer actives than testing the same number of compounds picked
at random.

Quoted as *"GNINA 2.58 versus Vina 0.90"*, that reads as one method being about
three times better than another method that works. One of them does not work.
**Keep the 1.0 in the sentence.**

## What the numbers cost in compounds

A million-compound library, 0.1% genuinely active, ten actives wanted in hand:

| Method | EF1% | Against chance | Compounds to test | Cost |
|---|---|---|---|---|
| random | 1.00 | **chance** | 10,000 | 500,000 |
| Vina | 0.90 | **worse** | 11,111 | 555,556 |
| GNINA (low) | 1.88 | better | 5,319 | 265,957 |
| GNINA (high) | 2.58 | better | 3,876 | 193,798 |

Ranking by Vina costs **55,556 more** than not ranking at all. GNINA at the top
of its range gets you there for 2.6× fewer compounds than random.

An EF1% of 2.58 means the top 1% of the ranked library is 2.58 times richer in
actives than the library as a whole. It does **not** mean 2.58 out of every 3
hits are real, which is how the number tends to get read. The gain is genuine,
useful, and modest.

## The GNINA pipeline does not run here

`scripts/rescore_with_gnina.sh` contains the pipeline and was attempted once.
It exits 3 with an explanation:

- GNINA is a compiled binary with a CUDA dependency.
- It is not on PyPI or conda-forge, and there is no Windows build.
- In practice it wants a GPU.

**No output is simulated.** The script prints the exact command the chapter
would run, including two flags worth knowing:

- `--cnn_scoring rescore` keeps Vina's poses and rescores them, which is the
  comparison the LIT-PCBA numbers come from. `--cnn_scoring all` also redoes
  the search and answers a different question.
- `--seed 42` — GNINA inherits Vina's default-seed behaviour, so the rule from
  Chapter 9 applies unchanged: set it and record it.

Recorded in `PROGRESS.md` under what could not run here.
