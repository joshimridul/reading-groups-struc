# Paper release worktree triage

Generated: 2026-06-17T21:42:51-07:00

This read-only triage separates the dirty worktree into release-review buckets for the active three-country R&R paper. It does not stage, restore, remove, or commit files.

If `PAPER_RELEASE_CANDIDATE_PATHS.txt` or `PAPER_RELEASE_CLEANUP_PATHS.txt` exists, treat it as review input for a future staging/cleanup pass, not as an instruction to stage or remove blindly.

## Summary

- Changed/untracked paths: 269
- Release-candidate review set: 207 paths
- Separate extension/legacy/generated review set: 58 paths
- Explicit cleanup decisions: 5 paths

## Recommended Release Order

1. Confirm coauthor approval and public/circulation mode; the active manuscript currently has no draft markers.
2. Review the release-candidate set below: guardrails/docs, canonical pipeline code, active manuscript inputs, and active generated outputs.
3. Keep inactive-output and legacy work out of the release unless the paper scope requires them.
4. Resolve local metadata and deleted-file decisions before tagging or committing a final release.

## Release-Candidate Review Set

These paths are the plausible three-country R&R paper release set. They still require human review before staging because the worktree contains many related changes.

- ` M .gitignore`
- ` D 4_Stata2/05_gates.R`
- ` M 4_Stata2/README.md`
- ` M 4_Stata2/build_main2_tables.py`
- ` D 4_Stata2/output/fig_gates_kenya.pdf`
- ` D 4_Stata2/output/fig_gates_liberia.pdf`
- ` D 4_Stata2/output/fig_varimp_kenya.pdf`
- ` D 4_Stata2/output/fig_varimp_liberia.pdf`
- ` D 4_Stata2/output/tab_gates.tex`
- ` M README.md`
- `?? 4_Stata2/audit_overleaf_artifacts.py`
- `?? 4_Stata2/check_numeric_claims.py`
- `?? 4_Stata2/check_pdf_render.py`
- `?? 4_Stata2/check_public_version.py`
- `?? 4_Stata2/check_release_readiness.py`
- `?? 4_Stata2/embed_active_figure_fonts.py`
- `?? 4_Stata2/triage_release_worktree.py`
- `?? 4_Stata2/verify_freeze_manifest.py`
- `?? GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md`
- `?? PAPER_RELEASE_CANDIDATE_PATHS.txt`
- `?? PAPER_RELEASE_CLEANUP_DECISIONS.md`
- `?? PAPER_RELEASE_CLEANUP_PATHS.txt`
- `?? PAPER_RELEASE_WORKTREE_TRIAGE.md`
- `?? bib.bib`
- `?? build/main_3country_new.structural_edit.pdf`
- `?? build_paper.sh`
- `?? docs/referee_feedback_tasklist_2026_06_08.md`
- `?? docs/referee_response_draft_2026_06_18.md`
- `?? docs/referee_response_letter_2026_06_18.md`
- `?? docs/referee_rnr_execution_plan_2026_06_17.md`
- `?? docs/submission_readiness_checklist_2026_06_18.md`
- `?? main_3country_new.structural_edit.tex`
- `?? paper_pipeline/README.md`
- `?? paper_pipeline/materialize_latex_inputs.py`
- `?? paper_pipeline/materialize_report.json`
- `?? paper_pipeline/migrate_to_reading_groups_struc.sh`
- `?? paper_pipeline/run_main_3country_pipeline.sh`
- `?? replication_audit/PIPELINE_MAP.md`
- `?? replication_audit/REPLICATION_AUDIT.md`
- `?? replication_audit/run_all.sh`
- `?? replication_audit/stata_scratch_core.do`
- `?? run_all.sh`
- ` M 3_Python/00_clean_kenya.py`
- ` M 4_Stata2/00_clean_kenya.do`
- ` M 4_Stata2/01_descriptives.do`
- ` M 4_Stata2/02_main_analysis.do`
- ` M 4_Stata2/03_diagnostics.do`
- ` M 4_Stata2/04_structural.do`
- ` M 4_Stata2/06_robustness.do`
- ` M 4_Stata2/07_lesson_completion.do`
- `?? 3_Python/README_structural.md`
- `?? 3_Python/make_assignment_value_figures.py`
- `?? 3_Python/make_paper_summary_figures.py`
- `?? 3_Python/structural_blockwise_redesign.py`
- `?? 3_Python/verify_structural_package.py`
- `?? 4_Stata2/00_clean_nigeria.do`
- `?? 4_Stata2/02_nigeria_main_analysis.do`
- `?? 4_Stata2/02b_nigeria_two_group.do`
- `?? 4_Stata2/03_pooled_analysis.do`
- `?? 4_Stata2/04c_assignment_channel_tests.do`
- `?? 4_Stata2/08_rnr_inference_attrition.do`
- `?? 4_Stata2/09_multiplicity_disclosure.do`
- `?? 4_Stata2/_master_paper.do`
- ` M 4_Stata2/output/ke_sampleflow.tex`
- ` M 4_Stata2/output/ke_sumstats.tex`
- ` M 4_Stata2/output/lib_sampleflow.tex`
- ` M 4_Stata2/output/lib_sumstats.tex`
- ` M 4_Stata2/output/tab_assignment_cutoffs.tex`
- ` M 4_Stata2/output/tab_attrition_1do.tex`
- ` M 4_Stata2/output/tab_balance_1do.tex`
- ` M 4_Stata2/output/tab_ceiling.tex`
- ` M 4_Stata2/output/tab_classroom_reallocation.tex`
- ` M 4_Stata2/output/tab_classsize_ctrl.tex`
- ` M 4_Stata2/output/tab_cutoff_het.tex`
- ` M 4_Stata2/output/tab_density_decomp.tex`
- ` M 4_Stata2/output/tab_dispersion_firststage.tex`
- ` M 4_Stata2/output/tab_lesson_completion.tex`
- ` M 4_Stata2/output/tab_peer_effects.tex`
- ` M 4_Stata2/output/tab_score_variance.tex`
- ` M 4_Stata2/output/tab_signal_quality.tex`
- ` M 4_Stata2/output/tab_signal_quality_alt.tex`
- ` M 4_Stata2/output/tab_spec_robust.tex`
- ` M 4_Stata2/output/tab_suffstat_kenya.tex`
- ` M 4_Stata2/output/tab_suffstat_liberia.tex`
- ` M 4_Stata2/output/tab_track_bins.tex`
- `?? 4_Stata2/output/tab_assignment_payoff_kenya.tex`
- `?? 4_Stata2/output/tab_assignment_payoff_kenya_power.tex`
- `?? 4_Stata2/output/tab_multiplicity_disclosure.tex`
- `?? 4_Stata2/output/tab_ng_attrition.tex`
- `?? 4_Stata2/output/tab_ng_balance.tex`
- `?? 4_Stata2/output/tab_ng_ceiling.tex`
- `?? 4_Stata2/output/tab_ng_classroom_reallocation.tex`
- `?? 4_Stata2/output/tab_ng_classsize_ctrl.tex`
- `?? 4_Stata2/output/tab_ng_density_decomp.tex`
- `?? 4_Stata2/output/tab_ng_dispersion.tex`
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
- `?? 4_Stata2/output/tab_ng_t3_ete.tex`
- `?? 4_Stata2/output/tab_ng_track_bins.tex`
- `?? 4_Stata2/output/tab_ng_two_group.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya.tex`
- `?? 4_Stata2/output/tab_pooled_dispersion.tex`
- `?? 4_Stata2/output/tab_pooled_itt.tex`
- `?? 4_Stata2/output/tab_pooled_peer_effects.tex`
- `?? 4_Stata2/output/tab_pooled_power.tex`
- `?? 4_Stata2/output/tab_pooled_upper_lower.tex`
- `?? 4_Stata2/output/tab_rnr_attrition_bounds.tex`
- `?? 4_Stata2/output/tab_rnr_inference_checks.tex`
- `?? stata_output/ke_sampleflow.tex`
- `?? stata_output/ke_sumstats.tex`
- `?? stata_output/lib_sampleflow.tex`
- `?? stata_output/lib_sumstats.tex`
- `?? stata_output/tab_assignment_cutoffs.tex`
- `?? stata_output/tab_assignment_payoff_kenya.tex`
- `?? stata_output/tab_assignment_payoff_kenya_power.tex`
- `?? stata_output/tab_attrition_1do.tex`
- `?? stata_output/tab_balance_1do.tex`
- `?? stata_output/tab_ceiling.tex`
- `?? stata_output/tab_classroom_reallocation.tex`
- `?? stata_output/tab_classsize_ctrl.tex`
- `?? stata_output/tab_cutoff_het.tex`
- `?? stata_output/tab_density_decomp.tex`
- `?? stata_output/tab_dispersion_firststage.tex`
- `?? stata_output/tab_lesson_completion.tex`
- `?? stata_output/tab_multiplicity_disclosure.tex`
- `?? stata_output/tab_ng_attrition.tex`
- `?? stata_output/tab_ng_balance.tex`
- `?? stata_output/tab_ng_ceiling.tex`
- `?? stata_output/tab_ng_classroom_reallocation.tex`
- `?? stata_output/tab_ng_classsize_ctrl.tex`
- `?? stata_output/tab_ng_density_decomp.tex`
- `?? stata_output/tab_ng_dispersion.tex`
- `?? stata_output/tab_ng_lee_bounds.tex`
- `?? stata_output/tab_ng_over_terms.tex`
- `?? stata_output/tab_ng_over_terms_interact.tex`
- `?? stata_output/tab_ng_peer_effects.tex`
- `?? stata_output/tab_ng_sampleflow.tex`
- `?? stata_output/tab_ng_score_variance.tex`
- `?? stata_output/tab_ng_signal_quality.tex`
- `?? stata_output/tab_ng_spec_robust.tex`
- `?? stata_output/tab_ng_suffstat.tex`
- `?? stata_output/tab_ng_sumstats.tex`
- `?? stata_output/tab_ng_t2_ete.tex`
- `?? stata_output/tab_ng_t3_ete.tex`
- `?? stata_output/tab_ng_track_bins.tex`
- `?? stata_output/tab_ng_two_group.tex`
- `?? stata_output/tab_peer_effects.tex`
- `?? stata_output/tab_peer_effects_exact_kenya.tex`
- `?? stata_output/tab_pooled_dispersion.tex`
- `?? stata_output/tab_pooled_itt.tex`
- `?? stata_output/tab_pooled_peer_effects.tex`
- `?? stata_output/tab_pooled_power.tex`
- `?? stata_output/tab_pooled_upper_lower.tex`
- `?? stata_output/tab_rnr_attrition_bounds.tex`
- `?? stata_output/tab_rnr_inference_checks.tex`
- `?? stata_output/tab_score_variance.tex`
- `?? stata_output/tab_signal_quality.tex`
- `?? stata_output/tab_signal_quality_alt.tex`
- `?? stata_output/tab_spec_robust.tex`
- `?? stata_output/tab_suffstat_kenya.tex`
- `?? stata_output/tab_suffstat_liberia.tex`
- `?? stata_output/tab_track_bins.tex`
- `?? structural_output/fig_assignment_mismatch_distributions.pdf`
- `?? structural_output/fig_counterfactual_ladder.pdf`
- `?? structural_output/fig_experiment_map.pdf`
- `?? structural_output/fig_firststage_payoff.pdf`
- `?? structural_output/fig_struct_complementarity_surface.pdf`
- `?? structural_output/fig_track_position_allcountries.pdf`
- `?? structural_output/tab_assignment_value_summary.tex`
- `?? structural_output/tab_counterfactuals.tex`
- `?? structural_output/tab_grade_signal_substitution.tex`
- `?? structural_output/tab_moment_fit.tex`
- `?? structural_output/tab_struct_assignment_value_sensitivity.tex`
- `?? structural_output/tab_struct_combined_uncertainty.tex`
- `?? structural_output/tab_struct_complementarity.tex`
- `?? structural_output/tab_struct_component_decomp.tex`
- `?? structural_output/tab_struct_delivery_activation.tex`
- `?? structural_output/tab_struct_delivery_thresholds.tex`
- `?? structural_output/tab_struct_influence.tex`
- `?? structural_output/tab_struct_local_identification.tex`
- `?? structural_output/tab_struct_market_influence.tex`
- `?? structural_output/tab_struct_nigeria_endpoint_sensitivity.tex`
- `?? structural_output/tab_struct_primitive_moments.tex`
- `?? structural_output/tab_struct_primitive_sensitivity.tex`
- `?? structural_output/tab_struct_primitive_uncertainty.tex`
- `?? structural_output/tab_struct_regularization_sensitivity.tex`
- `?? structural_output/tab_struct_resid_sensitivity.tex`
- `?? structural_output/tab_struct_signal_delivery_margins.tex`
- `?? structural_output/tab_struct_social_channel_sensitivity.tex`
- `?? structural_output/tab_struct_stage4_discipline.tex`
- `?? structural_output/tab_struct_stage4_normalizations.tex`
- `?? structural_output/tab_struct_stage4_param_uncertainty.tex`
- `?? structural_output/tab_struct_target_blocks.tex`
- `?? structural_output/tab_struct_tau_calibration.tex`
- `?? structural_output/tab_struct_tau_raw_thresholds.tex`
- `?? structural_output/tab_struct_tau_sensitivity.tex`
- `?? structural_output/tab_struct_validation_checks.tex`
- `?? structural_output/tab_structural_params.tex`

