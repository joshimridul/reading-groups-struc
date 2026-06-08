# Paper release worktree triage

Generated: 2026-06-06T18:16:45-07:00

This read-only triage separates the dirty worktree into release-review buckets for the canonical Kenya/Liberia paper. It does not stage, restore, remove, or commit files.

If `PAPER_RELEASE_CANDIDATE_PATHS.txt` or `PAPER_RELEASE_CLEANUP_PATHS.txt` exists, treat it as review input for a future staging/cleanup pass, not as an instruction to stage or remove blindly.

## Summary

- Changed/untracked paths: 161
- Release-candidate review set: 78 paths
- Separate extension/legacy/generated review set: 79 paths
- Explicit cleanup decisions: 5 paths

## Recommended Release Order

1. Decide whether the live manuscript should remain draft or be switched to public mode.
2. Review the release-candidate set below: guardrails/docs, canonical Kenya/Liberia pipeline code, and active `main2.tex` outputs.
3. Keep Nigeria, three-country, structural-extension, supplemental-diagnostic, inactive-output, and legacy work out of the Kenya/Liberia release unless the paper scope changes.
4. Resolve local metadata and deleted-file decisions before tagging or committing a final release.

## Release-Candidate Review Set

These paths are the plausible Kenya/Liberia paper release set. They still require human review before staging because the worktree contains many related changes.

- ` M .gitignore`
- ` M 4_Stata2/README.md`
- ` M 4_Stata2/build_main2_tables.py`
- ` M README.md`
- `?? 4_Stata2/audit_overleaf_artifacts.py`
- `?? 4_Stata2/check_numeric_claims.py`
- `?? 4_Stata2/check_pdf_render.py`
- `?? 4_Stata2/check_public_version.py`
- `?? 4_Stata2/check_release_readiness.py`
- `?? 4_Stata2/embed_active_figure_fonts.py`
- `?? 4_Stata2/triage_release_worktree.py`
- `?? 4_Stata2/verify_freeze_manifest.py`
- `?? OVERLEAF_ARCHIVE_PLAN.md`
- `?? OVERLEAF_FOLDER_MAP.md`
- `?? PAPER_COMPLETION_AUDIT.md`
- `?? PAPER_FINAL_READINESS.md`
- `?? PAPER_RELEASE_CANDIDATE_PATHS.txt`
- `?? PAPER_RELEASE_CLEANUP_PATHS.txt`
- `?? PAPER_RELEASE_WORKTREE_TRIAGE.md`
- `?? PAPER_REPRODUCIBILITY_FREEZE.md`
- ` M 3_Python/00_clean_kenya.py`
- ` M 4_Stata2/00_clean_kenya.do`
- ` M 4_Stata2/01_descriptives.do`
- ` M 4_Stata2/02_main_analysis.do`
- ` M 4_Stata2/03_diagnostics.do`
- ` M 4_Stata2/04_structural.do`
- ` M 4_Stata2/06_robustness.do`
- ` M 4_Stata2/07_lesson_completion.do`
- ` M 4_Stata2/output/fig_classroom_reallocation.pdf`
- ` M 4_Stata2/output/fig_cutoff_het.pdf`
- ` M 4_Stata2/output/fig_deterministic_cutoffs.pdf`
- ` M 4_Stata2/output/fig_four_margins.pdf`
- ` M 4_Stata2/output/fig_misclass.pdf`
- ` M 4_Stata2/output/fig_posterior_shrinkage.pdf`
- ` M 4_Stata2/output/fig_track_bins.pdf`
- ` M 4_Stata2/output/ke_attrition.tex`
- ` M 4_Stata2/output/ke_binscatter.pdf`
- ` M 4_Stata2/output/ke_bl_dist.pdf`
- ` M 4_Stata2/output/ke_classsize.pdf`
- ` M 4_Stata2/output/ke_dispersion_box.pdf`
- ` M 4_Stata2/output/ke_el_dist.pdf`
- ` M 4_Stata2/output/ke_sampleflow.tex`
- ` M 4_Stata2/output/ke_sumstats.tex`
- ` M 4_Stata2/output/lib_attrition.tex`
- ` M 4_Stata2/output/lib_binscatter.pdf`
- ` M 4_Stata2/output/lib_bl_dist.pdf`
- ` M 4_Stata2/output/lib_classsize.pdf`
- ` M 4_Stata2/output/lib_dispersion_box.pdf`
- ` M 4_Stata2/output/lib_el_dist.pdf`
- ` M 4_Stata2/output/lib_sampleflow.tex`
- ` M 4_Stata2/output/lib_sumstats.tex`
- ` M 4_Stata2/output/tab_assignment_cutoffs.tex`
- ` M 4_Stata2/output/tab_balance_1do.tex`
- ` M 4_Stata2/output/tab_ceiling.tex`
- ` M 4_Stata2/output/tab_classroom_reallocation.tex`
- ` M 4_Stata2/output/tab_classsize_ctrl.tex`
- ` M 4_Stata2/output/tab_cutoff_het.tex`
- ` M 4_Stata2/output/tab_density_decomp.tex`
- ` M 4_Stata2/output/tab_dispersion_firststage.tex`
- ` M 4_Stata2/output/tab_itt.tex`
- ` M 4_Stata2/output/tab_lee_bounds.tex`
- ` M 4_Stata2/output/tab_lesson_completion.tex`
- ` M 4_Stata2/output/tab_peer_effects.tex`
- ` M 4_Stata2/output/tab_score_variance.tex`
- ` M 4_Stata2/output/tab_signal_quality.tex`
- ` M 4_Stata2/output/tab_signal_quality_alt.tex`
- ` M 4_Stata2/output/tab_spec_robust.tex`
- ` M 4_Stata2/output/tab_suffstat_kenya.tex`
- ` M 4_Stata2/output/tab_suffstat_liberia.tex`
- ` M 4_Stata2/output/tab_track_bins.tex`
- ` M 4_Stata2/output/tab_upper_lower.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya.tex`

