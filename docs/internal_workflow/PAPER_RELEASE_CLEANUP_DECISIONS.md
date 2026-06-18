# Paper Release Cleanup Decisions

This memo records the remaining repository-state decisions before committing or tagging the three-country R&R package. It does not remove, restore, stage, or commit files.

## Recommended Defaults

The manuscript and response gates pass. The remaining release blockers are local repository hygiene issues, not paper defects.

Use these defaults unless a coauthor has a reason to override them:

1. Remove tracked local artifacts from version control and keep them ignored going forward:
   - `.DS_Store`
   - `1_Do/.DS_Store`
   - `1_Do/Analysis/.DS_Store`
   - `Rplots.pdf`

2. Do not include unrelated local reference PDFs in the R&R release commit:
   - `2011-peer-effects-teacher-incentives-and-the-impact-of-tracking-evidence-from-a-randomized-evaluation-in-kenya (1).pdf`
   - `VSC (Current WP).pdf`
   - `ai23-802.pdf`

3. Do not include DDK replication data in the paper-release commit unless the manuscript or response letter explicitly relies on a generated result from those files:
   - `ddk data/LICENSE.txt`
   - `ddk data/data/READ_ME.pdf`
   - `ddk data/data/analysis.do`

4. Keep archived `main2` release notes out of the active three-country R&R release unless the commit is meant to preserve project history:
   - `archive/main2_release_notes_2026-06-07/*`

5. Remove unrelated tracked utilities that would distract from the paper package:
   - `mp4_to_mp3_ffmpeg.ipynb`

## Current Release Gate Interpretation

`python3 4_Stata2/check_release_readiness.py --repo-root . --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output`

should pass all manuscript gates and remain blocked only by:

- the dirty worktree, until the release-candidate paths are deliberately reviewed and committed;
- tracked local artifacts, until the files above are removed from version control or restored deliberately.

## GitHub Desktop Workflow

1. Review `PAPER_RELEASE_CANDIDATE_PATHS.txt` first and include the active manuscript, generated active inputs, response materials, pipeline code, and release guardrails that belong in the R&R package.
2. Review `PAPER_RELEASE_CLEANUP_PATHS.txt` next. Use this memo to decide which entries should be removed, ignored, restored, or kept for a separate archival commit.
3. Rerun the release-readiness command after committing. A clean release should pass all manuscript gates and all release gates.
