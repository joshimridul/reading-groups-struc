# Paper reproducibility freeze manifest

Date: 2026-06-06

This manifest records the verified reproducibility state for the canonical
Kenya/Liberia manuscript. It is an artifact/source freeze for the current
advanced draft, not a final release tag: the repository worktree is dirty, the
live manuscript remains in draft mode, and the author/public switch has not yet
been made.

## Canonical target

- Live Overleaf folder: `/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited`
- Canonical manuscript: `main2.tex`
- Canonical PDF: `main2.pdf`
- PDF metadata: 66 pages, 699,365 bytes, PDF version 1.5
- PDF creation/modification time: Sat Jun 6 18:50:34 2026 PDT
- Embedded PDF metadata: title, author, and keyword fields populated from the paper front matter
- Draft status: `\publicversionfalse`, so the PDF intentionally prints `PRELIMINARY --- PLEASE DO NOT CIRCULATE`

## Verification gates

The following checks were run on the live Overleaf folder:

```sh
rg -n "(Warning|Undefined|Citation.*undefined|Reference.*undefined|There were undefined|Label.*multiply|Fatal|Emergency|Overfull|Underfull)" \
  '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited/main2.log'

pdfinfo '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited/main2.pdf'

python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited' \
  --entrypoint main2.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels
```

Results:

- Warning grep: clean; no output.
- Freeze manifest verification: `python3 4_Stata2/verify_freeze_manifest.py` passes with 71 hash rows checked and 49 active `main2.tex` exhibits.
- Release-readiness wrapper: `python3 4_Stata2/check_release_readiness.py` passes all manuscript gates, including PDF text hygiene, PDF font embedding, rendered-page integrity, and numeric prose-claim alignment. Its release gates also verify that `PAPER_RELEASE_CANDIDATE_PATHS.txt` and `PAPER_RELEASE_CLEANUP_PATHS.txt` still match the current triage and that tracked local artifacts are surfaced recursively; final release remains blocked on the intentionally unresolved draft/public switch, dirty worktree, and tracked local-artifact decision.
- Public-version dry-run checker: `python3 4_Stata2/check_public_version.py` builds a temp copy with `\publicversiontrue` and verifies a 66-page, 695,766-byte public PDF with all fonts embedded and all pages renderable without modifying live Overleaf files.
- Active exhibit audit: 49 `main2.tex` files referenced from `stata_output/`.
- Repo/Overleaf active exhibit sync: 49 synced, 0 different, 0 missing in repo, 0 missing in Overleaf.
- Label/ref audit: 67 labels, 52 distinct refs, 0 refs with missing labels, 0 unreferenced active exhibit labels.
- Folder-wide `stata_output` audit: 88 files, all 88 referenced by at least one retained root entrypoint.

## Git state

- Repo root: `/Users/mriduljoshi/Github/AbilityGrouping`
- Current `HEAD`: `f807a8e96eea892166606abd54182e827ccb2e65`
- Dirty-worktree shortstat at freeze-record creation: 64 files changed, 7697 insertions(+), 6897 deletions(-)

Because the worktree is dirty, this manifest should be treated as a current-state
freeze record, not as a clean version-control release. Before final circulation,
make a clean commit or tag after the public-version decision. Rerun
`git diff --shortstat` for the live working-tree count, since handoff-note and
verifier edits can change the shortstat without changing the frozen paper
artifacts.

## Canonical source and build hashes

| File | SHA-256 |
|---|---|
| live `main2.tex` | `810e685fb70cc689eb667c37e2b60e013ddd5e9b7edf03374a18dc6f1848bf17` |
| live `main2.pdf` | `ce9ad66bef0e07c2e73937dd655b2ae0292de7b9c07097ec310cea8d6b7c53e0` |
| live `main2.log` | `7989842a28d6bcd762283e672de5c675c27d0a691a0b6d17621ec03359e623a4` |

## Main generation and sync code hashes

