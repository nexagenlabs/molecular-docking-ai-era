#!/usr/bin/env python3
"""Chapter 10 — which side chains actually move?

    python ch10_flexibility/scripts/torsion_analysis.py

Measures every side-chain torsion of the binding-site residues across four
structures and eight chains, and reports which ones change rotamer.

Flexible-side-chain docking costs search time that grows with the number of
flexible residues, so the useful question is not "which residues *could* move"
but "which ones are *observed* to". Eight structures of the same protein answer
it directly.

Writes outputs/rotamers.json and outputs/rotamers.md.
"""
import json
import math
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"

ENTRIES = ["1L2S", "4JXS", "4JXV", "1GA9"]

# Binding-site residues in PDB numbering.
#
# NUMBERING TRAP: UniProt number = PDB number + 16. Ser64 here is Ser80 in
# UniProt P00811. Mixing the two selects the wrong residues silently.
SITE = {
    "64": "Ser", "67": "Lys", "119": "Leu", "120": "Gln", "150": "Tyr",
    "152": "Asn", "221": "Tyr", "293": "Leu", "315": "Lys", "316": "Thr",
    "317": "Gly", "318": "Ala", "346": "Asn", "349": "Arg",
}

# Standard side-chain torsions. Glycine and alanine have none -- they are in
# the site list because they matter chemically (the KTG motif, the oxyanion
# hole), not because they can move.
CHI = {
    "SER": [("N", "CA", "CB", "OG")],
    "THR": [("N", "CA", "CB", "OG1")],
    "CYS": [("N", "CA", "CB", "SG")],
    "VAL": [("N", "CA", "CB", "CG1")],
    "LEU": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "ILE": [("N", "CA", "CB", "CG1"), ("CA", "CB", "CG1", "CD1")],
    "ASN": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "OD1")],
    "ASP": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "OD1")],
    "GLN": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"),
            ("CB", "CG", "CD", "OE1")],
    "GLU": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"),
            ("CB", "CG", "CD", "OE1")],
    "LYS": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"),
            ("CB", "CG", "CD", "CE"), ("CG", "CD", "CE", "NZ")],
    "ARG": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD"),
            ("CB", "CG", "CD", "NE"), ("CG", "CD", "NE", "CZ")],
    "TYR": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "PHE": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "HIS": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "ND1")],
    "TRP": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "CD1")],
    "MET": [("N", "CA", "CB", "CG"), ("CA", "CB", "CG", "SD"),
            ("CB", "CG", "SD", "CE")],
    "GLY": [],
    "ALA": [],
    "PRO": [("N", "CA", "CB", "CG")],
}

# A residue whose rotamer-defining torsions all stay inside this window across
# eight chains is not moving, and making it flexible buys search cost only.
RIGID_THRESHOLD = 20.0

# Torsions with a two-fold symmetric terminal group. The last chi of Tyr and
# Phe is defined only modulo 180 degrees, because swapping CD1/CD2 gives the
# same physical ring. Comparing them unfolded invents a 180-degree "rotamer
# change" where nothing moved.
SYMMETRIC_LAST_CHI = {"TYR", "PHE"}

# Torsions that carry no rotamer information and are excluded outright:
#
#   Asn chi2, Gln chi3    The terminal amide's O and N are indistinguishable at
#   Asp chi2, Glu chi3    these resolutions, so which way round it was modelled
#   His chi2              is a refinement choice, not an observation.
#
#   Lys chi4, Arg chi4    A terminal -NH3+ or guanidinium is solvent-exposed and
#                         barely restrained. It moves, and it says nothing about
#                         whether the pocket changed shape.
#
# This exclusion is what separates a residue that moved from a residue whose tip
# was modelled differently. Without it Lys67 looks rotameric on the strength of
# chi4 alone, while its chi1 to chi3 vary by at most 19 degrees.
NOT_ROTAMER_DEFINING = {("ASN", 2), ("GLN", 3), ("ASP", 2), ("GLU", 3),
                        ("HIS", 2), ("LYS", 4), ("ARG", 4)}

# Canonical sp3 rotamer wells.
WELLS = {"g+": 60.0, "t": 180.0, "g-": -60.0}

# The well model does not apply to a folded symmetric torsion, so a change
# there is called on half a well instead.
SYMMETRIC_CHANGE_DEGREES = 60.0


