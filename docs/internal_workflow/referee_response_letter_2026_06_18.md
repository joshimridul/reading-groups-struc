# Response to Referee

We thank the referee for the careful and constructive report. The revision takes the central recommendation seriously: the paper now stands first on the reduced-form and implementation evidence, and uses the structural model as a calibrated assignment-delivery benchmark rather than as a substitute for an unobserved experiment. The revised manuscript's main claim is that cross-grade ability grouping in a scripted-instruction system is an assignment technology. It raises learning only when the placement rule improves assignment relative to grade, schools form the intended groups, and the assigned content is delivered.

Below we describe the main changes. We refer to sections and table labels rather than page and line numbers because pagination will change with journal formatting; these labels are stable in the current source.

## 1. Positioning of the Structural Exercise

**Comment.** The structural counterfactual was carrying more weight than the data could support.

**Response.** We agree. We retitled and rewrote the structural section as a calibrated benchmark (Section 7, "Calibrated Structural Benchmark"). The abstract, introduction, structural opening, and discussion now make the observed experimental results the starting point: the three implementations do not generate a clearly positive average effect, and each setting reveals a different missing input. The structural exercise asks whether those failures are consistent with a complementary assignment-delivery technology and what implementation regime would be required for meaningful gains.

The high-input estimate remains in the paper because it gives scale, but it is no longer the paper's main claim. The revised text emphasizes that the most stable implication is complementarity and a high delivery threshold, not the exact 0.19 SD point estimate.

## 2. Assignment Payoff Primitive

**Comment.** The structural assignment-payoff term used signal quality directly, even though the theory says the payoff should depend on whether the diagnostic improves assignment relative to grade.

**Response.** We rebuilt the preferred structural payoff object (the "Parameterization" subsection of Section 7). The assignment-payoff term now uses signed assignment value, defined as predicted mismatch under grade assignment minus predicted mismatch under the intended diagnostic rule. Signal quality remains in the sorting-compression equation, where it predicts how much the rule changes classroom composition, but the achievement payoff depends on assignment value relative to grade.

This change matters substantively. The model can now represent settings in which a diagnostic has low or negative assignment value. In particular, Nigeria's designed rule has slightly negative signed assignment value, so cleaner execution alone need not raise achievement. Table `tab:struct_assignment_value_sensitivity` compares the preferred signed-assignment-value model to positive-part, share-weighted, and legacy signal-quality payoff specifications.

## 3. Delivery Fidelity and Raw Units

**Comment.** The delivery-fidelity primitive was hard to interpret because the raw process moments differ across countries.

**Response.** We now describe delivery fidelity as a normalized assignment-channel delivery activation index and report the raw-unit mapping explicitly in the "Parameterization" subsection of Section 7. Table `tab:struct_tau_calibration` documents the process evidence used for each country. Table `tab:struct_tau_raw_thresholds` translates the counterfactual thresholds back into raw process units. Table `tab:struct_tau_sensitivity` reports lower and upper process-to-delivery mappings.

The revised text is explicit that Nigeria's high-delivery benchmark is a high-input benchmark, not a literal extrapolation from the observed 26 percent DI numeracy completion rate.

## 4. Nonlinear Activation and Scale Sensitivity

**Comment.** The nonlinear delivery activation term seemed to do too much work, and the high-input magnitude was sensitive to scale restrictions.

**Response.** We made this identification logic and sensitivity central rather than hidden. Kenya's revealed assignment-payoff tests now anchor the nonlinear activation term: Kenya has positive assignment value and clean execution, but students with larger predicted assignment gains do not benefit more at observed delivery (the "Assignment First Stage" subsection of Section 5 and Table `tab:assignment_payoff_kenya`). The model therefore cannot obtain the high-input result by assigning a large payoff to correct placement at observed fidelity.

We also moved the scale-sensitivity table into the main structural narrative (the "Counterfactuals" subsection of Section 7). The current table shows that the preferred high-input benchmark is 0.186 SD, while removing auxiliary scale restrictions allows the extrapolation to rise substantially. The manuscript now states that unrestricted scale choices can make the extrapolation too large; this is why the exact 0.19 number is not treated as the policy sufficient statistic.

## 5. Nigeria Endpoint and Attrition

**Comment.** Nigeria's T3 endpoint has differential attrition, so the structural target should not rely on a single endpoint.

