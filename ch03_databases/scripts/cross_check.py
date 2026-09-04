#!/usr/bin/env python3
"""Chapter 3 — get the same number by two routes and see whether they agree.

    python ch03_databases/scripts/cross_check.py

Every fact in this repository comes from somewhere. This chapter asks the
obvious follow-up: **does the source agree with itself?**

For each structure it takes the resolution, R-free and ligand identity from two
independent places — the REST API and the coordinate file's own header — and
compares them. For each ligand it compares the SMILES this repository docks
against the one the PDB chemical component dictionary holds.

Where a value disagrees, both are reported. Nothing is reconciled silently.

Needs network access. Writes outputs/cross_check.json and .md.
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from rdkit import Chem, RDLogger

CH = Path(__file__).resolve().parent.parent
REPO = CH.parent
OUT = CH / "outputs"
STRUCTURES = REPO / "data" / "structures"
LIGANDS = REPO / "data" / "ligands"

RDLogger.DisableLog("rdApp.*")

ENTRY_API = "https://data.rcsb.org/rest/v1/core/entry/%s"
CHEMCOMP_API = "https://data.rcsb.org/rest/v1/core/chemcomp/%s"

ENTRIES = ["1L2S", "4JXS", "4JXV", "1GA9"]
LIGAND_OF = {"1L2S": "STC", "4JXS": "18U", "4JXV": "1MU", "1GA9": "ETP"}

# Ki values, and where each came from. 1MU disagrees between two sources that
# are both cited in the literature; carrying both to the end is the only honest
# option, and Chapter 26 shows the disagreement is larger than the gap it would
# have to resolve.
AFFINITY = {
    "STC": {"chembl_uM": 26.0, "pdbbind_uM": 26.0},
    "18U": {"chembl_uM": 18.0, "pdbbind_uM": 18.0},
    "1MU": {"chembl_uM": 26.0, "pdbbind_uM": 31.0},
    "ETP": {"note": "83 nM, measured with a different substrate and buffer -- "
                    "NOT comparable to the values above, and not converted"},
}


def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {"__error__": str(exc)}


def from_header(pdb_id):
    """Resolution, R-free and the HETATM groups, from the local file."""
    import re
    path = STRUCTURES / ("%s.pdb" % pdb_id)
    if not path.exists():
        return None
    resolution = r_free = None
    groups = set()
    for line in path.read_text().splitlines():
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
        elif line.startswith("HETATM"):
            groups.add(line[17:20].strip())
    return {"resolution": resolution, "r_free": r_free,
            "hetatm_groups": sorted(groups)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"entries": {}, "ligands": {}, "affinity": AFFINITY}
    offline = False

    print("%-7s %-22s %-22s %s" % ("entry", "resolution (API/file)",
                                   "R-free (API/file)", "agree?"))
    for pdb_id in ENTRIES:
        api = fetch_json(ENTRY_API % pdb_id)
        header = from_header(pdb_id)
        if "__error__" in api:
            offline = True
            print("%-7s API unreachable: %s" % (pdb_id, api["__error__"]))
            results["entries"][pdb_id] = {"api_error": api["__error__"],
                                          "header": header}
            continue
        if header is None:
            print("%-7s local file missing -- run data/structures/fetch.sh" % pdb_id)
            continue

        entry_info = api.get("rcsb_entry_info", {})
        api_resolution = (entry_info.get("resolution_combined") or [None])[0]
        api_r_free = None
        for refine in api.get("refine", []) or []:
            # ls_R_factor_R_free, and note what sits beside it:
            # ls_number_reflns_R_free is an integer in the thousands. That is
            # the same trap the coordinate-file header sets, and it is the one
            # that put 2647 in a QC report while this repository was being
            # built. The API is not safer, it just fails differently.
            if refine.get("ls_R_factor_R_free") is not None:
                api_r_free = refine["ls_R_factor_R_free"]
                break

        if api_resolution is None or api_r_free is None:
            print("%-7s API returned no %s -- reported, not filled in"
                  % (pdb_id, "resolution" if api_resolution is None else "R-free"))
            results["entries"][pdb_id] = {"api_incomplete": True,
                                          "api_resolution": api_resolution,
                                          "api_r_free": api_r_free,
                                          "header_resolution": header["resolution"],
                                          "header_r_free": header["r_free"]}
            continue

        resolution_agrees = (api_resolution is not None
                             and abs(api_resolution - header["resolution"]) < 0.005)
        r_free_agrees = (api_r_free is not None
                         and abs(api_r_free - header["r_free"]) < 0.0005)
        results["entries"][pdb_id] = {
            "api_resolution": api_resolution,
            "header_resolution": header["resolution"],
            "resolution_agrees": bool(resolution_agrees),
            "api_r_free": api_r_free,
            "header_r_free": header["r_free"],
            "r_free_agrees": bool(r_free_agrees),
            "hetatm_groups": header["hetatm_groups"],
            "title": api.get("struct", {}).get("title"),
            "method": (api.get("exptl") or [{}])[0].get("method"),
            "deposited": api.get("rcsb_accession_info", {}).get("deposit_date"),
        }
        print("%-7s %-22s %-22s %s"
              % (pdb_id,
                 "%.2f / %.2f" % (api_resolution, header["resolution"]),
                 "%.3f / %.3f" % (api_r_free, header["r_free"]),
                 "yes" if resolution_agrees and r_free_agrees else "NO"))

    if not offline:
        print("\n%-6s %-12s %-46s %s"
              % ("ligand", "formula", "PDB chemical component SMILES", "matches ours?"))
        for pdb_id, ligand in LIGAND_OF.items():
            api = fetch_json(CHEMCOMP_API % ligand)
            if "__error__" in api:
                offline = True
                break
            descriptors = api.get("pdbx_chem_comp_descriptor", []) or []
            pdb_smiles = next((d["descriptor"] for d in descriptors
                               if d.get("type") == "SMILES_CANONICAL"), None)
            ours = None
            local = LIGANDS / ("%s.sdf" % ligand)
            if local.exists():
                mol = next(Chem.SDMolSupplier(str(local), removeHs=False))
                ours = Chem.MolToSmiles(Chem.RemoveHs(mol))

            same_skeleton = None
            if pdb_smiles and ours:
                theirs = Chem.MolFromSmiles(pdb_smiles)
                if theirs is not None:
                    # Compare the neutral skeletons: the PDB component is the
                    # molecule as modelled in the crystal, which is not
                    # protonated for pH 7.4. A difference here is expected and
                    # is the point -- see the README.
                    strip = Chem.MolFromSmiles(
                        Chem.MolToSmiles(Chem.MolFromSmiles(
                            ours.replace("[O-]", "O"))))
                    same_skeleton = (Chem.MolToSmiles(theirs) ==
                                     Chem.MolToSmiles(strip) if strip else None)
            results["ligands"][ligand] = {
                "chem_comp_id": ligand,
                "formula": api.get("chem_comp", {}).get("formula"),
                "name": api.get("chem_comp", {}).get("name"),
                "pdb_smiles": pdb_smiles,
                "our_smiles": ours,
                "same_neutral_skeleton": same_skeleton,
            }
            print("%-6s %-12s %-46s %s"
                  % (ligand, api.get("chem_comp", {}).get("formula", "?"),
                     (pdb_smiles or "?")[:46],
                     {True: "yes (neutral form)", False: "NO", None: "-"}[same_skeleton]))

    print("\nAffinity, and where it came from:")
    for ligand, values in AFFINITY.items():
        if "note" in values:
            print("   %-5s %s" % (ligand, values["note"]))
        elif values["chembl_uM"] != values["pdbbind_uM"]:
            print("   %-5s ChEMBL %.0f uM, PDBbind %.0f uM  <-- SOURCES DISAGREE"
                  % (ligand, values["chembl_uM"], values["pdbbind_uM"]))
        else:
            print("   %-5s %.0f uM (both sources)" % (ligand, values["chembl_uM"]))
    print("\n   Both 1MU values are carried to the end. Chapter 26 shows the")
    print("   disagreement is larger than the gap it would have to resolve.")
    print("   No conversion is performed between Ki, IC50 and Kd anywhere.")

    if offline:
        print("\nNETWORK UNAVAILABLE for part of this run. What is above came from")
        print("the local files; the API comparison is incomplete. Recorded, not")
        print("worked around.")
    results["offline"] = offline

    (OUT / "cross_check.json").write_text(json.dumps(results, indent=2) + "\n",
                                          encoding="utf-8")
    write_report(results)
    print("\nwrote %s" % (OUT / "cross_check.json"))


def write_report(results):
    lines = [
        "# Chapter 3 — databases, cross-checked against themselves", "",
        "Resolution and R-free taken from two independent places: the RCSB REST",
        "API, and the header of the coordinate file this repository downloaded.",
        "",
        "| Entry | Resolution (API / file) | R-free (API / file) | Agree? |",
        "|---|---|---|---|",
    ]
    for pdb_id, entry in results["entries"].items():
        if "api_error" in entry:
            lines.append("| %s | API unreachable | — | — |" % pdb_id)
            continue
        lines.append("| %s | %.2f / %.2f | %.3f / %.3f | %s |"
                     % (pdb_id, entry["api_resolution"], entry["header_resolution"],
                        entry["api_r_free"], entry["header_r_free"],
                        "yes" if entry["resolution_agrees"] and entry["r_free_agrees"]
                        else "**no**"))
    if results["ligands"]:
        lines += [
            "", "## Ligands, against the PDB chemical component dictionary", "",
            "| Ligand | Formula | Same neutral skeleton? |",
            "|---|---|---|",
        ]
        for ligand, entry in results["ligands"].items():
            lines.append("| %s | %s | %s |"
                         % (ligand, entry["formula"],
                            {True: "yes", False: "**no**",
                             None: "—"}[entry["same_neutral_skeleton"]]))
        lines += [
            "",
            "The comparison is against the **neutral** skeleton on purpose. The",
            "PDB component describes the molecule as modelled in the crystal,",
            "which carries no protonation state for pH 7.4. This repository docks",
            "STC at −1 and 18U and 1MU at −2. Those are different molecules, and",
            "the difference is the subject of Chapter 8 — so the check here is",
            "that the *skeleton* matches, and the charge is expected to differ.",
        ]
    lines += [
        "", "## Affinity", "",
        "| Ligand | ChEMBL | PDBbind | |",
        "|---|---|---|---|",
        "| STC | 26 µM | 26 µM | agree |",
        "| 18U | 18 µM | 18 µM | agree |",
        "| 1MU | 26 µM | 31 µM | **disagree** |",
        "",
        "Both 1MU values are carried through to the end rather than one being",
        "chosen. Chapter 26 shows why that matters: the disagreement between the",
        "sources is larger than the gap between 1MU and STC that a method would",
        "have to resolve to rank them.",
        "",
        "**ETP is 83 nM**, measured with a different substrate and buffer. It is",
        "not comparable to the values above and is never converted. No conversion",
        "between Ki, IC50 and Kd happens anywhere in this repository.",
        "",
    ]
    (OUT / "cross_check.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