def torsion(p0, p1, p2, p3):
    """Dihedral in degrees, from the standard cross-product construction."""
    b0 = [p0[i] - p1[i] for i in range(3)]
    b1 = [p2[i] - p1[i] for i in range(3)]
    b2 = [p3[i] - p2[i] for i in range(3)]
    norm = math.sqrt(sum(x * x for x in b1))
    b1 = [x / norm for x in b1]
    v = [b0[i] - sum(b0[j] * b1[j] for j in range(3)) * b1[i] for i in range(3)]
    w = [b2[i] - sum(b2[j] * b1[j] for j in range(3)) * b1[i] for i in range(3)]
    x = sum(v[i] * w[i] for i in range(3))
    cross = [b1[1] * v[2] - b1[2] * v[1],
             b1[2] * v[0] - b1[0] * v[2],
             b1[0] * v[1] - b1[1] * v[0]]
    y = sum(cross[i] * w[i] for i in range(3))
    return math.degrees(math.atan2(y, x))


def well(angle):
    """Nearest canonical rotamer well."""
    best, distance = None, 1e9
    for name, centre in WELLS.items():
        diff = abs(angle - centre) % 360.0
        diff = min(diff, 360.0 - diff)
        if diff < distance:
            best, distance = name, diff
    return best


def circular_spread(angles, period=360.0):
    """Largest pairwise separation, respecting the wrap-around.

    A naive max-minus-min calls -179 and +179 a 358-degree difference when they
    are 2 degrees apart. That alone would report half the site as rotameric.
    """
    if len(angles) < 2:
        return 0.0
    worst = 0.0
    for i, a in enumerate(angles):
        for b in angles[i + 1:]:
            diff = abs(a - b) % period
            worst = max(worst, min(diff, period - diff))
    return worst


