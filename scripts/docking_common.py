#!/usr/bin/env python3
"""Helpers shared by the chapter scripts: finding tools, running Vina, and
saying plainly which platform a number came from.

Kept in one place because every chapter needs the same three things and a
second copy of "find the Vina binary" is a second place for it to go wrong.
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Vina's default seed is 0, which means random. Two runs at the default differ
# and nothing in the log says so, so every call in this repository passes a seed
# explicitly and records it.
DEFAULT_SEED = 42


def find_vina():
    """Locate Vina 1.2.7: $VINA, then the repository's .tools, then PATH."""
    for candidate in (os.environ.get("VINA"),
                      REPO / ".tools" / "vina.exe",
                      REPO / ".tools" / "vina",
                      REPO / ".tools" / "vina_linux",
                      shutil.which("vina")):
        if candidate and Path(candidate).exists():
            return str(candidate)
    sys.exit("Vina not found. Set $VINA, or see environment/README.md.")


def find_tool(name):
    """Locate a console script from the virtual environment, then PATH."""
    for candidate in (REPO / ".venv" / "Scripts" / (name + ".exe"),
                      REPO / ".venv" / "bin" / name):
        if candidate.exists():
            return str(candidate)
    found = shutil.which(name) or shutil.which(name + ".py")
    if found is None:
        sys.exit("%s not found. See environment/README.md." % name)
    return found


def vina_version(vina=None):
    vina = vina or find_vina()
    out = subprocess.run([vina, "--version"], capture_output=True, text=True).stdout
    return out.strip().splitlines()[0] if out.strip() else "unknown"


def parse_modes(log):
    """Rows of Vina's affinity table: (mode, affinity, rmsd_lb, rmsd_ub).

    Mode 1's RMSD columns are 0.000 0.000 by construction -- they are the
    distance from mode 1, not from any crystal pose. See ch17 for the distance
    that actually tests a redock.
    """
    modes = []
    for line in log.splitlines():
        m = re.match(r"\s*(\d+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s*$", line)
        if m:
            modes.append((int(m.group(1)), float(m.group(2)),
                          float(m.group(3)), float(m.group(4))))
    return modes


def dock(receptor, ligand, centre, size, out_pdbqt, seed=DEFAULT_SEED,
         exhaustiveness=8, cpu=None, vina=None, log_path=None, extra=()):
    """Run Vina once. Returns (modes, wall_seconds, log)."""
    vina = vina or find_vina()
    cmd = [vina,
           "--receptor", str(receptor),
           "--ligand", str(ligand),
           "--center_x", "%.3f" % centre[0],
           "--center_y", "%.3f" % centre[1],
           "--center_z", "%.3f" % centre[2],
           "--size_x", str(size[0]), "--size_y", str(size[1]), "--size_z", str(size[2]),
           "--seed", str(seed),
           "--exhaustiveness", str(exhaustiveness),
           "--out", str(out_pdbqt)]
    if cpu is not None:
        cmd += ["--cpu", str(cpu)]
    cmd += list(extra)
    started = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    log = result.stdout + result.stderr
    if log_path is not None:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(log, encoding="utf-8")
    if result.returncode != 0:
        print(log)
        sys.exit("vina failed: " + " ".join(cmd))
    modes = parse_modes(log)
    if not modes:
        print(log)
        sys.exit("no docking modes parsed")
    return modes, elapsed, log


# -- platform ---------------------------------------------------------------
#
# The book's three-decimal values were measured on Linux, and they are not
# portable to that precision. Measured on this repository's synthetic system,
# same Vina 1.2.7, same meeko 0.8.0, same RDKit 2026.3.5:
#
#   native Linux    -4.905 / -4.911 / -2.748   <- the book
#   native Windows  -4.910 / -4.903 / -2.686
#
# Two independent causes, both established by experiment rather than argument:
# the Windows RDKit build's MMFF optimisation lands on a slightly different
# conformer, and the Windows Vina build scores differently even when handed the
# Linux conformer. Seed 42 gives byte-identical results within a build. It does
# not give identical results across builds, and nothing in the log says so.

EXACT_VALUES_PLATFORM = "linux"


def is_reference_platform():
    """True when three-decimal values from the book should reproduce exactly."""
    return sys.platform.startswith(EXACT_VALUES_PLATFORM)


def platform_banner():
    if is_reference_platform():
        return ("Platform: %s -- the book's three-decimal values should"
                " reproduce exactly here." % platform.platform())
    return ("Platform: %s -- NOT the book's reference platform (Linux).\n"
            "  Expect agreement in behaviour and to roughly two decimals, not"
            " to three.\n"
            "  See scripts/docking_common.py for the measurements behind that"
            " statement." % platform.platform())
