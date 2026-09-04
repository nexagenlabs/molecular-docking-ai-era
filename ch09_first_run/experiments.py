#!/usr/bin/env python3
"""Chapter 9's four demonstrations, run against the prepared inputs.

    1. The seed.          Vina's default is 0, which means random.
    2. Exhaustiveness.    What the cost of 8 versus 32 actually is.
    3. The box.           What a box too small for the ligand does.
    4. Mode 1's RMSD.     Why 0.000 is not a validation result.

Writes outputs/results.md and outputs/results.json, plus one log per run.
Compare against outputs/expected/results.md.
"""
import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CH = Path(__file__).resolve().parent
OUT = CH / "outputs"
LOGS = OUT / "logs"

# Fixed everywhere except where an experiment varies them.
SEED = 42
EXHAUSTIVENESS = 8      # Vina's default, and the baseline for experiment 3
CPU = 4                 # the book's timings are on 4 cores
BOX_SIZES = (20, 12, 8)


def find_vina():
    """Locate Vina 1.2.7: $VINA, then the repo's .tools, then PATH."""
    import os
    candidates = [os.environ.get("VINA"),
                  str(REPO / ".tools" / "vina.exe"),
                  str(REPO / ".tools" / "vina"),
                  shutil.which("vina")]
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("Vina not found. Set $VINA, or see environment/README.md.")


def vina_version(vina):
    out = subprocess.run([vina, "--version"], capture_output=True, text=True).stdout
    return out.strip().splitlines()[0] if out.strip() else "unknown"


def dock(vina, tag, centre, size, seed, exhaustiveness, cpu=CPU):
    """One Vina run. Returns (best affinity, wall seconds, output path, log)."""
    LOGS.mkdir(parents=True, exist_ok=True)
    out_pdbqt = OUT / ("pose_%s.pdbqt" % tag)
    cmd = [vina,
           "--receptor", str(OUT / "receptor.pdbqt"),
           "--ligand", str(OUT / "ligand.pdbqt"),
           "--center_x", "%.3f" % centre[0],
           "--center_y", "%.3f" % centre[1],
           "--center_z", "%.3f" % centre[2],
           "--size_x", str(size[0]), "--size_y", str(size[1]), "--size_z", str(size[2]),
           # The seed is never left to the default. Vina's default is 0, which
           # means "pick one at random", and nothing in the log says which.
           "--seed", str(seed),
           "--exhaustiveness", str(exhaustiveness),
           "--cpu", str(cpu),
           "--out", str(out_pdbqt)]
    started = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    log = result.stdout + result.stderr
    (LOGS / ("%s.log" % tag)).write_text(log)
    if result.returncode != 0:
        print(log)
        sys.exit("vina failed for %s" % tag)
    modes = parse_modes(log)
    if not modes:
        print(log)
        sys.exit("no docking modes parsed for %s" % tag)
    return modes, elapsed, out_pdbqt, log


