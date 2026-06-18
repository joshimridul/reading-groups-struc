Mridul Joshi
<mriduljoshi@stanford.edu>

(Prepared using Codex 5.5)

# Why Sorting Students Is Not Enough

This repository contains the manuscript, analysis code, generated exhibits, and
replication pipeline for **"Why Sorting Students Is Not Enough: Evidence from
Three Ability-Grouping Experiments."** The paper studies cross-grade ability
grouping in Kenya, Liberia, and Nigeria and asks when replacing grade assignment
with a diagnostic assignment rule improves learning.

The current paper version is:

```text
main_3country_new.structural_edit.tex
build/main_3country_new.structural_edit.pdf
```

The repository is organized so collaborators can regenerate the paper from the
analysis code, inspect the generated tables and figures used by LaTeX, and run
verification checks before sharing or extending the analysis.

## Main Result

The three randomized evaluations do not show a common positive average effect.
The country pattern is informative: Liberia uses a weak diagnostic; Kenya sorts
students cleanly but does not generate a revealed payoff at observed delivery
fidelity; Nigeria's intended high-input design breaks down in group formation
and curriculum delivery. A calibrated assignment-delivery benchmark implies
that meaningful gains require a diagnostic that improves on grade assignment,
faithful group formation, and high delivery of the assigned content.

## Quick Start

From the repository root:

```bash
./run_all.sh --existing
```

This verifies the current generated outputs, materializes the active LaTeX
inputs, audits table and figure references, and compiles the paper. It is the
best first command for a collaborator who wants to check the current version.

To regenerate the full paper pipeline:

```bash
./run_all.sh
```

The full run executes the Stata reduced-form pipeline, the Python structural and
figure pipeline, materializes the exact LaTeX inputs used by the manuscript,
audits active exhibits, and compiles the PDF.

## Software

### Stata

The Stata code is written for Stata 19. By default, the replication wrapper
looks for Stata at:

```bash
/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp
```

If your Stata binary is elsewhere, run:

```bash
STATA_BIN="/path/to/stata-mp" ./run_all.sh
```

The main Stata log is:

```text
build/logs/stata_master_paper.log
```

Inspect this log whenever a reduced-form table changes.

### Python

Use Python 3.9 or newer. Install the Python dependencies with:

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

The compiled PDF and LaTeX logs are written under `build/`.

## Data Availability

The repository does not publish restricted raw student-level data. The code
expects the local data roots under:

```text
2_Data/
```

Those files are ignored by Git. Collaborators with data access can place the
raw inputs in the expected directory structure and run `./run_all.sh`. The
paper-facing generated outputs in `stata_output/` and `structural_output/`
are included so readers can inspect the exact tables and figures used by the
current manuscript even when restricted data are not available.

## Pipeline

### 1. Reduced-Form Analysis

Entry point:

```text
4_Stata2/_master_paper.do
```

This Stata master regenerates the country-specific and pooled reduced-form
tables for Kenya, Liberia, and Nigeria. Primary Stata outputs are written to:

```text
4_Stata2/output/
```

The manuscript reads materialized copies from:

```text
stata_output/
```

### 2. Structural Benchmark and Figures

Canonical Python scripts:

```text
3_Python/structural_blockwise_redesign.py
3_Python/make_assignment_value_figures.py
3_Python/make_paper_summary_figures.py
```

The structural pipeline writes working outputs under:

```text
3_Python/output/structural_smm/
```

Paper-facing structural tables and figures are materialized into:

```text
structural_output/
```

The structural exercise is a calibrated assignment-delivery benchmark. It is not
a substitute for the randomized reduced-form evidence.

### 3. Materialization and Audit

The materializer parses the active manuscript and copies only referenced
generated inputs into the paper-facing folders:

```bash
python3 paper_pipeline/materialize_latex_inputs.py
```

It writes:

```text
paper_pipeline/active_inputs_manifest.csv
paper_pipeline/materialize_report.json
```

## Repository Structure

```text
main_3country_new.structural_edit.tex   Active manuscript
bib.bib                                 Bibliography
run_all.sh                              Full replication/build wrapper
build_paper.sh                          LaTeX-only build helper
1_Do/                                   Legacy original Stata code
2_Data/                                 Local restricted data root, ignored by Git
3_Python/                               Structural benchmark and paper figures
4_Stata2/                               Reduced-form Stata pipeline
docs/                                   Project notes and verification records
paper_pipeline/                         LaTeX input materialization tools
replication_audit/                      Independent pipeline audit notes
stata_output/                           Active Stata tables used by LaTeX
structural_output/                      Active structural tables/figures used by LaTeX
build/                                  Compiled PDF and build logs
```

## Verification

The current repository state has been checked with:

```bash
./run_all.sh --existing
python3 3_Python/verify_structural_package.py
```

## Notes for Collaborators

- Do not manually edit files in `stata_output/` or `structural_output/`. Edit
  the generating Stata or Python code, then rerun the pipeline.
- Use `./run_all.sh --existing` for a fast verification pass.
- See `docs/` for detailed project notes and audit records.
