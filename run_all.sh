#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATA_BIN="${STATA_BIN:-/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
ENTRYPOINT="${ENTRYPOINT:-main_3country_new.structural_edit.tex}"

RUN_STATA=1
RUN_PYTHON=1
RUN_BUILD=1

usage() {
  cat <<'USAGE'
Usage: ./run_all.sh [options]

Regenerate and verify the three-country ability-grouping paper.

Default:
  1. run the Stata reduced-form pipeline;
  2. run the Python structural/figure pipeline;
  3. materialize exactly the LaTeX inputs referenced by the active manuscript;
  4. audit active paper inputs;
  5. compile the active manuscript PDF under build/.

Options:
  --existing       Do not rerun Stata or Python; verify existing outputs and compile.
  --skip-stata     Skip Stata reduced-form regeneration.
  --skip-python    Skip Python structural/figure regeneration.
  --skip-build     Skip LaTeX compilation.
  -h, --help       Show this help text.

Environment overrides:
  STATA_BIN=/path/to/stata-mp
  PYTHON_BIN=/path/to/python
  ENTRYPOINT=main_3country_new.structural_edit.tex
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --existing)
      RUN_STATA=0
      RUN_PYTHON=0
      shift
      ;;
    --skip-stata)
      RUN_STATA=0
      shift
      ;;
    --skip-python)
      RUN_PYTHON=0
      shift
      ;;
    --skip-build)
      RUN_BUILD=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$ROOT/build/logs" "$ROOT/build/mplconfig" "$ROOT/build/xdg-cache"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$ROOT/build/mplconfig}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$ROOT/build/xdg-cache}"
export MPLBACKEND="${MPLBACKEND:-Agg}"

if [[ ! -f "$ROOT/$ENTRYPOINT" ]]; then
  echo "Manuscript entry point not found: $ROOT/$ENTRYPOINT" >&2
  exit 1
fi

echo "== Three-country ability-grouping replication =="
echo "Repo: $ROOT"
echo "Manuscript: $ENTRYPOINT"
echo

if [[ "$RUN_STATA" -eq 1 ]]; then
  if [[ ! -x "$STATA_BIN" ]]; then
    echo "Stata binary not found or not executable: $STATA_BIN" >&2
    echo "Set STATA_BIN=/path/to/stata-mp and rerun." >&2
    exit 1
  fi

  echo "== Stata reduced-form pipeline =="
  "$STATA_BIN" -b do "$ROOT/4_Stata2/_master_paper.do"
  echo "Stata log: build/logs/stata_master_paper.log"
  tail -n 60 "$ROOT/build/logs/stata_master_paper.log"
  if rg -n "r\\([0-9]+\\);" "$ROOT/build/logs/stata_master_paper.log"; then
    echo "Stata reported an r(...) error. Inspect build/logs/stata_master_paper.log." >&2
    exit 1
  fi
else
  echo "== Stata reduced-form pipeline skipped =="
fi

if [[ "$RUN_PYTHON" -eq 1 ]]; then
  echo
  echo "== Python structural and figure pipeline =="
  "$PYTHON_BIN" "$ROOT/3_Python/structural_blockwise_redesign.py"
  "$PYTHON_BIN" "$ROOT/3_Python/make_assignment_value_figures.py"
  "$PYTHON_BIN" "$ROOT/3_Python/make_paper_summary_figures.py"
else
  echo
  echo "== Python structural and figure pipeline skipped =="
fi

echo
echo "== Materialize active LaTeX inputs =="
"$PYTHON_BIN" "$ROOT/paper_pipeline/materialize_latex_inputs.py"

echo
echo "== Audit active paper inputs =="
"$PYTHON_BIN" "$ROOT/4_Stata2/audit_overleaf_artifacts.py" \
  --overleaf-dir "$ROOT" \
  --entrypoint "$ENTRYPOINT" \
  --repo-output-dir "$ROOT/4_Stata2/output" \
  --check-labels

if [[ "$RUN_BUILD" -eq 1 ]]; then
  echo
  echo "== Compile paper =="
  "$ROOT/build_paper.sh"
  LOG_BASENAME="${ENTRYPOINT%.tex}"
  if rg -n "undefined|Citation.*undefined|Reference.*undefined|There were undefined|Label\\(s\\) may have changed|Fatal|Emergency|Error|Overfull" "$ROOT/build/$LOG_BASENAME.log"; then
    echo "LaTeX log has unresolved references/citations or serious warnings." >&2
    exit 1
  fi
  echo "PDF: build/$LOG_BASENAME.pdf"
else
  echo
  echo "== LaTeX build skipped =="
fi

echo
echo "Replication pipeline complete."
