# Draft Response Map for Structural Referee Report

This memo converts the structural referee report into a point-by-point revision response. It is written as a working response map rather than a final submission letter. Table and section references refer to `main_3country_new.structural_edit.tex` as currently compiled.

## Summary of Revision Strategy

The revision no longer asks readers to accept the structural counterfactual as the paper's main source of evidence. The paper now stands first on the reduced-form and implementation facts: the three experiments do not produce a clearly positive average effect, and each muted result reveals a different missing input in the same assignment technology. The structural exercise is presented as a calibrated assignment-delivery benchmark for the unobserved high-input cell.

The central claim is now:

> Cross-grade ability grouping in a scripted-instruction system raises learning only when the placement rule improves assignment relative to grade, schools form the intended groups, and the assigned content is delivered. Measurement, execution, and delivery are complements.

The preferred high-input benchmark remains about 0.19 SD, but the manuscript treats that number as scale. The more robust implication is the high delivery threshold and the low return to one-at-a-time implementation fixes.

## Major Concern 1: The Structural Model Was Too Central

**Concern.** The referee argued that the structural model was underidentified and too calibrated to carry the headline claim.

**Revision.** We repositioned the model as a calibrated benchmark, not as a substitute for an unobserved experiment. The abstract, introduction, and structural opening now foreground the observed reduced-form facts and implementation failures. The structural section explicitly states that the model benchmarks the missing high-input cell and does not fit away the nulls.

**Where fixed.**

- Abstract: states that observed implementations do not generate a clearly positive average effect and that the benchmark interprets those facts.
- Introduction: the main narrative is signal substitution and organizational complements, not a recovered treatment effect.
- Section `Calibrated Structural Benchmark`: retitled and opened as a benchmark for the missing cell.
- Tables `tab_struct_regularization_sensitivity`, `tab_struct_nigeria_endpoint_sensitivity`, and `tab_struct_delivery_thresholds`: make sensitivity and thresholds visible in the main text.

**Residual caveat.** The model remains a calibrated counterfactual. The manuscript now says so directly and uses the structural result to support, not replace, the reduced-form implementation evidence.

## Major Concern 2: The Assignment-Payoff Term Did Not Match the Theory

**Concern.** The earlier payoff term was effectively positive signal quality times execution times delivery. That could not represent cases where diagnostic assignment worsens mismatch relative to grade, especially Liberia and Nigeria.

**Revision.** The preferred structural payoff primitive is now signed assignment value, `G`, defined as predicted mismatch under grade assignment minus predicted mismatch under the intended diagnostic assignment rule. Signal quality remains in the mechanical sorting/compression equation, but the achievement payoff depends on assignment value relative to grade.

**Where fixed.**

- Section `Parameterization`: equation `eq:str_ate_map` uses `lambda G_m omega_m tau_m^alpha`.
- Table `tab_assignment_value_summary`: reports assignment-value primitives.
- Table `tab_struct_assignment_value_sensitivity`: compares the preferred signed assignment-value model with positive-part, share-weighted, and legacy signal-quality payoff specifications.
- Section `Scope and Interpretation`: states that the model can generate gains only when positive assignment value is paired with high assignment-channel delivery.

**Why this matters.** The model now matches the paper's theory. A diagnostic can be predictive in a broad sense and still fail as an assignment rule if it does not improve instructional match relative to grade.

## Major Concern 3: Signal Quality Was Not Cleanly Separated from Assignment Value

**Concern.** The referee worried that signal quality combined reliability, predictive validity, assignment value, and subject/test differences.

**Revision.** The manuscript now separates four objects: signal quality, grade-signal/incremental diagnostic value, signed assignment value, and assignment execution. Signal quality is no longer treated as the payoff primitive.

**Where fixed.**

- Table `tab_grade_signal_substitution`: reports the grade-signal and diagnostic-increment evidence.
- Table `tab_assignment_value_summary`: reports predicted mismatch reduction relative to grade assignment.
- Table `tab_struct_primitive_moments`: separates the moments used to pin down signal quality, execution, and delivery before treatment effects enter.
- Section `Experimental Design and Data`: clarifies the diagnostic source and analysis-group definitions, including the Nigeria two-group collapse.

**Residual caveat.** Nigeria's placement process and endline subject differ from Kenya/Liberia. The manuscript now treats Nigeria-specific structural decompositions as mechanism evidence and reports endpoint sensitivity rather than leaning on a single Nigeria level estimate.

## Major Concern 4: Delivery Fidelity Was Hard to Interpret

**Concern.** The referee argued that `tau` mixed different raw units across countries and that high delivery was not interpretable.

**Revision.** We made `tau` a delivery-activation index and added raw-unit interpretation. The paper now distinguishes the process evidence for Kenya/Liberia from the Nigeria DI numeracy completion measure and shows what the high-delivery benchmark implies in raw units.

**Where fixed.**

- Table `tab_struct_tau_calibration`: documents the process-to-delivery mapping.
- Table `tab_struct_tau_raw_thresholds`: translates counterfactual thresholds back into raw implementation units.
- Table `tab_struct_tau_sensitivity`: reports lower and upper process-to-delivery mappings.
- Structural text: states that Nigeria's high-delivery benchmark should not be read as a literal extrapolation of the observed 26 percent DI completion rate.

**Residual caveat.** A perfectly common delivery measure across all three countries does not exist. The revision solves this by making the normalization transparent and sensitivity-tested.

## Major Concern 5: The Nonlinear Delivery Activation Was Doing Too Much Work

**Concern.** The high-input estimate depended on a nonlinear delivery activation parameter anchored by Kenya's null assignment-payoff slope.

