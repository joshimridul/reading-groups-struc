# Overleaf archive plan

Date: 2026-06-06

Overleaf project:

`/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited`

This plan records how to organize the Overleaf root while the canonical paper target is being finalized. It is intentionally conservative: archive rather than delete, and do not move active inputs until the chosen manuscript has been rebuilt after the move.

## Current recommendation

Keep `main2.tex` as the canonical working paper for now. Treat `main_3country_new.tex` as a buildable integrated extension draft, not a promotion-ready manuscript, until its unresolved `tab:mechanism` reference, unreferenced exhibit labels, Nigeria claims, and structural-counterfactual sections receive a full prose and identification audit.

Current live status: the active verified `main2.pdf` is 66 pages and 848,806 bytes, with title, author, and keyword PDF metadata populated. The warning grep is clean, the artifact/label audit reports 49 active `main2.tex` exhibit files synced byte-for-byte with `4_Stata2/output/`, the targeted PDF-text artifact scan is clean, and the draft/public switch defaults to draft mode. Earlier PDF sizes below are retained as pass history unless explicitly described as current.

## Completed on 2026-06-06

A conservative generated-output archive pass moved 112 unreferenced root-level generated artifacts into:

`archive/legacy_root_outputs/`

The move wrote a reversible manifest at:

`archive/legacy_root_outputs/MANIFEST_2026-06-06.txt`

Selection rule: a file had to match the legacy generated-output patterns below and neither its filename nor stem could appear in any other root-level `.tex` file. `Tables_combined.tex` and `Tables_combined.zip` were intentionally left at root during this pass because older `kenya_new.tex` referenced them; they were later archived together with `kenya_new.tex` in the old-fragments archive pass.

After this move, `main2.tex` was rebuilt from a fresh temp copy of the organized Overleaf folder. The verified `main2.pdf`/`main2.log` were copied back to Overleaf, and the final warning grep was clean.

Subsequent manuscript edits reactivated the Lee-bounds appendix table, replaced the stale combined attrition table with the current Liberia and Kenya attrition tables, tightened the zero-signal/Bayes-assignment theory benchmark, smoothed the introduction prose, referenced the core four-margin and dispersion-first-stage exhibits from the results text, softened the Liberia cutoff-heterogeneity interpretation to match the active table, added an appendix diagnostic roadmap, clarified baseline-score dispersion language, aligned the dispersion estimating equation with the active table notes, tightened the sample-flow/attrition wording against the active sample-flow and missing-endline tables, clarified the Kenya precision and GATES-ranking prose, relabeled the signal-quality table to avoid conflicting `\rho` notation, relabeled the four-margin assignment object as cutoff compliance rather than latent misclassification, changed that summary generator to compute compliance from the treated analytic sample, relabeled the assignment-cutoff table's observed cutoff-rule deviations as rule error rather than latent misclassification, cleaned the assignment-cutoff table caption, aligned EB-control wording with the actual ITT equation, softened cross-experiment mechanism claims, aligned appendix wording around model-implied latent misassignment, polished the title footnote into coauthored voice, aligned the scripted-curricula identification claim with the approximate conditioning strategy, made the score-variance robustness claim statistically conservative, aligned the GATES predictor-list prose with the current forest inputs, aligned appendix figure notes with the clustered inference and cluster-cross-fitting used by the generated tables/code, distinguished the Kenya private-school network from Liberia public-school management under LEAP, softened the theory/peer-identification language so scripted curricula are described as reducing rather than fully eliminating channel collinearity, weakened the Liberia peer-accounting wording to avoid unsupported claims about undetectable true peer effects, softened the introduction's Liberia diagnostic-hurdle language to avoid over-isolating signal quality from organizational costs, revised the headline treatment-effect language to say the experiments do not generate evidence of average gains rather than proving no positive effect, aligned remaining Kenya local-gain language with the same evidentiary standard, separated the exact design-based BH peer expectation from the approximate treatment-interacted cell control, softened residual Kenya ITT zero language while preserving the confidence-bound precision claim, softened Liberia ITT language to reflect the imprecise overall estimate, softened Liberia heterogeneity/conclusion language from generic harm/failure wording to table-supported negative estimates and constraints, distinguished Liberia predictive-sorting claims from the mechanical track-target misfit reduction, aligned peer-identification roster-composition language with the country-specific assignment units, updated the Kenya accounting table note to call Panel A an approximate Borusyak--Hull control function estimate, updated the exact Kenya peer-effects table note to use paper-facing `P_i(1)`/`P_i(0)` notation for the design-based Borusyak--Hull expectation, updated the density-decomposition table note to frame the peer-by-density interaction as an approximate diagnostic rather than a clean structural-rank estimate, updated the Lee-bounds table note to state that the table reports point-estimate bounds without standard errors, tightened the specification-robustness paragraph to state the table-supported interpretation directly, standardized active school grade group terminology, restored active generated-table placement to `[H]` after a sync briefly reintroduced fragile `[!h]` floats, relabeled the approximate peer table/text as a peer/rank diagnostic rather than a final mechanism estimate, clarified active diagnostics table notes, corrected Liberia grade group cutoff terminology, cleaned compiled-text artifacts from generated notes, archived legacy asset directories, tightened productive-time proxy and GATES-ranking wording, tightened the conclusion synthesis around exact implementation, weak predictive information, persistent predictive heterogeneity, and larger Liberia reading classes, clarified that the class-size-control estimates are post-treatment residualization checks rather than mediation evidence or proof that class size is irrelevant, softened the accounting interpretation so it does not isolate which reorganization margin is causal, cleaned remaining PDF text-layer artifacts in active text and generated notes, cleaned residual mixed-grade/within-class source artifacts after a paper-level read-through, standardized active generated table labels away from within-class/between-class hyphen forms, tightened the front-matter contribution framing around similar null average effects arising from different constraints, clarified the conclusion's distinction between Kenya's stronger predictive signal and Liberia's mechanical movement toward implemented track targets, softened Liberia subgroup language to emphasize estimates and point estimates where the interaction and cutoff gradients are imprecise, expanded the Liberia accounting table's panel label from BH shorthand to Borusyak--Hull, tightened the dispersion first-stage sentence to use standardized-score units, cleaned remaining active Liberia GATES/appendix loss-language wording, clarified that teacher attendance is a control in the lesson-completion productive-time check, tightened the Liberia appendix caption from generic misclassification to model-implied latent misassignment, relabeled the Liberia accounting row as absolute EB-to-target mismatch, aligned the introduction's subgroup wording with the later point-estimate language, corrected the dispersion equation's classroom notation from `k(i)` to `c(i)`, aligned the Liberia introduction with the measured-target rather than true-latent-mismatch interpretation, softened the score-variance robustness conclusion so it says the data do not point to distributional reshuffling as the explanation for the small Kenya ITT, softened Liberia upper-track language from classroom deterioration to classroom constraints, aligned the peer-identification example with grade-specific assignment rules, reframed cutoff-compliance wording around observed student track assignments, softened the GATES interpretation around stable heterogeneity and precision, removed code-facing `finsamp` language from the active sample-flow and summary-statistics notes, clarified the active attrition and Lee-bounds table labels, and standardized stale `Kenya Year 1` active table headers to `Kenya`. At that stage, the active verified `main2.pdf` was 65 pages and 841,921 bytes, and the copied-back `main2.log` remained clean. Later paper-quality passes superseded this build.

