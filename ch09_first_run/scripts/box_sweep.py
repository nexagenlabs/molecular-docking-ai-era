#!/usr/bin/env python3
"""An undersized box fails silently. This is the script that shows it.

    python ch09_first_run/scripts/box_sweep.py [--system synthetic|ampc]

Docks the same ligand into the same receptor at cube edges of 20, 12 and 8 A
and prints all three scores. **No error is raised at any size.** The 8 A box
cannot hold the ligand in every orientation and returns a worse number that
looks exactly like a result -- there is nothing in the output, the exit status
or the log to distinguish it from a successful run.

That is the point of this chapter. A docking score is only interpretable
alongside the box that produced it.
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
from docking_common import (dock, is_reference_platform, platform_banner,  # noqa: E402
                            vina_version)

SEED = 42
EXHAUSTIVENESS = 8      # Vina's default; the sweep isolates the box, nothing else
SIZES = (20, 12, 8)

# The book's values, from the synthetic system on Linux. They are asserted
# nowhere in this script -- comparison is the reader's job and the test suite's.
BOOK = {20: -4.905, 12: -4.911, 8: -2.748}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    systems.add_argument(ap)
    args = ap.parse_args()

    receptor, ligand, centre = systems.get(args.system)
    out = Path(receptor).parent
    print("Vina: %s" % vina_version())
    print(platform_banner())
    print("system: %s, seed %d, exhaustiveness %d\n" % (args.system, SEED, EXHAUSTIVENESS))

    scores = {}
    for size in SIZES:
        modes, _, _ = dock(receptor, ligand, centre, (size,) * 3,
                           out / ("box%d.pdbqt" % size),
                           seed=SEED, exhaustiveness=EXHAUSTIVENESS,
                           log_path=out / "logs" / ("box%d.log" % size))
        scores[size] = modes[0][1]
        line = "  %2d A cube   best %8.3f   exit status 0, no warning" % (size, modes[0][1])
        if args.system == "synthetic":
            line += "   book %.3f" % BOOK[size]
        print(line)

    print("\nNo error at any size. The undersized box returns a number, and the")
    print("number is the only sign that anything was wrong.")

    if args.system == "synthetic":
        worst = max(abs(scores[s] - BOOK[s]) for s in SIZES)
        print("\n  largest difference from the book: %.3f kcal/mol" % worst)
        if is_reference_platform():
            print("  This is the book's reference platform, so anything above")
            print("  0.001 is a real disagreement and must be investigated, not")
            print("  tuned away.")
        else:
            print("  This is not the book's reference platform (Linux). Windows")
            print("  RDKit gives a different MMFF conformer and the Windows Vina")
            print("  build scores differently even on identical input files, so")
            print("  a difference of this size is expected. See build-record/PROGRESS.md.")

    result = {"system": args.system, "seed": SEED,
              "exhaustiveness": EXHAUSTIVENESS,
              "scores": {str(k): v for k, v in scores.items()},
              "book": {str(k): v for k, v in BOOK.items()} if args.system == "synthetic" else None,
              "reference_platform": is_reference_platform()}
    (out / "box_sweep.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("\nwrote %s" % (out / "box_sweep.json"))


if __name__ == "__main__":
    main()