| File | SHA-256 |
|---|---|
| `4_Stata2/_master.do` | `739626d965f06a68e0499edd1daffd916c5ee3f6244c89359d50fdfcf86fd0a5` |
| `4_Stata2/00_clean_liberia.do` | `16cedde08468da178cb1b2657e17d0eb9d509748b46063fba992ad92315c218f` |
| `4_Stata2/00_clean_kenya.do` | `5e54bc9b429c73d96f4357fc2af1a2c0107cc676c7d24557dcc1f55294f96ef1` |
| `4_Stata2/01_descriptives.do` | `90874c302977b9dbd02058eaff0317d0b3d69cc3daf719425cc7aea2d00e61f4` |
| `4_Stata2/02_main_analysis.do` | `45cfa4c506d503ba1318f71c6585d880e6e3aefa50ce719d5d5d328cdf409e14` |
| `4_Stata2/03_diagnostics.do` | `db34e8f6e218ddb39c3e29322409ad13f8b1999242e4d0d0dbd5b60f2a12208a` |
| `4_Stata2/04_structural.do` | `d7432d19a4e9eefe7661efb89f601e9e53f69974b6ec01beaf06319f58ef3d80` |
| `4_Stata2/05_gates.R` | `409ce6919f922e72aa1d9d5d7a5ca35b607be4e60ea5c1b90ab3e4bbaeff7ca9` |
| `4_Stata2/06_robustness.do` | `bf7b14843a9e2978be679476a8e345d00f881502e6f9d94fc2831d1a85eaec3b` |
| `4_Stata2/07_lesson_completion.do` | `8cf53c3d7956d3dee378dee18355a57dc9bcd480477e8aa6d2d495147ec02db1` |
| `4_Stata2/build_main2_tables.py` | `420dd287d21d7c63a698f834447ef5fbce88720da7413abc1d1025b9a9087af9` |
| `4_Stata2/audit_overleaf_artifacts.py` | `a34953a8048486af4fdb6a261e20480b3aa91fa3939c736fb816bfb809018419` |
| `4_Stata2/verify_freeze_manifest.py` | `20c2a8c486223abe57fd9fe34c38313ec60bf5d5ba2e17f06d134e8c4b8840b5` |
| `4_Stata2/check_release_readiness.py` | `9bc529b02e226fa482640bf8309036e1b5a3b04d635750296d04d5f03af16d66` |
| `4_Stata2/check_public_version.py` | `884aa0cae91d888230c57f88bdcf4b749356a329d313b08cdc629eee076ac599` |
| `4_Stata2/embed_active_figure_fonts.py` | `c17124c6f269a0443bbcc8ba9651eb1e478ba2b9d5f94c7563352036603f9e5f` |
| `4_Stata2/check_numeric_claims.py` | `37ed2db63752da33eb0812a4db6331f8e31d44318ae625e3878286c20db8a4a2` |
| `4_Stata2/check_pdf_render.py` | `6130f8f28d2a093f2aa9569fcd4b5bb42fefeb83f812f0035ca75836eeccae62` |
| `4_Stata2/triage_release_worktree.py` | `b14e01c0495f700b97720ec1718c53768cc7ccaf8d56e3eba005916378fd0373` |

## Active exhibit hashes

Each active `main2.tex` exhibit below has the same SHA-256 in live Overleaf
`stata_output/` and repo `4_Stata2/output/`.

