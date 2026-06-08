# Pipeline Map: Active `main_3country_new` Manuscript

This map traces active generated exhibits in `main_3country_new.structural_edit.tex`.

## Source and build targets

- Local manuscript source: `main_3country_new.structural_edit.tex`
- Repo active source: `/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.tex`
- Repo active PDF: `/Users/mriduljoshi/Github/reading-groups-struc/main_3country_new.pdf`
- Stata outputs used by TeX: `stata_output/` in repo, mirrored in repo at `4_Stata2/output/`
- Structural outputs used by TeX: `structural_output/` in repo and repo
- Canonical structural working outputs: `3_Python/output/structural_smm/`
- Canonical structural LaTeX tables: `3_Python/output/structural_smm/latex/`

## Data sources

### Kenya and Liberia reduced-form Stata

- Raw data root: `2_Data/1_Raw/`
- Cleaned Stata outputs:
  - `4_Stata2/output/analysis_kenya.dta`
  - `4_Stata2/output/analysis_liberia.dta`
- Main cleaning scripts:
  - `4_Stata2/00_clean_kenya.do`
  - `4_Stata2/00_clean_liberia.do`

### Nigeria reduced-form Stata

- Raw data roots:
  - `2_Data/1_Raw/P123 Numeracy Groups/`
  - `2_Data/2_Cleaned/Nigeria/`
- Cleaned Stata outputs:
  - `4_Stata2/output/analysis_nigeria_wide.dta`
  - `4_Stata2/output/analysis_nigeria_attrition_long.dta`
- Main cleaning script:
  - `4_Stata2/00_clean_nigeria.do`

### Structural Python

- Python cleaned parquet inputs:
  - `3_Python/output/analysis_kenya.parquet`
  - `3_Python/output/analysis_liberia.parquet`
  - `3_Python/output/analysis_nigeria.parquet`
- Main structural generator:
  - `3_Python/structural_blockwise_redesign.py`
- Paper summary figure generator:
  - `3_Python/make_paper_summary_figures.py`
- Structural verifier:
  - `3_Python/verify_structural_package.py`

## Active Stata tables

| Manuscript line | Artifact | Generator | Status |
|---:|---|---|---|
| 828 | `stata_output/tab_pooled_itt` | `4_Stata2/03_pooled_analysis.do` | Present/synced; not scratch-rerun because script hard-codes output and repo copy |
| 829 | `stata_output/tab_pooled_power` | `4_Stata2/03_pooled_analysis.do` | Present/synced; not scratch-rerun |
| 830 | `stata_output/tab_pooled_upper_lower` | `4_Stata2/03_pooled_analysis.do` | Present/synced; not scratch-rerun |
| 831 | `stata_output/tab_ng_two_group` | `4_Stata2/02b_nigeria_two_group.do` | Present/synced; not scratch-rerun |
| 834 | `stata_output/tab_pooled_dispersion` | `4_Stata2/03_pooled_analysis.do` | Present/synced; not scratch-rerun |
| 835 | `stata_output/tab_assignment_payoff_kenya` | `4_Stata2/04c_assignment_channel_tests.do` | Present/synced; not scratch-rerun |
| 854 | `stata_output/lib_sumstats` | `4_Stata2/01_descriptives.do` | Scratch rebuild identical |
| 855 | `stata_output/ke_sumstats` | `4_Stata2/01_descriptives.do` | Scratch rebuild identical |
| 856 | `stata_output/tab_ng_sumstats` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 857 | `stata_output/tab_balance_1do` | `4_Stata2/build_main2_tables.py` materializes legacy alias | Present/synced; alias step needs update for active manuscript |
| 858 | `stata_output/tab_ng_balance` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 859 | `stata_output/tab_attrition_1do` | `4_Stata2/build_main2_tables.py` materializes legacy alias | Present/synced; alias step needs update |
| 860 | `stata_output/tab_ng_attrition` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 861 | `stata_output/lib_sampleflow` | `4_Stata2/01_descriptives.do` | Scratch rebuild identical |
| 862 | `stata_output/ke_sampleflow` | `4_Stata2/01_descriptives.do` | Scratch rebuild identical |
| 863 | `stata_output/tab_ng_sampleflow` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 866 | `stata_output/tab_ng_t2_ete` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 867 | `stata_output/tab_ng_t3_ete` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 868 | `stata_output/tab_ng_over_terms` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 869 | `stata_output/tab_ng_over_terms_interact` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 872 | `stata_output/tab_signal_quality` | `4_Stata2/03_diagnostics.do` | Scratch rebuild identical |
| 873 | `stata_output/tab_signal_quality_alt` | `4_Stata2/04_structural.do` | Scratch rebuild identical |
| 874 | `stata_output/tab_ng_signal_quality` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 875 | `stata_output/tab_assignment_cutoffs` | `4_Stata2/04_structural.do` | Scratch rebuild identical |
| 876 | `stata_output/tab_classroom_reallocation` | `4_Stata2/04_structural.do` | Scratch rebuild identical |
| 877 | `stata_output/tab_ng_classroom_reallocation` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 878 | `stata_output/tab_ng_dispersion` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 879 | `stata_output/tab_track_bins` | `4_Stata2/03_diagnostics.do` | Scratch rebuild identical |
| 880 | `stata_output/tab_ng_track_bins` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 881 | `stata_output/tab_cutoff_het` | `4_Stata2/03_diagnostics.do` | Scratch rebuild identical |
| 882 | `stata_output/tab_dispersion_firststage` | `4_Stata2/03_diagnostics.do` | Scratch rebuild identical |
| 883 | `stata_output/tab_lesson_completion` | `4_Stata2/07_lesson_completion.do` | Scratch rebuild identical |
| 886 | `stata_output/tab_peer_effects` | `4_Stata2/02_main_analysis.do` | Scratch rebuild identical |
| 887 | `stata_output/tab_ng_peer_effects` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 888 | `stata_output/tab_pooled_peer_effects` | `4_Stata2/03_pooled_analysis.do` | Present/synced; not scratch-rerun |
| 889 | `stata_output/tab_peer_effects_exact_kenya` | `4_Stata2/04_structural.do` | Scratch rebuild identical |
| 890 | `stata_output/tab_suffstat_kenya` | `4_Stata2/04_structural.do` | Scratch rebuild differs in caption/notes only |
| 891 | `stata_output/tab_suffstat_liberia` | `4_Stata2/04_structural.do` | Scratch rebuild differs in caption/notes only |
| 892 | `stata_output/tab_ng_suffstat` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 893 | `stata_output/tab_density_decomp` | `4_Stata2/04_structural.do` | Scratch rebuild identical |
| 894 | `stata_output/tab_ng_density_decomp` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 897 | `stata_output/tab_spec_robust` | `4_Stata2/06_robustness.do` | Scratch rebuild differs in wording only |
| 898 | `stata_output/tab_ng_spec_robust` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 899 | `stata_output/tab_ng_lee_bounds` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 900 | `stata_output/tab_classsize_ctrl` | `4_Stata2/06_robustness.do` | Scratch rebuild identical |
| 901 | `stata_output/tab_ng_classsize_ctrl` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 902 | `stata_output/tab_ceiling` | `4_Stata2/06_robustness.do` | Scratch rebuild identical |
| 903 | `stata_output/tab_ng_ceiling` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |
| 904 | `stata_output/tab_score_variance` | `4_Stata2/06_robustness.do` | Scratch rebuild identical |
| 905 | `stata_output/tab_ng_score_variance` | `4_Stata2/02_nigeria_main_analysis.do` | Present/synced; not scratch-rerun |

