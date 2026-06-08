# Overleaf folder map

Date: 2026-06-06

Overleaf project:

`/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited`

## Active entrypoints observed

- `main2.tex`: canonical Kenya/Liberia paper. Active generated inputs are synced from `4_Stata2/output/`; the current verified live build is `main2.pdf`, 66 pages, 848,806 bytes, with title/author/keyword PDF metadata populated, a clean warning grep, clean artifact/label audit, clean targeted PDF-text artifact scan, and draft/public switch defaulting to draft mode.
- `main_nigeria.tex`: Nigeria tables-only draft.
- `main_3country_new.tex`: integrated three-experiment draft retained for consideration; not canonical. The latest temp scope-gate build is 75 pages and buildable, but it has an unresolved `tab:mechanism` reference, a visible `Table ??`, and unreferenced active exhibit labels.

## `main2.tex` active inputs

`main2.tex` reads tables from `stata_output/`:

- `lib_sumstats`
- `ke_sumstats`
- `tab_balance_1do`
- `lib_attrition`
- `ke_attrition`
- `tab_itt`
- `tab_upper_lower`
- `tab_signal_quality`
- `tab_signal_quality_alt`
- `tab_assignment_cutoffs`
- `tab_classroom_reallocation`
- `tab_track_bins`
- `tab_cutoff_het`
- `tab_dispersion_firststage`
- `tab_peer_effects`
- `tab_peer_effects_exact_kenya`
- `tab_suffstat_kenya`
- `tab_lesson_completion`
- `tab_density_decomp`
- `tab_suffstat_liberia`
- `tab_spec_robust`
- `tab_lee_bounds`
- `tab_classsize_ctrl`
- `tab_ceiling`
- `tab_score_variance`
- `lib_sampleflow`
- `ke_sampleflow`

`main2.tex` reads figures from `stata_output/`:

- `fig_four_margins.pdf`
- `lib_bl_dist.pdf`
- `ke_bl_dist.pdf`
- `lib_dispersion_box.pdf`
- `ke_dispersion_box.pdf`
- `lib_binscatter.pdf`
- `ke_binscatter.pdf`
- `fig_cutoff_het.pdf`
- `fig_posterior_shrinkage.pdf`
- `fig_deterministic_cutoffs.pdf`
- `fig_classroom_reallocation.pdf`
- `lib_el_dist.pdf`
- `ke_el_dist.pdf`
- `lib_classsize.pdf`
- `ke_classsize.pdf`
- `fig_misclass.pdf`
- `fig_track_bins.pdf`

The active `main2.tex` set is 27 tables and 17 figures after removing the data-driven heterogeneity appendix. Reference scans on 2026-06-05 showed that `main2.tex`, `main_nigeria.tex`, `main_3country_new.tex`, and `main_3country.tex` draw active generated exhibits from `stata_output/` rather than from root-level `desc_*`, `diag_*`, `ke_*`, `lib_*`, `fig_a*`, or `tab_a*` files. A broader scan on 2026-06-06 found `stata_output/` references in seven root-level TeX files before old fragments were archived: `isitcredible.tex`, `main2.tex`, `main3.tex`, `main4.tex`, `main_3country.tex`, `main_3country_new.tex`, and `main_nigeria.tex`. After the latest superseded-entrypoint archive pass, only three root TeX files with `stata_output/` references remain: `main2.tex`, `main_3country_new.tex`, and `main_nigeria.tex`.

A read-only audit helper now makes this scan reproducible:

```sh
python3 4_Stata2/audit_overleaf_artifacts.py --show-extra
```

The latest run reports 3 root TeX files with `stata_output/` references, 88 files in `stata_output/`, 88 files referenced by at least one scanned TeX entrypoint, 49 files referenced by `main2.tex`, zero missing referenced files for either all scanned TeX files or `main2.tex`, and zero extra files versus any scanned TeX entrypoint. To additionally verify that the live Overleaf copies match the repo-generated outputs byte-for-byte and that active table/figure labels are integrated in the manuscript, run `python3 4_Stata2/audit_overleaf_artifacts.py --overleaf-dir '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited' --entrypoint main2.tex --repo-output-dir 4_Stata2/output --check-labels`; the current result is 49 active `main2.tex` exhibit files synced byte-for-byte, zero differences, zero missing files, zero refs with missing labels, and zero unreferenced active exhibit labels.