## Keep at root

Core source files:

- `bib.bib`
- `main2.tex`
- `main2.pdf`
- `main2.log` until the final build is verified elsewhere
- `main_3country_new.tex`
- `main_nigeria.tex`

Archived superseded entrypoints:

- `main3.tex`, `main4.tex`, and `main_3country.tex` have been moved to `archive/old_entrypoints/` with `MANIFEST_2026-06-06_superseded_entrypoints.txt`.
- `main.tex` was absent at root during the 2026-06-06 build-artifact archive pass.

Generated exhibit directory:

- `stata_output/`

The active entrypoint scan shows `main2.tex`, `main_nigeria.tex`, and `main_3country_new.tex` read current generated tables and figures from `stata_output/`.

A broader 2026-06-06 scan found `stata_output/` references in seven root-level TeX files before old fragments were archived: `isitcredible.tex`, `main2.tex`, `main3.tex`, `main4.tex`, `main_3country.tex`, `main_3country_new.tex`, and `main_nigeria.tex`. After the old-fragments and superseded-entrypoint archive passes, `stata_output/` contains 88 files; all 88 are referenced by at least one of the 3 remaining root TeX files with `stata_output/` references, no referenced `stata_output/` file is missing, and there are zero extra files versus all scanned TeX entrypoints. This scan can now be reproduced with:

```sh
python3 4_Stata2/audit_overleaf_artifacts.py --show-extra
```

To additionally verify that the active `main2.tex` Overleaf exhibits match the repo-generated outputs byte-for-byte, run:

```sh
python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir "/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited" \
  --entrypoint main2.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels
```

The current sync and label check reports 49 active `main2.tex` exhibit files synced byte-for-byte, zero differences, zero missing files, zero refs with missing labels, and zero unreferenced active exhibit labels.

## Generated-output archive status

Unreferenced root-level files matching these generated-output patterns have been moved to `archive/legacy_root_outputs/`; referenced exceptions are listed immediately below:

- `desc_*`
- `diag_*`
- `fig2_*`, `fig3_*`, `fig5_*`, `fig6_*`, `fig_a*`
- `ke_*`, `ke2_*`, `ke2_m_*`, `lib_*`
- `kdensity_grade*.pdf`
- `pooled*_fig_quartiles.pdf`
- `tab_a*`
- `Tables_combined.tex` / `Tables_combined.zip`
- `_ignore_main_tables_Ken.tex`
- `_ignore_main_tables_Lib.tex`
- old replication image/PDF artifacts such as `Replication_Liberiahet_*`

No generated-output exceptions remain at root from this pattern group. `Tables_combined.tex`, `Tables_combined.zip`, and `Tables_combined/` are preserved under `archive/old_fragments/` with the old `kenya_new.tex` fragment that referenced them.

## Build-artifact archive status

The orphaned inactive `main.*` build products have been moved to `archive/build_artifacts/` with `MANIFEST_2026-06-06.txt`:

- `main.aux`
- `main.bbl`
- `main.blg`
- `main.fdb_latexmk`
- `main.fls`
- `main.log`
- `main.out`
- `main.pdf`

`main.tex` was absent at root, so no source file was moved. A fresh temp rebuild of `main2.tex` from the organized root completed as a 62-page PDF with a clean warning grep.

The unreferenced demonstration table `test_tables.tex` has also been moved to `archive/misc_fragments/` with `MANIFEST_2026-06-06.txt`. It is a standalone stargazer Cake Data example, not a root entrypoint and not included by the current or candidate paper entrypoints scanned in the Overleaf root. A fresh temp rebuild of `main2.tex` after the move completed as a 64-page PDF with a clean warning grep and clean input-aware label parser.

## Old-fragments archive status

The old standalone manuscript fragments and their private asset directories have been moved to `archive/old_fragments/` with `MANIFEST_2026-06-06.txt`:

