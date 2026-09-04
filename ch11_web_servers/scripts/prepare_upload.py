#!/usr/bin/env python3
"""Chapter 11 — web servers: what you can upload, and what you cannot record.

    python ch11_web_servers/scripts/prepare_upload.py

Prepares the files a docking web server will accept, and then audits the
service against Chapter 20's seventeen protocol fields: which ones you can set,
which ones the server fixes without telling you, and which ones you cannot
record at all.

**No server is contacted.** Submitting to a third-party service is the user's
decision, not a script's, and an automated submission is also the fastest way
to violate a service's terms. What this produces is the upload set and the
audit; the upload itself is a human action.

Writes outputs/upload/ and outputs/server_audit.md.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
UPLOAD = OUT / "upload"
STRUCTURES = REPO / "data" / "structures"
LIGANDS = REPO / "data" / "ligands"

sys.path.insert(0, str(REPO / "scripts"))
import receptor_prep  # noqa: E402

CRYSTAL, CHAIN, LIGAND, PADDING = "1L2S", "B", "STC", 8.0

# Chapter 20's seventeen fields, against what a typical docking web server lets
# you control. "fixed" means the server decides and does not report the
# decision; "set" means you choose it; "recorded" means the result page tells
# you what was used.
#
# This is the audit that matters. A server is not worse than local software
# because it is remote -- it is worse because a field you cannot record is a
# field your protocol record cannot contain, and the seven tier-one fields are
# the ones that decide whether a run can be repeated at all.
AUDIT = [
    ("Receptor source and identifier", True, "you upload it", True),
    ("Chains and altlocs kept", False, "usually stripped or merged silently", False),
    ("Waters and ions", False, "removed by the server, rarely stated", False),
    ("Missing residues", False, "not reported", False),
    ("Receptor preparation tool and version", True, "the server's own, version rarely given", False),
    ("Ligand source", True, "you upload it", True),
    ("Ligand preparation", False, "server-side protonation, pH rarely stated", False),
    ("Stereochemistry as docked", False, "depends on what the server did to your file", False),
    ("Box centre", True, "usually settable", True),
    ("Box dimensions", True, "usually settable", True),
    ("Box derivation", True, "yours, if you computed it", True),
    ("Docking program and version", True, "named; exact version often not", False),
    ("Exhaustiveness / num_modes / energy_range", True, "sometimes settable", True),
    ("Random seed", False, "almost never settable, almost never reported", False),
    ("Redocking result", True, "yours to compute", True),
    ("Cross-docking or enrichment result", True, "yours to compute", True),
    ("Exclusions and deviations", True, "yours to write", True),
]

TIER_ONE = {"Receptor source and identifier", "Receptor preparation tool and version",
            "Ligand source", "Box centre", "Box dimensions",
            "Docking program and version", "Random seed"}


def main():
    UPLOAD.mkdir(parents=True, exist_ok=True)

    path = STRUCTURES / ("%s.pdb" % CRYSTAL)
    if not path.exists():
        sys.exit("%s missing -- run: bash data/structures/fetch.sh" % path)
    atoms, _, _ = receptor_prep.parse(path)

    # Receptor: one chain, no solvent, as PDB. Most servers take PDB and will
    # do their own conversion, so what you control is what is IN the file.
    kept = [a["line"] for a in atoms if a["rec"] == "ATOM" and a["chain"] == CHAIN
            and a["altloc"] in (" ", "A")]
    receptor = UPLOAD / ("%s_chain%s_clean.pdb" % (CRYSTAL, CHAIN))
    receptor.write_text("\n".join(kept) + "\nEND\n", encoding="utf-8")

    # Ligand: SDF, with the charge explicit. Never PDBQT -- the server will
    # make its own, and yours would only be a second chance to lose the charge.
    ligand_src = LIGANDS / ("%s.sdf" % LIGAND)
    if ligand_src.exists():
        shutil.copy(ligand_src, UPLOAD / ("%s.sdf" % LIGAND))

    copies = [c for c in receptor_prep.ligand_copies(atoms, LIGAND)
              if c["in_site"] and c["chain"] == CHAIN]
    centre, size, _ = receptor_prep.box_from_ligand(copies[0]["atoms"], PADDING)

    box = UPLOAD / "box.txt"
    box.write_text(
        "# Box for %s chain %s, from the centroid of %s %s/%s with %.0f A padding.\n"
        "# Paste these into the server's form. Compute them; do not eyeball them.\n"
        "center_x = %.3f\ncenter_y = %.3f\ncenter_z = %.3f\n"
        "size_x = %.2f\nsize_y = %.2f\nsize_z = %.2f\n"
        % (CRYSTAL, CHAIN, LIGAND, copies[0]["chain"], copies[0]["seq"], PADDING,
           centre[0], centre[1], centre[2], size[0], size[1], size[2]),
        encoding="utf-8")

    print("Upload set written to %s\n" % UPLOAD)
    for item in sorted(UPLOAD.iterdir()):
        print("   %-32s %6d bytes" % (item.name, item.stat().st_size))
    print("\n   receptor: chain %s only, altloc A, %d atoms, no solvent"
          % (CHAIN, len(kept)))
    print("   ligand:   SDF with explicit charge, NOT PDBQT -- the server makes")
    print("             its own, and yours would be a second chance to lose the")
    print("             formal charge")
    print("   box:      computed from the crystallographic ligand, not eyeballed")

    settable = [f for f, s, _, _ in AUDIT if s]
    recordable = [f for f, _, _, r in AUDIT if r]
    lost_tier_one = [f for f, _, _, r in AUDIT if not r and f in TIER_ONE]

    print("\nAgainst Chapter 20's seventeen fields:")
    print("   %d of 17 you can set" % len(settable))
    print("   %d of 17 the result page lets you record" % len(recordable))
    print("   %d TIER-ONE fields you cannot record: %s"
          % (len(lost_tier_one), ", ".join(lost_tier_one)))
    print("\n   The seed is the one that decides it. Almost no docking server")
    print("   lets you set a seed or tells you which one it used, so a server")
    print("   run cannot be repeated -- not by you, and not by the server.")
    print("\n   That does not make web servers useless. It makes them a way to")
    print("   get a look at a system, not a way to produce a result somebody")
    print("   else can check.")

    payload = {
        "upload_files": [p.name for p in sorted(UPLOAD.iterdir())],
        "receptor_atoms": len(kept),
        "box": {"centre": [round(c, 3) for c in centre], "size": list(size)},
        "audit": [{"field": f, "settable": s, "note": n, "recordable": r,
                   "tier_one": f in TIER_ONE} for f, s, n, r in AUDIT],
        "settable": len(settable),
        "recordable": len(recordable),
        "tier_one_not_recordable": lost_tier_one,
    }
    (OUT / "server_audit.json").write_text(json.dumps(payload, indent=2) + "\n",
                                           encoding="utf-8")
    write_report(payload)
    print("\nwrote %s" % (OUT / "server_audit.json"))


def write_report(payload):
    lines = [
        "# Chapter 11 — web servers", "",
        "## The upload set", "",
        "`outputs/upload/` holds what a docking server will accept:", "",
        "| File | What it is |",
        "|---|---|",
        "| `%s_chain%s_clean.pdb` | Chain %s only, altloc A, %d atoms, no solvent |"
        % (CRYSTAL, CHAIN, CHAIN, payload["receptor_atoms"]),
        "| `%s.sdf` | The ligand with its formal charge explicit |" % LIGAND,
        "| `box.txt` | Box centre and dimensions, computed |",
        "",
        "**The ligand goes up as SDF, not PDBQT.** The server will make its own",
        "PDBQT; sending one would only be a second opportunity to lose the formal",
        "charge, and the charge is the thing this series cannot afford to lose.",
        "",
        "**The box is computed, not eyeballed.** It is one of the few fields a",
        "server lets you control, so it is worth arriving with the number rather",
        "than dragging a cube around in a viewer.",
        "",
        "## The audit", "",
        "Against Chapter 20's seventeen protocol fields. ★ marks tier one.",
        "",
        "| Field | Can you set it? | Can you record it? | Note |",
        "|---|---|---|---|",
    ]
    for entry in payload["audit"]:
        lines.append("| %s%s | %s | %s | %s |"
                     % ("★ " if entry["tier_one"] else "", entry["field"],
                        "yes" if entry["settable"] else "**no**",
                        "yes" if entry["recordable"] else "**no**",
                        entry["note"]))
    lines += [
        "",
        "**%d of 17 fields can be recorded**, and **%d tier-one fields cannot**:"
        % (payload["recordable"], len(payload["tier_one_not_recordable"])),
        "",
    ] + ["- %s" % f for f in payload["tier_one_not_recordable"]] + [
        "",
        "## The seed decides it",
        "",
        "Almost no docking web server lets you set a random seed, and almost none",
        "reports the one it used. Chapter 9 measured what that costs: two runs at",
        "Vina's default seed differ, and nothing in the log distinguishes a",
        "defaulted seed from a fixed one.",
        "",
        "So **a web-server run cannot be repeated** — not by you, and not by the",
        "server. Re-submitting the same files gives a different answer and no way",
        "to tell whether the difference is the seed or something you changed.",
        "",
        "That does not make web servers useless. It makes them a way to get a",
        "first look at a system, and not a way to produce a result somebody else",
        "can check. Which of those you need is a decision worth taking before",
        "the upload rather than at the write-up.",
        "",
        "## Nothing is submitted",
        "",
        "This script contacts no server. Submitting data to a third-party service",
        "is the user's decision rather than a script's, and an automated",
        "submission is also the quickest way to breach a service's terms of use.",
        "",
    ]
    (OUT / "server_audit.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
