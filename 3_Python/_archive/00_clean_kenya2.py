#!/usr/bin/env python3
"""
00_clean_kenya2.py — Build analysis dataset from Kenya 2019 Reading Club CSVs.

Kenya 2019 experiment: Grades 1-3, cross-grade ability grouping (Year 2).
Same schools as Kenya Year 1 (Grades 1-2). Year 2 adds Grade 3 and a new G1 cohort.
Three instructional levels (G1/G2/G3 curriculum).

Reading group assignment carried forward from Year 1:
  - Y2 G2 students (ex-Y1 G1): purple if Y1 composite > 40
  - Y2 G3 students (ex-Y1 G2): purple if Y1 composite > 35
  - Unmatched G2/G3: inferred from Y2 BL score
  - New Y2 G1: Y2 BL > 35 (~33% upper, matching Y1 G1 rate)

Baseline = T1 Baseline (single Supplementary Literacy score, MaxScore=49).
Endline  = T3 Endline  (single Supplementary Literacy score, MaxScore=48).
Treatment at academy level (~46 treatment, ~240 control), stratified by constituency.

Produces: output/analysis_kenya2.parquet
"""

import numpy as np
import pandas as pd
from config import get_config, OUT
from utils import (standardise_by_grade, leave_self_out_mean,
                   print_sample_log)

pd.set_option("display.max_columns", 40)
cfg = get_config("kenya2")

print("=" * 70)
print("00_clean_kenya2.py — Building Kenya 2019 analysis dataset")
print("=" * 70)


