# Structural Extension Results Note (Blockwise Redesign)

This note summarizes the redesigned structural pipeline in
`3_Python/structural_blockwise_redesign.py` and its outputs in
`3_Python/output/structural_smm/`.

The redesign replaces the previous all-at-once fit with stage-wise estimation so each primitive is tied to the margin the data identify. The current version also separates mechanical sorting compression from the outcome payoff to correct placement, allows that payoff to activate nonlinearly with treatment-relevant delivery fidelity, uses harmonized study-specific ITT targets from the pooled Stata pipeline, scales class-size pressure into comparable units, and shrinkage-regularizes market residuals so the model cannot mechanically interpolate every country effect.

## 1) What is now implemented

The redesigned pipeline estimates in four blocks:

1. `rho` block (`estimate_rho_block`): control-group predictive-content moments only.
2. `omega` block (`estimate_omega_block`): assignment-execution moments only.
3. `tau` block (`estimate_tau_block`): treatment-relevant process calibration only.
4. Production block (`estimate_production_block`): outcome/reallocation moments conditional on fixed `rho`, `omega`, `tau`, including the Kenya assignment-payoff slope.

It also runs:

- `run_acceptance_tests`
- `simulate_counterfactual_surface`

## 2) Core output files from redesign

- `canonical_nigeria_implementation_moments.csv`
- `counterfactual_component_decomposition.csv`
- `stage1_rho_estimates.csv`
- `stage2_omega_estimates.csv`
- `stage3_tau_estimates.csv`
- `stage4_structural_parameters.csv`
- `target_vs_fitted_moments.csv`
- `acceptance_tests.json`
- `counterfactual_surface.csv`
- `counterfactual_summary.csv`
- `stage4_counterfactual_uncertainty.csv`
- `pooled_structural_diagnostics.csv`
- `residual_prior_sensitivity.csv`
- `primitive_benchmark_sensitivity.csv`
- `primitive_uncertainty_inputs.csv`
- `primitive_uncertainty_sensitivity.csv`
- `delivery_activation_sensitivity.csv`
- `nigeria_complementarity_decomposition.csv`
- `latex/tab_structural_params.tex`
- `latex/tab_struct_primitive_moments.tex`
- `latex/tab_moment_fit.tex`
- `latex/tab_struct_resid_sensitivity.tex`
- `latex/tab_struct_influence.tex`
- `latex/tab_struct_primitive_sensitivity.tex`
- `latex/tab_struct_primitive_uncertainty.tex`
- `latex/tab_struct_delivery_activation.tex`
- `latex/tab_counterfactuals.tex`
- `latex/tab_struct_component_decomp.tex`
- `latex/tab_struct_complementarity.tex`
- `structural_package_verification.json`
- `structural_redesign_note.md`

## 3) Stage estimates (current run)

From the latest redesign run:

- Signal informativeness (`rho`):
  - Kenya: 0.5329
  - Nigeria: 0.1207
  - Liberia: 0.0550
- Assignment execution (`omega`):
  - Kenya: 1.0000
  - Liberia: 1.0000
  - Nigeria: 0.8415
- Treatment-relevant delivery fidelity (`tau`):
  - Kenya: 0.5000
  - Liberia: 0.3848
  - Nigeria: 0.3116
- Common production/assignment parameters:
  - `lambda`: 0.4000
  - delivery activation `alpha`: 4.3175
  - sorting compression `kappa_sort`: 1.6487
  - social channel `phi`: 0.1917
  - rank weight `omega_r`: -0.2811
  - class-size pressure `chi_N`: 0.0328
  - grade dispersion `chi_V`: 0.0218
  - residuals: Kenya 0.0248, Liberia -0.1229, Nigeria 0.1342

Interpretation:

- The intended ranking `Kenya > Nigeria > Liberia` in signal quality is recovered.
- Kenya/Liberia execution is effectively deterministic, while Nigeria execution is materially lower.
- `tau` is no longer being used as an outcome residual absorber; it is set before production fitting.
- Market residuals are not allowed to do all the work. The preferred run uses a residual prior SD of 0.25, which trades exact country-ITT interpolation for a more defensible common production structure.

## 4) Acceptance tests (hard constraints)

From `acceptance_tests.json`:

- `rho_ordering`: PASS
- `omega_ordering`: PASS
- `tau_process_identification`: PASS
- `kenya_high_tau_monotonicity`: PASS
- `nigeria_execution_monotonicity`: PASS
- `theory_consistency`: PASS
- `nigeria_target_coherence`: PASS
- `reduced_form_respect`: PASS
- `idealized_dominance`: PASS
- Overall: `all_pass = true`

This means the redesign no longer exhibits the earlier structural failures (for example, Kenya high-`tau` becoming worse than observed Kenya).

## 5) Counterfactuals (current redesign run)

From `counterfactual_summary.csv`:

- Kenya observed: 0.0299
- Kenya high-`tau` (holding Kenya `rho`, `omega` fixed): 0.1546
- Liberia observed: -0.1761
- Nigeria realized: 0.0561
- Nigeria designed-execution (holding rosters fixed, improving `omega`): 0.0562
- Nigeria execution gap (designed - realized): 0.0000
- Fully idealized high-`rho`/high-`omega`/high-`tau`: 0.1868

One-at-a-time Nigeria:

- `rho` only: 0.0571
- `tau` only: 0.1148
- `omega` only: 0.0562

Conditional stage-4 uncertainty from `stage4_counterfactual_uncertainty.csv`:

- Fully idealized high-`rho`/high-`omega`/high-`tau`: point 0.1868, 5th--95th interval [0.0584, 0.2222].
- Kenya high-`tau`: point 0.1546, 5th--95th interval [0.0280, 0.2061].
- Nigeria `tau` only: point 0.1148, 5th--95th interval [-0.1054, 0.3056].

These intervals use 49 parametric bootstrap re-estimation draws of stage-4 target moments, conditional on stage-1 to stage-3 primitives. They are suitable for current paper drafting but should be replaced by a longer production run before submission if time permits.

## 5b) Residual-prior sensitivity

From `residual_prior_sensitivity.csv`, re-estimating the production block under alternative residual priors gives:

- Strict residual prior SD 0.15: fully idealized ATE 0.1831; max standardized ITT error 0.553.
- Preferred residual prior SD 0.25: fully idealized ATE 0.1868; max standardized ITT error 0.281.
- Loose residual prior SD 0.50: fully idealized ATE 0.1903; max standardized ITT error 0.097.
- Unrestricted residuals: fully idealized ATE 0.1939; max standardized ITT error 0.003; max absolute residual hits the 0.500 bound.

Interpretation: the DDK-sized high-input counterfactual is stable to residual discipline. The unrestricted fit should not be the preferred model because it interpolates country ITTs by using a boundary market residual.

## 5c) Primitive benchmark sensitivity

From `primitive_benchmark_sensitivity.csv`, evaluating alternative high-input primitive benchmarks holding the preferred production mapping fixed gives:

- Conservative joint benchmark (`rho` = lower Kenya grade-specific estimate 0.509, `omega` = 0.95, `tau` = 0.90): ATE 0.1420.
- Lower `rho` only: ATE 0.1791.
- Lower `omega` only: ATE 0.1816.
- Lower `tau` only: ATE 0.1519.
- Preferred high-input benchmark: ATE 0.1868.
- Upper Kenya grade-specific `rho`: ATE 0.1951.

Interpretation: the high-input counterfactual is most sensitive to the delivery-fidelity benchmark, but remains positive and economically meaningful under a conservative joint primitive benchmark.

## 5d) Primitive-estimation uncertainty sensitivity

From `primitive_uncertainty_sensitivity.csv`, propagating uncertainty in stage-1 to stage-3 primitives while holding the preferred production mapping fixed gives:

- Fully high-input cell: point 0.1868; 5th--95th range [0.1813, 0.1921].
- Kenya high delivery: point 0.1546; 5th--95th range [0.1502, 0.1589].
- Nigeria high delivery only: point 0.1148; 5th--95th range [0.1045, 0.1271].
- Nigeria high signal plus delivery: point 0.2028; 5th--95th range [0.1847, 0.2211].
- Nigeria all three: point 0.2175; 5th--95th range [0.2133, 0.2216].

Interpretation: the high-input result is not fragile to sampling uncertainty in the primitive estimates. The wider movement is in the Nigeria high-signal-plus-delivery exercise because it combines Nigeria's uncertain implementation environment with Kenya's estimated signal quality, but the complementarity remains large throughout the primitive-uncertainty range.

## 5e) Delivery-activation functional-form sensitivity

From `delivery_activation_sensitivity.csv`, re-estimating the stage-4 production block under alternative exponents in `tau^alpha` gives:

- Linear activation (`alpha=1`): high-input ATE 0.1270; Kenya assignment-payoff fitted 0.1007 versus target 0.0080.
- Quadratic activation (`alpha=2`): high-input ATE 0.1682; Kenya assignment-payoff fitted 0.0526.
- Cubic activation (`alpha=3`): high-input ATE 0.1839; Kenya assignment-payoff fitted 0.0266.
- Preferred estimated activation (`alpha=4.3175`): high-input ATE 0.1868; Kenya assignment-payoff fitted 0.0107.
- Steeper activation (`alpha=6`): high-input ATE 0.1795; Kenya assignment-payoff fitted 0.0033.

Interpretation: the DDK-sized point estimate relies on nonlinear activation, but nonlinearity is empirically disciplined by the Kenya assignment-payoff diagnostic. Linear activation predicts too much payoff at realized Kenya delivery fidelity. Specifications that fit that near-zero assignment-payoff moment imply high-input gains around 0.18--0.19 SD.

## 5f) Counterfactual component decomposition

From `counterfactual_component_decomposition.csv`, the preferred model decomposes ATEs into assignment payoff, social channel, class/grade pressure, and the shrinkage-regularized market residual:

- Fully high-input cell: assignment 0.1674; social approximately 0; class/grade -0.0054; residual 0.0248; ATE 0.1868.
- Kenya high delivery: assignment 0.1353; social approximately 0; class/grade -0.0054; residual 0.0248; ATE 0.1546.
- Nigeria realized: assignment 0.0003; social -0.0387; class/grade -0.0396; residual 0.1342; ATE 0.0561.
- Nigeria all three: assignment 0.1285; social -0.0056; class/grade -0.0396; residual 0.1342; ATE 0.2175.

Interpretation: the high-input result is an assignment-payoff result, not a residual-interpolation result. Nigeria's realized positive point estimate is partly a positive country residual offsetting adverse social and class/grade terms; the complementarity exercise is therefore most informative once the assignment component is separated from the residual.

## 5g) Nigeria primitive-complementarity decomposition

From `nigeria_complementarity_decomposition.csv`, evaluating single, pairwise, and joint primitive upgrades in Nigeria's production environment gives:

- Realized Nigeria: ATE 0.0561.
- Upgrade `rho` only to Kenya's estimate: ATE 0.0571.
- Upgrade `omega` only to 0.95: ATE 0.0562.
- Upgrade `tau` only to 0.90: ATE 0.1148.
- Upgrade `rho` and `tau` jointly: ATE 0.2028.
- Upgrade all three primitives: ATE 0.2175.

The nonadditive gains are large: the `rho + tau` gain exceeds the sum of the separate `rho` and `tau` gains by 0.087 SD, and the all-three gain exceeds the sum of the three separate gains by 0.102 SD.