def parse_modes(log):
    """Rows of the affinity table: (mode, affinity, rmsd_lb, rmsd_ub)."""
    modes = []
    for line in log.splitlines():
        m = re.match(r"\s*(\d+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s*$", line)
        if m:
            modes.append((int(m.group(1)), float(m.group(2)),
                          float(m.group(3)), float(m.group(4))))
    return modes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true",
                    help="skip the exhaustiveness-32 timing run")
    args = ap.parse_args()

    inputs = json.loads((OUT / "inputs.json").read_text())
    centre = inputs["box"]["centre"]
    vina = find_vina()
    version = vina_version(vina)
    print("Vina: %s  (%s)" % (version, vina))
    print("box centre: %.3f %.3f %.3f\n" % tuple(centre))
    results = {"vina_version": version,
               "platform": platform.platform(),
               "python": platform.python_version(),
               "box_centre": centre,
               "cpu": CPU}

    # -- 1. the seed ---------------------------------------------------------
    # Two runs at the default seed differ. Two at a fixed seed are identical,
    # byte for byte. Nothing in either log distinguishes the two situations,
    # which is why an unrecorded seed makes a protocol unrepeatable.
    print("1. THE SEED")
    seed_runs = {}
    for seed in (0, 42):
        for repeat in (1, 2):
            tag = "seed%d_run%d" % (seed, repeat)
            modes, _, pose, _ = dock(vina, tag, centre, (20, 20, 20), seed, EXHAUSTIVENESS)
            seed_runs[tag] = {"best": modes[0][1], "sha256_16": digest(pose)}
            print("   seed %-2d run %d   best %8.3f   pose sha256[:16] %s"
                  % (seed, repeat, modes[0][1], seed_runs[tag]["sha256_16"]))
    seed0_same = seed_runs["seed0_run1"]["sha256_16"] == seed_runs["seed0_run2"]["sha256_16"]
    seed42_same = seed_runs["seed42_run1"]["sha256_16"] == seed_runs["seed42_run2"]["sha256_16"]
    print("   seed 0  twice -> %s" % ("IDENTICAL" if seed0_same else "different"))
    print("   seed 42 twice -> %s" % ("byte-identical" if seed42_same else "DIFFERENT"))
    results["seed"] = {"runs": seed_runs,
                       "seed0_reproducible": seed0_same,
                       "seed42_reproducible": seed42_same}

    # -- 2. exhaustiveness ---------------------------------------------------
    print("\n2. EXHAUSTIVENESS (%d cores)" % CPU)
    exhaustiveness = {}
    for value in (8,) if args.quick else (8, 32):
        modes, elapsed, _, _ = dock(vina, "exh%d" % value, centre, (20, 20, 20),
                                    SEED, value)
        exhaustiveness[value] = {"seconds": round(elapsed, 2), "best": modes[0][1]}
        print("   exhaustiveness %-2d   %6.2f s   best %8.3f" % (value, elapsed, modes[0][1]))
    if 32 in exhaustiveness:
        ratio = exhaustiveness[32]["seconds"] / exhaustiveness[8]["seconds"]
        print("   factor %.1f -- wall time, so it varies with the machine; the"
              " ratio is the claim that travels" % ratio)
        exhaustiveness["ratio"] = round(ratio, 2)
    results["exhaustiveness"] = exhaustiveness

    # -- 3. the box ----------------------------------------------------------
    # A box too small to hold the ligand raises no error. It returns a worse
    # score that looks exactly like a result, and the only sign is the number.
    print("\n3. BOX SIZE (cubes, seed %d, exhaustiveness %d)" % (SEED, EXHAUSTIVENESS))
    print("   ligand's longest interatomic distance: %.2f A"
          % inputs["box"]["longest_interatomic_distance"])
    box = {}
    for size in BOX_SIZES:
        modes, _, _, _ = dock(vina, "box%d" % size, centre, (size,) * 3,
                              SEED, EXHAUSTIVENESS)
        box[size] = {"best": modes[0][1], "error_raised": False}
        fits = size >= inputs["box"]["longest_interatomic_distance"]
        print("   %2d A cube   best %8.3f   exit status 0, no warning   "
              "(cube %s hold the ligand in any orientation)"
              % (size, modes[0][1], "can" if fits else "CANNOT"))
    results["box"] = box

    # -- 4. mode 1's RMSD ----------------------------------------------------
    # Mode 1 reports 0.000 0.000 because the column is distance from mode 1.
    # It is not a comparison with a crystal pose, and reading it as one is the
    # single most common way a docking run appears to validate itself.
    print("\n4. MODE 1 RMSD")
    modes, _, _, _ = dock(vina, "modes", centre, (20, 20, 20), SEED, EXHAUSTIVENESS)
    for mode, affinity, lb, ub in modes[:3]:
        print("   mode %d   affinity %8.3f   rmsd l.b. %5.3f   u.b. %5.3f"
              % (mode, affinity, lb, ub))
    mode1_zero = modes[0][2] == 0.0 and modes[0][3] == 0.0
    print("   mode 1 reports 0.000 0.000: distance from mode 1, not from a"
          " crystal pose.")
    print("   Chapter 17 measures the distance that matters, with spyrmsd and"
          " no superposition.")
    results["modes"] = [{"mode": m, "affinity": a, "rmsd_lb": lb, "rmsd_ub": ub}
                        for m, a, lb, ub in modes]
    results["mode1_rmsd_is_zero"] = mode1_zero

    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    write_report(results, inputs)
    print("\nwrote %s and %s" % (OUT / "results.json", OUT / "results.md"))
    print("compare against %s" % (OUT / "expected" / "results.md"))


