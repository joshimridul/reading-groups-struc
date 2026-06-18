# Three-Country Paper Pipeline

This folder contains the paper-facing materialization utilities for the active
manuscript:

```text
main_3country_new.structural_edit.tex
```

The goal is simple: the pipeline should produce the exact tables and figures
that LaTeX reads, with no silent manual transfer from analysis folders to the
paper folder. The `reading-groups-struc` repository is linked directly to
Overleaf, so this pipeline writes only inside the repository.

## Active Build Contract

The manuscript reads generated artifacts from two repo-root folders:

```text
stata_output/
structural_output/
```

The sources for those artifacts are:

```text
4_Stata2/output/                         # reduced-form Stata tables
3_Python/output/structural_smm/latex/     # structural LaTeX tables
3_Python/output/structural_smm/           # canonical structural figure
structural_output/                        # paper-summary figures not yet in structural_smm
```

Run this after regenerating outputs:

```bash
python3 paper_pipeline/materialize_latex_inputs.py
```

The script parses the active manuscript, currently
`main_3country_new.structural_edit.tex`, finds every active
`\input{stata_output/...}`, `\input{structural_output/...}`, and
`\includegraphics{structural_output/...}`, and materializes only those files.
It also writes:

```text
paper_pipeline/active_inputs_manifest.csv
paper_pipeline/materialize_report.json
```

Unreferenced files in `stata_output/` or `structural_output/` are moved to
`archive/stale_paper_inputs/`. This keeps the active LaTeX input folders as a
literal inventory of the current manuscript exhibits.

Use a dry run when checking a dirty repo:

```bash
python3 paper_pipeline/materialize_latex_inputs.py --check-only
```

## Canonical Wrapper

The wrapper below regenerates the structural model outputs and paper-summary
figures, then materializes the manuscript inputs:

```bash
bash paper_pipeline/run_main_3country_pipeline.sh
```

For a fast materialization pass without rerunning Python:

```bash
bash paper_pipeline/run_main_3country_pipeline.sh --skip-regenerate
```

## Current Limits

This folder is not the full replication entry point. Collaborators should use:

```bash
./run_all.sh
```

from the repository root. The root runner calls the Stata, Python,
materialization, audit, and LaTeX build stages in order.
