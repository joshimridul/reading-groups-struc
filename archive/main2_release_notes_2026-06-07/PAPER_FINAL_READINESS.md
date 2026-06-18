# Paper final-readiness checklist

Date: 2026-06-06

Canonical paper target:

- Live Overleaf folder: `/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited`
- Canonical manuscript: `main2.tex`
- Current verified PDF: `main2.pdf`, 66 pages, 699,365 bytes
- Current status: advanced draft, not yet marked final

## Proven Current Gates

- Clean LaTeX build: live `main2.log` warning grep is clean for unresolved references, undefined citations, overfull/underfull boxes, fatal errors, and rerun warnings.
- Active exhibit integrity: `4_Stata2/audit_overleaf_artifacts.py --overleaf-dir '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited' --entrypoint main2.tex --repo-output-dir 4_Stata2/output --check-labels` reports 49 active `main2.tex` exhibits synced byte-for-byte, zero missing files, zero refs with missing labels, and zero unreferenced active exhibit labels.
- Folder organization: the Overleaf root contains only the active/candidate entrypoints, active `main2.*` and `main_nigeria.*` build products, `bib.bib`, `stata_output/`, `archive/`, and transient `.DS_Store`.
- Empirical-methods alignment: the manuscript now separates randomized ITT estimates from post-treatment classroom diagnostics, approximate peer/rank accounting, exact Borusyak--Hull checks, Lee-bounds attrition checks, and post-treatment class-size residualization.
- Current logic caveats: exact Kenya peer/rank specifications attenuate the approximate diagnostic; Liberia signal quality is low but not isolated from institutional differences; class-size controls are not interpreted as causal mediation.
- PDF text-layer hygiene: targeted scans have removed known joined-word artifacts and code-facing labels from the active manuscript and active generated table notes.
- PDF portability: all active figure PDFs now have embedded fonts, and the compiled live PDF passes the `pdffonts` embedding gate.
- PDF render integrity: `4_Stata2/check_pdf_render.py` renders all 66 live PDF pages at low resolution, verifies consistent page dimensions, and checks that no page is blank or malformed.
- Headline and robustness numeric-claim hygiene: `4_Stata2/check_numeric_claims.py` now checks the central prose claims against active generated tables for ITTs, signal quality, sample flow, attrition, classroom reallocation, dispersion, upper/lower-track effects, peer/rank diagnostics, class-size controls, ceiling checks, score variance, specification robustness, and Lee bounds. It also verifies that the 0.01 EB-shrinkage floor in the cleaning scripts is nonbinding in the current signal-quality table, so the manuscript's statement that the implemented EB weight is the control-group baseline-endline `R^2` remains accurate for the active data. The peer/rank checks now pin down the exact Kenya attenuation values and the non-causal interpretation of the nonzero exact `\mu_i^{BH}` predictable-exposure control. The Lee-bounds checks now guard both the active rates/bounds and the trimming logic in `06_robustness.do`: attrition is computed on the full analytic sample, the lower-attrition arm is trimmed, lower bounds trim high outcomes, and upper bounds trim low outcomes.
- Conclusion generalization: the final cross-domain paragraph now says the two experiments "illustrate" why diagnostic information need not guarantee better outcomes, rather than overextending the evidence with "show." This keeps the external-validity language aligned with the paper's caveated empirical claims.
- Public-version dry run: `4_Stata2/check_public_version.py` now reproduces the public-copy dry run from the live Overleaf folder without editing live files. Its latest run completed cleanly as a 66-page, 695,766-byte PDF with all fonts embedded and all pages renderable. The PDF text has the current date, title, authors, keywords, and JEL codes, with no `PRELIMINARY --- PLEASE DO NOT CIRCULATE` marker; PDF metadata and the artifact/label audit remain clean. The live Overleaf source is still intentionally in draft mode.
- Scope-gate check: a forced temp rebuild of `main_3country_new.tex` completed as a 75-page, 874,716-byte PDF, but it has an unresolved reference to `tab:mechanism`, a visible `Table ??` in the peer-effects section, and 39 unreferenced active exhibit labels in the artifact audit. This confirms that `main2.tex` remains the safer canonical target for now.
- Current reproducibility freeze record: `PAPER_REPRODUCIBILITY_FREEZE.md` records the verified canonical `main2.tex` source/PDF/log hashes, the 49 active exhibit hashes, main generation-code hashes, live build metadata, audit commands, and the dirty-worktree caveat. `4_Stata2/verify_freeze_manifest.py` now checks that manifest against current files.
- PDF metadata polish: the live PDF now embeds the paper title, authors, and keywords in its PDF metadata fields, matching the front matter while leaving the manuscript text and generated exhibits unchanged.
- Repository-facing documentation: the root `README.md` now points to canonical `main2.tex`, uses baseline-endline `R^2` language for predictive power, and describes the Kenya peer/rank evidence as diagnostic and not robust to exact recentering rather than as a settled offsetting mechanism.
- Release-readiness wrapper: `4_Stata2/check_release_readiness.py` reports all manuscript gates as passing, including live PDF text hygiene, PDF font embedding, PDF render integrity, and numeric prose-claim alignment. Its release gates also check that `PAPER_RELEASE_CANDIDATE_PATHS.txt` and `PAPER_RELEASE_CLEANUP_PATHS.txt` have not drifted from the current worktree triage and recursively surface tracked local artifacts. The remaining release blockers are explicit: draft mode, dirty worktree, and the tracked `.DS_Store`/`Rplots.pdf` cleanup decision.