- `intro.tex`
- `empiricalframework.tex`
- `isitcredible.tex`
- `HeterogeneityAnalysis.tex`
- `Replication.tex`
- `kenya_new.tex`
- `liberia2024.tex`
- `liberia_with_text.tex`
- `Tables_combined.tex`
- `Tables_combined.zip`
- `Tables_combined/`
- `Replication_Liberia/`
- `Liberia2024/`

The demonstration fragment `test_tables.tex` had already been moved to `archive/misc_fragments/`, so it is not duplicated in this archive. A fresh temp rebuild of `main2.tex` after the old-fragments move completed as a clean 64-page PDF; the verified `main2.pdf` and `main2.log` were copied back to Overleaf and match the temp build byte-for-byte.

## Old table-directory archive status

The old top-level table directories have been moved to `archive/old_table_dirs/` with `MANIFEST_2026-06-06.txt`:

- `Tables_Kenya/` (12 files)
- `Tables_Liberia/` (29 files)

Current non-archived root TeX files do not reference these directories; the only references found were inside already archived files under `archive/`. A fresh temp rebuild of `main2.tex` after the move completed as a clean 64-page PDF; the verified `main2.pdf` and `main2.log` were copied back to Overleaf and match the temp build byte-for-byte.

## Archive after target is chosen

Move any remaining inactive build byproducts to `archive/build_artifacts/` after their entrypoints are archived or explicitly retained:

- `*.aux`
- `*.bbl`
- `*.blg`
- `*.fdb_latexmk`
- `*.fls`
- `*.out`
- stale `*.log` files for inactive entrypoints
- stale PDFs for inactive entrypoints, once the source is archived or explicitly retained

## Do not archive yet

- Any file remaining under `stata_output/`
- `main2.*` while `main2.tex` remains canonical
- `main_nigeria.*` while `main_nigeria.tex` remains an active observed entrypoint
- `main_3country_new.tex` and its live temp-build evidence while the three-country path remains under consideration
- `main_nigeria.tex`, because it is still useful for checking Nigeria tables independently

The `stata_output/` files not referenced by any root-level TeX entrypoint have been moved to `archive/stata_output_unreferenced/` with `MANIFEST_2026-06-06.txt`: `analysis_kenya.dta`, `analysis_liberia.dta`, `fig_overid_kenya.pdf`, `fig_overid_kenya_quintile.pdf`, `tab_dispersion.tex`, `tab_dispersion_firststage_1do.tex`, `tab_four_margins.tex`, `tab_kenya_accounting.tex`, and `tab_lib_sensitivity.tex`. This was an archive, not a deletion.

The old top-level `output/`, `tables/`, and `figures/` directories have been moved to `archive/legacy_asset_dirs/` with `MANIFEST_2026-06-06.txt`. This archived 130 files after confirming that no retained non-archived root TeX entrypoint references those directories. The original directory names are preserved inside the archive, and the active Overleaf root now keeps active generated exhibits under `stata_output/` only.

## Verification after any move

After archiving, rebuild the chosen entrypoint from the Overleaf folder and grep the log:

```sh
latexmk -g -pdf -interaction=nonstopmode -halt-on-error main2.tex
rg -n "undefined|Undefined|Citation .* undefined|There were undefined|Overfull|Underfull|Float too large|duplicate|Label\\(s\\) may have changed|Rerun to get|float specifier" main2.log
```

If the three-country draft becomes canonical, run the same check for `main_3country_new.tex`.

## Latest non-archive note audit

The appendix notes for `fig:track_bins` and `fig:gates` have been aligned with the current generated tables and code: the track-bin figure now states school-grade group clustered inference, and the GATES figure now states cluster-cross-fitted causal-forest predictions plus cluster-robust intervals at school level in Kenya and school-grade group level in Liberia. No files were moved in this pass.

The conclusion has also been aligned with the reallocation and dispersion exhibits: Liberia is now described as mechanically reducing distance to its implemented track targets while still lacking strong endline-predictive sorting, rather than as simply failing to reduce mismatch. No files were moved in this pass.

The abstract and theory benchmark now make the same object distinction: low signal quality limits endline-predictive sorting improvement and true instructional-mismatch reductions, even when the implemented cutoff rule mechanically reduces distance to its own targets. No files were moved in this pass.

The sample-flow notes now use "sample construction" rather than "sample-construction" in the Stata generator, repo-generated tables, and live Overleaf tables, avoiding the compiled text-layer artifact `sampleconstruction`. No files were moved in this pass.

Active manuscript/table-note terminology now uses "school-grade group" rather than "school-grade-group" for the Liberia randomization and clustering unit. The wording was updated in the active manuscript, active Overleaf generated tables, repo generated outputs, and Stata/R generators. No files were moved in this pass.

Active generated table placement now uses `[H]` for the `main2.tex` table inputs and the corresponding active Stata/R generators. This restores the warning-clean Overleaf layout after a sync briefly reintroduced `[!h]` placements that caused float-packing warnings in a temp build. No files were moved in this pass.

The approximate peer-effects table is now captioned and labeled as an approximate peer/rank diagnostic (`tab:peer_effects`), and the results text now states that this estimate is a first-pass channel diagnostic rather than a final peer-effect estimate. No files were moved in this pass.

The peer-identification prose now makes the exclusion restriction explicit before interpreting roster-composition variation: roster differences are not automatically identifying, and the approximate control-function coefficient has a causal peer/rank interpretation only if the exclusion restriction and expected-exposure approximation are credible. No files were moved in this pass.

