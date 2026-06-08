# Three-Country Paper Pipeline

This folder is the canonical paper-facing pipeline for the active manuscript:

```text
main_3country_new.tex
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

The script parses `main_3country_new.structural_edit.tex`, finds every active
`\input{stata_output/...}`, `\input{structural_output/...}`, and
`\includegraphics{structural_output/...}`, and materializes only those files.
It also writes:

```text
paper_pipeline/active_inputs_manifest.csv
paper_pipeline/materialize_report.json
```

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

This is a clean paper-input pipeline, not yet a full raw-data replication
package. The remaining cleanup is concentrated in the reduced-form Stata stack:

- `03_pooled_analysis.do`, `02_nigeria_main_analysis.do`,
  `02b_nigeria_two_group.do`, and `00_clean_nigeria.do` still need a fully
  scratch-safe no-sync mode.
- Several old release scripts still target `main2.tex` and should stay out of
  the active build path.
- `3_Python/verify_structural_package.py` currently fails prose-gate checks
  even though the structural tables and figures are materialized.

The replication audit in `replication_audit/` gives the detailed status of
those issues. This folder is the replacement entry point for the active
three-country paper.
