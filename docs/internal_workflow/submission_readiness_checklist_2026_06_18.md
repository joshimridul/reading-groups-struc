# Submission Readiness Checklist

Active manuscript: `main_3country_new.structural_edit.tex`

Compiled manuscript: `build/main_3country_new.structural_edit.pdf`

Response letter: `docs/referee_response_letter_2026_06_18.md`

## Verified

- The manuscript no longer has preliminary title-page language.
- The abstract is 150 words and includes the 0.19 SD high-input benchmark.
- The introduction, structural section, and conclusion frame the structural exercise as a calibrated assignment-delivery benchmark rather than as a substitute for an unobserved experiment.
- The preferred structural payoff primitive is signed assignment value, while signal quality remains in the sorting/compression equation.
- Delivery fidelity is described as an assignment-channel delivery activation index, with raw-unit calibration and threshold tables in the main structural section.
- Nigeria endpoint sensitivity, reduced-form inference checks, attrition/Lee-bound checks, multiplicity disclosure, and Kenya assignment-payoff/MDE diagnostics are in the manuscript package.
- Nigeria main grouped estimates use the support-aware Red versus Blue/Yellow collapse; unrestricted three-group estimates remain in the appendix.
- The appendix now includes prose anchors for all included exhibit clusters; the artifact audit reports zero unreferenced exhibit labels.
- The active PDF has title, author, and keyword metadata populated; all fonts are embedded and all 96 pages render successfully.
- The numeric prose-claim checker is aligned to the current three-country manuscript and passes against the active generated tables.
- The release-readiness wrapper now validates the response letter: the file exists, has matched point-by-point comment/response blocks, has no placeholder or draft text, cites table labels that exist in the active manuscript, and aligns key response-letter numeric claims with generated structural tables.
- The public-version dry run builds a temporary 96-page PDF, checks metadata/fonts/rendering/text hygiene, and does not modify live files.
- The release-readiness wrapper reports all manuscript gates as passing; remaining release gates are repository-state decisions, not manuscript defects.
- Release review files now exist: `GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md`, `PAPER_RELEASE_WORKTREE_TRIAGE.md`, `PAPER_RELEASE_CANDIDATE_PATHS.txt`, `PAPER_RELEASE_CLEANUP_PATHS.txt`, and `PAPER_RELEASE_CLEANUP_DECISIONS.md`. The release-readiness wrapper confirms both pathspecs match the current triage.
- The release-readiness wrapper also validates that `PAPER_RELEASE_CLEANUP_DECISIONS.md` covers every cleanup-decision path in `PAPER_RELEASE_CLEANUP_PATHS.txt`.
- The response letter addresses the main structural referee concerns: payoff primitive, delivery-fidelity interpretation, nonlinear activation, scale sensitivity, Nigeria endpoint/attrition, peer/rank channels, reduced-form inference, Nigeria support, and manuscript organization.

## Verification Commands

Run from the repository root:

```bash
./run_all.sh --existing
python3 3_Python/verify_structural_package.py
python3 4_Stata2/check_numeric_claims.py --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
python3 4_Stata2/check_public_version.py --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
python3 4_Stata2/check_release_readiness.py --repo-root . --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
rg -n "undefined|Citation.*undefined|Reference.*undefined|There were undefined|Label\\(s\\) may have changed|Fatal|Emergency|Error|Overfull|referenced but does not exist" build/main_3country_new.structural_edit.log
```

Current verified status:

- `./run_all.sh --existing` passes.
- `python3 3_Python/verify_structural_package.py` passes.
- The final LaTeX log scan returns no serious issues.
- Materialization reports 90 artifacts, zero missing sources, zero missing labels, and zero unreferenced exhibit labels.
- Numeric prose-claim checks pass.
- Public-version dry run passes and does not modify live files.
- Release-readiness manuscript gates pass: log scan, active exhibit sync, label integrity, active input hashes, PDF metadata, font embedding, PDF rendering, PDF text hygiene, and numeric claims.
- Response-letter validation passes: 9 point-by-point responses, 12 verified manuscript labels, and checked response-letter numeric claims for the preferred high-input benchmark, Nigeria DI delivery, and Nigeria's negative assignment-value primitive.
- Release pathspec drift checks pass: 197 release-candidate paths and 20 cleanup-decision paths match the current worktree triage.
- Cleanup-decision memo validation passes: all 20 cleanup-decision paths are covered by `PAPER_RELEASE_CLEANUP_DECISIONS.md`.

## Remaining Submission Decisions

- Choose the target journal and tailor the response-letter salutation, tone, and section numbering to that journal's R&R format.
- Decide whether the 96-page compiled file should be submitted as one manuscript with appendix or split into a main manuscript and online appendix.
- Confirm coauthor preferences on title-page acknowledgments and author affiliations.
- Decide whether to add journal-specific AI-use, data-availability, or ethics/disclosure language outside the manuscript text.
- Confirm whether the response letter should include table numbers from the compiled PDF once table order is frozen, or continue using stable LaTeX labels.
- Decide how to handle release-gate repository items before tagging or sharing through GitHub Desktop: the worktree is dirty, and tracked local artifacts (`.DS_Store`, `Rplots.pdf`) need a keep/remove decision. Use `GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md`, `PAPER_RELEASE_WORKTREE_TRIAGE.md`, `PAPER_RELEASE_CANDIDATE_PATHS.txt`, `PAPER_RELEASE_CLEANUP_PATHS.txt`, and `PAPER_RELEASE_CLEANUP_DECISIONS.md` as review aids.

## GitHub Desktop Notes

The current repository state includes untracked manuscript, response, generated-output, and pipeline files. Before committing in GitHub Desktop, start with `GITHUB_DESKTOP_RNR_COMMIT_CHECKLIST.md`, then open `PAPER_RELEASE_WORKTREE_TRIAGE.md`. The release-candidate pathspec lists the plausible R&R package; the cleanup pathspec lists local artifacts, old archives, DDK files, and unrelated deletions that need a deliberate keep/remove/ignore decision. `PAPER_RELEASE_CLEANUP_DECISIONS.md` records conservative defaults for those choices.