The peer section now harmonizes grade notation with the theory section: the conditional-independence assumption, exact-BH conditioning set, approximate control-function equation, and scripted-instruction paragraph use `g(i)`/`g(\ell)` consistently. No files were moved in this pass.

The abstract and Kenya introduction now use the same peer/rank caveat as the results section: approximate diagnostics are adverse, but exact control-function and recentering checks do not support a robust causal peer/rank interpretation. No files were moved in this pass.

The peer-effects exclusion restriction now describes the excluded peer-composition object as the score-grade roster of other students in the assignment unit, aligning Assumption 2 with the exact Borusyak--Hull expectation's conditioning set. No files were moved in this pass.

The mismatch terminology now distinguishes absolute EB-to-target mismatch reduction in the four-margin and accounting exhibits from squared track-target misfit in the classroom-reallocation table; the generated table notes and Stata generator were updated with the same labels. No files were moved in this pass.

One root-level test fragment was archived after the latest scan: `test_tables.tex` moved to `archive/misc_fragments/` because it was an unreferenced Cake Data demonstration table rather than a paper source. This was a reversible organization pass.

Active generated inference notes now use consistent paper-facing grammar for clustering units: "the school level in Kenya" and "the school-grade group level in Liberia" where both countries are described. The active Stata/R generators, repo-generated outputs, and Overleaf table inputs were updated together. No files were moved in this pass.

The GATES table note now distinguishes the causal-forest prediction feature set from the sorted-GATES/BLP outcome-regression adjustment: grouped estimates adjust for raw baseline score and randomization-strata fixed effects, not the EB transform. No files were moved in this pass.

The main robustness text now describes the Lee interval and upper endpoint as point-estimate bounds, matching the generated Lee table note that no standard errors are shown. No files were moved in this pass.

The ceiling-effects table note now matches the active Stata generator: OLS and trimmed OLS use EB ability plus strata fixed effects, while the Tobit robustness check uses raw baseline score plus strata fixed effects. No files were moved in this pass.

The retained single-country balance tables `ke_balance.tex` and `lib_balance.tex` were originally left in `stata_output/` because `main3.tex` referenced them, and their generator and synced table notes were cleaned to use country-specific clustering language. After the later superseded-entrypoint archive pass moved `main3.tex` out of the root, these two tables were moved to `archive/stata_output_unreferenced/` with `MANIFEST_2026-06-06_balance_tables_after_entrypoint_archive.txt`.

The cutoff-heterogeneity table note now includes its significance-star legend, and the dispersion-first-stage table note now distinguishes baseline-score specifications from predicted-outcome/endline-score specifications in the same way as the Stata generator. No files were moved in this pass.

The active diagnostics outputs were regenerated with StataNow/StataMP 19.5 after the note audit. The signal-quality table writer now uses `\(R^2\)` rather than dollar-delimited math to avoid Stata global-macro expansion while writing the LaTeX source. No files were moved in this pass.

The active manuscript wording now avoids residual "Kenya zero/null" phrasing in the accounting, lesson-completion, ceiling-effects, and score-variance paragraphs. These passages describe the evidence as a small Kenya ITT or measured sorting changes that do not translate into average score gains. No files were moved in this pass.

The latest numeric-claim wording pass also softened two overstatements: the introduction now says the experiments do more than report two imprecise average effects, and the Kenya class-size-control sentence now says coefficients are essentially unchanged rather than unchanged exactly. No files were moved in this pass.

The latest conclusion-tone wording pass softened two final-looking claims in the conclusion: measured informational gains did not translate into average achievement gains, and improved sorting by itself is not enough to generate detectable average gains. No files were moved in this pass.

The latest lesson-completion data-grain pass clarified the data-section description of NewGlobe administrative records. The active data section now says lesson completion and teacher attendance are used at the school-grade lesson-cell level, aligning the data prose with `07_lesson_completion.do` and `tab_lesson_completion.tex`. No files were moved in this pass.

The latest lesson-completion table-transparency pass regenerated `tab_lesson_completion.tex` from `07_lesson_completion.do` with a control-mean row for each estimation sample. This makes the manuscript's approximately 17\% control-group completion-rate scale calculation visible in the active table. No files were moved in this pass.

The latest robustness-prose precision pass tightened two active robustness claims: raw-baseline replacement leaves ITT estimates unchanged to three decimals, and Kenya class-size controls leave the track coefficients essentially unchanged. No files were moved in this pass.

An earlier `stata_output` archive pass moved the nine files not referenced by any scanned root-level TeX entrypoint to `archive/stata_output_unreferenced/` with a manifest. Its post-move audit reported 90 files in `stata_output/`, all 90 referenced by at least one scanned entrypoint, zero missing referenced files, and zero extras versus all scanned entrypoints. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF.

The latest superseded-entrypoint archive pass moved `main3.tex`, `main4.tex`, and `main_3country.tex` to `archive/old_entrypoints/` with a manifest. The only generated files made unreferenced by that move, `ke_balance.tex` and `lib_balance.tex`, were moved to `archive/stata_output_unreferenced/` with a separate manifest. The post-move audit reports 3 root TeX files with `stata_output/` references, 88 files in `stata_output/`, all 88 referenced by at least one remaining root entrypoint, zero missing referenced files, zero extras versus all scanned entrypoints, and 49 active `main2.tex` exhibit files synced byte-for-byte with `4_Stata2/output/`. A fresh temp rebuild of `main2.tex` from the organized folder completed as a clean 65-page, 841,921-byte PDF.