Current root audit on 2026-06-06: the live Overleaf root contains only `.DS_Store`, `archive/`, `bib.bib`, `main2.*`, `main_nigeria.*`, `main_3country_new.tex`, and `stata_output/`. This matches the archive policy in `OVERLEAF_ARCHIVE_PLAN.md`: retain `main2.*` while `main2.tex` is canonical, retain `main_nigeria.*` while `main_nigeria.tex` is an active observed entrypoint, retain `main_3country_new.tex` as a candidate manuscript, and treat `.DS_Store` as transient Finder/Dropbox metadata.

The active diagnostics tables and figures from `03_diagnostics.do` have been regenerated with StataNow/StataMP 19.5 and synced to `stata_output/`. The signal-quality table now writes the R-squared label as `\(R^2\)` so Stata does not treat `$R` as a global macro while writing LaTeX.

The retained legacy/candidate balance tables `ke_balance.tex` and `lib_balance.tex` were referenced only by `main3.tex`. After archiving that superseded entrypoint, both tables were moved from `stata_output/` to `archive/stata_output_unreferenced/` with `MANIFEST_2026-06-06_balance_tables_after_entrypoint_archive.txt`.

Files formerly in `stata_output/` that were not referenced by any root-level TeX entrypoint in the 2026-06-06 scan:

- `analysis_kenya.dta`
- `analysis_liberia.dta`
- `fig_overid_kenya.pdf`
- `fig_overid_kenya_quintile.pdf`
- `tab_dispersion.tex`
- `tab_dispersion_firststage_1do.tex`
- `tab_four_margins.tex`
- `tab_kenya_accounting.tex`
- `tab_lib_sensitivity.tex`

These files have been moved to `archive/stata_output_unreferenced/` with `MANIFEST_2026-06-06.txt`. The archive is reversible, and the post-move artifact audit reports zero missing referenced files and zero extra `stata_output` files versus all scanned TeX entrypoints.

On 2026-06-06, a conservative archive pass moved 112 unreferenced root-level generated artifacts to `archive/legacy_root_outputs/`. The selection rule was: file matched legacy generated-output patterns and neither its filename nor stem appeared in any other root-level `.tex` file. `Tables_combined.tex` and `Tables_combined.zip` were left at root during this pass because older `kenya_new.tex` referenced them, then archived later together with `kenya_new.tex` in `archive/old_fragments/`. The archive manifest is `archive/legacy_root_outputs/MANIFEST_2026-06-06.txt`.

The old standalone draft fragments and their private asset directories have been moved to `archive/old_fragments/` with `MANIFEST_2026-06-06.txt`: `intro.tex`, `empiricalframework.tex`, `isitcredible.tex`, `HeterogeneityAnalysis.tex`, `Replication.tex`, `kenya_new.tex`, `liberia2024.tex`, `liberia_with_text.tex`, `Tables_combined.tex`, `Tables_combined.zip`, `Tables_combined/`, `Replication_Liberia/`, and `Liberia2024/`. The archive is reversible and the post-move rebuild of `main2.tex` remained clean.

The old top-level legacy table directories have been moved to `archive/old_table_dirs/` with `MANIFEST_2026-06-06.txt`: `Tables_Kenya/` and `Tables_Liberia/`. Current non-archived root TeX files do not reference those directories; the only references found were inside already archived files under `archive/`. The archive is reversible and the post-move rebuild of `main2.tex` remained clean.

The latest refreshed temp evidence shows `main_3country_new.tex` can compile after targeted fixes and a Nigeria Stata rerun, but it is not canonical. The forced temp build completed as a 75-page, 874,716-byte PDF and the active candidate exhibits are synced, but the warning grep and artifact audit still flag one unresolved `tab:mechanism` reference and 39 unreferenced active exhibit labels. Until the project explicitly chooses the three-country path and fixes those integration issues, keep its generated Nigeria, pooled, and structural exhibits available and do not archive them.

## Safe organization target

Current/recommended organized layout:

