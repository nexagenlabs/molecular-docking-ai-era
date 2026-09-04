#!/usr/bin/env bash
# Chapter 20 - the protocol record, filled from the files a run leaves behind.
#
#   bash ch20_protocol_record/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/Scripts/python.exe" ]; then
  PYTHON=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

if [ ! -f ch09_first_run/config/vina_config.txt ]; then
  echo "ch09 has not been run; running it to produce a config and a log."
  bash ch09_first_run/run.sh
fi

$PYTHON ch20_protocol_record/scripts/fill_record.py "$@"

echo
echo "Blank template: ch20_protocol_record/templates/blank_record.md"
echo "Filled record:  ch20_protocol_record/outputs/filled_record.md"
echo "Worked example: ch20_protocol_record/outputs/expected/ampc_record.md"