Interpretation: the one-at-a-time decomposition understates the mechanism. Signal quality has almost no payoff when treatment-relevant delivery fidelity is low, but a large payoff once high delivery fidelity is present. This gives the structural section a positive economic story: the null observed implementations do not imply that ability grouping has no value; they imply that the value of accurate sorting is latent unless the curriculum channel through which correct placement matters is actually delivered.

## 6) Nigeria implementation coherence rule

The redesign uses one canonical Nigeria implementation file with explicit role separation:

- Estimation set: computed moments from cleaned treated sample.
- Validation set: external design-level targets.

The code warns when these conflict and does not force both sets simultaneously in estimation.

## 7) Practical paper language

Recommended framing:

1. Reduced-form results remain the primary empirical evidence.
2. Structural block is a disciplined counterfactual device.
3. Identification is stage-specific and transparent (`rho`, `omega`, `tau` separated).
4. Counterfactuals are reported only after passing hard theory-consistency acceptance tests.
5. The Kenya assignment-payoff diagnostic is not a reason to abandon the paper's mechanism. It is a discipline on the model: at realized `tau`, the payoff to the implemented assignment margin is near zero; at high treatment-relevant delivery fidelity, the same sorting technology can have much larger payoff.

## 8) Remaining caveats

This redesign improves economic interpretability and comparative-static discipline, but counterfactual magnitudes still depend on functional-form assumptions in the stage-4 production mapping and on the residual-shrinkage prior. Report point estimates with caution and keep reduced-form evidence central.

The current stage-4 fit matches Kenya's ITT, within-class dispersion compression, and the near-zero assignment-payoff slope closely. Because market residuals are shrinkage-regularized, it no longer exactly matches Liberia and Nigeria ITTs; both misses are inside the large reduced-form SEs. The remaining empirical weakness is the peer/rank composite: it is directionally correct in Kenya but understated, and Liberia's peer/rank moment remains weakly fit. That is less damaging than the previous dispersion miss because the exact peer/rank diagnostics are noisy and specification-sensitive.

## 9) Output provenance status

The blockwise structural run has been regenerated with the nonlinear delivery-activation specification:

- `counterfactual_summary.csv` reports Kenya high-`tau` = `0.1546` and fully idealized = `0.1868`.
- `acceptance_tests.json` reports the same Kenya high-`tau` value = `0.1546`, with `tau_benchmark = 0.90`.
- `target_vs_fitted_moments.csv` reports Kenya dispersion `-0.1931` fitted as `-0.1931` and Kenya assignment-payoff slope `0.0080` fitted as `0.0107`.
- `latex/tab_struct_primitive_moments.tex` reports the non-outcome moments used to identify `rho`, `omega`, and `tau`.
- `primitive_uncertainty_sensitivity.csv` reports the fully high-input cell 5th--95th range as `[0.1813, 0.1921]`.
- `delivery_activation_sensitivity.csv` reports the high-input range across activation forms as `[0.1270, 0.1868]`.
- `counterfactual_component_decomposition.csv` reports high-input assignment payoff `0.1674` out of total ATE `0.1868`.
- `nigeria_complementarity_decomposition.csv` reports `rho` plus `tau` = `0.2028` and all three primitives = `0.2175`.
- `stage4_influence_sensitivity.csv` re-estimates the stage-4 production block after omitting each major target block. The high-input counterfactual remains positive (`0.159` to `0.189`), but the Nigeria `rho + tau` exercise is sensitive to omitting Nigeria's ITT; this supports treating the Nigeria decomposition as conditional mechanism accounting rather than the main DDK comparison.
- `structural_package_verification.json` reports `PASS`, confirms all structural manuscript inputs are canonical generated tables, and verifies the headline high-input, Nigeria-designed, complementarity, component-decomposition, and conditional-uncertainty claims against the generated CSVs.
- `run_manifest.json` records the current benchmark definitions, canonical generated outputs, and archived legacy all-at-once outputs.

Legacy all-at-once outputs have been moved under `output/structural_smm/legacy_all_at_once/`. They are retained for auditability only and are not canonical paper inputs.
