# Chapter 11 — web servers

What you can upload, and what you cannot record.

## Run

```bash
bash ch11_web_servers/run.sh
```

**No server is contacted.** Submitting data to a third-party service is the
user's decision rather than a script's, and an automated submission is also the
quickest way to breach a service's terms of use. What this produces is the
upload set and the audit; the upload is a human action.

## The upload set

`outputs/upload/` holds what a docking server will accept:

| File | What it is |
|---|---|
| `1L2S_chainB_clean.pdb` | Chain B only, altloc A, 2,761 atoms, no solvent |
| `STC.sdf` | The ligand with its formal charge explicit |
| `box.txt` | Box centre and dimensions, computed |

**The ligand goes up as SDF, not PDBQT.** The server will build its own PDBQT;
sending one would only be a second opportunity to lose the formal charge, and
the charge is the thing this series cannot afford to lose (Chapter 4).

**The box is computed, not eyeballed.** It is one of the few fields a server
lets you control, so it is worth arriving with the number rather than dragging
a cube around in a viewer.

## The audit

Against Chapter 20's seventeen protocol fields:

| | Count |
|---|---|
| Fields you can set | 11 of 17 |
| Fields the result page lets you record | **9 of 17** |
| **Tier-one fields you cannot record** | **3** |

The three tier-one fields lost are:

- Receptor preparation tool and version
- Docking program and version
- **Random seed**

## The seed decides it

Almost no docking web server lets you set a random seed, and almost none
reports the one it used. Chapter 9 measured what that costs: two runs at Vina's
default differ, and nothing in the log distinguishes a defaulted seed from a
fixed one.

So **a web-server run cannot be repeated** — not by you, and not by the server.
Re-submitting the same files gives a different answer, with no way to tell
whether the difference is the seed or something you changed.

That does not make web servers useless. It makes them a way to get a first look
at a system, and not a way to produce a result somebody else can check. Which
of those you need is a decision worth taking before the upload rather than at
the write-up.
