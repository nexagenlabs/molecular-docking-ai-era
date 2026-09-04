# Environment

**The book's numbers were produced with pip on Ubuntu, Python 3.12.3.** Not
conda. If you want the published values, reproduce that:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
sudo apt install openbabel        # 3.2.1, a system binary -- not a pip package
obabel -V                         # confirm it says 3.2.1
```

`environment/environment.yml` is provided as a convenience for conda users. It
carries the same version pins, but **conda-forge may resolve transitive
dependencies differently even at an identical pin**, so it is not a guarantee
of identical output. If a number here disagrees with the book, reproduce it
under pip before concluding the book is wrong.

## Which pins matter

Six packages can change a published value, and are pinned exactly:

| Package | Version | What it moves |
|---|---|---|
| rdkit | 2026.3.5 | ch08 conformer counts; ch18 BEDROC cross-check |
| vina | 1.2.7 | every score and timing in ch09, ch17, ch26 |
| spyrmsd | 0.9.0 | every RMSD |
| meeko | 0.8.0 | PDBQT preparation, and so every docked pose |
| numpy | 2.4.4 | the arithmetic under all of the above |
| Open Babel | 3.2.1 | ch04's format round-trips are literally its output |

`gemmi` 0.7.5 is pinned too — meeko depends on it, so it reaches the poses by
that route. `matplotlib` and `scipy` carry minimum bounds only: they draw
plots and cannot move a number.

Vina 1.2.5 was superseded in February 2025. Nothing in this repository was
measured with it.

## resolved.txt

Record what you actually got, not what you asked for:

```bash
pip freeze > environment/resolved.txt
obabel -V >> environment/resolved.txt
```

`resolved.txt` is deliberately not committed — it is yours, describing your
machine. Keep it with your results and attach it to the protocol record
(`protocols/reproducibility_record.md`, section 6). When a number differs from
the book's, the diff between two `resolved.txt` files is usually where the
reason is.
