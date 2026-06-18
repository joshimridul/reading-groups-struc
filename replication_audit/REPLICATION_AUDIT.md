# Replication Audit: AbilityGrouping Three-Country Paper

Audit date: 2026-06-07  
Repo root: `/Users/mriduljoshi/Github/AbilityGrouping`  
Manuscript source audited: `main_3country_new.structural_edit.tex`  
Repo source compared: `/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.tex`  
Repo PDF compared: `/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.pdf`

## Bottom line

The active repo manuscript and local manuscript source are byte-identical, and the active generated Stata and structural artifacts used by `main_3country_new.tex` are present in repo. The repo-side active Stata outputs are also byte-identical to repo's active `stata_output/` files, and `structural_output/` is byte-identical between repo and repo.

This is not yet a clean shareable replication package. The main blockers are stale release/verifier scripts keyed to `main2.tex`, hard-coded output and repo-copy behavior in several Stata scripts, a structural verifier that now fails on manuscript-prose gates, and missing/obsolete artifacts expected by older checks.

## Files changed by this audit

- `replication_audit/REPLICATION_AUDIT.md`
- `replication_audit/PIPELINE_MAP.md`
- `replication_audit/run_all.sh`
- `replication_audit/stata_scratch_core.do`
- `replication_audit/stata_scratch_core.log`
- `replication_audit/stata_scratch/` outputs from the scratch Stata run

One verification command also rewrote the ignored/generated file `3_Python/output/structural_smm/structural_package_verification.json` while reporting failure. It does not show in `git status --short`, but the command writes that path.

## Commands tried

From repo root unless noted:

```bash
git status --short
rg --files
rg -n -F "\\input" main_3country_new.structural_edit.tex
rg -n -F "\\includegraphics" main_3country_new.structural_edit.tex
rg -n -F "\\label" main_3country_new.structural_edit.tex
find . -maxdepth 4 -type f \( -name '*.dta' -o -name '*.csv' -o -name '*.tex' -o -name '*.pdf' \) -print
find "/Users/mriduljoshi/Github/reading-groups-struc" -maxdepth 3 -type f \( -name '*.tex' -o -name '*.pdf' -o -name '*.bib' \) -print
python3 4_Stata2/audit_overleaf_artifacts.py --overleaf-dir "/Users/mriduljoshi/Github/reading-groups-struc" --entrypoint main_3country_new.tex --repo-output-dir 4_Stata2/output --check-labels
python3 4_Stata2/audit_overleaf_artifacts.py --overleaf-dir "/Users/mriduljoshi/Github/reading-groups-struc" --entrypoint main2.tex --repo-output-dir 4_Stata2/output --check-labels
python3 3_Python/verify_structural_package.py
/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do /Users/mriduljoshi/Github/AbilityGrouping/replication_audit/stata_scratch_core.do
tail -n 100 replication_audit/stata_scratch_core.log
rg -n "r\([0-9]+\)|no observations|not found|file .* not found|invalid|conformability|already defined|cannot|fail|error" replication_audit/stata_scratch_core.log
diff -qr structural_output "/Users/mriduljoshi/Github/reading-groups-struc/structural_output"
diff -qr structural_output 3_Python/output/structural_smm/latex
diff -qr replication_audit/stata_scratch 4_Stata2/output
python3 4_Stata2/check_numeric_claims.py
python3 4_Stata2/check_pdf_render.py
python3 4_Stata2/check_release_readiness.py
diff -u main_3country_new.structural_edit.tex "/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.tex"
shasum -a 256 main_3country_new.structural_edit.tex "/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.tex" "/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.pdf"
pdfinfo "/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.pdf"
rg -n "Warning|Error|Undefined|Citation|Reference|Overfull|Underfull|rerun|TODO|\?\?" "/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.log"
```

## What replicates or traces cleanly

- Local manuscript source equals Repo active source:
  - SHA-256 for both `main_3country_new.structural_edit.tex` and repo `main_3country_new.tex`: `5d109e3a30807e182199a6678ad47dca8a9459d5d5bb0f59d91e3d191f8cab28`.
