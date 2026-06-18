# Nigeria Ability Grouping Analysis — Handover Note

## What this is

A randomized evaluation of cross-grade ability grouping in NewGlobe academies in Lagos, Nigeria. Students in Grades 1–3 were sorted into three numeracy tracks (Red = bottom, Blue = middle, Yellow = top) based on a placement test. Treatment randomized at the academy level (~30 academies). Follow-up assessments at four time points: T2 midterm, T2 endterm, T3 midterm, T3 endterm — spanning roughly two academic terms.

This experiment is being developed as a standalone paper, separate from a companion paper on two earlier ability grouping experiments (Kenya and Liberia) by the same school operator.

## Key files

### Data cleaning
- `4_Stata2/00_clean_nigeria.do` — builds the analysis dataset from raw data
  - Inputs: `2_Data/2_Cleaned/Nigeria/ng_assessments_student_long.dta`, placement spreadsheet, IRT scores
  - Outputs: `4_Stata2/output/analysis_nigeria_wide.dta` (one row per student), `analysis_nigeria_attrition_long.dta`
  - Creates: `bl_score` (T1 end-of-term maths — **NOT** the placement test; see below), z-scored outcomes, `group_id` (1=Red, 2=Blue, 3=Yellow), counterfactual groups for control students (baseline terciles within grade)

### Main analysis
- `4_Stata2/02_nigeria_main_analysis.do` — generates all 33 LaTeX tables
  - Master runner: `4_Stata2/_master_nigeria.do`
  - Output directory: `4_Stata2/output/tab_ng_*.tex`
  - Also copies to the repo-local paper input folder: `stata_output/`

### LaTeX
- Legacy standalone file: `archive/legacy_root_entrypoints_2026-06-07_ability_migration/main_nigeria.tex`
  - Nigeria is now integrated into the active three-country manuscript at `main_3country_new.tex`.
  - The `reading-groups-struc` repository is linked directly to Overleaf.

### Companion paper (Kenya + Liberia)
- `4_Stata2/02_main_analysis.do` — Kenya/Liberia main tables
- `4_Stata2/04_structural.do` — structural model, peer effects, diagnostics
- Legacy manuscript: `archive/legacy_root_entrypoints_2026-06-07_ability_migration/main2.tex`

### Raw experimental documentation
- `2_Data/newglobe-lagos-numeracygroups.pdf` — NewGlobe's presentation on the Nigeria intervention

### Implementation fidelity audit
- `2_Data/1_Raw/P123 Numeracy Groups/Phone Call Auditing Form_ Lagos Numeracy Groups, 2020.xlsx` — 61 phone-call audits of treated and control schools. **Read this.** It reveals that many schools didn't form three groups as designed.

### Placement data
- `2_Data/1_Raw/P123 Numeracy Groups/[Data Entry] Numeracy Groups Placement - 2020-2021.xlsx` — group assignments (Red/Blue/Yellow) by student. Contains treatment status, academy, grade, group label. **Does NOT contain the placement test score.**
- The placement test score (`PlacementExamScore`) lives on the **roster file** (`Roster of Pupils (P123 T2).xlsx`), read by the Python pipeline (`3_Python/00_clean_nigeria.py`, line 127). A standardized version (`placement_score_z`) is available in `2_Data/2_Cleaned/Nigeria/ng_t3_ete_numeracy_irt_student.csv`. **This score is NOT currently used in the Stata analysis.**

## CRITICAL: The Placement Test Problem

### What we discovered

The intervention was supposed to assign students to Red/Blue/Yellow groups based on a purpose-built placement test. We investigated whether the data support this.

### Three candidate "baseline" scores

| Score | What it is | Corr with placement_score_z | Predicts group? |
|-------|-----------|---------------------------|-----------------|
| `bl_score` (T1 ETE maths) | Term 1 end-of-term maths exam | r = 0.02 | No — Yellow has **lowest** mean |
| `percscoret2_mte_numeracy` | Term 2 midterm numeracy | r = 0.06 | No — means identical across groups |
| `placement_score_z` | The actual placement exam from roster | — | Weakly — rho = 0.17, correct ordering |

### The placement score barely predicts groups

- **Spearman rho = 0.17** between `placement_score_z` and group assignment (treated students, N=952)
- Means are in the right order (Red = -0.11, Blue = +0.06, Yellow = +0.51) but ranges overlap completely
- **With academy-grade fixed effects** (the correct specification, since assignment was within school-grade): **b = 0.019, p = 0.23, F = 1.56**. The first stage disappears.
- The multinomial logit shows placement score predicts Yellow vs Red (coeff = 0.56, p = 0.001) but NOT Blue vs Red (coeff = 0.11, p = 0.19)
- **0 out of 39** academy-grade cells show clean score-based separation between groups

