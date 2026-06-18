#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$ROOT/main_3country_new.tex" ]]; then
  ENTRYPOINT="main_3country_new.tex"
else
  ENTRYPOINT="main_3country_new.structural_edit.tex"
fi

latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build "$ENTRYPOINT"
