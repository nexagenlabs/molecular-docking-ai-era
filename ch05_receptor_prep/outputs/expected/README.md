# Chapter 5 — expected output

`qc_1L2S.md` is the reference report for 1L2S. Your run should match it apart
from nothing at all: this chapter reads a fixed file and does arithmetic on it,
so unlike the docking chapters it is platform-independent.

The values that matter, and that `tests/test_ch05_receptor_prep.py` asserts:

| | |
|---|---|
| 1L2S | 1.94 Å, R-free 0.207 |
| STC copies | 2.70, 2.70 and **22.72** Å from Ser64 OG |
| Chain A gap | Lys290–Ala292 |
| Altloc | Gln250, the only one in the entry |
| Bridging waters, chain B | HOH 403 (2.68 Å, Asn346 + Arg349) and HOH 481 (2.70 Å, Thr316 + Lys315 + Tyr150) |
| Phosphate in 1L2S | none |
| Nearest phosphate elsewhere | 7.83 Å, in 4JXS |
| 4JXS | 1.90 Å, R-free 0.212, ligand in chain B only |
| 4JXV | 1.76 Å, R-free 0.232, ligand in both chains |
| 1GA9 | 2.10 Å, R-free 0.249, covalent LINK 1.64 Å (A) / 1.62 Å (B), plus a K⁺ ion |

If your 1L2S report shows a phosphate, the HETATM parsing is wrong — and then
the ligand selection cannot be trusted either.