The latest source-hygiene pass changed only active `main2.tex`, removing the stale internal comment block about removed minimum-distance and Liberia-sensitivity figures. The remaining comment lines are section dividers or table-group labels, not draft notes. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,921-byte PDF, and the verified `main2.pdf` and `main2.log` were copied back to Overleaf byte-for-byte.

A metadata cleanup removed `archive/.DS_Store`. The root `.DS_Store` reappeared immediately, likely because the folder is managed by Finder/Dropbox; it is transient macOS metadata rather than an active paper source or generated exhibit.

The latest front-matter polish pass added keywords and JEL codes to active `main2.tex`. A fresh temp rebuild completed as a clean 65-page, 843,605-byte PDF, the PDF text layer contains the new keywords/JEL lines, the warning grep and artifact audit remained clean, and the verified `main2.pdf` and `main2.log` were copied back to Overleaf byte-for-byte.

The latest visible text-artifact cleanup changed active `main2.tex` and synchronized generated table notes to remove remaining joined words in the compiled PDF text layer (`withingrade`, `Metaanalyses`, and `gradebased`). A fresh temp rebuild completed as a clean 65-page, 843,553-byte PDF, the targeted PDF text scan is empty, the warning grep and artifact audit remained clean, and the verified `main2.pdf` and `main2.log` were copied back to Overleaf byte-for-byte.

A broader visible text-artifact cleanup then removed the remaining targeted joined compounds found by a longer `pdftotext` scan, including `gradelevel`, `treatmentcontrol`, `baselinescored`, `treatmentinteracted`, `treatmentinduced`, `schoolclustered`, `gradedispersion`, `differentlyinformative`, `baselineability`, and `classroomlevel`. The pass also rendered the de Roux--Riehl bibliography-title hyphen with `\mbox{-}` so the extracted text preserves `higher-achieving`. A fresh temp rebuild completed as a clean 65-page, 843,554-byte PDF, the broad targeted PDF text scan is empty, the warning grep and artifact audit remained clean, and the verified `main2.pdf` and `main2.log` were copied back to Overleaf byte-for-byte.

The latest public-release gate pass changed only active `main2.tex`: it now defines `\publicversionfalse` and uses that switch to control whether the title page prints `PRELIMINARY --- PLEASE DO NOT CIRCULATE`. The default draft build is intentionally unchanged; flipping the switch to `\publicversiontrue` suppresses the circulation marker and leaves the date as `\today`. A fresh temp rebuild completed as a clean 65-page, 843,554-byte PDF, the PDF text layer still contains the draft marker by default plus the keywords/JEL lines, the warning grep and artifact audit remained clean, and the verified `main2.pdf` and `main2.log` were copied back to Overleaf byte-for-byte.

The latest LaTeX typography lint pass changed active `main2.tex` plus active generated table notes and their Stata generators. It fixed abbreviation-aware sentence spacing for `SD`, `ITT`, `GATES`, and generated-table `FE` notes, changed the GATES methods citation to `\citet`, tightened appendix figure-reference spacing, and spelled out attrition/signal-quality note abbreviations. A fresh temp rebuild completed as a clean 65-page, 843,582-byte PDF; the warning grep, artifact audit, copied-back byte comparison, and focused lacheck missing-spacing/ref-hint scan are clean.

The latest methods-alignment pass changed only active `main2.tex`: the exact Borusyak--Hull paragraph now states that Table~\ref{tab:peer_effects_exact_kenya} uses design-based `\mu_i^{BH}` together with flexible controls in own score interacted with treatment and grade, and the orthogonality paragraph refers to flexible own-score controls rather than "the same" controls. A fresh temp rebuild completed as a clean 65-page, 843,646-byte PDF; the warning grep, artifact audit, copied-back byte comparison, and focused PDF-text scan are clean.

The latest prose-tightening pass changed only active `main2.tex`: it made the dispersion and peer-identification transitions more paper-facing and removed a repeated "The data therefore" construction from the score-variance robustness paragraph. A fresh temp rebuild completed as a clean 65-page, 843,534-byte PDF; the warning grep, artifact audit, copied-back byte comparison, and targeted source/PDF phrase scans are clean.

The latest reproducibility hygiene pass found zero stale-note hits in the active `main2.tex` table input set for the checked strings (`[!h]`, old cluster-note language, old Borusyak--Hull/BH labels, `finsamp`, joined-grade terms, and old front-facing abbreviations). It also updated the retained repo-only `tab_classsize_diag.tex` output and `03_diagnostics.do` generator to use the current country-specific clustering note if that inactive diagnostic is regenerated. No Overleaf files moved, and the active PDF was unchanged.

The latest attrition-methods wording pass changed no files outside `main2.tex`. It clarifies that the main ITT coefficient is the observed-endline-sample estimand and that reading it as the full analytic-sample effect requires nonselective outcome observation, with the existing attrition diagnostics and Lee bounds providing the robustness evidence. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF.

The latest exhibit-navigation wording pass changed no files outside `main2.tex`. It now refers to sample-flow exhibits as Appendix Tables A1--A2 and attrition regressions as regular Tables 4--5, matching the compiled labels. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF.

