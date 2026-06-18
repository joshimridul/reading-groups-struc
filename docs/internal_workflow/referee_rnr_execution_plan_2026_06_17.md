# R&R Execution Plan: Structural and Empirical Revision

Draft reviewed: `main_3country_new.structural_edit.tex`

Source report: `/Users/mriduljoshi/.codex/attachments/356418b2-784c-4953-b09d-5418996bed0e/pasted-text.txt`

## Revision Strategy

The referee's central objection is not that the paper lacks a contribution. The objection is that the structural counterfactual is doing more work than the current data and model can support. The revision should therefore make the paper stand first on the reduced-form and implementation evidence, while rebuilding the structural exercise into a transparent calibrated benchmark tied directly to the paper's assignment-gain objects.

The paper's target claim should be:

> Cross-grade ability grouping in a scripted-instruction system is an assignment technology. It raises learning only when the diagnostic improves on grade, schools execute the grouping rule, and assigned content is delivered.

The structural model should support this claim; it should not be the paper's main source of credibility.

## Priority 1: Structural Payoff Object

### Referee concern

The current preferred assignment-payoff term is effectively `lambda * rho * omega * tau^alpha`. This does not match the theory's assignment-gain object and cannot by itself generate negative assignment value when the diagnostic worsens mismatch.

### Fix

Promote predicted mismatch reduction to the preferred structural payoff primitive:

`lambda * G_m * omega_m * tau_m^alpha`

where `G_m` is computed from predicted mismatch under grade assignment versus diagnostic assignment. The existing `rho` model should become a sensitivity or legacy benchmark.

### Implementation steps

1. Use existing student-level assignment-gain objects from `3_Python/output/control_trained_gains/*_predicted_gains.parquet`.
2. Construct country-level payoff primitives:
   - mean net mismatch reduction;
   - positive-part mismatch reduction;
   - share-weighted positive reduction;
   - optionally realized-rule version for Nigeria if available.
3. Use the preferred assignment-gain primitive in the main stage-4 production block.
4. Keep `rho` in the mechanical sorting equation, where it belongs.
5. Rename structural outputs so the main tables report assignment-value primitives, not `rho` as the payoff object.
6. Add a sensitivity table comparing assignment-value, positive-part, share-weighted, and legacy `rho`.

### Manuscript changes

The structural section should say that signal quality remains a measurement primitive, but the payoff primitive is assignment value relative to grade.

## Priority 2: Status of Structural Model

### Referee concern

The structural model is too calibrated and underidentified to support a headline estimated high-input ATE.

### Fix

Reposition the model as a calibrated benchmark/response surface, not an estimated high-input treatment effect.

### Implementation steps

1. Remove or downgrade `+0.19 SD` from the abstract.
2. Rename “Structural Estimation and Counterfactuals” to emphasize calibrated benchmarking.
3. Keep scale sensitivity in the main text.
4. Report high-input results as a range:
   - preferred/assignment-value model;
   - weaker scale normalizations;
   - no auxiliary scale restriction;
   - alternative Nigeria endpoint targets.
5. Move low-value structural diagnostics to appendix where possible.

## Priority 3: Nigeria Endpoint Sensitivity

### Referee concern

Nigeria T3 has differential attrition and wide Lee bounds, so structural targets should not rely only on T3.

### Fix

Repeat structural stage-4 results under alternative Nigeria ITT targets:

1. T3 primary endpoint;
2. T2 endterm endpoint;
3. stacked endterm endpoint;
4. conservative Lee-bound adjusted T3 endpoint if feasible.

### Implementation steps

1. Locate Nigeria endpoint estimates in Stata outputs or compute from analysis parquet.
2. Add a stage-4 sensitivity wrapper that replaces the Nigeria ITT and peer/rank targets while holding primitives fixed.
3. Output a table with high-input, Kenya high-delivery, and Nigeria complementarity results under each endpoint.
4. Use T2/stacked as robustness checks in the main structural narrative.

## Priority 4: Delivery Fidelity in Raw Units