def write_report(results, inputs):
    exh = results["exhaustiveness"]
    box = results["box"]
    lines = [
        "# Chapter 9 - results from this machine",
        "",
        "| | |",
        "|---|---|",
        "| Vina | %s |" % results["vina_version"],
        "| Platform | %s |" % results["platform"],
        "| Python | %s |" % results["python"],
        "| Cores | %d |" % results["cpu"],
        "| Box centre | %.3f %.3f %.3f |" % tuple(results["box_centre"]),
        "| Receptor | 1L2S chain %s, waters deleted, %d side chains typed as ALA |"
        % (inputs["receptor"]["chain"], len(inputs["receptor"]["side_chains_typed_as_ala"])),
        "| Ligand | %s, formal charge %+d |"
        % (inputs["ligand"]["file"], inputs["ligand"]["formal_charge"]),
        "",
        "## 1. The seed",
        "",
        "| Run | Best affinity | Pose digest |",
        "|---|---|---|",
    ]
    for tag, run in results["seed"]["runs"].items():
        lines.append("| %s | %.3f | `%s` |" % (tag, run["best"], run["sha256_16"]))
    lines += [
        "",
        "- seed 0 twice: **%s**" % ("identical" if results["seed"]["seed0_reproducible"]
                                    else "different"),
        "- seed 42 twice: **%s**" % ("byte-identical"
                                     if results["seed"]["seed42_reproducible"] else "different"),
        "",
        "Vina's default seed is 0, which means random. Nothing in the log says",
        "which seed was actually used, so a run at the default cannot be repeated",
        "even by the person who made it.",
        "",
        "## 2. Exhaustiveness",
        "",
        "| Exhaustiveness | Wall time (s) | Best affinity |",
        "|---|---|---|",
    ]
    for value in (8, 32):
        if value in exh:
            lines.append("| %d | %.2f | %.3f | " % (value, exh[value]["seconds"],
                                                    exh[value]["best"]))
    if "ratio" in exh:
        lines += ["", "Cost factor **%.1f** on %d cores. Wall time depends on the"
                  % (exh["ratio"], results["cpu"]),
                  "machine; the ratio is what travels."]
    lines += [
        "",
        "## 3. Box size",
        "",
        "Ligand's longest interatomic distance: **%.2f A**. A cube smaller than"
        % inputs["box"]["longest_interatomic_distance"],
        "that cannot hold it in every orientation.",
        "",
        "| Cube edge | Best affinity | Error raised? |",
        "|---|---|---|",
    ]
    for size in BOX_SIZES:
        lines.append("| %d A | %.3f | no |" % (size, box[size]["best"]))
    lines += [
        "",
        "**No error is raised at any size.** The undersized box returns a number",
        "that looks like a result.",
        "",
        "## 4. Mode 1's RMSD",
        "",
        "| Mode | Affinity | RMSD l.b. | RMSD u.b. |",
        "|---|---|---|---|",
    ]
    for m in results["modes"][:5]:
        lines.append("| %d | %.3f | %.3f | %.3f |"
                     % (m["mode"], m["affinity"], m["rmsd_lb"], m["rmsd_ub"]))
    lines += [
        "",
        "Mode 1 reports `0.000 0.000` because the column is distance from mode 1.",
        "It says nothing about the crystal pose. Chapter 17 measures that, with",
        "spyrmsd, symmetry-corrected, and without superposition.",
        "",
    ]
    (OUT / "results.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