```text
Reading groups revisited/
  main2.tex
  main2.pdf
  main2.log
  main2 auxiliary build byproducts retained while canonical
  main_nigeria.tex
  main_nigeria.pdf
  main_nigeria.log
  main_nigeria auxiliary build byproducts retained while active observed
  main_3country_new.tex
  main_3country_new.pdf (only after live rebuild, if chosen as active)
  bib.bib
  stata_output/
    active generated tables and figures used by current entrypoints
  archive/
    legacy_asset_dirs/
      MANIFEST_2026-06-06.txt
      archived root `output/`, `tables/`, and `figures/` directories
    legacy_root_outputs/
      MANIFEST_2026-06-06.txt
      archived legacy root generated artifacts
    build_artifacts/
      MANIFEST_2026-06-06.txt
      archived inactive `main.*` build artifacts
    misc_fragments/
      MANIFEST_2026-06-06.txt
      archived unreferenced test/demo fragments
    stata_output_unreferenced/
      MANIFEST_2026-06-06.txt
      archived `stata_output/` files not referenced by any scanned root TeX entrypoint
    old_fragments/
      MANIFEST_2026-06-06.txt
      archived old standalone drafts and their private asset directories
    old_table_dirs/
      MANIFEST_2026-06-06.txt
      archived old top-level Kenya/Liberia table directories
    old_entrypoints/
      MANIFEST_2026-06-06_superseded_entrypoints.txt
      archived superseded root entrypoints `main3.tex`, `main4.tex`, and `main_3country.tex`
```

## Root-level files likely stale for `main2.tex`

The main generated-output clutter pass has been completed for unreferenced files matching these root-level groups:

- `desc_*`
- `diag_*`
- `fig2_*`, `fig3_*`, `fig5_*`, `fig6_*`, `fig_a*`
- `ke_*`, `ke2_*`, `lib_*`
- `tab_a*`

Still intentionally left at root for now:

- build byproducts for active or candidate entrypoints such as `main2.*` and `main_nigeria.*`

The orphaned inactive `main.*` build artifacts (`main.aux`, `main.bbl`, `main.blg`, `main.fdb_latexmk`, `main.fls`, `main.log`, `main.out`, `main.pdf`) have been moved to `archive/build_artifacts/`. `main.tex` was not present at root during that pass, so no source file was moved.

The unreferenced root-level `test_tables.tex` file has been moved to `archive/misc_fragments/`. It is a standalone stargazer Cake Data demonstration table, not a paper entrypoint and not included by the current or candidate root TeX files scanned during the archive pass.

The nine `stata_output/` files not referenced by any scanned root-level TeX entrypoint have been moved to `archive/stata_output_unreferenced/`. This removes stale generated tables, unused figures, and copied analysis `.dta` files from the active generated-output folder while preserving them with a manifest.

The superseded root entrypoints `main3.tex`, `main4.tex`, and `main_3country.tex` have been moved to `archive/old_entrypoints/`. After that move, `ke_balance.tex` and `lib_balance.tex` were no longer referenced by any remaining root entrypoint and were moved to `archive/stata_output_unreferenced/` with a separate manifest.

The old standalone manuscript fragments and their private asset directories have been moved to `archive/old_fragments/`. This removes the remaining non-canonical draft fragments from the root while preserving provenance and the assets needed to rebuild those old fragments if needed.

The old top-level `Tables_Kenya/` and `Tables_Liberia/` directories have been moved to `archive/old_table_dirs/`. This removes legacy structural/replication table fragments from the root while preserving the archived table trees and manifest.

The old top-level `output/`, `tables/`, and `figures/` directories have been moved to `archive/legacy_asset_dirs/`. Current non-archived root TeX entrypoints do not reference these directories; the archive preserves the original directory names and includes a manifest with 130 files.

Archive rather than delete. This folder is synced with Overleaf, so preserving reversibility matters. The current active verified `main2.pdf` is 66 pages and 848,806 bytes with title/author/keyword PDF metadata populated; warning grep, artifact audit, repo-output sync, label/reference checks, and targeted PDF-text/prose scans are clean. For detailed pass history, see `PAPER_COMPLETION_AUDIT.md` and `OVERLEAF_ARCHIVE_PLAN.md`.

For an actionable archive manifest, see `OVERLEAF_ARCHIVE_PLAN.md`.