**Response.** We added a Nigeria endpoint sensitivity exercise (the "Counterfactuals" subsection of Section 7 and Table `tab:struct_nigeria_endpoint_sensitivity`). The table re-estimates the production block after replacing the Nigeria ITT target with the T2 estimate, T3 estimate, stacked estimate, and T3 Lee lower and upper bounds. The fully high-input benchmark remains in a narrow range, while Nigeria-specific levels are more sensitive. The revised text therefore treats Nigeria's endpoint uncertainty as important for Nigeria-specific decompositions, not as identifying the high-input result.

We also added consolidated attrition and inference checks in Appendix Tables `tab:rnr_attrition_bounds` and `tab:rnr_inference_checks`, discussed in the "Specification, Inference, and Attrition" subsection of Section 6.

## 6. Peer and Rank Channels

**Comment.** The peer/rank evidence is weak and should not be used as a clean structural peer effect.

**Response.** We now treat peer/rank estimates as composite diagnostics, not as a separately identified social production technology (the peer/rank subsections of Sections 4 and 6). The structural model allows a residual social channel, but the main result is assignment-delivery complementarity. Appendix Table `tab:struct_social_channel_sensitivity` shows that fixing the rank weight to zero leaves the high-input benchmark nearly unchanged.

## 7. Reduced-Form Inference and Multiple Testing

**Comment.** If the reduced-form and implementation facts carry the paper, inference and attrition need to be airtight.

**Response.** We added three referee-facing checks, discussed in the "Specification, Inference, and Attrition" subsection of Section 6 and documented in the appendix. Appendix Table `tab:rnr_inference_checks` reports clustered, wild-cluster, and randomization-inference p-values for the main country ITTs. Appendix Table `tab:rnr_attrition_bounds` reports attrition, IPW, and Lee-bound checks across countries and waves. Appendix Table `tab:multiplicity_disclosure` separates primary endpoints, heterogeneity/mechanism estimates, and Kenya assignment-payoff diagnostics, and reports false-discovery-rate q-values within each displayed family.

## 8. Nigeria Two-Group Collapse

**Comment.** Nigeria's Yellow/top group is sparse, so unrestricted three-group estimates risk overinterpretation.

**Response.** The main Nigeria specification now uses a support-aware two-group collapse, Red versus Blue/Yellow (the Nigeria experiment subsection of Section 3 and the Nigeria robustness discussion in Section 6; Main Table `tab:ng_two_group`). This choice is based on support and implementation logic, not outcome patterns. The unrestricted Red/Blue/Yellow specification remains in the appendix for transparency.

## 9. Manuscript Organization

**Comment.** The paper was too structurally centered and long.

**Response.** We changed the hierarchy. The introduction and conclusion now emphasize the assignment-technology idea and the reduced-form implementation facts. The structural section has been shortened and reframed as a benchmark. We removed the old validation language that made the high-input counterfactual look like a model-validation criterion. The table now titled `Model Fit, Maintained Restrictions, and Sensitivity Checks` separates measured primitives, fit, maintained comparative-static restrictions, and sensitivity checks; the high-input estimate is not a validation row (the "Model Fit, Restrictions, and Counterfactuals" subsection of Section 7; Table `tab:struct_validation_checks`).

In a final architecture pass, we also removed repeated scope-and-interpretation language from the structural section and compressed the model-design, fit, and counterfactual discussion. The structural section now presents the primitives, fit, counterfactuals, and main sensitivities without repeating the same caveat at each step.

## Verification

After revision, we ran the full replication pipeline:

`./run_all.sh`

This runs the Stata reduced-form master, the Python structural and figure pipeline, active-input materialization, artifact audit, and LaTeX compilation. The pipeline completed successfully. The artifact audit reports 90 materialized inputs, zero missing sources, and zero missing labels. The structural package verifier also passes:

`python3 3_Python/verify_structural_package.py`

The current compiled manuscript is `build/main_3country_new.structural_edit.pdf`.

After the final prose and submission-readiness pass, we also reran:

`./run_all.sh --existing`

and re-ran the structural package verifier. The compiled manuscript remains clean, with 90 materialized inputs, zero missing sources, zero missing labels, and a passing structural verifier. The current release-readiness checker also passes all manuscript gates: LaTeX warning scan, active exhibit sync, label/reference integrity, active input hashes, PDF metadata, font embedding, PDF rendering, PDF text hygiene, and numeric prose claims.

We believe these revisions make the paper's contribution clearer and its structural interpretation more disciplined. The paper now uses the experiments for what they identify directly, and uses the calibrated model to summarize the missing high-input cell without making that counterfactual substitute for experimental evidence.
