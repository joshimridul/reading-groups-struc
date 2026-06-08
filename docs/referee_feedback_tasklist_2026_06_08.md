# Referee Feedback Tasklist and Response Map

This note converts the June 8, 2026 feedback into revision tasks and records how the current pass addressed each concern.

## Completed in this pass

1. Recenter the paper on observed failures rather than a positive structural headline.
   - Revised the title, abstract, introduction, structural opening, scope, and conclusion.
   - The paper now states that the observed implementations do not generate a clearly positive average effect and that the failures identify missing complements.

2. Replace structural "recovery" language with calibrated benchmarking language.
   - Replaced language saying the model "recovers" the missing high-input case with "benchmarks," "calibrated assignment-delivery model," and "counterfactual benchmark."
   - Clarified that the model is not a substitute experiment and that the exact 0.19 SD magnitude is not the central claim.

3. Make Kenya the central negative restriction.
   - Preserved and sharpened the Kenya mover/stayer, cutoff-distance, and predicted-assignment-gain discussion.
   - The manuscript now says Kenya creates the intended reallocation but shows that sorting alone is not the treatment.

4. Treat Nigeria positive effects as suggestive and foreground implementation failure.
   - Added main-text attrition language: T3 Lee bounds are wide, so the T3 positive estimate is suggestive.
   - Clarified that the support-aware Red versus Blue/Yellow collapse is based on support and implementation logic, with unrestricted three-group estimates in the appendix.
   - Clarified that Nigeria's value is diagnostic: the high-input design did not realize high execution or delivery.

5. Clarify pre-specified endpoints and analysis groups.
   - Added a data/design paragraph defining Kenya and Liberia primary outcomes, Nigeria T3 as the primary endpoint, T2 and stacked estimates as checks, and Nigeria Red versus Blue/Yellow as a support-aware grouped analysis.
   - Added language distinguishing intended assignment, realized roster assignment, observed classroom grouping, and analysis groups.

6. Put the incumbent-grade-signal evidence in the main text.
   - Added Table `tab:grade_signal_substitution`, which reports grade-only predictive power, grade + diagnostic predictive power, incremental diagnostic value, and rank persistence for all three countries.
   - This directly supports the signal-substitution framing.

7. Move delivery-fidelity calibration into the main structural section.
   - Promoted Table `tab:struct_tau_calibration` and Table `tab:struct_tau_sensitivity` from appendix to main text.
   - Added plain-English interpretation: tau is not general school quality and not a causal treatment-control lesson-completion effect; it is a bounded assignment-channel delivery index.

8. Move scale-sensitivity evidence into the main structural interpretation.
   - Promoted Table `tab:struct_regularization_sensitivity` into the main text.
   - Added the key interpretation: sign and complementarity are robust; the exact 0.19 magnitude is not.

9. Emphasize delivery thresholds over the point estimate.
   - Strengthened the paragraph around Table `tab:struct_delivery_thresholds`.
   - The text now states that meaningful gains require very high assignment-channel delivery fidelity and that modest implementation improvements would not have transformed the observed experiments.

10. Fix presentation inconsistency on authorship.
   - Changed title-page footnote from "I am grateful/errors are my own" to "We are grateful/errors are our own."

11. Clarify omega.
   - Added a plain-English explanation that omega is not the share of correctly assigned students; it summarizes how much of the intended assignment structure survives roster, group-formation, and missing-assignment frictions.

12. Add assignment-value diagnostics.
   - Added Table `tab:assignment_value_summary`, which compares predicted squared mismatch under grade assignment and intended diagnostic assignment.
   - Added Figure `fig:assignment_mismatch_distributions`, which plots the distribution of predicted mismatch under the grade and diagnostic rules by country.
   - The new diagnostics show that Kenya lowers predicted mismatch on average, Liberia is mixed despite some mean reduction, and Nigeria's designed rule does not lower predicted mismatch on average.

13. Make leave-one-country structural diagnostics easier to interpret.
   - Added main-text language summarizing Appendix Table `tab:struct_market_influence`.
   - The high-input benchmark remains positive when omitting any one country from stage-4 targets, while the Nigeria-environment decomposition is more sensitive and is therefore treated as mechanism evidence.

## Partly addressed, still worth deeper work

1. Incumbent-grade signal table with vertical-scale outcomes.
   - Current table uses raw follow-up-score predictive diagnostics already in the pipeline. If vertically scaled outcomes become available across all countries, this table should be upgraded.

2. Nigeria implementation gradient.
   - Audited the existing exploratory implementation-gradient output. The available implementation-quality interaction is based on a sparse school-level proxy and is not stable enough to include as supportive evidence.
   - Existing output: `3_Python/output/control_trained_gains/table_nigeria_implementation_validation.csv`. The triple interaction of treatment, predicted gain, and implementation quality is negative in this exploratory specification, so the paper should not claim a positive implementation gradient without a cleaner construction.

3. Further length reduction.
   - This pass improved hierarchy and interpretation but did not cut 25--35 percent of the introduction or formal theory. A later pass should shorten repeated signal-substitution exposition.

4. Main-text architecture.
   - The paper now foregrounds the reduced form more clearly, but the full section order was not rebuilt around the exact Kenya-Liberia-Nigeria sequence proposed in the feedback.

## Referee-facing summary

We revised the manuscript so the observed experimental failures are the starting point rather than a problem for the structural model to undo. The abstract, introduction, results, structural section, and conclusion now state that the three RCTs do not show a clearly positive average effect and that the contribution is to explain why: Liberia lacks a valid signal, Kenya shows that correct sorting alone has no payoff at observed fidelity, and Nigeria shows how a high-input design can fail on execution and delivery. We recast the structural exercise as a calibrated assignment-delivery benchmark, not an identified substitute experiment; promoted the delivery-fidelity calibration, tau sensitivity, scale sensitivity, and delivery-threshold tables to the main text; added a main table documenting the diagnostic's incremental value over grade; added assignment-value diagnostics showing how predicted mismatch changes under grade versus diagnostic assignment; made Nigeria attrition and the support-aware two-group collapse explicit; clarified the interpretation of the assignment-execution primitive; and summarized leave-one-country structural influence diagnostics in the main text.