An earlier old-fragments archive pass moved old standalone drafts and their private asset directories to `archive/old_fragments/` with a manifest. Its post-move audit reported 6 root TeX files with `stata_output/` references, 90 files in `stata_output/`, all 90 referenced by at least one scanned entrypoint, zero missing referenced files, and zero extras versus all scanned entrypoints. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest institutional-interpretation wording pass changed no tables or generated outputs. It reframes the Kenya-Liberia institutional contrast as an interpretation consistent with the evidence, states that these channels are not experimentally isolated, and cautions against treating diagnostic accuracy as independent of the production environment. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest headline-caveat wording pass changed no tables or generated outputs. It aligns the abstract and early introduction with the body-text caveats: diagnostics now "point to" different constraints and requirements rather than claiming the experiments cleanly identify separate reasons. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest requirements-language wording pass changed no tables or generated outputs. It softens the Liberia and Kenya synthesis paragraphs: Liberia's assignment gains are described as not accompanied by positive achievement effects, and Kenya is described as clearing the signal-quality part of the test while exposing the second requirement. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest conclusion-alignment wording pass changed no tables or generated outputs. It aligns the conclusion with the caveated introduction: diagnostics now point to constraints rather than fully explaining the shared absence of average gains, and the policy sentence says to look for evidence that both thresholds are cleared. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest generated-note and folder-organization pass corrected the retained legacy combined attrition table from "academy-grade group" to "school-grade group" in the repo legacy source, repo output, and live Overleaf `stata_output/tab_attrition_1do.tex`. It also archived the unreferenced top-level `Tables_Kenya/` and `Tables_Liberia/` directories under `archive/old_table_dirs/` with a manifest. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, the artifact audit still reports zero missing referenced `stata_output` files and zero extras versus all scanned entrypoints, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest methods-alignment pass changed the peer-effects random-assignment assumption in `main2.tex` from unconditional random assignment to random assignment conditional on the stratum, `S_j`. The surrounding prose now says Assumption 1 holds by within-stratum randomization and describes the Borusyak--Hull shock as treatment assignment within strata. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, the artifact audit still reports zero missing referenced `stata_output` files and zero extras versus all scanned entrypoints, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest design-language pass corrected Liberia cutoff terminology from grade-specific to grade group where the manuscript and generated notes discuss Liberia distance-from-cutoff diagnostics. The Stata diagnostics generator, repo output, live Overleaf `tab_cutoff_het.tex`, and three `main2.tex` figure notes were updated together. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, the artifact audit still reports zero missing referenced `stata_output` files and zero extras versus all scanned entrypoints, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest compiled-text artifact and retained pooled-note cleanup pass changed Liberia cutoff notes from "grade-group" to "grade group" to avoid the PDF text-layer artifact `gradegroup`, and corrected the retained pooled ITT table note for country-specific clustering units. The pooled Stata generator, repo output, live Overleaf `tab_pooled_itt.tex`, diagnostics generator/output, live Overleaf `tab_cutoff_het.tex`, and `main2.tex` figure notes were updated consistently. A fresh temp rebuild of `main2.tex` remained a clean 64-page PDF, the warning grep and artifact audit were clean, a PDF-text scan was clean for the known joined-word artifacts, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest legacy asset-directory archive pass moved the old top-level `output/`, `tables/`, and `figures/` directories to `archive/legacy_asset_dirs/` with a manifest. Current non-archived root TeX entrypoints do not reference those directories. After the move, the Overleaf root directories are only `archive/` and `stata_output/`; the artifact audit still reports zero missing referenced `stata_output` files and zero extras versus all scanned entrypoints. A fresh temp rebuild of `main2.tex` from the organized root remained a clean 64-page PDF with a clean warning grep.

The latest productive-time proxy and GATES-ranking wording pass changed only `main2.tex`. The Kenya lesson-completion paragraph now says the administrative lesson-completion measure is one observable component of productive time and narrower than total effective instructional time. The sorted-GATES paragraph now names Group 1 and Group 5 explicitly, matching the generated table note that Group 1 is the lowest predicted-effect quintile and Group 5 is the highest. A fresh temp rebuild of `main2.tex` completed as a clean 65-page PDF, the warning grep, artifact audit, and PDF-text artifact scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest conclusion-synthesis wording pass changed only `main2.tex`. The conclusion now separates exact implementation from the Liberia signal/classroom constraints: the rule was implemented exactly and mechanically moved students closer to track targets, but the diagnostic had little predictive information, classrooms remained heterogeneous on predictive dimensions, and reading-class sizes rose by roughly one-third. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,212-byte PDF, the warning grep, artifact audit, and PDF-text scans for known joined-word artifacts and stale conclusion phrases were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest class-size-control caveat pass changed only `main2.tex`. The Liberia heterogeneity paragraph now calls the class-size-control specification a post-treatment residualization check and says it does not identify the separate causal contribution of class size. The robustness paragraph now also says the class-size-control estimates should not be interpreted as a causal mediation exercise or as evidence that class size is irrelevant. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,345-byte PDF, the warning grep, artifact audit, and PDF-text scan for the replaced mediation wording were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