## Remaining Gates Before Calling The Paper Final

- Author/public switch: decide whether to flip the live source from `\publicversionfalse` to `\publicversiontrue`; the dry run verifies that the switch works, but the default live build intentionally still prints `PRELIMINARY --- PLEASE DO NOT CIRCULATE`.
- Scope decision: keep `main2.tex` as the Kenya/Liberia paper, or deliberately promote the three-country `main_3country_new.tex` draft only after fixing the unresolved `tab:mechanism` reference, integrating or retiring unreferenced exhibits, and completing a full prose/identification review of the Nigeria and structural-counterfactual claims.
- Coauthor/content approval: confirm the current title, acknowledgments, author footnotes, and public-circulation status.
- Final read-through: do one uninterrupted PDF read for argument flow, table/figure order, and appendix navigation after the author/public switch decision.
- Release freeze: after the author/public switch and coauthor approval, make a clean version-control commit or tag for the chosen final source. If any generated exhibit changes after `PAPER_REPRODUCIBILITY_FREEZE.md`, rerun the audit and update the hashes.
- Repo hygiene before release: `.gitignore` now blocks regenerated Python caches, local `.claude/` worktrees, and default `Rplots.pdf` output from reappearing as new untracked clutter. `4_Stata2/triage_release_worktree.py` classifies the remaining dirty worktree into release-review buckets and can write `PAPER_RELEASE_WORKTREE_TRIAGE.md`, a durable release-review checklist separating the plausible Kenya/Liberia release set from Nigeria, three-country, structural-extension, supplemental-diagnostic, inactive-output, and legacy work. It can also write and check `PAPER_RELEASE_CANDIDATE_PATHS.txt`, a review-only pathspec for a future staging pass, and `PAPER_RELEASE_CLEANUP_PATHS.txt`, a review-only pathspec for remove/restore/keep cleanup decisions. The release-readiness wrapper runs both drift checks. The already tracked `.DS_Store` files and `Rplots.pdf`, including nested `.DS_Store` paths, still need an explicit final clean-up decision before committing.

## Useful Commands

```sh
python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited' \
  --entrypoint main2.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels

python3 4_Stata2/verify_freeze_manifest.py

python3 4_Stata2/embed_active_figure_fonts.py

python3 4_Stata2/check_numeric_claims.py

python3 4_Stata2/check_pdf_render.py

python3 4_Stata2/check_public_version.py

python3 4_Stata2/check_release_readiness.py

python3 4_Stata2/triage_release_worktree.py

python3 4_Stata2/triage_release_worktree.py \
  --write-markdown PAPER_RELEASE_WORKTREE_TRIAGE.md

python3 4_Stata2/triage_release_worktree.py \
  --write-markdown PAPER_RELEASE_WORKTREE_TRIAGE.md \
  --write-pathspec PAPER_RELEASE_CANDIDATE_PATHS.txt \
  --write-cleanup-pathspec PAPER_RELEASE_CLEANUP_PATHS.txt \
  --check-pathspec PAPER_RELEASE_CANDIDATE_PATHS.txt \
  --check-cleanup-pathspec PAPER_RELEASE_CLEANUP_PATHS.txt

rg -n "(Warning|Undefined|Citation.*undefined|Reference.*undefined|There were undefined|Label.*multiply|Fatal|Emergency|Overfull|Underfull)" \
  '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited/main2.log'

pdfinfo '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited/main2.pdf'
```