def load_score_file(path, grade):
    """Load a Kenya 2019 score CSV, extract key columns."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "AcademyCode": "academycode",
        "StudyID": "studyid",
        "Score": "score",
        "MaxScore": "maxscore",
        "TreatmentAssignment": "treatmentassignment",
        "Constituency1": "constituency",
        "County": "county",
        "DemographicLocation": "demographiclocation",
        "Academy_Cohort": "academy_cohort",
        "Enrolled_Date": "enrolled_date",
        "GradeName": "gradename",
        "Stream": "stream",
        "AssessmentStatus": "assessmentstatus",
    })
    df["grade"] = grade
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df.loc[df["score"] == -1, "score"] = np.nan
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 1. LOAD BASELINE (T1 Baseline — single Literacy score)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading baseline (T1 Baseline) ---")

bl_parts = []
for grade, bl_file in [(1, cfg["FILE_G1_BL"]),
                        (2, cfg["FILE_G2_BL"]),
                        (3, cfg["FILE_G3_BL"])]:
    raw = load_score_file(bl_file, grade)
    raw = raw.rename(columns={"score": "score_bl", "maxscore": "max_bl"})

    keep = ["academycode", "studyid", "grade", "score_bl", "max_bl",
            "treatmentassignment", "constituency", "county",
            "demographiclocation", "academy_cohort", "enrolled_date",
            "stream"]
    bl_parts.append(raw[keep])
    n_valid = raw["score_bl"].notna().sum()
    print(f"  Grade {grade}: {len(raw):,d} rows, {n_valid:,d} valid scores")

bl = pd.concat(bl_parts, ignore_index=True)
print(f"  Total baseline: {len(bl):,d} students, "
      f"{bl['academycode'].nunique()} academies")


# ═════════════════════════════════════════════════════════════════════════════
# 2. LOAD ENDLINE (T3 Endline — single Literacy score)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading endline (T3 Endline) ---")

el_parts = []
for grade, el_file in [(1, cfg["FILE_G1_EL"]),
                        (2, cfg["FILE_G2_EL"]),
                        (3, cfg["FILE_G3_EL"])]:
    raw = load_score_file(el_file, grade)
    raw = raw.rename(columns={"score": "score_el", "maxscore": "max_el"})
    keep = ["academycode", "studyid", "grade", "score_el", "max_el"]
    el_parts.append(raw[keep])
    n_valid = raw["score_el"].notna().sum()
    print(f"  Grade {grade}: {len(raw):,d} rows, {n_valid:,d} valid scores")

el = pd.concat(el_parts, ignore_index=True)
print(f"  Total endline: {len(el):,d} students")


# ═════════════════════════════════════════════════════════════════════════════
# 3. MERGE BL + EL
# ═════════════════════════════════════════════════════════════════════════════

df = bl.merge(el[["academycode", "studyid", "score_el", "max_el"]],
              on=["academycode", "studyid"], how="outer", indicator="_mel")

df["in_bl"] = df["_mel"] != "right_only"
df["in_el"] = df["_mel"] != "left_only"
df.drop(columns=["_mel"], inplace=True)
print(f"\nAfter BL-EL merge: {len(df):,d} rows")

df["treat"] = (df["treatmentassignment"] == "Treatment").astype(float)
df.loc[df["treatmentassignment"].isna(), "treat"] = np.nan

df["grade"] = df["grade"].fillna(
    df.merge(el[["academycode", "studyid", "grade"]],
             on=["academycode", "studyid"], how="left", suffixes=("", "_el"))
    .get("grade_el", pd.Series(dtype=float))
)

df["stream"] = df["stream"].str.strip()
df["constituency"] = df["constituency"].str.strip()
df["county"] = df["county"].str.strip()


# ═════════════════════════════════════════════════════════════════════════════
# 4. SAMPLE RESTRICTIONS
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Sample restriction log ---")
print_sample_log("Starting merged dataset", len(df))

df = df[df["grade"].isin([1, 2, 3])].copy()
print_sample_log("Valid grade (1-3)", len(df))

df = df[df["treat"].notna()].copy()
print_sample_log("Non-missing treatment", len(df))

df = df[~(df["stream"] == "B")].copy()
print_sample_log("Drop Stream B", len(df))

df["g12"] = (df["grade"].isin([1, 2])).astype(int)

df["ggroup"] = df.groupby("academycode").ngroup()

# Drop academies with only 1 grade present
grade_counts = df.groupby("academycode")["grade"].nunique()
single_grade_acads = grade_counts[grade_counts == 1].index
df = df[~df["academycode"].isin(single_grade_acads)].copy()
print_sample_log("Drop single-grade academies", len(df))

bl_by_acad = df.groupby("academycode")["score_bl"].transform(
    lambda x: x.notna().sum())
df = df[bl_by_acad > 0].copy()
print_sample_log("BL scores exist in academy", len(df))

dup_mask = df.duplicated(subset=["studyid"], keep=False)
dup_acad = df[dup_mask].groupby("studyid")["academycode"].nunique()
movers = dup_acad[dup_acad > 1].index
if len(movers) > 0:
    df = df[~df["studyid"].isin(movers)].copy()
    print_sample_log(f"Drop {len(movers)} students in multiple academies", len(df))

df["has_bl"] = df["score_bl"].notna()
df["has_el"] = df["score_el"].notna()

bl_counts = df.groupby("ggroup")["score_bl"].transform(
    lambda x: x.notna().sum())
df["finsamp"] = df["has_bl"] & (bl_counts > 1)
print_sample_log("Final sample (has BL, ≥2 BL in academy)", df["finsamp"].sum())
print_sample_log("  ... of whom have endline", (df["finsamp"] & df["has_el"]).sum())


# ═════════════════════════════════════════════════════════════════════════════
# 5. CONSTRUCT VARIABLES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Constructing variables ---")

df["strata"] = df.groupby("constituency").ngroup()

acad_treat = df.drop_duplicates("academycode")[["academycode", "treat", "strata"]]
strata_pt = acad_treat.groupby("strata")["treat"].mean()
df["P_t"] = df["strata"].map(strata_pt)
df["P_c"] = 1 - df["P_t"]
print(f"  Propensity (P_t): mean={df['P_t'].mean():.3f}, "
      f"range=[{df['P_t'].min():.3f}, {df['P_t'].max():.3f}]")

# ── Upper group: carry forward Year 1 reading group assignment ───────────
# Load Y1 composite BL scores and construct purple assignment
print("\n  Loading Year 1 data for reading-group carryover...")
y1_cutoffs = cfg["Y1_CUTOFFS"]
y1_assignments = []
for y1_grade, cutoff in y1_cutoffs.items():
    lit = pd.read_csv(cfg[f"Y1_G{y1_grade}_BL_LIT"])
    eng = pd.read_csv(cfg[f"Y1_G{y1_grade}_BL_ENG"])
    lit["Score"] = pd.to_numeric(lit["Score"], errors="coerce")
    eng["Score"] = pd.to_numeric(eng["Score"], errors="coerce")
    m = lit[["StudyID", "Score"]].rename(columns={"Score": "lit"}).merge(
        eng[["StudyID", "Score"]].rename(columns={"Score": "eng"}),
        on="StudyID", how="outer")
    m["comp_y1"] = m["lit"] + m["eng"]  # NaN if either subject missing
    m["purple_y1"] = np.where(m["comp_y1"].notna(),
                              (m["comp_y1"] > cutoff).astype(int), np.nan)
    m["grade_y1"] = y1_grade
    y1_assignments.append(m[["StudyID", "purple_y1", "grade_y1"]])

y1_assign = pd.concat(y1_assignments, ignore_index=True)
y1_assign = y1_assign.rename(columns={"StudyID": "studyid"})
print(f"    Y1 students loaded: {len(y1_assign)}")
for g in y1_cutoffs:
    sub = y1_assign[y1_assign["grade_y1"] == g]
    print(f"    Y1 G{g}: {len(sub)}, purple={sub['purple_y1'].sum()} "
          f"({sub['purple_y1'].mean():.0%}), cutoff=comp>{y1_cutoffs[g]}")

# Match Y2 students to Y1 via StudyID
df = df.merge(y1_assign[["studyid", "purple_y1", "grade_y1"]],
              on="studyid", how="left")

n_matched = df["purple_y1"].notna().sum()
print(f"\n  Y2→Y1 match: {n_matched}/{len(df)} students ({n_matched/len(df):.0%})")
for g2 in [1, 2, 3]:
    sub = df[df["grade"] == g2]
    matched = sub["purple_y1"].notna().sum()
    print(f"    Y2 G{g2}: {matched}/{len(sub)} matched ({matched/len(sub):.0%})")

# Assign upper_group:
#   Matched G2/G3: use Y1 purple directly
#   Unmatched G2: infer from Y2 BL > 45 (best-separating cutoff, ~66% acc)
#   Unmatched G3: infer from Y2 BL > 41 (best-separating cutoff, ~64% acc)
#   New G1: Y2 BL > 35 (matches Y1 G1 ~33% upper rate)
FALLBACK_CUTOFFS = {1: 35, 2: 45, 3: 41}

df["upper_group"] = np.nan
n_from_y1, n_from_bl, n_missing = 0, 0, 0

# Vectorised assignment
matched_mask = df["purple_y1"].notna()
df.loc[matched_mask, "upper_group"] = df.loc[matched_mask, "purple_y1"]
n_from_y1 = matched_mask.sum()

for g2, bl_cut in FALLBACK_CUTOFFS.items():
    unmatched = (df["grade"] == g2) & df["purple_y1"].isna() & df["score_bl"].notna()
    df.loc[unmatched, "upper_group"] = (df.loc[unmatched, "score_bl"] > bl_cut).astype(float)
    n_from_bl += unmatched.sum()

still_missing = df["upper_group"].isna() & df["treat"].notna()
df.loc[still_missing, "upper_group"] = 0.0
n_missing = still_missing.sum()

print(f"\n  upper_group assignment:")
print(f"    From Y1 carryover:  {n_from_y1:,d}")
print(f"    From Y2 BL cutoff:  {n_from_bl:,d}")
print(f"    Missing BL (→ 0):   {n_missing:,d}")
for g2 in [1, 2, 3]:
    sub = df[(df["grade"] == g2) & df["upper_group"].notna()]
    frac = sub["upper_group"].mean() if len(sub) > 0 else 0
    print(f"    G{g2}: {frac:.0%} upper (N={len(sub)})")

# ── 3 instructional levels (G1/G2/G3 curriculum) ────────────────────────
# Year 2 has 3 reading groups. Year 1 binary assignment maps as follows:
#   Level 1 (G1 curriculum): new G1 students who are lower
#   Level 2 (G2 curriculum): new G1 upper + all returning ex-Y1 lower
#   Level 3 (G3 curriculum): all returning ex-Y1 upper
# Returning students move up one level from their Y1 assignment.
is_new = df["purple_y1"].isna()  # no Y1 match → new student (almost all G1)
is_returning_lower = df["purple_y1"].notna() & (df["upper_group"] == 0)
is_returning_upper = df["purple_y1"].notna() & (df["upper_group"] == 1)
is_new_lower = is_new & (df["upper_group"] == 0)
is_new_upper = is_new & (df["upper_group"] == 1)

df["std_grp"] = np.nan
df.loc[is_new_lower, "std_grp"] = 1       # Level 1: new G1 lower
df.loc[is_new_upper, "std_grp"] = 2       # Level 2: new G1 upper
df.loc[is_returning_lower, "std_grp"] = 2  # Level 2: ex-Y1 lower (moved up)
df.loc[is_returning_upper, "std_grp"] = 3  # Level 3: ex-Y1 upper (moved up)

# For unmatched G2/G3 whose upper_group was inferred from BL:
# they're likely returning students (73-75% match rate), so treat inferred
# lower as Level 2 and inferred upper as Level 3
for g2 in [2, 3]:
    inferred_lower = is_new & (df["grade"] == g2) & (df["upper_group"] == 0)
    inferred_upper = is_new & (df["grade"] == g2) & (df["upper_group"] == 1)
    df.loc[inferred_lower, "std_grp"] = 2
    df.loc[inferred_upper, "std_grp"] = 3

# Fill any remaining NaN (students with missing BL and no Y1 match)
df.loc[df["std_grp"].isna() & df["treat"].notna(), "std_grp"] = 1

# matched_grp: True if group assignment is known (Y1 carryover or new G1)
# False for unmatched G2/G3 whose assignment was inferred from Y2 BL (~65% acc)
df["matched_grp"] = True
unmatched_g23 = df["purple_y1"].isna() & df["grade"].isin([2, 3])
df.loc[unmatched_g23, "matched_grp"] = False

n_matched_grp = df["matched_grp"].sum()
n_inferred = (~df["matched_grp"]).sum()
print(f"\n  Group assignment quality:")
print(f"    Known (Y1 match or new G1):  {n_matched_grp:,d}")
print(f"    Inferred (unmatched G2/G3):  {n_inferred:,d}")

for lev in [1, 2, 3]:
    n_lev = (df["std_grp"] == lev).sum()
    grade_dist = df.loc[df["std_grp"] == lev, "grade"].value_counts().sort_index()
    gd_str = ", ".join(f"G{int(g)}={n}" for g, n in grade_dist.items())
    print(f"  Level {lev}: N={n_lev:,d}  ({gd_str})")

df.drop(columns=["purple_y1", "grade_y1"], inplace=True)

# Effective cutoffs for dist_from_cutoff (approximate, for downstream use)
cutoffs = FALLBACK_CUTOFFS

ctrl = df["treat"] == 0
df["std_score_bl"] = standardise_by_grade(df, "score_bl", ctrl)
df["std_score_el"] = standardise_by_grade(df, "score_el", ctrl)
print("  Standardised BL/EL scores")

# Reliability r² = R²(BL→EL) in control, by grade
r2_by_grade = {}
for g in [1, 2, 3]:
    mask = ctrl & (df["grade"] == g) & df["score_bl"].notna() & df["score_el"].notna()
    if mask.sum() > 10:
        r2_by_grade[g] = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
    else:
        r2_by_grade[g] = 0.05
print("  Diagnostic reliability r² = R²(BL→EL) by grade: "
      + ", ".join(f"G{g}={v:.4f}" for g, v in sorted(r2_by_grade.items())))

df["eb_ability"] = np.nan
for g in [1, 2, 3]:
    r2 = max(r2_by_grade.get(g, 0.05), 0.01)
    g_ctrl = ctrl & (df["grade"] == g)
    mu_g = df.loc[g_ctrl, "score_bl"].mean()
    has_bl = (df["grade"] == g) & df["score_bl"].notna()
    no_bl = (df["grade"] == g) & df["score_bl"].isna()
    df.loc[has_bl, "eb_ability"] = mu_g + r2 * (df.loc[has_bl, "score_bl"] - mu_g)
    df.loc[no_bl, "eb_ability"] = mu_g

df["std_eb"] = standardise_by_grade(df, "eb_ability", ctrl)
print("  Empirical Bayes predicted ability constructed")

df["exp0"] = 1
df["exp1"] = 0
df["exp2"] = (df["grade"].isin([1, 2])).astype(int)
for g in [1, 2, 3]:
    df[f"g{g}"] = (df["grade"] == g).astype(int)
df["g4"] = 0


# ═════════════════════════════════════════════════════════════════════════════
# 6. PEER VARIABLES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Computing peer variables ---")

df["peer_bl_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_score_bl")
df["peer_bl_ctrl"]  = leave_self_out_mean(df, ["academycode", "grade"],   "std_score_bl")

df["peer_eb_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_eb")
df["peer_eb_ctrl"]  = leave_self_out_mean(df, ["academycode", "grade"],   "std_eb")

df["exp_peer_bl"] = df["P_t"] * df["peer_bl_treat"] + df["P_c"] * df["peer_bl_ctrl"]
df["exp_peer_eb"] = df["P_t"] * df["peer_eb_treat"] + df["P_c"] * df["peer_eb_ctrl"]

df["peer_bl"] = np.where(df["treat"] == 1, df["peer_bl_treat"], df["peer_bl_ctrl"])
df["peer_eb"] = np.where(df["treat"] == 1, df["peer_eb_treat"], df["peer_eb_ctrl"])
print("  Peer means computed")

for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    med = df.groupby(["academycode", grp_type])["std_eb"].transform("median")
    df[f"dist_med_{suffix}"] = (df["std_eb"] - med).abs()

df["exp_dist_med"] = df["P_t"] * df["dist_med_treat"] + df["P_c"] * df["dist_med_ctrl"]
df["dist_med"] = np.where(df["treat"] == 1, df["dist_med_treat"], df["dist_med_ctrl"])

for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_score_el"].transform("mean")
    df[f"dev_el_{suffix}"] = (df["std_score_el"] - mn).abs()
df["dev_el"] = np.where(df["treat"] == 1, df["dev_el_treat"], df["dev_el_ctrl"])

for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_eb"].transform("mean")
    df[f"dev_eb_{suffix}"] = (df["std_eb"] - mn).abs()
df["dev_eb"] = np.where(df["treat"] == 1, df["dev_eb_treat"], df["dev_eb_ctrl"])
df["exp_dev_eb"] = df["P_t"] * df["dev_eb_treat"] + df["P_c"] * df["dev_eb_ctrl"]
print("  Distance and dispersion variables computed")

for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    df[f"csize_{suffix}"] = df.groupby(
        ["academycode", grp_type])["studyid"].transform("count")
df["exp_csize"] = df["P_t"] * df["csize_treat"] + df["P_c"] * df["csize_ctrl"]
df["csize"] = np.where(df["treat"] == 1, df["csize_treat"], df["csize_ctrl"])
print("  Class sizes computed")

df["bl_decile"] = np.nan
for g in [1, 2, 3]:
    mask = (df["grade"] == g) & df["score_bl"].notna()
    if mask.sum() > 10:
        df.loc[mask, "bl_decile"] = pd.qcut(
            df.loc[mask, "score_bl"], q=10, labels=False, duplicates="drop") + 1

has_bl = df["score_bl"].notna()
eb_for_mean = df["std_eb"].where(has_bl)
class_mean_treat = df.assign(_eb=eb_for_mean).groupby(
    ["academycode", "std_grp"])["_eb"].transform("mean")
class_mean_ctrl = df.assign(_eb=eb_for_mean).groupby(
    ["academycode", "grade"])["_eb"].transform("mean")
df["class_mean_eb"] = np.where(df["treat"] == 1, class_mean_treat, class_mean_ctrl)
df["misfit"] = (df["std_eb"] - df["class_mean_eb"]) ** 2

df["dist_from_cutoff"] = np.nan
for g, cutoff in cutoffs.items():
    mask = (df["grade"] == g) & df["score_bl"].notna()
    df.loc[mask, "dist_from_cutoff"] = (df.loc[mask, "score_bl"] - cutoff).abs()
print("  Baseline deciles, misfit, distance-from-cutoff computed")


# ═════════════════════════════════════════════════════════════════════════════
# 7. SAVE
# ═════════════════════════════════════════════════════════════════════════════

df["score_ml"] = np.nan
df["std_score_ml"] = np.nan
df["maxscore_ml"] = np.nan
df["maxscore_el"] = np.nan
df["in_ml"] = False
df["acad_year"] = np.nan
df["pupilattendance"] = np.nan
df["lp_comp"] = np.nan
df["lp_opened"] = np.nan
df["tch_attn"] = np.nan

keep_cols = [
    "academycode", "studyid", "grade", "stream", "county", "constituency",
    "ggroup", "strata", "acad_year", "g12",
    "treat", "P_t", "P_c",
    "upper_group", "std_grp",
    "score_bl", "score_ml", "score_el",
    "maxscore_ml", "maxscore_el",
    "std_score_bl", "std_score_ml", "std_score_el",
    "eb_ability", "std_eb",
    "peer_bl", "peer_bl_treat", "peer_bl_ctrl", "exp_peer_bl",
    "peer_eb", "peer_eb_treat", "peer_eb_ctrl", "exp_peer_eb",
    "dist_med", "dist_med_treat", "dist_med_ctrl", "exp_dist_med",
    "dev_el", "dev_el_treat", "dev_el_ctrl",
    "dev_eb", "dev_eb_treat", "dev_eb_ctrl", "exp_dev_eb",
    "bl_decile", "class_mean_eb", "misfit", "dist_from_cutoff",
    "csize", "csize_treat", "csize_ctrl", "exp_csize",
    "pupilattendance", "lp_comp", "lp_opened", "tch_attn",
    "exp0", "exp1", "exp2", "g1", "g2", "g3", "g4",
    "has_bl", "has_el", "finsamp", "matched_grp", "in_bl", "in_ml", "in_el",
]
keep_cols = [c for c in keep_cols if c in df.columns]
df = df[keep_cols].copy()

df.to_parquet(cfg["ANALYSIS_FILE"], index=False)
print(f"\n✓ Kenya 2019 dataset saved to {cfg['ANALYSIS_FILE']}")
print(f"  {len(df):,d} rows, {len(df.columns)} columns")
print(f"  Final sample (finsamp): {df['finsamp'].sum():,d}")
print(f"  Final sample with endline: {(df['finsamp'] & df['has_el']).sum():,d}")

print("\n--- Quick summary ---")
print(df.groupby(["grade", "treat"]).agg(
    n=("studyid", "count"),
    n_finsamp=("finsamp", "sum"),
    mean_bl=("score_bl", "mean"),
    mean_el=("score_el", "mean"),
    pct_has_el=("has_el", "mean"),
).round(3).to_string())
