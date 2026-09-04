# Protocol record

Copy this file, fill it in, and keep it with the results it describes.

★ marks the **tier-one** fields: the seven whose absence stops re-execution.
Everything else changes the answer; these decide whether there is an answer at
all. A field you cannot fill is a finding — write "not recorded" rather than
deleting the line.

Most of this can be filled by machine. Run:

```bash
python ch20_protocol_record/scripts/fill_record.py \
    --config <your vina config> --log <your vina log> \
    --structure <PDBID> --chain <CHAIN> --ligand <LIGAND>
```

| # | Field | Value |
|---|---|---|
| 1 | ★ **Receptor source and identifier** | |
| 2 | Chains and altlocs kept | |
| 3 | Waters and ions | |
| 4 | Missing residues | |
| 5 | ★ **Receptor preparation tool and version** | |
| 6 | ★ **Ligand source** | |
| 7 | Ligand preparation | |
| 8 | Stereochemistry as docked | |
| 9 | ★ **Box centre** | |
| 10 | ★ **Box dimensions** | |
| 11 | Box derivation | |
| 12 | ★ **Docking program and version** | |
| 13 | Exhaustiveness / num_modes / energy_range | |
| 14 | ★ **Random seed** | |
| 15 | Redocking result | |
| 16 | Cross-docking or enrichment result | |
| 17 | Exclusions and deviations | |

## Notes on the fields that catch people

**14, the seed.** Vina's default is 0, which means *random*. Two runs at the
default differ and nothing in the log distinguishes a defaulted seed from a
fixed one. This is why the seed is tier one: a record without it cannot be
re-executed even though every other field is present.

**9 and 10, the box.** A box too small to hold the ligand raises no error and
returns a worse score that looks like a result. The dimensions are what make
the score interpretable; the derivation is what makes them reproducible.

**15, the redocking result.** State how the RMSD was computed: heavy-atom,
symmetry-corrected, and **without superposition**. `--minimize` superimposes
before measuring and makes every validation pass.

**17, exclusions.** The one field no tool can fill, and the reason the record
exists. What did you leave out, and on what grounds?