**Revision.** We made that identification logic explicit and moved the key sensitivity checks into the main text. The paper now says the exact 0.19 magnitude is not tightly identified; the stable result is complementarity and a high delivery threshold.

**Where fixed.**

- Table `tab_assignment_payoff_kenya`: reports mover/stayer, predicted-gain, and top predicted-gain tercile payoff tests.
- Table `tab_assignment_payoff_kenya_power`: reports realized MDEs for the Kenya payoff diagnostics.
- Table `tab_struct_delivery_activation`: compares delivery-activation restrictions.
- Table `tab_struct_regularization_sensitivity`: shows the high-input estimate under alternative scale restrictions, including the no-auxiliary-scale case.
- Section `Scope and Interpretation`: states that the model cannot obtain the high-input result by assuming that correct placement already had a large payoff in Kenya.

**Response logic.** Kenya is not used to prove that delivery is the only binding constraint. It is the negative restriction: positive assignment value and clean execution do not produce gains at observed delivery.

## Major Concern 6: The Three Countries Differ Along Many Dimensions

**Concern.** The referee noted that country, subject, curriculum, governance, calendar, and implementation are confounded with the three structural primitives.

**Revision.** The manuscript now treats the model as a structured benchmark across three related experiments, not a general production function identified from clean orthogonal variation. Market residuals are regularized, not used to force a perfect fit. Leave-one-country diagnostics test whether the high-input benchmark is driven by any single country.

**Where fixed.**

- Table `tab_moment_fit`: reports fitted and model-implied moments.
- Table `tab_struct_market_influence`: reports leave-one-market diagnostics.
- Table `tab_struct_stage4_discipline`: reports objective decomposition and optimizer diagnostics.
- Section `Scope and Interpretation`: states that the model is not a ranking of all possible tracking designs or a universally portable high-input ATE.

**Residual caveat.** The paper cannot eliminate all country-level confounding. It now says the model is a disciplined benchmark for these experiments, not an externally valid universal technology estimate.

## Major Concern 7: Peer/Rank Channels Were Weak

**Concern.** The referee objected to using weak and specification-sensitive peer/rank estimates as structural evidence.

**Revision.** Peer/rank effects are now described as diagnostic and composite rather than as a separately identified structural peer effect. The structural text reports a sensitivity check fixing the rank weight to zero and states that the main result is assignment-delivery complementarity.

**Where fixed.**

- Empirical Strategy: peer/rank diagnostics are explicitly described as composite and not decisive.
- Robustness: exact Kenya control-function/recentering checks are described as limiting causal peer/rank interpretation.
- Table `tab_struct_social_channel_sensitivity`: fixes the rank weight to zero; the high-input benchmark remains close to preferred.
- Section `Parameter Estimates`: states that the result is not a claim about a separately identified rank effect.

## Major Concern 8: Reduced-Form Inference, Attrition, and Multiple Testing

**Concern.** The referee wanted the reduced-form evidence to be airtight if it is to carry the paper.

**Revision.** We added consolidated inference, attrition, Lee-bound, IPW, and multiplicity/status tables.

**Where fixed.**

- Table `tab_rnr_inference_checks`: reports clustered, wild cluster, and randomization-inference p-values for the main country ITTs.
- Table `tab_rnr_attrition_bounds`: reports attrition, IPW, and Lee-bound checks across countries and waves.
- Table `tab_multiplicity_disclosure`: separates primary endpoints, heterogeneity/mechanism diagnostics, and assignment-payoff tests, and reports false-discovery-rate q-values by family.
- Nigeria text: treats T3 as suggestive because attrition bounds are wide and gives more interpretive weight to T2 and implementation evidence.

## Major Concern 9: Nigeria Support and the Two-Group Collapse

**Concern.** The Yellow/top cell is thin, so unrestricted three-group estimates risk overinterpretation.

**Revision.** Nigeria's preferred main specification now collapses Blue and Yellow into a higher-level instructional group based on support and implementation logic, not outcome patterns. The unrestricted Red/Blue/Yellow specification is retained in the appendix for transparency.

**Where fixed.**

- Section `Data`: defines Nigeria's two-group collapse as a support-aware analysis choice.
- Table `tab_ng_two_group`: reports the preferred Nigeria two-group estimates.
- Table `tab_ng_over_terms_interact`: reports the unrestricted three-group estimates in the appendix.
- Main pooled track tables use the two-group Nigeria version consistently.

## Major Concern 10: Manuscript Was Too Long and Structurally Heavy

**Concern.** The referee worried that the paper read as too structurally centered and mechanically unwieldy.

**Revision.** We changed the hierarchy. The introduction and discussion now start from signal substitution and the reduced-form implementation facts. The structural section is framed as a calibrated benchmark. The structural scope subsection was shortened to avoid repeating the discussion. Obsolete validation language was removed; the high-input estimate is not presented as a validation check.

**Where fixed.**

- Introduction: foregrounds the grade-as-incumbent-signal argument, the Joplin/DDK contrast, and the country failure modes.
- Structural section: uses the title `Calibrated Structural Benchmark`.
- Table `tab_struct_validation_checks`: retitled `Model Fit, Maintained Restrictions, and Sensitivity Checks`; high-input dominance is not a validation row.
- Discussion: interprets the tracking debate through implementation regimes and closes with policy questions about signal quality, execution, and delivery.

## Remaining Work Before Submission

1. Run a full from-scratch Stata and Python replication once the manuscript text is frozen.
2. Convert this working response map into a formal journal response letter.
3. Do one final length pass after coauthor review, especially on the structural section and appendix ordering.
