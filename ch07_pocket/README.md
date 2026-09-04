# Chapter 7 — defining the pocket

Four ways to place the search box, one identical protocol, and the honest
answer to what the choice costs.

## Run

```bash
bash ch07_pocket/run.sh
```

## The four definitions

| Definition | What it means | Available when |
|---|---|---|
| `ligand` | Centroid of the crystallographic ligand, 8 Å padding | **Never, in real work** |
| `residues` | Centroid of the known binding-site residues | The site is known from the literature |
| `catalytic` | A 22 Å cube on Ser64 OG alone | One annotated residue is all you have |
| `blind` | A box around the whole chain | You know nothing |

The `ligand` row is the ceiling, not a method. If you knew where the ligand sat
you would not be docking.

## The result

| Definition | Box (Å) | Volume (Å³) | Centre off by | Affinity | RMSD | Modes in site | Seconds |
|---|---|---|---|---|---|---|---|
| ligand | 23.7 × 20.6 × 23.2 | 11,336 | 0.00 Å | −7.377 | 1.114 Å | 9/9 | 17.2 |
| residues | 31.8 × 34.5 × 37.6 | 41,173 | 4.50 Å | −7.465 | 1.025 Å | 8/9 | 19.5 |
| catalytic | 22.0 × 22.0 × 22.0 | 10,648 | 4.71 Å | −7.445 | 1.028 Å | 8/9 | 16.2 |
| blind | 60.0 × 60.8 × 51.4 | 187,700 | 10.84 Å | −7.392 | 1.108 Å | 8/9 | 20.3 |

**All four land within 0.09 Å of each other.** Blind docking over the entire
chain — seventeen times the volume, a box centre 10.8 Å from the truth — finds
the same pose, and eight of its nine modes are still in the real site.

This is not the expected answer and it is reported as measured. The reason is a
property of the system: **AmpC has one dominant pocket and STC is a good binder
for it.** A protein with several plausible pockets, or a weaker ligand, is
where a careless box costs you the result. One system cannot establish that
blind docking is generally safe, and this chapter does not claim it does.

What the large box does cost here is grid volume: 17× it, for 1.4× the wall
time. On a single run that is nothing. Multiplied across a screen of 100,000
compounds it is the whole compute budget, which is the argument for a tight box
that survives regardless of what happens to the pose.

## The useful practical finding

The `residues` and `catalytic` definitions — the two you can actually use —
both put the box centre about 4.5 Å from the true ligand centroid and both
recovered the pose. **A box centre does not have to be right; it has to be
close enough that the pocket is inside the box.** That is a much weaker
requirement than it is usually treated as, and it is why "I do not know exactly
where the ligand binds" is rarely the thing that stops a docking run.
