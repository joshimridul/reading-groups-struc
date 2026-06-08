#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$ROOT/main_3country_new.tex" ]]; then
  MANUSCRIPT="$ROOT/main_3country_new.tex"
else
  MANUSCRIPT="$ROOT/main_3country_new.structural_edit.tex"
fi
CHECK_ONLY=0
SKIP_REGENERATE=0

usage() {
  cat <<'USAGE'
Usage: paper_pipeline/run_main_3country_pipeline.sh [options]

Paper-input materialization wrapper for the three-country paper.

Options:
  --check-only          Do not copy artifacts; only report missing or stale inputs.
  --skip-regenerate    Skip Python structural/figure regeneration and only materialize.
  -h, --help            Show this help text.

Notes:
  This wrapper is useful for refreshing structural outputs and then
  materializing the exact tables and figures read by LaTeX. Use ./run_all.sh
  from the repository root for the full collaborator-facing replication run.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check-only)
      CHECK_ONLY=1
      shift
      ;;
    --skip-regenerate)
      SKIP_REGENERATE=1
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

if [[ "$SKIP_REGENERATE" -eq 0 ]]; then
  python3 "$ROOT/3_Python/structural_blockwise_redesign.py"
  python3 "$ROOT/3_Python/make_paper_summary_figures.py"
fi

args=(--manuscript "$MANUSCRIPT")
if [[ "$CHECK_ONLY" -eq 1 ]]; then
  args+=(--check-only)
fi
python3 "$ROOT/paper_pipeline/materialize_latex_inputs.py" "${args[@]}"

echo "Three-country paper inputs are materialized."