### Referee concern

The current `tau` index mixes treatment-control lesson-completion differences in Kenya/Liberia with DI completion levels in Nigeria.

### Fix

Keep `tau` as a normalized activation index only if the paper also shows raw observed implementation units side by side.

### Implementation steps

1. Build one implementation dashboard with common rows for all countries:
   - diagnostic used for assignment;
   - predictive R2/incremental R2;
   - assignment rule compliance;
   - missing assignment;
   - intended groups formed;
   - actual groups observed;
   - assignment-channel lesson completion;
   - wrong-track delivery;
   - teacher attendance;
   - pupil attendance;
   - class size;
   - grade mixing.
2. Mark unavailable cells explicitly as unavailable rather than silently omitting countries.
3. Make the dashboard a main table before the structural section.

## Priority 5: Signal Quality and Assignment Value

### Referee concern

`rho` combines reliability, predictive validity, and assignment value. Nigeria's actual placement diagnostic may differ from the baseline score used to estimate `rho`.

### Fix

Split the text and tables into:

1. actual diagnostic used for placement;
2. predictive validity for endline outcomes;
3. incremental value over grade;
4. assignment value measured by predicted mismatch reduction.

### Implementation steps

1. Add a diagnostic-source table for Kenya, Liberia, Nigeria.
2. For Nigeria, state whether `placement_score` or Term 1 math score is used for each object.
3. If feasible, compute predictive power using Nigeria `placement_score`; otherwise report missing/limitations clearly.

## Priority 6: Reduced-Form Inference

### Referee concern

The reduced-form evidence is the paper's strongest part, but inference and attrition need to be airtight.

### Fixes

1. Liberia clustering:
   - confirm randomization level;
   - if school-level, re-run Liberia inference clustered at school;
   - add randomization-inference p-values if feasible.
2. Kenya attrition:
   - add unadjusted and adjusted attrition differences;
   - add Lee bounds;
   - add IPW robustness if feasible.
3. Nigeria:
   - keep T3 as primary only if PAP supports it;
   - make T2 and stacked endpoint evidence prominent;
   - label Blue/Yellow heterogeneity as suggestive.
4. Multiple testing:
   - label primary outcomes vs mechanism diagnostics;
   - add BH/FDR or family-wise adjusted p-values for main heterogeneity families if feasible.

## Priority 7: Kenya Payoff Tests

### Referee concern

The Kenya mover/stayer and predicted-gain tests are the best evidence and should be expanded.

### Fixes

1. Add Grade 1 movers-up and Grade 2 movers-down effects if data support it.
2. Add effects for largest predicted mismatch-reduction students.
3. Report MDE for mover/stayer interaction or predicted-gain interaction.
4. If content receipt data exist, show whether movers actually received different content.

## Priority 8: Manuscript Architecture

### Referee concern

The paper is too structurally centered and over-built.

### Fix

Reorganize the narrative:

1. Introduction: reduced-form facts first.
2. Conceptual framework: signal substitution and complements.
3. Design and implementation dashboard.
4. Reduced-form effects.
5. Assignment first stage and Kenya payoff diagnostics.
6. Mechanism synthesis.
7. Calibrated structural benchmark.
8. Discussion.

## Work Log

