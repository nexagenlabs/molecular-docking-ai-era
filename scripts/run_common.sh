# Shared preamble for every chapter's run.sh. Sourced, never executed:
#
#   cd "$(dirname "$0")/.."
#   . scripts/run_common.sh
#
# Sets PYTHON to the interpreter *this shell can run*, and stops with one
# message if the only candidate is one it cannot.
#
# WHY THE TEST IS EXECUTION AND NOT EXISTENCE
#
# `[ -x ".venv/Scripts/python.exe" ]` is true in any shell that can SEE the
# file, including one that cannot RUN it. A WSL bash sees a Windows-side clone
# over DrvFs, passes that test, selects the .exe and exits 126 with
# `Exec format error`. Nothing in that message names the cause, and without
# this helper a reader meets it once per chapter, twenty-five times, never
# learning what is wrong. The reverse configuration fails the same way: a
# Windows shell cannot exec a Linux venv either.
#
# Neither direction is supported -- see environment/README.md -- so this is
# not a case to probe around and accommodate. It is a case to name once and
# stop on. That is the whole reason this file exists rather than one extra
# line in each of the twenty-five wrappers.

run_common_pick_python() {
    local candidate unusable=""

    for candidate in ".venv/Scripts/python.exe" ".venv/bin/python"; do
        [ -x "$candidate" ] || continue
        # Execution, not existence. One interpreter start, ~30 ms, and it is
        # the only thing that distinguishes a usable venv from a visible one.
        if "$candidate" -c "" >/dev/null 2>&1; then
            PYTHON="$candidate"
            return 0
        fi
        # Keep looking: a tree provisioned under both platforms has both, and
        # the one this shell can run may be the second.
        unusable="$candidate"
    done

    if [ -n "$unusable" ]; then
        run_common_refuse "$unusable"
    fi

    PYTHON="${PYTHON:-python3}"
}

run_common_refuse() {
    local unusable="$1"
    local kernel
    kernel="$(uname -s 2>/dev/null || echo unknown)"

    cat >&2 <<REFUSAL

This shell cannot execute the interpreter in .venv/, so no chapter here can
run. The virtual environment and the shell are from different platforms.

  shell:       ${SHELL:-bash} (uname -s: $kernel)
  interpreter: $unusable  (exists, is marked executable, will not exec)

The usual cause is WSL driving a clone that lives on the Windows side, under
/mnt/c or //wsl.localhost. A Windows .exe is not executable from a Linux
shell, and a Linux venv is not executable from Windows. Running this
repository across that boundary is not supported.

Pick one side and stay on it:

  - clone inside WSL (somewhere under your Linux home, not /mnt/c) and
    provision it there with environment/README.md's Linux recipe; or
  - run on Windows, in the Git for Windows bash that environment/README.md
    documents, against a venv built by Windows Python.

REFUSAL
    exit 1
}

run_common_pick_python