## Keep Separate Unless Scope Changes

These paths are inactive generated outputs, supplemental diagnostics not directly active, legacy work, or other extensions. They should not be mixed into a clean R&R release without an explicit scope decision.

- `?? 3_Python/00_clean_nigeria.py`
- `?? 3_Python/build_nigeria_assessments_long.py`
- `?? 3_Python/build_nigeria_raw_panels.py`
- `?? 3_Python/nigeria_full_stack_replication.py`
- `?? 3_Python/run_nigeria_irt_outcomes.py`
- `?? 4_Stata2/_master_nigeria.do`
- `?? 4_Stata2/output/tab_ng_irt.tex`
- `?? 4_Stata2/output/tab_ng_t2_mte.tex`
- `?? 4_Stata2/output/tab_ng_t2_over_time.tex`
- `?? 4_Stata2/output/tab_ng_t3_mte.tex`
- `?? 4_Stata2/output/tab_ng_t3_over_time.tex`
- `?? 4_Stata2/output/tab_ng_upper_lower.tex`
- `?? 4_Stata2/output/tab_pooled_gradient.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_irt.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_t2_mte.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_t2_over_time.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_t3_mte.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_t3_over_time.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_ng_upper_lower.tex`
- `?? archive/stale_paper_inputs/stata_output/tab_pooled_gradient.tex`
- ` M 3_Python/structural_estimation_revision.py`
- `?? 3_Python/bootstrap_counterfactuals.py`
- `?? 3_Python/control_trained_assignment_gains.py`
- `?? 3_Python/empirical_moments.py`
- `?? 3_Python/estimate_smm.py`
- `?? 3_Python/make_tables_figures.py`
- `?? 3_Python/model_primitives.py`
- `?? 3_Python/simulate_markets.py`
- `?? 4_Stata2/04b_peer_diagnostics.do`
- ` M 4_Stata2/output/fig_four_margins.pdf`
- ` M 4_Stata2/output/fig_overid_kenya.pdf`
- ` M 4_Stata2/output/fig_overid_kenya_quintile.pdf`
- ` M 4_Stata2/output/fig_posterior_shrinkage.pdf`
- ` M 4_Stata2/output/ke_attrition.tex`
- ` M 4_Stata2/output/ke_balance.tex`
- ` M 4_Stata2/output/ke_binscatter.pdf`
- ` M 4_Stata2/output/legacy_1do/Kenya_new/baseline_balance_K.tex`
- ` M 4_Stata2/output/legacy_1do/attrition.tex`
- ` M 4_Stata2/output/legacy_1do/eff_on_disp_bl.tex`
- ` M 4_Stata2/output/lib_attrition.tex`
- ` M 4_Stata2/output/lib_balance.tex`
- ` M 4_Stata2/output/lib_binscatter.pdf`
- ` M 4_Stata2/output/tab_classsize_diag.tex`
- ` M 4_Stata2/output/tab_dispersion.tex`
- ` M 4_Stata2/output/tab_four_margins.tex`
- ` M 4_Stata2/output/tab_itt.tex`
- ` M 4_Stata2/output/tab_lee_bounds.tex`
- ` M 4_Stata2/output/tab_lib_sensitivity.tex`
- ` M 4_Stata2/output/tab_upper_lower.tex`
- `?? 4_Stata2/output/assignment_channel_tests_kenya.md`
- `?? 4_Stata2/output/kenya_exact_bh_note.md`
- `?? 4_Stata2/output/ng_two_group_note.md`
- `?? 4_Stata2/output/tab_assignment_channel_tests_kenya.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya_controls.tex`
- `?? 4_Stata2/output/tab_peer_effects_exact_kenya_diag.tex`
- ` M 1_Do/Analysis/KenyaVersion/balance.do`
- ` M 1_Do/Analysis/descriptives.do`
- ` M 1_Do/_master.do`

## Explicit Cleanup Decisions

These paths need an explicit remove, restore, keep, or ignore decision before a clean release. The list includes tracked local artifacts even when they are not currently modified.

- ` M .DS_Store`
- ` M 1_Do/.DS_Store`
- ` M Rplots.pdf`
- ` D mp4_to_mp3_ffmpeg.ipynb`
- `tracked 1_Do/Analysis/.DS_Store`
