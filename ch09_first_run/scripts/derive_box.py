#!/usr/bin/env python3
"""Write the AmpC docking box into config/vina_config.txt.

    python ch09_first_run/scripts/derive_box.py

The box centre is computed from the reference ligand's centroid and written
into the config file, so that what ends up in the config was calculated rather
than typed. A typed centre is a centre nobody can check.

Requires ch09_first_run/outputs/ampc/inputs.json, from prepare_ampc.py.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
INPUTS = CH / "outputs" / "ampc" / "inputs.json"
CONFIG = CH / "config" / "vina_config.txt"

# Vina's defaults, stated rather than inherited. num_modes and energy_range are
# Vina's own defaults; exhaustiveness 32 is this chapter's choice for the AmpC
# run, against the default 8 used for the box sweep so that the sweep isolates
# the box.
NUM_MODES = 9
ENERGY_RANGE = 3
EXHAUSTIVENESS = 32
SEED = 42
PADDING = 8.0


def main():
    if not INPUTS.exists():
        sys.exit("%s missing -- run scripts/prepare_ampc.py first" % INPUTS)
    inputs = json.loads(INPUTS.read_text())
    box = inputs["box"]
    centre = box["centre"]
    size = box["derived_size_at_8A_padding"]
    ref = inputs["reference_pose"]

    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Vina configuration for the AmpC run in Chapter 9.",
        "#",
        "# Written by scripts/derive_box.py on %s."
        % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "# Every value carries where it came from. Edit derive_box.py, not this",
        "# file: a hand-edited centre is a centre that no longer matches the",
        "# ligand it was supposed to be derived from.",
        "",
        "receptor = ../outputs/ampc/receptor.pdbqt   # 1L2S chain B; chain A is missing Lys290-Ala292",
        "ligand = ../outputs/ampc/ligand.pdbqt       # from data/ligands/STC.sdf, formal charge -1",
        "",
        "# Centroid of STC %s, the copy %.2f A from Ser64 OG. Selected by that"
        % (ref["copy"], ref["distance_to_ser64_og"]),
        "# distance, not by file order: 1L2S also holds a copy 22.7 A away, at a",
        "# chain interface, and nothing in the file marks which is which.",
        "center_x = %.3f" % centre[0],
        "center_y = %.3f" % centre[1],
        "center_z = %.3f" % centre[2],
        "",
        "# Ligand extent %.2f x %.2f x %.2f A, plus %.0f A padding on each side."
        % (box["ligand_extent"][0], box["ligand_extent"][1], box["ligand_extent"][2],
           PADDING),
        "# The ligand's longest interatomic distance is %.2f A; a box smaller than"
        % box["longest_interatomic_distance"],
        "# that cannot hold it in every orientation, and Vina raises no error.",
        "size_x = %.2f" % size[0],
        "size_y = %.2f" % size[1],
        "size_z = %.2f" % size[2],
        "",
        "# Vina's default seed is 0, which means random. Two runs at the default",
        "# differ, two at a fixed seed are byte-identical, and nothing in the log",
        "# tells them apart. This line is the difference between a protocol and",
        "# an anecdote.",
        "seed = %d" % SEED,
        "",
        "exhaustiveness = %d   # this chapter's choice for AmpC; the box sweep uses Vina's default 8" % EXHAUSTIVENESS,
        "num_modes = %d        # Vina's default" % NUM_MODES,
        "energy_range = %d     # Vina's default, kcal/mol" % ENERGY_RANGE,
        "",
    ]
    CONFIG.write_text("\n".join(lines))
    print("box centre %.3f %.3f %.3f, size %.2f x %.2f x %.2f"
          % (centre[0], centre[1], centre[2], size[0], size[1], size[2]))
    print("derived from the centroid of STC %s (%.2f A from Ser64 OG)"
          % (ref["copy"], ref["distance_to_ser64_og"]))
    print("wrote %s" % CONFIG)


if __name__ == "__main__":
    main()
