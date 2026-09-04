#!/usr/bin/env python3
"""Show that Vina's default seed is random and that a fixed seed is not.

    python ch09_first_run/scripts/verify_run.py [--system synthetic|ampc]

Runs twice at seed 0 and twice at seed 42, and prints both outcomes side by
side. The point is meant to be visible, not merely asserted: the two seed-0
digests differ, the two seed-42 digests are the same, and the logs give no
indication that anything different happened.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(CH / "scripts"))

import systems  # noqa: E402
from docking_common import dock, platform_banner, vina_version  # noqa: E402

EXHAUSTIVENESS = 8


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    systems.add_argument(ap)
    args = ap.parse_args()

    receptor, ligand, centre = systems.get(args.system)
    out = Path(receptor).parent
    print("Vina: %s" % vina_version())
    print(platform_banner())
    print("system: %s\n" % args.system)

    runs = {}
    for seed in (0, 42):
        for repeat in (1, 2):
            tag = "seed%d_run%d" % (seed, repeat)
            pose = out / ("verify_%s.pdbqt" % tag)
            modes, _, _ = dock(receptor, ligand, centre, (20, 20, 20), pose,
                               seed=seed, exhaustiveness=EXHAUSTIVENESS,
                               log_path=out / "logs" / (tag + ".log"))
            runs[tag] = {"best": modes[0][1], "sha256": digest(pose)}
            print("  seed %-2d run %d   best %8.3f   sha256 %s"
                  % (seed, repeat, modes[0][1], runs[tag]["sha256"][:16]))

    seed0_same = runs["seed0_run1"]["sha256"] == runs["seed0_run2"]["sha256"]
    seed42_same = runs["seed42_run1"]["sha256"] == runs["seed42_run2"]["sha256"]
    print("\n  seed 0  twice -> %s" % ("IDENTICAL" if seed0_same else "different"))
    print("  seed 42 twice -> %s" % ("byte-identical" if seed42_same else "DIFFERENT"))
    print("\nVina's default seed is 0, and 0 means 'choose one at random'. Neither")
    print("log records which seed was actually used, so a run at the default")
    print("cannot be repeated even by the person who made it.")

    result = {"system": args.system, "runs": runs,
              "seed0_reproducible": seed0_same, "seed42_reproducible": seed42_same}
    (out / "verify_run.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("\nwrote %s" % (out / "verify_run.json"))

    # A failure here is a real one: it would mean the seed does not control the
    # search, and nothing else in this repository could be trusted to repeat.
    if not seed42_same:
        sys.exit("seed 42 did not reproduce -- stop and investigate")
    if seed0_same:
        print("\nNOTE: the two seed-0 runs came out identical. That can happen by")
        print("chance on a small search space; run again before concluding")
        print("anything from it.")


if __name__ == "__main__":
    main()