- 2026-06-17: Created plan from referee report. Next implementation target: structural payoff primitive.
- 2026-06-17: Rebuilt the preferred structural payoff object around signed assignment value `G_m`, keeping `rho` in the sorting/compression equation. The structural script now reports assignment-value payoff sensitivity, raw-unit tau thresholds, delivery-calibration sensitivity, scale sensitivity, and component decompositions.
- 2026-06-17: Added Nigeria endpoint-target sensitivity. The stage-4 production block is re-estimated after replacing only the Nigeria ITT target with the harmonized T3 estimate, T3 ETE index, T2 ETE index, stacked all-waves estimate, and T3 Lee lower/upper bounds. The fully high-input benchmark remains in the range `+0.173` to `+0.189`, while the Nigeria-environment `G+tau` counterfactual is sensitive to the endpoint target.
- 2026-06-17: Compiled `main_3country_new.structural_edit.tex` through `./run_all.sh --existing`; materialization reported 86 artifacts and 0 missing sources, and the final LaTeX log had no undefined references/citations, fatal errors, or overfull boxes.
- 2026-06-18: Added `4_Stata2/08_rnr_inference_attrition.do` and wired it into `_master_paper.do`. The new R&R tables report country-level cluster/randomization inference checks and consolidated attrition/IPW/Lee-bound checks. The Kenya and Liberia null/negative estimates are stable to these checks; Nigeria T2 Lee bounds are tight while T3 Lee bounds remain wide.
- 2026-06-18: Ran the new Stata do-file with Stata 19 and inspected `08_rnr_inference_attrition.log` plus the generated tables. Then compiled through `./run_all.sh --existing`; materialization reported 88 artifacts and 0 missing sources, and the final LaTeX log had no undefined references/citations, fatal errors, or overfull boxes.
- 2026-06-18: Extended the Kenya assignment-payoff diagnostics in `04c_assignment_channel_tests.do`. The paper-facing table now includes top predicted-gain tercile effects and a new MDE table. The top predicted-gain tercile ITT is `-0.004` (SE `0.056`), the treatment-by-top-tercile interaction is `-0.036` (SE `0.089`), and realized 80 percent MDEs are `0.230` for the mover interaction, `0.191` for the predicted-gain interaction, `0.157` for the top-tercile ITT, and `0.249` for the top-tercile interaction.
- 2026-06-18: Ran `04c_assignment_channel_tests.do` with Stata 19 and inspected `04c_assignment_channel_tests.log`, `tab_assignment_payoff_kenya.tex`, and `tab_assignment_payoff_kenya_power.tex`. Then compiled through `./run_all.sh --existing`; materialization reported 89 artifacts and 0 missing sources, and the final LaTeX log had no undefined references/citations, fatal errors, or overfull boxes.
- 2026-06-18: Added `4_Stata2/09_multiplicity_disclosure.do` and wired it into `_master_paper.do`. The new appendix table separates primary endpoints, track-position/heterogeneity estimates, Nigeria two-group contrasts, peer/rank diagnostics, and Kenya assignment-payoff tests, and reports false-discovery-rate q-values within each displayed family.
- 2026-06-18: Cleaned stale structural wording after the assignment-value revision, including the appendix discussion of the Nigeria-environment `G+tau` decomposition and the stage-4 optimizer table note. Then compiled through `./run_all.sh --existing`; materialization reported 90 artifacts and 0 missing sources, and the final LaTeX log had no undefined references/citations, fatal errors, or overfull boxes.
- 2026-06-18: Completed a focused architecture pass on the structural section. The main text now refers to the missing positive-assignment-value, high-execution, high-delivery cell rather than the old `rho-omega-tau` payoff shorthand, and the `Scope and Interpretation` subsection is shorter and less defensive.
- 2026-06-18: Drafted `docs/referee_response_draft_2026_06_18.md`, a point-by-point response map covering the structural payoff object, delivery-fidelity interpretation, nonlinear activation, country confounding, peer/rank treatment, inference/attrition, Nigeria support, multiplicity, and manuscript architecture.
- 2026-06-18: Ran the full `./run_all.sh` replication pipeline from Stata through Python, input materialization, artifact audit, and LaTeX. The first full audit found a reproducibility bug in Matplotlib/fontconfig cache handling; `run_all.sh` now sets repo-local `MPLCONFIGDIR`, `XDG_CACHE_HOME`, and `MPLBACKEND=Agg`, and both figure scripts force the `Agg` backend. A subsequent full `./run_all.sh` completed successfully with 90 materialized artifacts, 0 missing sources, 0 missing labels, and a compiled 100-page PDF.
- 2026-06-18: Corrected regenerated scale-sensitivity prose. The current table shows the preferred high-input benchmark at `+0.186`, rising to `+0.300` without the `lambda/phi` priors and to `+0.368` with no auxiliary scale restriction. The manuscript now frames this as evidence that unrestricted scale choices can over-extrapolate, so the exact `+0.19` magnitude is not the policy sufficient statistic.
- 2026-06-18: Replaced the stale structural verifier with a current-contract verifier. `python3 3_Python/verify_structural_package.py` now checks generated structural outputs, acceptance tests, key counterfactual ranges, active paper artifacts, current terminology, and the LaTeX log; it passes after the full pipeline.
- 2026-06-18: Drafted `docs/referee_response_letter_2026_06_18.md`, a submission-style response letter skeleton based on the working response map.
- 2026-06-18: Completed a final internal length and architecture pass on the structural section. The section now removes the repeated `Scope and Interpretation` subsection, compresses the structural design, model-fit, and counterfactual prose, and preserves all generated estimates and table references. The structural section now runs about 3,900 words, down from about 4,900 in the earlier audit.
- 2026-06-18: Re-ran `./run_all.sh --existing` and `python3 3_Python/verify_structural_package.py` after the final pass. The fast pipeline completed with 90 materialized artifacts, 0 missing sources, 0 missing labels, and a compiled 97-page PDF. The structural verifier passes, and the LaTeX log scan finds no undefined references/citations, fatal errors, overfull boxes, or stale anchor warnings.
- 2026-06-18: Added a short transparency and replication paragraph to the manuscript before the references. It distinguishes country-specific primary ITTs from harmonized pooled estimates, support-aware Nigeria grouped estimates, mechanism diagnostics, and the structural benchmark.
- 2026-06-18: Updated the collaborator-facing README and `run_all.sh --help` language so the documented active manuscript and compiled PDF match the current repository entrypoint, `main_3country_new.structural_edit.tex`.
- 2026-06-18: Completed an additional top-manuscript compression pass on the introduction and discussion/conclusion. The pass removed repeated central-claim language, tightened the roadmap, and compressed the conclusion's tracking/equity/policy synthesis without changing estimates or table references. The introduction now runs about 2,200 words and the discussion/conclusion about 1,350 words.
- 2026-06-18: Completed a submission-readiness language pass. The manuscript title page no longer says `PRELIMINARY --- PLEASE DO NOT CIRCULATE`; the transparency paragraph now refers to the replication package without calling the paper a draft; the response letter replaces generic `robust implication` language with `most stable implication`; and the README describes the current manuscript rather than a draft.
- 2026-06-18: Added `docs/submission_readiness_checklist_2026_06_18.md`, which records verified manuscript/response/pipeline status and separates the remaining coauthor/journal decisions from completed R&R work. The README now points collaborators to this checklist.
- 2026-06-18: Added compact prose anchors for the design summary, appendix table blocks, structural-diagnostic tables, and supplementary figures. The artifact audit now reports 90 materialized artifacts, 0 missing sources, 0 missing labels, and 0 unreferenced exhibit labels; the structural verifier passes and the LaTeX log scan finds no serious issues.
- 2026-06-18: Updated the public/readiness checkers for the active three-country manuscript. `check_numeric_claims.py` now validates the current three-country prose against generated tables, `check_public_version.py` now builds a temporary public dry run for the no-switch manuscript without modifying live files, and `check_release_readiness.py` now reads the active build outputs, PDF metadata, active-input manifest, and current front matter. All manuscript gates pass; release gates remain blocked only by repository-state decisions: dirty worktree, missing release/cleanup pathspecs, and tracked local artifacts.
- 2026-06-18: Updated and ran `4_Stata2/triage_release_worktree.py` for the active three-country R\&R package. It now uses `paper_pipeline/active_inputs_manifest.csv`, lists untracked files individually, treats deliberate gates removals as release candidates, and keeps scratch/inactive outputs separate. It wrote `PAPER_RELEASE_WORKTREE_TRIAGE.md`, `PAPER_RELEASE_CANDIDATE_PATHS.txt`, and `PAPER_RELEASE_CLEANUP_PATHS.txt`; release-readiness drift checks now pass for both pathspecs.
- 2026-06-18: Added `GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md`, a short handoff for reviewing the R\&R package in GitHub Desktop. The checklist points to the release triage, release-candidate pathspec, cleanup-decision pathspec, and expected verification commands.
- 2026-06-18: Added `.gitignore` rules for local build/font caches and `replication_audit/stata_scratch/`, reducing untracked review noise without deleting any files. After adding the cleanup-decision memo, the current triage reports 286 changed/untracked paths, with 197 release-candidate paths and 20 cleanup-decision paths.
- 2026-06-18: Added response-letter validation to the release-readiness wrapper. The checker now requires matched point-by-point responses, no placeholder/draft text, coverage of the main structural referee concerns, table labels that exist in the active manuscript, and response-letter numeric claims that match generated structural tables. The current response letter passes with 9 point-by-point responses, 12 verified manuscript labels, and checked numeric claims for the preferred high-input benchmark, Nigeria DI delivery, and Nigeria's negative assignment-value primitive.
- 2026-06-18: Added `PAPER_RELEASE_CLEANUP_DECISIONS.md`, a non-destructive cleanup memo with conservative defaults for tracked local artifacts, local reference PDFs, DDK files, archived `main2` notes, and unrelated deleted files before using GitHub Desktop for the release commit.
- 2026-06-18: Added cleanup-decision memo validation to `check_release_readiness.py`. The release checker now requires every path in `PAPER_RELEASE_CLEANUP_PATHS.txt` to be covered by `PAPER_RELEASE_CLEANUP_DECISIONS.md`; the current memo covers all 20 cleanup-decision paths.