### Why: the audit data explains it

The phone call auditing form (`Phone Call Auditing Form_ Lagos Numeracy Groups, 2020.xlsx`) reveals:

- **"There is no Yellow group. The red group is divided into two. Red group 1 and Red group 2."**
- **"All pupils are in the RED group."**
- **"There are 2 Red groups and 1 Blue group..."** (many schools)
- **"P2 Teacher teaches Blue lesson instead of Red..."** (wrong lesson for group)
- **"Grouping has only happened once..."**

Most schools, especially in Primary 1, put nearly all students into Red. The placement test existed but was not binding — academy managers exercised heavy discretion. The heatmap in the intervention presentation (`newglobe-lagos-numeracygroups.pdf`, slide 3) confirms: P1 is almost entirely Red; differentiation only emerges in P2/P3.

### Group composition reflects this

| Group | N (treated) | % of treated with group |
|-------|-------------|------------------------|
| Red | 696 | 61% |
| Blue | 278 | 24% |
| Yellow | 168 | 15% |
| Missing | 600 | — |

Red has 4x as many students as Yellow. This is not tercile-based assignment.

### Implications for the analysis

1. **`bl_score` is fine as a regression covariate** — it's a pre-treatment assessment. Its near-zero correlation with the placement test means it's independent of the (noisy) assignment mechanism, which is actually clean for OLS.
2. **The counterfactual group assignment for control students** (currently based on `bl_score` terciles) doesn't approximate the actual assignment mechanism, since the placement test is a different instrument. This weakens the interaction analysis.
3. **No RDD is possible** — there are no sharp or fuzzy cutoffs to exploit.
4. **The "first stage" of ability grouping is weak** — the intervention barely achieved differentiation in P1 (the largest grade). This should be front and center in the paper.
5. **The implementers called this "solid"** — they defined fidelity as "the program runs daily and detects variation in later grades," not "groups are sharply differentiated by ability." From a research perspective, the treatment intensity is low.

### Cronbach's alpha

The T3 ETE numeracy assessment (50 binary items, item-level data in `2_Data/2_Cleaned/Nigeria/ng_itemlevel_t3_ete_numeracy.dta`) has alpha = **0.91** (full sample, N=2,522) and 0.91 (control only, N=1,315). This indicates excellent internal consistency of the outcome measure.

## The 33 Nigeria tables

### Data and Sample (Tables 1–4)
1. `tab_ng_sumstats` — summary statistics
2. `tab_ng_sampleflow` — sample construction
3. `tab_ng_balance` — covariate balance
4. `tab_ng_attrition` — attrition rates by wave

### Main Results (Tables 5–9)
5. `tab_ng_t2_mte` — T2 midterm ITT (math, numeracy, index)
6. `tab_ng_t2_ete` — T2 endterm ITT (math, numeracy, index) — **best average ITT: +0.146\* on index**
7. `tab_ng_t3_mte` — T3 midterm ITT
8. `tab_ng_t3_ete` — T3 endterm ITT — **effect fades to +0.105 (n.s.)**
9. `tab_ng_upper_lower` — upper (Yellow) vs lower track interaction

### Signal Quality and Classroom Reallocation (Tables 10–12)
10. `tab_ng_signal_quality` — **incremental R² = 0.11–0.22; rank persistence = 0.38–0.49**
11. `tab_ng_classroom_reallocation` — class size drops by 3; grade mixing increases to 2.6 grades/class
12. `tab_ng_dispersion` — within-class dispersion slightly *increases* (+0.104\*) because grade mixing dominates

### Treatment Effect Heterogeneity (Table 13)
13. `tab_ng_track_bins` — within-group ability tercile effects (T3 ETE)

### Mechanisms (Tables 14–16)
14. `tab_ng_peer_effects` — BH peer effects: -0.109 (n.s.) at T3 ETE
15. `tab_ng_suffstat` — accounting decomposition: peer contribution +0.026, remainder +0.079
16. `tab_ng_density_decomp` — peer effects by score density tercile

