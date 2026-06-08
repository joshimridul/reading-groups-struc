#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATA="/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp"

cd "$ROOT/replication_audit"

if [[ ! -x "$STATA" ]]; then
  echo "Stata binary not found: $STATA" >&2
  exit 1
fi

echo "== AbilityGrouping replication audit draft =="
echo "Repo root: $ROOT"
echo
echo "This runner is intentionally conservative."
echo "It rebuilds the Kenya/Liberia Stata core into replication_audit/stata_scratch/"
echo "and runs read-mostly verification checks. It does not sync to Overleaf."
echo

echo "== Stata scratch: Kenya/Liberia core =="
"$STATA" -b do "$ROOT/replication_audit/stata_scratch_core.do"
tail -n 80 "$ROOT/replication_audit/stata_scratch_core.log"

echo
echo "== Repo-local active Stata artifact audit =="
python3 "$ROOT/4_Stata2/audit_overleaf_artifacts.py" \
  --overleaf-dir "$ROOT" \
  --entrypoint main_3country_new.tex \
  --repo-output-dir "$ROOT/4_Stata2/output"

echo
echo "== Structural package verifier =="
python3 "$ROOT/3_Python/verify_structural_package.py"

echo
echo "Audit draft complete. Inspect the log and report before treating this as a replication package."
