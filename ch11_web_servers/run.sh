#!/usr/bin/env bash
# Chapter 11 - web servers: what you can upload and what you cannot record.
#
#   bash ch11_web_servers/run.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x ".venv/Scripts/python.exe" ]; then PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then PYTHON=".venv/bin/python"
else PYTHON="${PYTHON:-python3}"; fi
if [ ! -f data/structures/1L2S.pdb ]; then bash data/structures/fetch.sh; fi
if [ ! -f data/ligands/STC.sdf ]; then $PYTHON data/ligands/generate.py; fi
$PYTHON ch11_web_servers/scripts/prepare_upload.py
echo
echo "Results:  ch11_web_servers/outputs/"
echo "Expected: ch11_web_servers/outputs/expected/"
