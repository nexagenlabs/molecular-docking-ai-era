# Environment

**The book's numbers were produced with pip on Ubuntu, Python 3.12.3.** Not
conda. That is the stock Python of Ubuntu 24.04, and the recipe below was run
end to end on a fresh 24.04 install: it reproduces the box-sweep scores to
three decimals, `−4.905 / −4.911 / −2.748`, difference 0.000.

```bash
sudo apt install python3.12-venv  # venv on Debian/Ubuntu ships without ensurepip
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

# Vina, as a BINARY. `pip install vina` gives the Python bindings only -- there
# is no `vina` command afterwards, and every script here calls Vina through its
# command line. Without this, 69 tests error with "Vina not found".
curl -sSL -o .tools/vina \
  https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.7/vina_1.2.7_linux_x86_64
chmod +x .tools/vina
./.tools/vina --version           # confirm: AutoDock Vina v1.2.7

sudo apt install openbabel
obabel -V                         # see the note below: you will get 3.1.1
```

Two of those lines are there because following the previous version of this
section on a clean machine did not work. `python3.12 -m venv` fails outright
without `python3.12-venv`, and `pip install -r requirements.txt` succeeds while
leaving you unable to dock anything.

**Open Babel: you will get 3.1.1, not the pinned 3.2.1.** Ubuntu 24.04 does not
package 3.2.1 and no form of the command will produce it. Open Babel is one of
the six packages that can move a published value, so the difference is recorded
rather than glossed: `ch04_formats/outputs/expected/results.md` names the
version its numbers came from, and none of its conclusions change between
3.1.0, 3.1.1 and 3.2.1. If you need 3.2.1 exactly you will have to build it.

## On Windows

**`pip install -r requirements.txt` does not work on Windows.** Not "works
except for Vina" — it installs *nothing at all*. `vina==1.2.7` publishes
manylinux and musllinux wheels for cp38–cp312 and no Windows wheel, so pip
falls back to the source distribution, which needs Boost. The build fails while
pip is still resolving, and pip abandons the whole transaction. Measured on a
fresh Python 3.12.10 venv: `pip list` afterwards is empty.

This works:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
# every line of requirements.txt except the vina pin
findstr /v /b "vina==" requirements.txt > requirements-windows.txt
pip install -r requirements-windows.txt
pip install openbabel-wheel==3.1.1.23
```

(In Git Bash: `grep -v '^vina==' requirements.txt > requirements-windows.txt`.)

Then get Vina itself as a binary — `vina_1.2.7_win.exe` from the
[AutoDock Vina 1.2.7 release](https://github.com/ccsb-scripps/AutoDock-Vina/releases/tag/v1.2.7)
— put it on `PATH`, or in `.tools/vina.exe`, or point `$VINA` at it, and
confirm it reports `AutoDock Vina v1.2.7`. Scripts here call Vina through its
command line, so the binary and the Python bindings are interchangeable for
this purpose: same upstream code, same version.

**Open Babel on Windows comes from `openbabel-wheel`,** the pip package in the
recipe above, and that is what this repository's own Windows environment uses.
It is not the system binary and it is not the pinned version: it gives **Open
Babel 3.1.0, not 3.2.1**, because openbabel-wheel ships no 3.2.1 build for
Windows. Open Babel is on the list of six things that can move a published
value, so the difference is recorded rather than glossed —
`ch04_formats/outputs/expected/results.md` names the version its numbers were
produced with, and none of its conclusions change between the two.

Without Open Babel, `ch04_formats` cannot run: its round-trips are that
program's output.

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
