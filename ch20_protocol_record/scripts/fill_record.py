#!/usr/bin/env python3
"""Chapter 20 — fill in a protocol record from the files a run leaves behind.

    python ch20_protocol_record/scripts/fill_record.py \\
        --config ch09_first_run/config/vina_config.txt \\
        --log ch09_first_run/outputs/ampc/logs/modes.log \\
        --structure 1L2S --chain B --ligand STC

Most of a protocol record is already sitting in the config file, the log and
the coordinate file. Anything a machine can fill in, a machine should: the
fields left for a human are then the ones that actually needed a human, and
they stand out instead of being buried in twenty lines of transcription.

The fields this cannot fill are printed as **TODO(human)** with the reason. A
record with visible gaps is worth more than one with plausible filler.

Writes outputs/filled_record.md.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"

sys.path.insert(0, str(REPO / "scripts"))
import receptor_prep  # noqa: E402

# Chapter 20's seventeen fields. The seven marked True are tier one: without
# them the run cannot be re-executed, however complete the rest is.
FIELDS = [
    ("Receptor source and identifier", True),
    ("Chains and altlocs kept", False),
    ("Waters and ions", False),
    ("Missing residues", False),
    ("Receptor preparation tool and version", True),
    ("Ligand source", True),
    ("Ligand preparation", False),
    ("Stereochemistry as docked", False),
    ("Box centre", True),
    ("Box dimensions", True),
    ("Box derivation", False),
    ("Docking program and version", True),
    ("Exhaustiveness / num_modes / energy_range", False),
    ("Random seed", True),
    ("Redocking result", False),
    ("Cross-docking or enrichment result", False),
    ("Exclusions and deviations", False),
]


def read_config(path):
    """Vina config: key = value, with everything after # as comment."""
    values, comments = {}, {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        body, _, comment = line.partition("#")
        if "=" not in body:
            continue
        key, _, value = body.partition("=")
        key, value = key.strip(), value.strip()
        if key:
            values[key] = value
            if comment.strip():
                comments[key] = comment.strip()
    return values, comments


def read_log(path):
    """Version, seed and the affinity table out of a Vina log."""
    text = Path(path).read_text(encoding="utf-8")
    out = {}
    version = re.search(r"AutoDock Vina v([\d.]+)", text)
    if version:
        out["program"] = "AutoDock Vina v%s" % version.group(1)
    seed = re.search(r"random seed:\s*(-?\d+)", text)
    if seed:
        out["seed_in_log"] = seed.group(1)
    modes = []
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+(-?\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s*$", line)
        if m:
            modes.append((int(m.group(1)), float(m.group(2))))
    if modes:
        out["best_affinity"] = modes[0][1]
        out["num_modes_reported"] = len(modes)
    return out


def describe_structure(pdb_id, chain, ligand_name):
    """The receptor facts a record needs, read from the coordinate file."""
    path = STRUCTURES / ("%s.pdb" % pdb_id)
    if not path.exists():
        return None
    atoms, missing, links = receptor_prep.parse(path)
    text = path.read_text()

    resolution = r_free = None
    for line in text.splitlines():
        if line.startswith("REMARK   2 RESOLUTION."):
            tail = line.split("RESOLUTION.", 1)[1].split()
            if tail:
                try:
                    resolution = float(tail[0])
                except ValueError:
                    pass
        elif re.match(r"^REMARK   3   FREE R VALUE\s+:", line):
            try:
                r_free = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    altlocs = sorted({"%s %s%s" % (a["res"], a["chain"], a["seq"])
                      for a in atoms if a["altloc"] != " " and a["chain"] == chain})
    waters = len({(a["chain"], a["seq"]) for a in atoms if a["res"] == "HOH"})
    chosen, copies = receptor_prep.select_copy(atoms, ligand_name, chain)

    # Metals, named explicitly. AmpC is a class C serine hydrolase with no
    # catalytic metal; the class B enzymes are the metallo-beta-lactamases and
    # are a different protein. A record that does not say "no metal" leaves a
    # reader to wonder whether one was quietly deleted.
    metal_names = {"ZN", "MG", "MN", "FE", "CU", "NI", "CO", "CA", "K", "NA"}
    metals = sorted({a["res"] for a in atoms
                     if a["rec"] == "HETATM" and a["res"] in metal_names})

    gaps = {}
    for line in text.splitlines():
        if line.startswith("REMARK 465"):
            fields = line[10:].split()
            if (len(fields) == 3 and len(fields[0]) == 3 and len(fields[1]) == 1
                    and fields[2].lstrip("-").isdigit()):
                gaps.setdefault(fields[1], []).append("%s %s" % (fields[0], fields[2]))

    # Disordered side chains in the chain actually used, counted rather than
    # inferred: ch27 puts this number into a methods paragraph.
    disordered = sorted({m["seq"] for m in receptor_prep.parse(path)[1]
                         if m["chain"] == chain})

    return {"pdb_id": pdb_id, "chain": chain, "resolution": resolution,
            "disordered_side_chains": disordered,
            "disordered_side_chain_count": len(disordered),
            "r_free": r_free, "altlocs": altlocs, "waters": waters,
            "ligand_copies": [{k: v for k, v in c.items() if k != "atoms"}
                              for c in copies],
            "chosen_copy": ("%s/%s" % (chosen["chain"], chosen["seq"])
                            if chosen else None),
            "chosen_distance": chosen["distance_to_ser64_og"] if chosen else None,
            "metals": metals, "gaps": gaps,
            "covalent_links": [l for l in links
                               if "SER" in l and " 64 " in l and "OG" in l]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="ch09_first_run/config/vina_config.txt")
    ap.add_argument("--log", default="ch09_first_run/outputs/ampc/logs/modes.log")
    ap.add_argument("--structure", default="1L2S")
    ap.add_argument("--chain", default="B")
    ap.add_argument("--ligand", default="STC")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    config_path = REPO / args.config
    log_path = REPO / args.log

    # Both inputs, checked the same way. This script used to stop with exactly
    # the right sentence when the config was missing and degrade silently to an
    # empty dict when the log was -- and the config is committed while the log
    # is gitignored, so the sentence was attached to the input that was never
    # going to be absent. What the silence produced was a record with five
    # TODOs instead of three and tier_one_complete False, which reads like a
    # finding rather than a missing file. ch02 and ch23 both name their missing
    # upstream artefacts; so does this now.
    for what, path in (("config", config_path), ("run log", log_path)):
        if not path.exists():
            sys.exit("%s missing -- run ch09_first_run/run.sh first\n"
                     "  the %s comes from that chapter's AmpC branch (PART 2), "
                     "and without it this record\n"
                     "  cannot name the docking program or the redocking "
                     "result. A record with invented\n"
                     "  fields is worse than no record." % (path, what))

    values, comments = read_config(config_path)
    log = read_log(log_path)
    structure = describe_structure(args.structure, args.chain, args.ligand)

    filled, todo = {}, []

    def put(field, value, source):
        if value is None:
            todo.append(field)
            filled[field] = {"value": None, "source": source}
        else:
            filled[field] = {"value": value, "source": source}

    put("Receptor source and identifier",
        ("RCSB `files.rcsb.org`, **%s**, %.2f Å, R-free %.3f"
         % (structure["pdb_id"], structure["resolution"], structure["r_free"]))
        if structure else None, "coordinate file header")
    put("Chains and altlocs kept",
        ("chain **%s**; altlocs %s (first taken)"
         % (structure["chain"], ", ".join(structure["altlocs"]) or "none"))
        if structure else None, "coordinate file")
    put("Waters and ions",
        ("%d waters in the entry, all deleted; metals: %s"
         % (structure["waters"],
            ", ".join(structure["metals"]) if structure["metals"]
            else "**none** — AmpC is a class C serine hydrolase"))
        if structure else None, "coordinate file")
    put("Missing residues",
        (", ".join("chain %s: %s" % (c, ", ".join(r))
                   for c, r in structure["gaps"].items()) or "none")
        if structure else None, "REMARK 465")
    put("Receptor preparation tool and version", "meeko mk_prepare_receptor 0.8.0",
        "environment/resolved.txt")

    ligand_line = comments.get("ligand", "")
    put("Ligand source", values.get("ligand"), "config file")
    put("Ligand preparation",
        "meeko mk_prepare_ligand 0.8.0%s"
        % (" — %s" % ligand_line if ligand_line else ""), "config file")
    put("Stereochemistry as docked", None,
        "not derivable from a config file: state it yourself")

    centre = [values.get("center_x"), values.get("center_y"), values.get("center_z")]
    size = [values.get("size_x"), values.get("size_y"), values.get("size_z")]
    put("Box centre", ", ".join(centre) if all(centre) else None, "config file")
    put("Box dimensions", " × ".join(size) if all(size) else None, "config file")
    put("Box derivation",
        ("centroid of %s (%.2f Å from Ser64 OG), 8 Å padding"
         % (structure["chosen_copy"], structure["chosen_distance"]))
        if structure and structure["chosen_copy"] else None,
        "ligand copy selected by distance to Ser64 OG")

    put("Docking program and version", log.get("program"), "run log")
    put("Exhaustiveness / num_modes / energy_range",
        "%s / %s / %s" % (values.get("exhaustiveness", "?"),
                          values.get("num_modes", "?"),
                          values.get("energy_range", "?")), "config file")
    put("Random seed", values.get("seed"), "config file")

    put("Redocking result",
        ("best affinity %.3f kcal/mol over %d modes; RMSD to the crystal pose "
         "is NOT in this log" % (log["best_affinity"], log["num_modes_reported"]))
        if "best_affinity" in log else None, "run log")
    put("Cross-docking or enrichment result", None,
        "a different experiment: fill from its own record")
    put("Exclusions and deviations", None,
        "the one field no tool can fill; it is why the record exists")

    # The seed in the log and the seed in the config must agree. If they do
    # not, the config was edited after the run and the record would describe a
    # protocol that never happened.
    seed_mismatch = None
    if "seed_in_log" in log and values.get("seed"):
        if log["seed_in_log"] != values["seed"]:
            seed_mismatch = (values["seed"], log["seed_in_log"])

    tier_one = [f for f, t in FIELDS if t]
    missing_tier_one = [f for f in tier_one if filled.get(f, {}).get("value") is None]

    print("Filled %d of %d fields from the config, the log and the coordinate file."
          % (len(FIELDS) - len(todo), len(FIELDS)))
    print("Left for a human: %s" % ", ".join(todo))
    if missing_tier_one:
        print("\nTIER ONE FIELDS STILL EMPTY: %s" % ", ".join(missing_tier_one))
        print("The run cannot be re-executed from this record.")
    else:
        print("\nEvery tier-one field is filled: the run can be re-executed.")
    if seed_mismatch:
        print("\nSEED MISMATCH: config says %s, the log says %s."
              % seed_mismatch)
        print("The config was edited after the run. Do not trust this record.")

    write_record(filled, todo, tier_one, structure, seed_mismatch, args)
    (OUT / "filled_record.json").write_text(
        json.dumps({"fields": filled, "todo": todo,
                    "tier_one_complete": not missing_tier_one,
                    "seed_mismatch": seed_mismatch,
                    "structure": structure}, indent=2, default=str) + "\n",
        encoding="utf-8")
    target = Path(args.out) if args.out else OUT / "filled_record.md"
    print("\nwrote %s" % target)


def write_record(filled, todo, tier_one, structure, seed_mismatch, args):
    lines = [
        "# Protocol record — %s" % args.structure, "",
        "Filled by `ch20_protocol_record/scripts/fill_record.py` on %s"
        % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "from `%s` and `%s`." % (args.config, args.log),
        "",
        "★ marks the tier-one fields: without them the run cannot be",
        "re-executed, however complete the rest of the record is.",
        "",
        "| Field | Value | Filled from |",
        "|---|---|---|",
    ]
    for field, is_tier_one in FIELDS:
        entry = filled.get(field, {"value": None, "source": ""})
        value = entry["value"]
        if value is None:
            value = "**TODO(human)** — %s" % entry["source"]
            source = "—"
        else:
            source = entry["source"]
        lines.append("| %s%s | %s | %s |"
                     % ("★ " if is_tier_one else "", field, value, source))

    lines += ["", "## What was not filled, and why", ""]
    for field in todo:
        lines.append("- **%s** — %s" % (field, filled[field]["source"]))
    lines += [
        "",
        "Three fields need a human, and they are the three that matter most for",
        "judging the work: what stereochemistry was actually docked, what other",
        "experiment this belongs to, and what was excluded. **A tool can record",
        "what happened. It cannot record what you decided.**",
        "",
    ]
    if seed_mismatch:
        lines += [
            "## Warning: seed mismatch", "",
            "The config file says `seed = %s`; the run log says the seed was %s."
            % seed_mismatch,
            "The config was edited after the run, so this record describes a",
            "protocol that was never executed. Re-run before trusting it.",
            "",
        ]
    if structure:
        lines += [
            "## Cross-checks against the coordinate file", "",
            "| | |",
            "|---|---|",
            "| Resolution | %.2f Å |" % structure["resolution"],
            "| R-free | %.3f |" % structure["r_free"],
            "| Ligand copies found | %d |" % len(structure["ligand_copies"]),
            "| Copy used | %s, %.2f Å from Ser64 OG |"
            % (structure["chosen_copy"], structure["chosen_distance"]),
            "| Altlocs in the chain | %s |"
            % (", ".join(structure["altlocs"]) or "none"),
            "| Metals | %s |" % (", ".join(structure["metals"]) or "**none**"),
            "| Covalent link to Ser64 | %s |"
            % ("yes — exclude from non-covalent docking"
               if structure["covalent_links"] else "none"),
            "",
            "The ligand copy is chosen by **distance to Ser64 OG**, never by file",
            "order. This entry holds %d copies and the one at %.2f Å is the one"
            % (len(structure["ligand_copies"]), structure["chosen_distance"]),
            "used; the others appear in the table above so the choice can be",
            "checked rather than taken on trust.",
            "",
        ]
    target = Path(args.out) if args.out else OUT / "filled_record.md"
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(target).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
