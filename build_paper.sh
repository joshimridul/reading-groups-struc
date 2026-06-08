#!/usr/bin/env bash
set -euo pipefail

latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main_3country_new.tex