def read_chains(pdb_id):
    """Side-chain atoms per chain, taking altloc A or blank."""
    path = STRUCTURES / ("%s.pdb" % pdb_id)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    chains = {}
    for line in path.read_text().splitlines():
        if not line.startswith("ATOM"):
            continue
        if line[16] not in (" ", "A"):
            continue
        chain, seq = line[21], line[22:26].strip()
        if seq not in SITE:
            continue
        chains.setdefault(chain, {}).setdefault(
            seq, {"res": line[17:20].strip(), "atoms": {}})
        chains[chain][seq]["atoms"][line[12:16].strip()] = (
            float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return chains


def measure():
    measured, chain_labels, incomplete = {}, [], []
    for pdb_id in ENTRIES:
        for chain, residues in sorted(read_chains(pdb_id).items()):
            label = "%s:%s" % (pdb_id, chain)
            chain_labels.append(label)
            for seq, info in residues.items():
                name = "%s%s" % (SITE[seq], seq)
                for index, quad in enumerate(CHI.get(info["res"], []), start=1):
                    if not all(atom in info["atoms"] for atom in quad):
                        # A disordered side chain (REMARK 470) has no torsion to
                        # measure. Recorded rather than skipped: a residue that
                        # looks rigid because half its data is missing is the
                        # failure mode this analysis has to avoid.
                        incomplete.append({"residue": name, "chain": label,
                                           "chi": index})
                        continue
                    angle = torsion(*[info["atoms"][a] for a in quad])
                    measured.setdefault(name, {}).setdefault(
                        index, {})[label] = round(angle, 1)
    return measured, chain_labels, incomplete


def classify(measured):
    """Two separate questions, and CLAUDE.md asks both.

        "varies <= 20 degrees in every torsion"   -- is it still at all?
        "changes rotamer"                         -- did it move to another well?

    They are not the same question, and conflating them is what makes this
    analysis come out wrong. A residue can vary by 35 degrees and stay in one
    well: that is a side chain breathing, not switching.
    """
    spreads, per_chi, changing = {}, {}, []
    for name, chis in measured.items():
        worst, residue_changes = 0.0, False
        per_chi[name] = {}
        three = name[:3].upper()
        for index, angles in sorted(chis.items()):
            values = list(angles.values())
            if (three, index) in NOT_ROTAMER_DEFINING:
                per_chi[name][index] = {
                    "spread": round(circular_spread(values), 1),
                    "excluded": True,
                    "reason": "terminal group: ambiguous or unrestrained",
                    "angles": angles}
                continue
            symmetric = (three in SYMMETRIC_LAST_CHI and index == max(chis))
            spread = circular_spread(values, 180.0 if symmetric else 360.0)
            if symmetric:
                wells, chi_changes = None, spread > SYMMETRIC_CHANGE_DEGREES
            else:
                wells = sorted({well(a) for a in values})
                chi_changes = len(wells) > 1
            residue_changes = residue_changes or chi_changes
            per_chi[name][index] = {"spread": round(spread, 1),
                                    "symmetric": symmetric,
                                    "excluded": False,
                                    "wells": wells,
                                    "changes_well": chi_changes,
                                    "angles": angles}
            worst = max(worst, spread)
        spreads[name] = round(worst, 1)
        if residue_changes:
            changing.append(name)
    return spreads, per_chi, sorted(changing)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    measured, chain_labels, incomplete = measure()
    if len(chain_labels) != 8:
        print("WARNING: %d chains, expected 8" % len(chain_labels))
    spreads, per_chi, rotamer_changing = classify(measured)

    rigid = sorted(n for n, s in spreads.items()
                   if s <= RIGID_THRESHOLD and n not in rotamer_changing)
    breathing = sorted(n for n, s in spreads.items()
                       if s > RIGID_THRESHOLD and n not in rotamer_changing)
    no_torsions = sorted("%s%s" % (SITE[seq], seq) for seq in SITE
                         if "%s%s" % (SITE[seq], seq) not in spreads)

    print("Chains analysed: %s\n" % ", ".join(chain_labels))
    print("%-10s %-8s %s" % ("residue", "spread", "verdict"))
    for name in sorted(spreads, key=lambda n: -spreads[n]):
        if name in rotamer_changing:
            verdict = "CHANGES ROTAMER"
        elif name in breathing:
            verdict = "moves > %.0f deg, same rotamer well" % RIGID_THRESHOLD
        else:
            verdict = "rigid"
        print("%-10s %6.1f   %s" % (name, spreads[name], verdict))
    for name in no_torsions:
        print("%-10s      -   no side-chain torsion" % name)

    print("\nRotamer-changing (%d): %s"
          % (len(rotamer_changing), ", ".join(rotamer_changing)))
    print("Rigid, <= %.0f deg in every rotamer-defining torsion (%d): %s"
          % (RIGID_THRESHOLD, len(rigid), ", ".join(rigid)))
    if breathing:
        print("Moves more but stays in one well (%d): %s"
              % (len(breathing), ", ".join(breathing)))
    if incomplete:
        print("\nTorsions not measurable (disordered side chains): %d" % len(incomplete))

    results = {
        "chains": chain_labels,
        "threshold_degrees": RIGID_THRESHOLD,
        "max_spread": spreads,
        "per_chi": per_chi,
        "rotamer_changing": rotamer_changing,
        "rigid": rigid,
        "moves_within_one_well": breathing,
        "residues_without_torsions": no_torsions,
        "unmeasurable": incomplete,
    }
    (OUT / "rotamers.json").write_text(json.dumps(results, indent=2) + "\n",
                                       encoding="utf-8")

    lines = [
        "# Chapter 10 — which side chains actually move", "",
        "Every side-chain torsion of the %d binding-site residues, across the %d "
        "chains of" % (len(SITE), len(chain_labels)),
        "1L2S, 4JXS, 4JXV and 1GA9.", "",
        "| Residue | Largest spread | Verdict |",
        "|---|---|---|",
    ]
    for name in sorted(spreads, key=lambda n: -spreads[n]):
        if name in rotamer_changing:
            verdict = "**changes rotamer**"
        elif name in breathing:
            verdict = "moves, same well"
        else:
            verdict = "rigid"
        lines.append("| %s | %.1f° | %s |" % (name, spreads[name], verdict))
    for name in no_torsions:
        lines.append("| %s | — | no side-chain torsion |" % name)
    lines += [
        "",
        "**%s** are the rotamer-changing residues, and the only" % ", ".join(rotamer_changing),
        "defensible choices for flexible-residue docking here.",
        "",
        "%d residues stay inside %.0f° in every rotamer-defining torsion across"
        % (len(rigid), RIGID_THRESHOLD),
        "all %d chains. %d have no side-chain torsion at all." % (len(chain_labels),
                                                                 len(no_torsions)),
    ]
    if breathing:
        lines += [
            "",
            "%s moves more than %.0f° and still stays in one rotamer well. That"
            % (", ".join(breathing), RIGID_THRESHOLD),
            "is a side chain breathing rather than switching, and it is why",
            "\"varies by more than 20°\" and \"changes rotamer\" have to be asked",
            "as two separate questions.",
        ]
    lines += [
        "",
        "## Three ways to get this wrong",
        "",
        "- **Ignoring the wrap-around.** −179° and +179° are two degrees apart,",
        "  not 358. A naive max-minus-min reports half the site as rotameric.",
        "- **Ignoring terminal symmetry.** The last χ of Tyr and Phe is defined",
        "  only modulo 180°, because swapping CD1/CD2 gives the same ring.",
        "- **Trusting terminal groups.** Asn χ2 and Gln χ3 record which way an",
        "  amide was modelled, not which way it points — O and N are",
        "  indistinguishable at this resolution. Lys χ4 and Arg χ4 are",
        "  solvent-exposed and barely restrained. Include them and Lys67 looks",
        "  rotameric on χ4 alone, while its χ1–χ3 vary by at most 19°.",
        "",
    ]
    (OUT / "rotamers.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nwrote %s" % (OUT / "rotamers.json"))


if __name__ == "__main__":
    main()