- repo PDF exists and is recent:
  - `main_3country_new.pdf`
  - SHA-256: `06bbfe847455d3aec9d904e56133974e0049a608ea79e3e6dfbca66d7867431c`
  - Built by pdfTeX at 2026-06-07 16:20:53 PDT.
  - `pdfinfo` reports 94 pages.
- Active Stata manuscript inputs:
  - `main_3country_new.tex` references 50 `stata_output/` table inputs.
  - `audit_overleaf_artifacts.py` reports 0 missing active Stata files for `main_3country_new.tex`.
  - The 50 active Stata files are byte-identical between `4_Stata2/output/` and repo `stata_output/`.
- Active structural manuscript inputs:
  - 25 structural tables and 5 structural figures are referenced.
  - Repo `structural_output/` is byte-identical to repo `structural_output/`.
  - Structural TeX tables in `structural_output/` are byte-identical to `3_Python/output/structural_smm/latex/`.
- Scratch Stata run:
  - `replication_audit/stata_scratch_core.do` rebuilt the Kenya/Liberia Stata core into `replication_audit/stata_scratch/`.
  - Log inspected: `replication_audit/stata_scratch_core.log`.
  - Log ends with `Scratch Stata audit run complete.`
  - Overlapping active manuscript tables mostly match repo outputs exactly.
  - Differences are text-only in three overlapping tables: `tab_suffstat_kenya.tex`, `tab_suffstat_liberia.tex`, `tab_spec_robust.tex`.

## What does not replicate cleanly

### P0: Release/verifier scripts are stale relative to the active manuscript

`python3 4_Stata2/check_release_readiness.py` blocks. Main failures:

- It still audits `main2.tex`-era dependencies and reports missing legacy files:
  - `fig_gates_kenya.pdf`, `fig_gates_liberia.pdf`, `fig_varimp_kenya.pdf`, `fig_varimp_liberia.pdf`
  - `ke_attrition.tex`, `lib_attrition.tex`
  - `tab_gates.tex`, `tab_itt.tex`, `tab_lee_bounds.tex`, `tab_upper_lower.tex`
- Freeze manifest is stale:
  - missing `4_Stata2/05_gates.R`
  - hash drift in `4_Stata2/build_main2_tables.py`
  - hash drift in `4_Stata2/check_numeric_claims.py`
  - missing manifest rows for `ke_attrition.tex` and `lib_attrition.tex`
- PDF render check expects 66 pages, but current `main2.pdf` is 67 pages.
- Release status is blocked by `\publicversionfalse`, 159 changed/untracked paths, and pathspec drift.

### P0: `check_numeric_claims.py` is not aligned with `main_3country_new`

`python3 4_Stata2/check_numeric_claims.py` fails immediately:

```text
FileNotFoundError: Missing required file: /Users/mriduljoshi/Github/AbilityGrouping/4_Stata2/output/tab_itt.tex
```

The active manuscript now uses pooled tables such as `tab_pooled_itt.tex`, while this checker still requires deleted older outputs. This is a real reproducibility gate failure, not a manuscript artifact failure.

### P0: Several Stata scripts hard-code output and repo sync

The shipped masters and several three-country scripts overwrite repo outputs or copy to repo:

- `_master.do` sets `global out "$root/4_Stata2/output"`.
- `_master_nigeria.do` sets `global out "$root/4_Stata2/output"`.
- `00_clean_nigeria.do`, `02_nigeria_main_analysis.do`, `02b_nigeria_two_group.do`, and `03_pooled_analysis.do` hard-code `$out` and/or repo-local paper-copy behavior.
- `02_nigeria_main_analysis.do`, `02b_nigeria_two_group.do`, and `03_pooled_analysis.do` include `copy_to_paper` helpers.

That makes a safe independent rebuild hard without either patching scripts or running in a copied repo. The audit therefore scratch-ran only the Kenya/Liberia core scripts that honor a custom `$out`.

### P1: Structural verifier fails, although artifact/claim checks mostly pass

