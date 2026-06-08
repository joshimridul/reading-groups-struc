# 4_Stata2 — Stata Replication Pipeline

## Current Status for the Three-Country Paper

The active paper is now `main_3country_new.tex` in the
`reading-groups-struc` repository, not the old `main2.tex` release track. Use
`paper_pipeline/` as the paper-facing entry point: it materializes the exact
active LaTeX inputs from `4_Stata2/output/` and
`3_Python/output/structural_smm/` into repo-local paper folders.

Several scripts documented below still belong to the old Kenya/Liberia
`main2.tex` workflow. They are useful provenance, but they should not be
treated as the active release checklist until all release checks target
`main_3country_new.tex`.

Stata replication of the Python pipeline in `3_Python/`, covering both experiments
(Kenya Y1 and Liberia).

## Requirements

- StataNow/StataMP 19.5 in this local environment:
  `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp`
- Raw CSV data in `2_Data/1_Raw/`

## Running

```bash
'/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp' -b do \
  /Users/mriduljoshi/Github/AbilityGrouping/4_Stata2/_master.do
```

Inspect the generated Stata log before treating any regenerated output as
validated.

To build the full set of generated table and figure inputs currently referenced by `main2.tex`
without editing the TeX file, run:

```bash
python3 4_Stata2/build_main2_tables.py
```

This runs the Stata pipeline, materializes legacy alias tables still referenced
by `main2.tex`, validates the required figure files, and copies the required
`.tex` and figure files into the Overleaf `stata_output/` directory.

To audit the current repo-local paper inputs, run:

```bash
python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir "/Users/mriduljoshi/Github/reading-groups-struc" \
  --entrypoint main_3country_new.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels
```

Or set globals and run individual scripts:

```stata
global root "/Users/mriduljoshi/Github/AbilityGrouping"
global raw  "$root/2_Data/1_Raw"
global out  "$root/4_Stata2/output"
global do   "$root/4_Stata2"

do "$do/00_clean_liberia.do"
```

## Pipeline Structure

| Script | Replicates | Description |
|--------|-----------|-------------|
| `_master.do` | — | Sets globals, runs all scripts |
| `00_clean_liberia.do` | `00_clean.py` | Loads raw Liberia CSVs, merges BL/ML/EL, applies sample restrictions, constructs EB ability, peer variables, class size, misfit |
| `00_clean_kenya.do` | `00_clean_kenya.py` | Same for Kenya Y1 (composite Literacy + English scores) |
| `01_descriptives.do` | `make_descriptives.py` | Summary stats, balance tables, attrition, sample flow |
| `02_main_analysis.do` | `structural_estimation_revision.py` (ITT section) | ITT estimates, upper/lower track effects, within-class dispersion, Borusyak-Hull peer effects |
| `03_diagnostics.do` | `round1_diagnostics.py`, `round2_mechanisms.py` | Signal quality (R^2), assignment accuracy, classroom reallocation, cutoff heterogeneity, track x ability bins, class-size controls |
| `04_structural.do` | `structural_estimation_revision.py` (structural section) | Signal quality table, Kenya reduced-form accounting, minimum-distance decomposition, Liberia sensitivity grid, four-margin summary |
| `05_sufficientstats.do` | — | Deprecated compatibility wrapper that now calls `04_structural.do` |
| `06_robustness.do` | — | Specification robustness, ceiling, score-variance, class-size robustness, Lee bounds |
| `07_lesson_completion.do` | — | Kenya lesson-completion table used by the current manuscript |

## Key Variables

| Variable | Definition |
|----------|-----------|
| `score_bl`, `score_el` | Raw baseline/endline scores (Liberia: single; Kenya: literacy + English composite) |
| `std_score_bl`, `std_score_el` | Standardized by grade, control-group mean/SD |
| `eb_ability`, `std_eb` | Empirical Bayes predicted ability: grade mean + control-group baseline-endline R^2 x score residual |
| `upper_group` | 1 if score > cutoff (deterministic assignment) |
| `std_grp` | Reading-group classroom label |
| `peer_eb`, `peer_bl` | Leave-self-out peer mean (realized) |
| `exp_peer_eb` | Expected peer quality (BH conditioning variable) |
| `misfit` | (θ̂_i − Ī_k)²: squared distance from class mean EB |
| `dev_eb` | |θ̂_i − mean(θ̂)_class|: within-class EB dispersion |
| `csize` | Class size (treatment: std_grp; control: grade) |
| `finsamp` | Final analytic sample flag |

## Cross-Validation

Numbers to compare between Stata and Python output:

1. **Sample sizes**: `finsamp` counts by grade × treatment
2. **Signal quality**: control-group baseline-endline R^2 by grade
3. **ITT point estimates**: coefficient on `treat` in main specification
4. **Peer-effect coefficients**: BH estimates of β_P
5. **Sensitivity grid values**: Liberia predicted effects under parameter combinations
