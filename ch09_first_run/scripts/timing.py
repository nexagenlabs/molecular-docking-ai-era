#!/usr/bin/env python3
"""What exhaustiveness costs.

    python ch09_first_run/scripts/timing.py [--system synthetic|ampc]

Measures exhaustiveness 8 against 32 on four cores and reports the ratio.

Absolute times are hardware-specific and will not match the book. The ratio is
the part that travels, and even that is not the factor of 4 the exhaustiveness
ratio suggests, because grid computation is a fixed cost that does not scale
with the search. That fixed cost is a larger share of the short run on a faster
machine, so the ratio *falls* as hardware improves: 4.18 on the book's machine,
3.34 on Windows, 2.80 on Ubuntu 24.04. Only 1.5 < ratio < 4.0 holds everywhere,
4.0 being exact linearity. Record your own number; do not tune to any of these.
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
from docking_common import dock, platform_banner, vina_version  # noqa: E402

CPU = 4          # the book's timings are on four cores
SEED = 42
LEVELS = (8, 32)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    systems.add_argument(ap)
    ap.add_argument("--repeats", type=int, default=1,
                    help="repeat each level and take the fastest run")
    args = ap.parse_args()

    receptor, ligand, centre = systems.get(args.system)
    out = Path(receptor).parent
    print("Vina: %s" % vina_version())
    print(platform_banner())
    print("system: %s, %d cores, seed %d\n" % (args.system, CPU, SEED))

    timings = {}
    for level in LEVELS:
        best = None
        for repeat in range(args.repeats):
            modes, elapsed, _ = dock(receptor, ligand, centre, (20, 20, 20),
                                     out / ("timing_exh%d.pdbqt" % level),
                                     seed=SEED, exhaustiveness=level, cpu=CPU,
                                     log_path=out / "logs" / ("timing_exh%d.log" % level))
            if best is None or elapsed < best[1]:
                best = (modes[0][1], elapsed)
        timings[level] = {"seconds": round(best[1], 2), "best_affinity": best[0]}
        print("  exhaustiveness %-2d   %6.2f s   best %8.3f"
              % (level, best[1], best[0]))

    ratio = timings[32]["seconds"] / timings[8]["seconds"]
    print("\n  ratio %.1f" % ratio)
    print("\nFour times the exhaustiveness does not cost four times the time, and")
    print("on a fast machine it can cost rather less: the grid is computed once")
    print("whatever the search does. Absolute seconds belong to the machine they")
    print("were measured on; only the ratio is worth quoting.")

    if not 1.5 < ratio < 4.0:
        print("\nNOTE: ratio %.1f is outside 1.5-4.0, the band that has held on" % ratio)
        print("every machine measured. Below 1.5, quadrupling exhaustiveness barely")
        print("cost anything; at or above 4.0 no fixed cost is being amortised at")
        print("all. Either way, record the measurement; do not tune the script.")

    result = {"system": args.system, "cpu": CPU, "timings": timings,
              "ratio": round(ratio, 2)}
    (out / "timing.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("\nwrote %s" % (out / "timing.json"))


if __name__ == "__main__":
    main()
