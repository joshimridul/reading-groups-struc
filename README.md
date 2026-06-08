# When Does Ability Grouping Improve Learning?

This repository contains the manuscript, analysis code, generated exhibits, and
replication pipeline for the three-country paper on cross-grade ability grouping
in Kenya, Liberia, and Nigeria.

The active manuscript is:

```text
main_3country_new.tex
```

The compiled paper is written to:

```text
build/main_3country_new.pdf
```

## Quick Start

From the repository root:

```bash
./run_all.sh
```

This is the full paper pipeline. It runs the Stata reduced-form code, runs the
Python structural and figure code, materializes the exact LaTeX inputs used by
the manuscript, audits the active tables/figures, and compiles the PDF.

If you only want to verify the current generated outputs and compile the paper:

```bash
./run_all.sh --existing
```

This is the best first command for collaborators who are checking the draft
rather than regenerating every estimate.

## Software

### Stata

The Stata code is written for Stata 19. In Mridul's local environment the
expected binary is:

```bash
/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp
```

If your Stata binary is elsewhere, run:

```bash
STATA_BIN="/path/to/stata-mp" ./run_all.sh
```

Stata logs are written to:

```text
build/logs/stata_master_paper.log
```

Always inspect this log if a table changes unexpectedly. Stata can sometimes
continue after a printed warning, so the log is the authoritative record of the
run.

### Python

Use Python 3.9 or newer. Install packages from:

```bash
python3 -m pip install -r 3_Python/requirements.txt
```

If your Python executable is not `python3`, run:

```bash
PYTHON_BIN="/path/to/python" ./run_all.sh
```

### LaTeX

The local build uses `latexmk` and `bibtex`:

```bash
./build_paper.sh
```

The build helper keeps auxiliary files in `build/` rather than the repository
root.

## Pipeline Stages

### 1. Stata Reduced-Form Pipeline

Entry point:

```text
4_Stata2/_master_paper.do
```

This runs the table-producing Stata pipeline for all three countries:

- Kenya and Liberia cleaning;
- Kenya/Liberia descriptives, ITT tables, diagnostics, assignment-payoff checks,
  robustness tables, and lesson-completion tables;
- Nigeria cleaning and reduced-form tables;
- the preferred Nigeria two-group table;
- pooled three-country tables.

Primary Stata output folder:

```text
4_Stata2/output/
```

Paper-facing Stata table folder:

```text
stata_output/
```

The manuscript reads from `stata_output/`, not directly from `4_Stata2/output/`.
The materializer and audit ensure that only active manuscript inputs sit there.

### 2. Python Structural/Figure Pipeline

Canonical scripts:

```text
3_Python/structural_blockwise_redesign.py
3_Python/make_paper_summary_figures.py
```

The structural pipeline writes canonical working outputs under:

```text
3_Python/output/structural_smm/
```

Paper-facing structural tables and figures are materialized into:

```text
structural_output/
```

The structural section is a disciplined counterfactual exercise built on the
reduced-form evidence. For details on primitives, assumptions, and diagnostics,
see:

```text
3_Python/README_structural.md
```

### 3. Materialization

Entry point:

```bash
python3 paper_pipeline/materialize_latex_inputs.py
```

This script reads `main_3country_new.tex`, finds every active generated input,
and copies only those files into the paper-facing folders:

```text
stata_output/
structural_output/
```

It writes an audit trail:

```text
paper_pipeline/active_inputs_manifest.csv
paper_pipeline/materialize_report.json
```

If a previous Stata or Python run left unreferenced files in these paper-facing
folders, the materializer moves them to:

```text
archive/stale_paper_inputs/
```

This is intentional. It keeps collaborators from mistaking old tables or
figures for current manuscript evidence while preserving the files for audit.

### 4. Artifact Audit

The active paper-input audit is:

```bash
python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir . \
  --entrypoint main_3country_new.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels
```

Despite the historical script name, this now audits the repository-local paper
folder. A clean audit means:

- every Stata table referenced by `main_3country_new.tex` exists;
- no stale Stata files remain in `stata_output/`;
- active Stata files match `4_Stata2/output/`;
- table and figure references resolve.

### 5. Paper Build

Compile the manuscript:

```bash
./build_paper.sh
```

Output:

```text
build/main_3country_new.pdf
```

## Repository Structure

```text
reading-groups-struc/
├── main_3country_new.tex # active manuscript
├── bib.bib               # bibliography
├── run_all.sh            # full collaborator-facing pipeline
├── build_paper.sh        # LaTeX-only build helper
├── build/                # compiled PDF, TeX build products, logs
├── 1_Do/                 # legacy original Stata code
├── 2_Data/               # data roots
├── 3_Python/             # structural estimation and paper figures
├── 4_Stata2/             # reduced-form Stata pipeline
├── data/                 # additional local data inputs, including DDK
├── docs/                 # handover notes and project documentation
├── literature/           # PDF literature anchors
├── paper_pipeline/       # materialization and pipeline utilities
├── replication_audit/    # independent audit notes and scratch checks
├── stata_output/         # active Stata tables read by LaTeX
├── structural_output/    # active structural tables/figures read by LaTeX
└── archive/              # old entrypoints and inactive documentation
```

## Changing the Analysis

For reduced-form table changes:

1. edit the relevant do-file in `4_Stata2/`;
2. run `./run_all.sh --skip-python` if the structural outputs do not depend on
   the change;
3. inspect `build/logs/stata_master_paper.log`;
4. check the changed `.tex` file in `4_Stata2/output/` and `stata_output/`;
5. read the corresponding table in `build/main_3country_new.pdf`.

For structural model changes:

1. edit the relevant script in `3_Python/`;
2. run `./run_all.sh --skip-stata`;
3. inspect `3_Python/output/structural_smm/run_manifest.json`;
4. inspect the changed table or figure in `structural_output/`;
5. read the structural section in the compiled PDF.

For manuscript-only changes:

```bash
./build_paper.sh
```

## Troubleshooting

- If Stata fails immediately, check `STATA_BIN`. Do not assume `stata` is on the
  shell path.
- If a table is missing from LaTeX, run `python3 paper_pipeline/materialize_latex_inputs.py`.
- If a stale table or figure appears in a paper-facing folder, rerun the
  materializer; unreferenced files should move to `archive/stale_paper_inputs/`.
- If bibliography or cross-references look wrong, rerun `./build_paper.sh`.
- If structural outputs seem stale, rerun `./run_all.sh --skip-stata`.

## Current Verification Status

The repo-local paper pipeline has been verified to:

- materialize 80 active paper artifacts with zero missing sources;
- keep exactly 50 active Stata tables in `stata_output/`;
- compile `build/main_3country_new.pdf`;
- resolve active table/figure labels and references.