An accounting-interpretation caveat pass changed only `main2.tex`. The Kenya accounting paragraph replaced stronger "succeeds on its own terms" language; a later terminology pass now describes those objects as measured classroom margins rather than structural assignment gains. The Liberia accounting paragraph says the evidence is more consistent with broader reorganization constraints than with a peer composition channel, but it does not isolate which reorganization margin is causal. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,422-byte PDF, the warning grep, artifact audit, and PDF-text scan for the replaced accounting overclaim were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest PDF text-artifact cleanup pass changed wording in `main2.tex`, active generated table outputs, and their Stata/R generators, with no estimate changes. Hyphenated forms that `pdftotext` joined were rewritten as spaced forms, including school grade group, control function, randomization stratum, class size, reading class size, within class variance, score based, cross grade, and track target language. The phrase "become equally more mixed-grade" now reads "also become more mixed by grade." A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,524-byte PDF, the warning grep and artifact audit were clean, the PDF-text scan was clean for the target joined-word artifacts, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest argument-flow and residual PDF text-artifact pass reviewed the active abstract, introduction, empirical strategy, results, robustness, and conclusion for overclaiming and unresolved placeholders. The main claims remain caveated to diagnostic and table-supported evidence. The pass changed remaining active-source phrases from "mixed-grade exposure" to "mixed grade exposure" and from "within-class" forms to "within class" forms where they risked PDF text-layer artifacts; the retained inactive class-size diagnostic generator/output now says "school grade level." A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,519-byte PDF, the warning grep and artifact audit were clean, the PDF-text scan was clean for the target joined-word artifacts including `mixedgrade`, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest active generated-table label cleanup pass changed only labels and captions in active and retained generated tables. The active classroom-reallocation, dispersion-first-stage, and score-variance tables now use spaced "within class" and "between class" labels in their Stata generators, repo outputs, and live Overleaf copies. Retained Nigeria classroom-reallocation and score-variance outputs were updated in parallel. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,522-byte PDF, the warning grep and artifact audit were clean, the PDF-text scan was clean for the target joined-word artifacts including `withinclass` and `betweenclass`, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest front-matter contribution-framing pass changed one introduction contribution sentence. It now says the two-experiment design gives leverage on why similar null average effects can arise from different constraints, rather than saying more loosely that it explains why ability grouping has different effects across settings. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,541-byte PDF, the warning grep, artifact audit, active exhibit sync check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest conclusion signal/target distinction pass changed one conclusion sentence. It now says that neither Kenya's stronger predictive signal nor Liberia's mechanical movement toward implemented track targets was accompanied by average achievement gains once classroom-reorganization margins were included. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,578-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest Liberia subgroup wording pass changed only `main2.tex`. The treatment-effects and heterogeneity sections now refer to the Liberia upper-track total, negative point estimates, and largest negative estimates rather than saying students "lose" or that negative estimates are definitively concentrated. This keeps the prose aligned with the imprecise upper-track interaction and suggestive tercile/cutoff-gradient evidence. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,648-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest Liberia Borusyak--Hull table-label pass changed the active `tab_suffstat_liberia.tex` panel label from "Approximate BH peer estimate" to "Approximate Borusyak--Hull peer estimate" in `4_Stata2/04_structural.do`, repo output, and live Overleaf `stata_output/`. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,738-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest deterministic-cutoff caption and dispersion-units pass changed the active `tab_assignment_cutoffs.tex` caption from "Recovered deterministic assignment cutoffs" to "Deterministic assignment cutoffs" in `4_Stata2/04_structural.do`, repo output, and live Overleaf `stata_output/`. It also changed the `main2.tex` dispersion first-stage sentence to report the coefficient as a reduction in each student's absolute deviation from the classroom mean, measured in standardized-score units. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,768-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest Liberia heterogeneity wording and productive-time data-description pass changed only `main2.tex`. Remaining active "losses" language in the Liberia GATES paragraph, cutoff-heterogeneity figure note, track-bin figure note, and appendix roadmap now uses "negative estimates," "most negative point estimates," or "more or less negative predicted effects." The data section now says lesson completion is the productive-time proxy and teacher attendance enters as a control. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,912-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest latent-misassignment and mismatch-label pass changed `main2.tex`, `4_Stata2/04_structural.do`, `4_Stata2/output/tab_suffstat_liberia.tex`, and the live Overleaf `stata_output/tab_suffstat_liberia.tex`. The appendix figure caption now says "Model-Implied Latent Misassignment" and the note says "predicted latent misassignment," preserving the distinction from observed rule error. The Liberia accounting table row now says `\Delta` absolute EB-to-target mismatch, matching the empirical-strategy text and Kenya accounting table. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,926-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest introduction wording pass changed only `main2.tex`: the Liberia summary paragraph now says the negative point estimates are concentrated in the upper track and extend across the ability distribution, aligning the introduction with the later precision caveat on the upper-track interaction. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,960-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest dispersion-equation notation pass changed only `main2.tex`: the within-class-dispersion equation now uses `c(i)` for the reading classroom mean rather than `k(i)`, avoiding a conflict with the track index notation used elsewhere. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 842,003-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest Liberia measured-target wording pass changed only `main2.tex`: the introduction now says regrouping reduces measured EB-to-track-target mismatch and moves students toward implemented track targets, rather than implying proven reductions in true latent mismatch. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,898-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest score-variance distributional-reshuffling wording pass changed only `main2.tex`: the measurement/distributional-concerns paragraph now says the data do not point to distributional reshuffling as the explanation for the small Kenya ITT, rather than saying the ITT is unlikely to be an artifact of reshuffling. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,904-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest Liberia upper-track-constraint wording pass changed only `main2.tex`: the introduction and heterogeneity section now describe the suggestive Liberia pattern as more consistent with constraints in the upper-track classroom, rather than deterioration of that classroom. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,907-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest peer-identification grade-specificity and cutoff-compliance wording pass changed only `main2.tex`: the peer-identification example now conditions on the same baseline score and enrolled grade before saying students share the same deterministic track, and the deterministic-cutoff paragraph and figure note now describe observed student track assignments rather than assignment units as following the published cutoffs. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,975-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest GATES interpretation-softening pass changed only `main2.tex`: the robustness section now frames the causal-forest exercise as testing for stable policy-relevant heterogeneity beyond the average effect, says Kenya's reversed realized ranking illustrates prediction instability rather than proving it, and treats the Liberia pattern as consistent with low signal quality while acknowledging limited precision. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,830-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest sample-flow and summary-statistics note pass changed only generated table notes and labels in `4_Stata2/01_descriptives.do`, repo outputs, and live Overleaf `stata_output/`. The active sample-flow tables now use the paper-facing row label "Analytic sample" and define it in words; the summary-statistics notes no longer expose `finsamp==1`. Estimates and counts are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,931-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan for leaked `finsamp` language were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest attrition and Lee-bounds table-label pass changed only generated table labels/notes in `4_Stata2/01_descriptives.do`, `4_Stata2/06_robustness.do`, repo outputs, and live Overleaf `stata_output/`. The active attrition tables now label the unadjusted missing-endline shares as `T missing` and `C missing`, and the Lee-bounds table now labels the attrition difference row explicitly. Estimates and rates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,944-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan for the old ambiguous labels were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest class-size and active table-header audit verified that realized reading class size is generated as treatment-track classes in treatment and grade classes in control, matching the manuscript's post-treatment residualization interpretation of class-size controls. The only edit was to standardize stale active table headers from `Kenya Year 1` to `Kenya` in `4_Stata2/04_structural.do`, `tab_assignment_cutoffs.tex`, and `tab_classroom_reallocation.tex`. Values are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 65-page, 841,921-byte PDF, the warning grep, artifact audit, active exhibit sync and label check, and PDF-text scan for stale `Kenya Year 1` labels were clean, and the verified `main2.pdf`/`main2.log` were copied back to Overleaf byte-for-byte.