## Active structural tables

All structural tables below are generated by `3_Python/structural_blockwise_redesign.py`, copied to `structural_output/`, and mirrored to repo. They are also checked by `3_Python/verify_structural_package.py`, although that verifier currently fails prose-gate checks.

| Manuscript line | Artifact | Status |
|---:|---|---|
| 647 | `structural_output/tab_struct_target_blocks.tex` | Present/synced |
| 653 | `structural_output/tab_struct_primitive_moments.tex` | Present/synced |
| 660 | `structural_output/tab_structural_params.tex` | Present/synced |
| 671 | `structural_output/tab_moment_fit.tex` | Present/synced |
| 686 | `structural_output/tab_struct_validation_checks.tex` | Present/synced |
| 695 | `structural_output/tab_counterfactuals.tex` | Present/synced |
| 701 | `structural_output/tab_struct_component_decomp.tex` | Present/synced |
| 713 | `structural_output/tab_struct_complementarity.tex` | Present/synced |
| 717 | `structural_output/tab_struct_signal_delivery_margins.tex` | Present/synced |
| 723 | `structural_output/tab_struct_delivery_thresholds.tex` | Present/synced |
| 956 | `structural_output/tab_struct_tau_calibration.tex` | Present/synced |
| 960 | `structural_output/tab_struct_tau_sensitivity.tex` | Present/synced |
| 962 | `structural_output/tab_struct_local_identification.tex` | Present/synced |
| 966 | `structural_output/tab_struct_stage4_param_uncertainty.tex` | Present/synced |
| 968 | `structural_output/tab_struct_social_channel_sensitivity.tex` | Present/synced |
| 972 | `structural_output/tab_struct_stage4_discipline.tex` | Present/synced |
| 974 | `structural_output/tab_struct_stage4_normalizations.tex` | Present/synced |
| 980 | `structural_output/tab_struct_resid_sensitivity.tex` | Present/synced |
| 982 | `structural_output/tab_struct_regularization_sensitivity.tex` | Present/synced |
| 984 | `structural_output/tab_struct_influence.tex` | Present/synced |
| 986 | `structural_output/tab_struct_market_influence.tex` | Present/synced |
| 988 | `structural_output/tab_struct_primitive_sensitivity.tex` | Present/synced |
| 990 | `structural_output/tab_struct_primitive_uncertainty.tex` | Present/synced |
| 992 | `structural_output/tab_struct_combined_uncertainty.tex` | Present/synced |
| 994 | `structural_output/tab_struct_delivery_activation.tex` | Present/synced |

## Active structural figures

| Manuscript line | Artifact | Generator | Status |
|---:|---|---|---|
| 785 | `structural_output/fig_experiment_map.pdf` | `3_Python/make_paper_summary_figures.py` | Present/synced; not covered by structural verifier |
| 794 | `structural_output/fig_firststage_payoff.pdf` | `3_Python/make_paper_summary_figures.py` | Present/synced; not covered by structural verifier |
| 803 | `structural_output/fig_struct_complementarity_surface.pdf` | `3_Python/structural_blockwise_redesign.py` | Present/synced; covered by structural verifier |
| 812 | `structural_output/fig_counterfactual_ladder.pdf` | `3_Python/make_paper_summary_figures.py` | Present/synced; not covered by structural verifier |
| 1002 | `structural_output/fig_track_position_allcountries.pdf` | `3_Python/make_paper_summary_figures.py` | Present/synced; not covered by structural verifier |

## Unsafe or incomplete runner status

`replication_audit/run_all.sh` is a conservative audit draft. It does not run the full paper pipeline. It:

1. runs `replication_audit/stata_scratch_core.do` into `replication_audit/stata_scratch/`;
2. audits active Stata artifact sync for `main_3country_new.tex`;
3. runs the structural verifier.

It intentionally avoids the hard-coded repo-copy scripts until those scripts can honor caller-specified output locations and a no-sync mode.
