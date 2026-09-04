# Chapter 11 — web servers

## The upload set

`outputs/upload/` holds what a docking server will accept:

| File | What it is |
|---|---|
| `1L2S_chainB_clean.pdb` | Chain B only, altloc A, 2761 atoms, no solvent |
| `STC.sdf` | The ligand with its formal charge explicit |
| `box.txt` | Box centre and dimensions, computed |

**The ligand goes up as SDF, not PDBQT.** The server will make its own
PDBQT; sending one would only be a second opportunity to lose the formal
charge, and the charge is the thing this series cannot afford to lose.

**The box is computed, not eyeballed.** It is one of the few fields a
server lets you control, so it is worth arriving with the number rather
than dragging a cube around in a viewer.

## The audit

Against Chapter 20's seventeen protocol fields. ★ marks tier one.

| Field | Can you set it? | Can you record it? | Note |
|---|---|---|---|
| ★ Receptor source and identifier | yes | yes | you upload it |
| Chains and altlocs kept | **no** | **no** | usually stripped or merged silently |
| Waters and ions | **no** | **no** | removed by the server, rarely stated |
| Missing residues | **no** | **no** | not reported |
| ★ Receptor preparation tool and version | yes | **no** | the server's own, version rarely given |
| ★ Ligand source | yes | yes | you upload it |
| Ligand preparation | **no** | **no** | server-side protonation, pH rarely stated |
| Stereochemistry as docked | **no** | **no** | depends on what the server did to your file |
| ★ Box centre | yes | yes | usually settable |
| ★ Box dimensions | yes | yes | usually settable |
| Box derivation | yes | yes | yours, if you computed it |
| ★ Docking program and version | yes | **no** | named; exact version often not |
| Exhaustiveness / num_modes / energy_range | yes | yes | sometimes settable |
| ★ Random seed | **no** | **no** | almost never settable, almost never reported |
| Redocking result | yes | yes | yours to compute |
| Cross-docking or enrichment result | yes | yes | yours to compute |
| Exclusions and deviations | yes | yes | yours to write |

**9 of 17 fields can be recorded**, and **3 tier-one fields cannot**:

- Receptor preparation tool and version
- Docking program and version
- Random seed

## The seed decides it

Almost no docking web server lets you set a random seed, and almost none
reports the one it used. Chapter 9 measured what that costs: two runs at
Vina's default seed differ, and nothing in the log distinguishes a
defaulted seed from a fixed one.

So **a web-server run cannot be repeated** — not by you, and not by the
server. Re-submitting the same files gives a different answer and no way
to tell whether the difference is the seed or something you changed.

That does not make web servers useless. It makes them a way to get a
first look at a system, and not a way to produce a result somebody else
can check. Which of those you need is a decision worth taking before
the upload rather than at the write-up.

## Nothing is submitted

This script contacts no server. Submitting data to a third-party service
is the user's decision rather than a script's, and an automated
submission is also the quickest way to breach a service's terms of use.