| Active exhibit | SHA-256 |
|---|---|
| `fig_classroom_reallocation.pdf` | `78ea01a88727e69d4102399a9252f74b18337d28bbed0b71d2742cb94592b322` |
| `fig_cutoff_het.pdf` | `fb103bdfb4b0eeaf316a50a961f8843dfcd730aeb49fa9be218976c2c1fbe7d9` |
| `fig_deterministic_cutoffs.pdf` | `7ea1fd7b80f17e28cf2ecebda19a2984f526aa8b6343f04a77ae6a9867b045af` |
| `fig_four_margins.pdf` | `d1b33303edc60654702cf2a635aa12cf4c5a60a2bfcd37e17fa3710566034aae` |
| `fig_misclass.pdf` | `f3369dca36183e2f6643b67fdfc070645fca4a8c902d8bce2bd8bbbc3217d19f` |
| `fig_posterior_shrinkage.pdf` | `78d45b35b2b2170ac637eb39eace2afc3145fb21cb3d60a5d0ea8fe6ba59c7fd` |
| `fig_track_bins.pdf` | `3d7b36c4c14765ec259ac3577045e8e4dc3f43f3726f1693f9fa92ba2bf34def` |
| `ke_attrition.tex` | `0e39023b69929ea87f78b8e4306fd1e9c5aff0dd2e34c60684a0890cb648ec87` |
| `ke_binscatter.pdf` | `5405b92eab3c6a469a80e20e3d8e1c660c2ebdf3ee305e0625a4d4385d468eff` |
| `ke_bl_dist.pdf` | `99fcc35d8dc09bf081484de7cf6ce9902f031f08653afca2e7c69e2dd82eb6da` |
| `ke_classsize.pdf` | `73fb2ee8be48f9cba9b81366ce3c35cb73977d1f35c110406f3d9ac52dab0f84` |
| `ke_dispersion_box.pdf` | `7e16f14310f925a54b3c79d088f8631cf13c434ae61bde5b21ead35cabebe75b` |
| `ke_el_dist.pdf` | `88262da4cbc9a08046351ff6eec50fbe1d2c9cfe4f0bc00f672df07028723f63` |
| `ke_sampleflow.tex` | `4238de1d5446acde4252b60567ca880f7a451750012b3e2ffab142efea6cf0b6` |
| `ke_sumstats.tex` | `a47f225cb1b639fafd5784366f4ee375ce74f29935ec2c76163ebd437148865c` |
| `lib_attrition.tex` | `3447a3726bfd5cb2ba1bb961095d4f7773ed79ea082f165cea123e5666f5e872` |
| `lib_binscatter.pdf` | `8ca34c63135e5d1c05067bd092f601c5ecca4d5afd7fc13213953285bae63625` |
| `lib_bl_dist.pdf` | `1681948e3f0e1b99c651b011181861ac5b4e6fcfcf765d5e6c6b1f31dfe69f7e` |
| `lib_classsize.pdf` | `193f6b1fc35a001a1a463e2801514c45c1a4ccca49421f55230869f48f6cae9d` |
| `lib_dispersion_box.pdf` | `64dd459ac57e38eaa249adbcb6ab74531e7563b96a1f531ac236ab8e354e8aa3` |
| `lib_el_dist.pdf` | `2b421232a7c2756d2bb565bd9682998fb6a80e4d02ae3037cdfdfdff0ae7ef30` |
| `lib_sampleflow.tex` | `4431112b2a9e912455fab65eea14a1fc08f5986849e6a230ffcfbe393dd57cc6` |
| `lib_sumstats.tex` | `929dca56c297eac7571b7acfd0e1b07770fdfad5b8d325c058bcb17c51c46f92` |
| `tab_assignment_cutoffs.tex` | `b76852ced09d7d5ef59f332037e179ea0a1bb1e839b392ff752e3d9d86e119bb` |
| `tab_balance_1do.tex` | `93cd5109efb566c2e162dfe73e12b5add9e8f300ccac95009f525ab211924084` |
| `tab_ceiling.tex` | `43b29de5fda1c0f6f5c6461105507a269651ba2d4cb247124b0101576744bfdc` |
| `tab_classroom_reallocation.tex` | `04f94aeeb56e419d2291417a30d387ae277d5c893a9778c66543ad673f9a1001` |
| `tab_classsize_ctrl.tex` | `5f4333cf1e9d6715b86a13927c5ea71c79b5fc910cdd24b090ad3125d1f6bbbf` |
| `tab_cutoff_het.tex` | `a62a6db9bb008751aaad24f2a242caa4b2850fc8dd752246e587ec96f859fd7e` |
| `tab_density_decomp.tex` | `17d54601bc8e69dc841d138c8d06c8fdcfb986d6580d8d1d419b7145df556ea5` |
| `tab_dispersion_firststage.tex` | `5132bd1947cca4a62a27f4e574b035c99eb0ed65bc693dd9edcffee2cf005d13` |
| `tab_itt.tex` | `f902100ac681974ae47cfda3bed440a6a09e8c439a1bb99c8a796b36617cb07d` |
| `tab_lee_bounds.tex` | `37446141948593f5f5b3cd8b707bfbedffb2d123601c71907f4013d133a614af` |
| `tab_lesson_completion.tex` | `8e0f7a1b5bfdf39e524fe331215a9093603f0b491fdf4cdd9329096855377385` |
| `tab_peer_effects.tex` | `81cd881d6324b7e40ed65b7e0638d404478ca5dd81bbe3805f9e3128b8313dc9` |
| `tab_peer_effects_exact_kenya.tex` | `45c2b512b3f8c1e0621ce7e0920c2e45e83e9bf835bc8e426c3534392455dc9e` |
| `tab_score_variance.tex` | `aa84ca668a97f40e9a1ad5396fbe43b9d89d75c98c79717e4118bbef7a3e29be` |
| `tab_signal_quality.tex` | `3ba0511d39fbcb897af5b3fc705305083da9aa775bf08902c1a01981eac870f9` |
| `tab_signal_quality_alt.tex` | `0f6b2093dc2337609977c31d1779b2d2b59832da1dfbcef4a63bc01b6251056a` |
| `tab_spec_robust.tex` | `dd4bfa0488085fe59fad910ab646107b3dab4b4333fede7dacb6e71b1954456a` |
| `tab_suffstat_kenya.tex` | `c96f65601910941dd477eb5a2289def819b87f1e4d03da07228525846e838b20` |
| `tab_suffstat_liberia.tex` | `d40e8d6bfa5d511e63162dacf3fc369ba784810e95481bd910cc198b7e08584e` |
| `tab_track_bins.tex` | `a70fb522ba5857f75ea32fc659ec2cbc95a775c6d885d7595960742eb286d4df` |
| `tab_upper_lower.tex` | `0a668275d5c6e2e4379220777e86ce44f7b024109f10bd3989e8ed988aeb7ed9` |