### Robustness (Tables 17–21)
17. `tab_ng_spec_robust` — alternative specs, wild bootstrap, permutation
18. `tab_ng_classsize_ctrl` — class-size controls don't change results
19. `tab_ng_ceiling` — Tobit and trimmed OLS
20. `tab_ng_score_variance` — within/between variance decomposition
21. `tab_ng_lee_bounds` — Lee bounds for attrition

### Over-Time Specifications (Tables 22–24)
22. `tab_ng_over_terms` — pooled MTE+ETE panel (all 4 waves)
23. `tab_ng_t2_over_time` — pooled T2 panel (MTE+ETE)
24. `tab_ng_t3_over_time` — pooled T3 panel (MTE+ETE)

### IRT Outcomes (Table 25)
25. `tab_ng_irt` — IRT-scored T3 ETE numeracy

### Group-Color Interactions (Tables 26–33) — **THE KEY TABLES**
26. `tab_ng_t2_mte_interact` — T2 MTE by Red/Blue/Yellow
27. `tab_ng_t2_ete_interact` — T2 ETE by Red/Blue/Yellow
28. `tab_ng_t3_mte_interact` — T3 MTE by Red/Blue/Yellow
29. `tab_ng_t3_ete_interact` — T3 ETE by Red/Blue/Yellow
30. `tab_ng_over_terms_interact` — **pooled all waves by group: Yellow +0.225, Red +0.077, Blue +0.037**
31. `tab_ng_t2_over_time_interact` — pooled T2 by group
32. `tab_ng_t3_over_time_interact` — pooled T3 by group
33. `tab_ng_irt_interact` — IRT by group

## The central results

### Group-specific effects (pooled across all 4 waves, index outcome, SEs clustered at academy):
- **Yellow (top track): +0.225 (0.141)** — large and positive, but imprecise with academy-level clustering (p ≈ 0.11)
- **Red (bottom track): +0.077 (0.091)** — weak positive, driven by numeracy not math
- **Blue (middle track): +0.037 (0.109)** — null
- Yellow T2 pooled math: +0.339** (0.144) — this is the strongest single result

### Yellow group effects by wave (math + numeracy index):
| Wave | Effect | SE |
|------|--------|----|
| T2 MTE | +0.181 | 0.140 |
| T2 ETE | +0.252\* | 0.141 |
| T3 MTE | +0.200 | 0.197 |
| T3 ETE | +0.247 | 0.244 |
| Pooled | +0.225 | 0.141 |

The Yellow effect is positive in every wave, but with correct academy-level clustering the estimates are imprecise. The apparent "fade" in the average ITT may reflect averaging across groups with different trajectories, but the T3 Lee bounds and group-specific standard errors mean this should be framed as suggestive rather than definitive. Only the T2 pooled Yellow math effect (0.339**, SE 0.144) clears 5% significance.

### Signal quality:
- Incremental R² (baseline → follow-up, beyond grade FE): 0.22 at T2, 0.11 at T3
- Rank persistence: 0.47–0.49 at T2, 0.38–0.39 at T3
- For comparison: Kenya = 0.52, Liberia = 0.05

### Classroom reallocation:
- Class size: 30.2 (control) → 27.2 (treatment) — shrinks by 3
- Grades per class: 1.0 → 2.6 — substantial grade mixing
- Within-class baseline SD: 0.69 → 0.81 — dispersion increases (grade mixing > ability sorting)
- Peer mean shift: -0.24 SD (treatment students face lower-ability peers on average)

## What we think the standalone paper is about

**When does ability grouping actually differentiate?**

The core finding is not about average treatment effects. It's about whether the intervention achieved its goal of creating differentiated classroom environments, and what happens when it does vs when it doesn't.

In Primary 1, ability grouping failed to differentiate: virtually all students were placed in Red, because 6-year-olds don't vary enough in numeracy for a placement test to separate them. The treatment was a relabeling exercise — the "first stage" of grouping was near zero.

In Primary 2 and especially Primary 3, some differentiation occurred, with Blue and Yellow groups forming. The Yellow group — the only group genuinely pulled out of the default grade-level classroom — has positive point estimates across all four assessment waves, but those estimates are imprecise under academy-level clustering.

This reframes the null average ITT. It's not that "ability grouping doesn't work." It's that ability grouping may require real differentiation before effects are detectable. For two-thirds of the sample (P1 + Red in P2/P3), the intervention barely changed the classroom environment. For the Yellow students who were genuinely recomposed into a distinct group, the estimates are consistently positive but not definitive.

