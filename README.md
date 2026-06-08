# When Does Ability Grouping Improve Learning?

This repository contains the analysis code and paper inputs for the active
three-country economics paper on cross-grade ability grouping in Kenya, Liberia,
and Nigeria.

The live manuscript source in the Overleaf-linked repository is:

```text
main_3country_new.tex
```

The active Overleaf-linked repository is:

```text
/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.tex
```

## Paper Pipeline

Use `paper_pipeline/` as the active paper-facing entry point. It parses the
manuscript, identifies the exact generated tables and figures LaTeX reads, and
materializes them into the repo-root input folders:

```text
stata_output/
structural_output/
```

Fast check:

```bash
python3 paper_pipeline/materialize_latex_inputs.py --check-only
```

Materialize active inputs:

```bash
python3 paper_pipeline/materialize_latex_inputs.py
```

Regenerate structural outputs and paper-summary figures, then materialize:

```bash
bash paper_pipeline/run_main_3country_pipeline.sh
```

The materializer writes:

```text
paper_pipeline/active_inputs_manifest.csv
paper_pipeline/materialize_report.json
```

These files are the current audit trail from analysis outputs to LaTeX inputs.

## Repository Structure

```text
reading-groups-struc/
├── main_3country_new.tex # active manuscript
├── bib.bib               # bibliography used by the manuscript
├── build_paper.sh        # local build helper; outputs go to build/
├── build/                # local compiled PDF and TeX build products
├── 1_Do/                 # legacy original Stata do-files
├── 2_Data/               # raw and cleaned data roots
├── 3_Python/             # structural estimation and figure pipeline
├── 4_Stata2/             # reduced-form Stata pipeline and outputs
├── data/                 # additional local data inputs, including DDK
├── docs/                 # handover notes and project documentation
├── literature/           # PDF literature anchors used in framing/modeling
├── paper_pipeline/       # active manuscript-input materialization pipeline
├── replication_audit/    # independent audit notes and scratch replication checks
├── stata_output/         # active reduced-form tables read by LaTeX
├── structural_output/    # active structural tables and figures read by LaTeX
└── archive/              # old paper-release notes and inactive documentation
```

## Current Status

The active manuscript uses three experiments. The reduced-form Stata outputs
live in `4_Stata2/output/`; structural tables are generated under
`3_Python/output/structural_smm/latex/`; paper-facing structural figures are
materialized into `structural_output/`.

The pipeline is now organized around the paper’s actual LaTeX dependencies, but
the repository is not yet a polished public replication package. Known remaining
cleanup items are documented in `replication_audit/REPLICATION_AUDIT.md`:

- update or retire release scripts that still target `main2.tex`;
- make all Nigeria and pooled Stata scripts scratch-safe and no-sync by default;
- update stale numeric/prose verification gates for the active three-country
  paper;
- turn the current audit wrapper into a complete raw-data replication runner.

## Stata

Use the installed StataNow binary rather than assuming a PATH wrapper:

```bash
/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp
```

When rerunning Stata code, inspect the generated `.log` before treating a run as
successful.

## Python

The structural pipeline is centered on:

```text
3_Python/structural_blockwise_redesign.py
3_Python/make_paper_summary_figures.py
3_Python/README_structural.md
```

The canonical wrapper in `paper_pipeline/` calls those scripts before
materializing the active LaTeX inputs.
