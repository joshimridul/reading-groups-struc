# GitHub Desktop R&R Commit Checklist

This checklist is for committing the active three-country R&R package after the manuscript gates have passed. It does not replace reviewing the diff.

## Current State

- Active manuscript: `main_3country_new.structural_edit.tex`
- Compiled PDF: `build/main_3country_new.structural_edit.pdf`
- Readiness checklist: `docs/submission_readiness_checklist_2026_06_18.md`
- Worktree triage: `PAPER_RELEASE_WORKTREE_TRIAGE.md`
- Release-candidate path list: `PAPER_RELEASE_CANDIDATE_PATHS.txt`
- Cleanup-decision path list: `PAPER_RELEASE_CLEANUP_PATHS.txt`
- Cleanup-decision memo: `PAPER_RELEASE_CLEANUP_DECISIONS.md`

## Before Committing

Run:

```bash
./run_all.sh --existing
python3 3_Python/verify_structural_package.py
python3 4_Stata2/check_numeric_claims.py --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
python3 4_Stata2/check_public_version.py --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
python3 4_Stata2/check_release_readiness.py --repo-root . --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
```

Expected result: all manuscript gates pass, including response-letter label and numeric-claim validation. Release pathspec and cleanup-memo validation should also pass. The release-readiness script should remain blocked only because the worktree is dirty and tracked local artifacts need a decision.

## In GitHub Desktop

1. Review `PAPER_RELEASE_WORKTREE_TRIAGE.md`.
2. Use `PAPER_RELEASE_CANDIDATE_PATHS.txt` as the review set for files likely to belong in the R&R commit.
3. Use `PAPER_RELEASE_CLEANUP_PATHS.txt` as the list of files that should receive an explicit keep, ignore, restore, or remove decision. `PAPER_RELEASE_CLEANUP_DECISIONS.md` gives conservative defaults for these decisions.
4. Do not stage cleanup-decision files automatically. In particular, decide what to do with `.DS_Store`, `Rplots.pdf`, old archived main2 release notes, DDK files, and local cache files.
5. Confirm that deleted gates files are intentional; the gates material was removed from the manuscript.

## Practical Review Order

In GitHub Desktop, first review and include the files listed in `PAPER_RELEASE_CANDIDATE_PATHS.txt`. This list currently contains the active manuscript, response materials, generated paper inputs, active pipeline code, and release-check scripts.

Then review `PAPER_RELEASE_CLEANUP_PATHS.txt` alongside `PAPER_RELEASE_CLEANUP_DECISIONS.md`. These files are not automatically wrong, but they need an explicit choice:

- restore or remove tracked local artifacts such as `.DS_Store` and `Rplots.pdf`;
- keep or omit old archived `main2` release notes;
- keep or omit DDK data/reference files;
- keep or omit unrelated deleted files such as `mp4_to_mp3_ffmpeg.ipynb`.

The `.gitignore` now ignores local build/font caches and replication scratch outputs, so these should not keep reappearing as untracked noise.

## Suggested Commit Message

```text
Revise three-country ability-grouping R&R manuscript and pipeline
```

## After Committing

Rerun:

```bash
python3 4_Stata2/check_release_readiness.py --repo-root . --overleaf-dir . --entrypoint main_3country_new.structural_edit.tex --repo-output-dir 4_Stata2/output
```

Expected result: manuscript gates still pass. Release gates should pass once the worktree is clean and local artifact decisions have been resolved.
