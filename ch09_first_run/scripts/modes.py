#!/usr/bin/env python3
"""Mode 1's RMSD columns are not a validation result.

    python ch09_first_run/scripts/modes.py [--system synthetic|ampc]

Prints Vina's mode table. Mode 1 reads `0.000 0.000` in every run ever made,
because the column is the distance from mode 1 and mode 1 is zero from itself
by construction. It is not a comparison with a crystal pose.

Reading it as one is the most common way a docking run appears to validate
itself. Chapter 17 measures the distance that matters: symmetry-corrected,
heavy-atom, and without superposition.
"""
import argparse
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(CH / "scripts"))

import systems  # noqa: E402
from docking_common import dock, vina_version  # noqa: E402

SEED = 42
EXHAUSTIVENESS = 8


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    systems.add_argument(ap)
    args = ap.parse_args()

    receptor, ligand, centre = systems.get(args.system)
    out = Path(receptor).parent
    print("Vina: %s\nsystem: %s\n" % (vina_version(), args.system))

    modes, _, _ = dock(receptor, ligand, centre, (20, 20, 20),
                       out / "modes.pdbqt", seed=SEED,
                       exhaustiveness=EXHAUSTIVENESS,
                       log_path=out / "logs" / "modes.log")
    print("  mode | affinity | rmsd l.b. | rmsd u.b.")
    print("  -----+----------+-----------+----------")
    for mode, affinity, lb, ub in modes:
        print("  %4d | %8.3f | %9.3f | %8.3f" % (mode, affinity, lb, ub))

    mode1 = modes[0]
    print("\nMode 1: %.3f %.3f. Distance from mode 1, not from anything"
          % (mode1[2], mode1[3]))
    print("crystallographic. Every Vina run prints this and it means nothing")
    print("about whether the pose is right.")

    (out / "modes.json").write_text(json.dumps(
        {"system": args.system,
         "modes": [{"mode": m, "affinity": a, "rmsd_lb": lb, "rmsd_ub": ub}
                   for m, a, lb, ub in modes],
         "mode1_rmsd_is_zero": mode1[2] == 0.0 and mode1[3] == 0.0},
        indent=2) + "\n")
    print("\nwrote %s" % (out / "modes.json"))


if __name__ == "__main__":
    main()