### Connection to Kenya/Liberia companion paper
Kenya had sharp cutoffs and a strong first stage, but weak average effects in the current companion-paper estimates. Nigeria had noisy, discretionary assignment and weak average effects. This keeps the assignment-quality margin central, but it also means the cross-country story should not claim a simple monotone relationship between sorting quality and average achievement. The placement test problem (not binding, heavily overridden by teachers) is a key Nigeria mechanism. The intervention presentation explicitly noted they designed a "better placement test" for Nigeria, but the test was not the only bottleneck — compliance with test-based assignment and track-specific delivery also mattered.

## Design and specification details

- **Treatment**: Academy-level randomization (~30 academies)
- **Groups**: Red (bottom) / Blue (middle) / Yellow (top) — nominally based on placement test, but in practice heavily discretionary
- **Outcomes**: z-scored (control mean 0, SD 1) percent-correct scores in math and numeracy, plus an index (rowmean of the two z-scores)
- **Specification**: OLS with baseline score control, constituency FE, grade FE, SEs clustered at academy
- **Interactions**: `treat × group_id` with Red as base; reported effects are the total effect for each group (not the differential)
- **Panel**: Pooled OLS on stacked student-wave observations with wave FE, clustered at academy level
- **Peer effects**: Borusyak-Hull with baseline-decile × treatment × grade FE, leave-out peer mean of standardized baseline score

## Known issues and caveats

1. **Power**: ~30 clusters is thin. MDE is roughly 0.20+ SD for the average effect. Group-specific estimates are less powered in cross-section but the pooled panel specs gain precision.
2. **Multiple testing**: 3 groups × 4 waves × 3 outcomes = 36 cells. The Yellow pattern is economically meaningful but imprecise under academy-level clustering, and individual wave × group cells should be interpreted cautiously.
3. **Dispersion increases**: Unlike Kenya (where grouping compressed dispersion), Nigeria's 3-track system increases within-class dispersion because grade mixing dominates. The "first stage" looks different from what the theory predicts for successful sorting.
4. **Subject domain**: This is numeracy, not reading. Kenya and Liberia were reading experiments. Comparisons across the two papers should note this.
5. **Control group also grouped**: The placement file shows control students with Red/Blue/Yellow labels. The intervention PDF says "control group also targeted — all kids learn." Both arms did some form of grouping. The treatment contrast is about the precision and intensity of grouping, not grouping vs no grouping.
6. **Baseline instrument mismatch**: `bl_score` (T1 ETE maths) is essentially uncorrelated with the actual placement test (r = 0.02). It's fine as a regression covariate but does not capture the assignment mechanism. The counterfactual groups for control students (bl_score terciles) don't approximate the actual placement process.
7. **Cronbach's alpha**: T3 ETE numeracy instrument alpha = 0.91 (excellent). Only available for this one assessment wave (item-level data).

## What to look at critically

1. **The placement test problem is the central issue.** The intervention was designed around a placement test, but the test wasn't binding. Read the audit form — it's the most informative single file for understanding why the results look the way they do.

2. **Is the Yellow effect real or a statistical artifact?** It's stable across 4 waves and significant in some specs, but the correctly-clustered SEs are large. With 168 Yellow students across ~19 schools, the effective sample is thin. Look at the track bins table (Table 13) for within-Yellow heterogeneity.

3. **Why does Blue gain nothing?** If the middle group was also differentiated, they should benefit. The audit data suggests Blue was often not a distinct group — many schools had "2 Red groups and 1 Blue group" with the Red/Blue distinction being arbitrary.

4. **The apparent "no fade" pattern for Yellow**: The average ITT fades from T2 to T3, while Yellow's point estimates remain positive. Is this a real persistent top-track effect, or does it reflect T3 sample selection and differential attrition by group?

5. **Control contamination**: Both arms did grouping. The treatment effect is the *incremental* benefit of the treated arm's version. If control schools also achieved some differentiation, the effect is downward biased relative to a pure no-grouping counterfactual.

6. **Does the peer effects analysis make sense for Nigeria?** The BH strategy requires within-cell variation in peer composition. With ~30 academies and 3 groups, the cells (decile × treatment × grade) may be very thin.

7. **Read the intervention documentation** (`2_Data/newglobe-lagos-numeracygroups.pdf`) to understand exactly what instruction each group received. If Yellow got a qualitatively different or more advanced curriculum, that's a confound — the effect would be curriculum, not grouping.

8. **Consider whether `placement_score_z` should replace or supplement `bl_score`** in some analyses — for instance, signal quality should arguably be measured against the actual placement instrument, not the T1 maths exam.