`python3 3_Python/verify_structural_package.py` returns `FAIL`. The JSON reports that the numeric claim checks inside the structural verifier pass, but manuscript-prose gates fail. Missing prose-gate names include:

- `stage4_regularization_framing`
- `parameter_level_identification`
- `validation_framing`
- `paper_punchline`
- `headline_scale_framing`
- `delivery_activation_objective_profile`
- `market_influence`
- `tau_sensitivity_results`
- `delivery_thresholds`

This is not an artifact mismatch: structural repo outputs and Repo outputs are synced. It means the structural verifier is currently stricter than the active manuscript prose, or the manuscript was edited without updating verifier expectations.

### P1: Four structural figures are outside the canonical structural verifier path

The main structural surface figure is generated by `3_Python/structural_blockwise_redesign.py`. The other paper-facing structural figures are generated by `3_Python/make_paper_summary_figures.py`:

- `fig_experiment_map.pdf`
- `fig_firststage_payoff.pdf`
- `fig_counterfactual_ladder.pdf`
- `fig_track_position_allcountries.pdf`

These are present and synced, but they are not in `3_Python/output/structural_smm/latex/`, and the canonical structural verifier is not enough to regenerate all structural figures used by the manuscript.

### P1: Stata scratch rebuild exposes text drift in three active tables

Scratch rebuild vs repo output:

- `tab_suffstat_kenya.tex`: numbers match; caption/notes changed from the script output to the repo/Repo output.
- `tab_suffstat_liberia.tex`: numbers match; caption/notes changed from the script output to the repo/Repo output.
- `tab_spec_robust.tex`: numbers match; wording changed from `$p$-value` to `$p$ value`.

This suggests some generated outputs were manually edited or produced by a script version different from the current working-tree script state.

### P2: Stata logs contain confusing nonfatal diagnostics

Recent Stata logs and the scratch log include lines printed with `di as error`, e.g. missing optional variables in approximate peer diagnostics. The runs continue and finish, but these should be downgraded to normal warnings or made explicit in log summaries. Otherwise future auditors may misclassify them as fatal errors.

### P2: Repo layout cannot compile the active manuscript without materialization

The active TeX source references `stata_output/...` and `structural_output/...`. The repo has `structural_output/`, but does not have a repo-root `stata_output/`; active Stata outputs are in `4_Stata2/output/`. A shareable package needs a deterministic step to materialize active manuscript inputs into a compile folder.

## Stata scratch run details

Command:

```bash
/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do /Users/mriduljoshi/Github/AbilityGrouping/replication_audit/stata_scratch_core.do
```

Log checked:

```text
replication_audit/stata_scratch_core.log
```

Generated output directory:

```text
replication_audit/stata_scratch/
```

Important limitation: this scratch runner intentionally excludes Nigeria/pooled scripts that hard-code `$out` and `$overleaf`. Those outputs are traced to scripts in `PIPELINE_MAP.md`, and existing logs were inspected, but they were not safely rerun in scratch.

## Prioritized fix list

1. Update all release/audit scripts from `main2.tex` to `main_3country_new.tex`.
2. Replace the freeze manifest with a current active-output manifest for `main_3country_new.tex`.
3. Make every Stata script honor caller-supplied `$out` and disable repo copy by default.
4. Add a no-sync, scratch-safe full Stata master that runs Kenya, Liberia, Nigeria, pooled, two-group, peer, assignment, and lesson-completion outputs.
5. Update `check_numeric_claims.py` to use active table names, especially `tab_pooled_itt.tex` rather than deleted `tab_itt.tex`.
6. Decide whether structural verifier prose gates should be updated to the manuscript or the manuscript should be revised. Do not call the structural package verified until this is resolved.
7. Bring `make_paper_summary_figures.py` into the canonical structural run and verifier, or document it as a separate required figure stage.
8. Add a manifest table with columns: artifact, manuscript line, generator, input data, output path, repo path, status, notes.
9. Build a clean compile folder with `main_3country_new.tex`, `bib.bib`, active `stata_output/`, and active `structural_output/`.
10. Only then create a public replication README with data restrictions, Stata/Python versions, exact commands, expected logs, and expected checksums.
