#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTRYPOINT="${ENTRYPOINT:-main_3country_new.structural_edit.tex}"

if [[ ! -f "$ROOT/$ENTRYPOINT" ]]; then
  echo "Manuscript entry point not found: $ROOT/$ENTRYPOINT" >&2
  exit 1
fi

cd "$ROOT"
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build "$ENTRYPOINT"