## Reproduction commands

Use StataNow/StataMP 19.5 for Stata work:

```sh
'/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp' -b do \
  /Users/mriduljoshi/Github/AbilityGrouping/4_Stata2/_master.do
```

After any regeneration, inspect the Stata log before trusting output, then embed active figure fonts, sync,
and audit the Overleaf exhibits:

```sh
python3 4_Stata2/build_main2_tables.py

python3 4_Stata2/embed_active_figure_fonts.py

python3 4_Stata2/audit_overleaf_artifacts.py \
  --overleaf-dir '/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups revisited' \
  --entrypoint main2.tex \
  --repo-output-dir 4_Stata2/output \
  --check-labels

python3 4_Stata2/verify_freeze_manifest.py

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
```

Build the manuscript from a temp copy of the Overleaf folder, then copy back the
verified `main2.*` files only after the warning grep and artifact audit are
clean:

```sh
latexmk -g -pdf -interaction=nonstopmode -halt-on-error main2.tex

rg -n "(Warning|Undefined|Citation.*undefined|Reference.*undefined|There were undefined|Label.*multiply|Fatal|Emergency|Overfull|Underfull)" main2.log
```

## Remaining release-freeze items

- Decide whether to keep `\publicversionfalse` or flip to `\publicversiontrue`.
- Confirm coauthor/content approval for title, author footnotes, acknowledgments, and circulation status.
- Make a clean version-control commit or tag for the chosen final source.
- If any generated exhibit changes after this manifest, rerun the audit and update this file's hashes.
- Run `python3 4_Stata2/verify_freeze_manifest.py`, `python3 4_Stata2/check_numeric_claims.py`, `python3 4_Stata2/check_public_version.py`, and `python3 4_Stata2/check_release_readiness.py` immediately before circulation or tagging.