## Keep Separate Unless Scope Changes

These paths belong to Nigeria, three-country, structural, supplemental-diagnostic, inactive generated-output, or legacy work. They should not be mixed into a clean Kenya/Liberia release without an explicit scope decision.

- `?? 3_Python/00_clean_nigeria.py`
- `?? 3_Python/build_nigeria_assessments_long.py`
- `?? 3_Python/build_nigeria_raw_panels.py`
- `?? 3_Python/nigeria_full_stack_replication.py`
- `?? 3_Python/run_nigeria_irt_outcomes.py`
- `?? 4_Stata2/00_clean_nigeria.do`
- `?? 4_Stata2/02_nigeria_main_analysis.do`
- `?? 4_Stata2/03_pooled_analysis.do`
- `?? 4_Stata2/_master_nigeria.do`
- `?? 4_Stata2/output/tab_ng_attrition.tex`
- `?? 4_Stata2/output/tab_ng_balance.tex`
- `?? 4_Stata2/output/tab_ng_ceiling.tex`
- `?? 4_Stata2/output/tab_ng_classroom_reallocation.tex`
- `?? 4_Stata2/output/tab_ng_classsize_ctrl.tex`
- `?? 4_Stata2/output/tab_ng_density_decomp.tex`
- `?? 4_Stata2/output/tab_ng_dispersion.tex`
- `?? 4_Stata2/output/tab_ng_irt.tex`
- `?? 4_Stata2/output/tab_ng_irt_interact.tex`
- `?? 4_Stata2/output/tab_ng_lee_bounds.tex`
- `?? 4_Stata2/output/tab_ng_over_terms.tex`
- `?? 4_Stata2/output/tab_ng_over_terms_interact.tex`
- `?? 4_Stata2/output/tab_ng_peer_effects.tex`
- `?? 4_Stata2/output/tab_ng_sampleflow.tex`
- `?? 4_Stata2/output/tab_ng_score_variance.tex`
- `?? 4_Stata2/output/tab_ng_signal_quality.tex`
- `?? 4_Stata2/output/tab_ng_spec_robust.tex`
- `?? 4_Stata2/output/tab_ng_suffstat.tex`
- `?? 4_Stata2/output/tab_ng_sumstats.tex`
- `?? 4_Stata2/output/tab_ng_t2_ete.tex`
- `?? 4_Stata2/output/tab_ng_t2_ete_interact.tex`
- `?? 4_Stata2/output/tab_ng_t2_mte.tex`
- `?? 4_Stata2/output/tab_ng_t2_mte_interact.tex`
- `?? 4_Stata2/output/tab_ng_t2_over_time.tex`
- `?? 4_Stata2/output/tab_ng_t2_over_time_interact.tex`
- `?? 4_Stata2/output/tab_ng_t3_ete.tex`
- `?? 4_Stata2/output/tab_ng_t3_ete_interact.tex`
- `?? 4_Stata2/output/tab_ng_t3_mte.tex`
- `?? 4_Stata2/output/tab_ng_t3_mte_interact.tex`
- `?? 4_Stata2/output/tab_ng_t3_over_time.tex`
- `?? 4_Stata2/output/tab_ng_t3_over_time_interact.tex`
- `?? 4_Stata2/output/tab_ng_track_bins.tex`
- `?? 4_Stata2/output/tab_ng_upper_lower.tex`
- `?? 4_Stata2/output/tab_pooled_dispersion.tex`
- `?? 4_Stata2/output/tab_pooled_gradient.tex`
- `?? 4_Stata2/output/tab_pooled_itt.tex`
- `?? 4_Stata2/output/tab_pooled_peer_effects.tex`
- `?? 4_Stata2/output/tab_pooled_upper_lower.tex`
- `?? HANDOVER_NIGERIA.md`
- `?? 3_Python/README_structural.md`
- `?? 3_Python/bootstrap_counterfactuals.py`
- `?? 3_Python/control_trained_assignment_gains.py`
- `?? 3_Python/empirical_moments.py`
- `?? 3_Python/estimate_smm.py`
- `?? 3_Python/make_tables_figures.py`
- `?? 3_Python/model_primitives.py`
- `?? 3_Python/simulate_markets.py`
- `?? 3_Python/structural_blockwise_redesign.py`
- `?? STRUCTURAL_RESULTS_NOTE.md`
- `?? 4_Stata2/04b_peer_diagnostics.do`
- `?? 4_Stata2/04c_assignment_channel_tests.do`
- ` M 4_Stata2/output/fig_overid_kenya.pdf`
- ` M 4_Stata2/output/fig_overid_kenya_quintile.pdf`
- ` M 4_Stata2/output/ke_balance.tex`
- ` M 4_Stata2/output/legacy_1do/Kenya_new/baseline_balance_K.tex`
- ` M 4_Stata2/output/legacy_1do/attrition.tex`
- ` M 4_Stata2/output/legacy_1do/eff_on_disp_bl.tex`
- ` M 4_Stata2/output/lib_balance.tex`
- ` M 4_Stata2/output/tab_attrition_1do.tex`
- ` M 4_Stata2/output/tab_classsize_diag.tex`
- ` M 4_Stata2/output/tab_dispersion.tex`
- ` M 4_Stata2/output/tab_four_margins.tex`
- ` M 4_Stata2/output/tab_lib_sensitivity.tex`
- `?? 4_Stata2/output/assignment_channel_tests_kenya.md`
- `?? 4_Stata2/output/kenya_exact_bh_note.md`
- `?? 4_Stata2/output/tab_assignment_channel_tests_kenya.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya_controls.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya_diag.tex`
- ` M 1_Do/Analysis/KenyaVersion/balance.do`
- ` M 1_Do/Analysis/descriptives.do`

## Explicit Cleanup Decisions

These paths need an explicit remove, restore, keep, or ignore decision before a clean release. The list includes tracked local artifacts even when they are not currently modified.

- ` M .DS_Store`
- ` M 1_Do/.DS_Store`
- ` M Rplots.pdf`
- ` D mp4_to_mp3_ffmpeg.ipynb`
- `tracked 1_Do/Analysis/.DS_Store`