## Current Status After 2026-06-18 Internal Pass

Completed:

1. Priority 1, structural payoff object: preferred payoff primitive is now signed predicted mismatch reduction rather than raw signal quality.
2. Priority 2, status of structural model: prose now frames the model as a calibrated benchmark with scale and sensitivity restrictions visible in the main text.
3. Priority 3, Nigeria endpoint sensitivity: implemented, generated, and added to the main structural section.
4. Priority 4, delivery fidelity raw units: raw-unit tau threshold and calibration tables are generated and included.
5. Priority 5, signal quality and assignment value: signal quality, incremental grade value, and assignment-value primitives are separated in the structural exposition and tables.
6. Priority 6, reduced-form inference: added cluster/randomization inference checks, consolidated attrition/IPW/Lee-bound checks across countries, and added a family-level multiplicity/status disclosure table for primary, heterogeneity, and mechanism estimates.
7. Priority 7, Kenya payoff tests: added top predicted-gain tercile tests, retained mover-direction estimates, and added realized MDEs for the main payoff interactions.
8. Priority 8, manuscript architecture: reduced-form and implementation evidence now carry the paper, structural results are framed as a calibrated benchmark, and the structural section has been tightened.
9. Appendix and exhibit architecture: all included appendix tables and figures are now referenced from prose, so the appendix reads as a curated record of diagnostics rather than an unanchored table bank.
10. Submission-readiness gates: compile, active input hashes, exhibit sync, label integrity, PDF metadata/font/render checks, PDF text hygiene, public dry run, structural verification, and numeric prose-claim checks now pass for `main_3country_new.structural_edit.tex`.

Open only before external circulation or submission:

1. Coauthor/journal length pass: the manuscript is still long, especially because the main file contains tables and appendix material. Further compression may be useful after coauthors decide the target journal and appendix strategy.
2. Final journal response polish: `docs/referee_response_letter_2026_06_18.md` is drafted and aligned with the revisions, but it should be tailored once the revision is frozen and the submission target is chosen.
3. Repository release decision: before tagging or sharing through GitHub Desktop, review `GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md` and `PAPER_RELEASE_WORKTREE_TRIAGE.md`, stage or omit the 197 release-candidate paths deliberately, and decide whether tracked local artifacts such as `.DS_Store` and `Rplots.pdf` should be removed or restored.