The latest numeric-claim audit changed no manuscript or generated-output files. It checked the active abstract, introduction, results, robustness, and conclusion numeric claims against the live Overleaf tables for ITT effects, signal quality, classroom reallocation, dispersion, peer/accounting diagnostics, Lee bounds, GATES, ceiling effects, and score variance. The checked claims matched the active tables or acceptable rounded values, and a PDF text scan found no stale joined-word or code-label artifacts. Because no paper source changed, no rebuild was needed beyond the already verified clean 65-page, 841,921-byte `main2.pdf`.

The latest exact-BH peer/rank wording pass changed only `main2.tex`. It clarifies that the exact checks put the coefficient on realized or recentered peer exposure close to zero, while the nonzero coefficient on `\mu_i^{BH}` is a coefficient on predictable exposure induced by the assignment rule and roster composition rather than residual peer/rank variation used for identification. Estimates are unchanged. A fresh temp rebuild of `main2.tex` completed as a clean 66-page, 847,355-byte PDF; the warning grep, artifact audit, active exhibit sync and label check, PDF-text scan, and byte-for-byte live sync checks were clean.

The latest PDF text-layer polish pass changed only wording and generated-table notes/generators, with no estimate, sample, model, or inference changes. Hyphenated phrases that were still producing joined `pdftotext` artifacts were rewritten as spaced paper-facing forms, including within grade, within class, grade group assignment, and school grade group terminology in active table notes. A fresh temp rebuild of `main2.tex` completed as a clean 66-page, 847,365-byte PDF; the warning grep, artifact audit, active exhibit sync and label check, targeted PDF-text artifact scan, and byte-for-byte live sync checks were clean.

The latest theory productive-time wording pass changed only `main2.tex`. The productive-time channel now frames grade dispersion as raising the teacher's coordination and classroom-management burden rather than claiming that each student's probability of disruption rises with developmental distance from the classroom's modal stage. This keeps the model's `\tau_c(N_c,V^g_c)` channel while making the behavioral claim more conservative. A fresh temp rebuild of `main2.tex` completed as a clean 66-page, 847,386-byte PDF; the warning grep, artifact audit, active exhibit sync and label check, PDF-text scan for the revised wording, and byte-for-byte live sync checks were clean.

The latest LaTeX style-lint pass changed only `main2.tex`, adding `\@` after the acronym `ATE` in the theory proof sketch so TeX uses correct sentence spacing before "Part (ii)." A fresh temp rebuild of `main2.tex` completed as a clean 66-page, 847,392-byte PDF; the warning grep, artifact audit, active exhibit sync and label check, and byte-for-byte live sync checks were clean. A focused `lacheck` check confirms the prior real `missing \@` warning is gone; remaining `lacheck` messages are known false positives from theorem declarations, appendix group endings, and generated table alignment syntax.

The latest public-version dry run changed only a temp copy of `main2.tex`, flipping `\publicversionfalse` to `\publicversiontrue`. The temp public PDF built cleanly as a 66-page, 846,183-byte PDF, with title, author, and keyword PDF metadata populated; its text layer contains the title, authors, current date, keywords, and JEL codes, but not `PRELIMINARY --- PLEASE DO NOT CIRCULATE`. The temp artifact/label audit remained clean. No live Overleaf source was changed; live `main2.tex` still defaults to draft mode until the authors choose to circulate a public version.

The latest three-country scope-gate run changed no live Overleaf files. A forced temp rebuild of `main_3country_new.tex` completed as a 75-page, 874,716-byte PDF, but the log and PDF text confirm an unresolved `tab:mechanism` reference (`Table ??` in the peer-effects discussion). The temp artifact/label audit reports 67 active candidate exhibits synced byte-for-byte with `4_Stata2/output`, zero missing referenced files, one missing label, and 39 unreferenced active exhibit labels. The candidate should stay retained but not canonical until those integration issues and the broader Nigeria/structural identification claims are audited.

The latest conclusion generalization pass changed only `main2.tex`. The final cross-domain paragraph now says the two experiments "illustrate" the assignment-rule lesson rather than saying they "show" it, keeping the conclusion aligned with the paper's identification caveats. A fresh temp rebuild of `main2.tex` completed as a clean 66-page, 847,392-byte PDF; the warning grep, artifact audit, active exhibit sync and label check, PDF-text confirmation, and byte-for-byte live sync checks were clean.
