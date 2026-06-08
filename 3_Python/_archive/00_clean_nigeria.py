#!/usr/bin/env python3
"""
00_clean_nigeria.py — Build analysis dataset from Lagos P123 Numeracy Groups RCT.

Lagos, Nigeria (Jan–Jul 2021). P1-P3 students across 20 RCT academies (10 T, 10 C).
Treatment: cross-grade ability grouping for numeracy (Red/Blue/Yellow groups).
Baseline: T1 ETE Maths (Dec 2020).
Endline:  T3 ETE Numeracy (Jul 2021, same 50-item test for T and C).

CRITICAL: The Treatment variable in assessment files encodes RCT membership (1=in study),
NOT treatment/control. Actual treatment comes from the placement file.

Produces: output/analysis_nigeria.parquet
"""

import numpy as np
import pandas as pd
from config import get_config, OUT
from utils import (standardise_by_grade, leave_self_out_mean,
                   print_sample_log)

pd.set_option("display.max_columns", 40)
cfg = get_config("nigeria")

print("=" * 70)
print("00_clean_nigeria.py — Building Nigeria (Lagos) analysis dataset")
print("=" * 70)


def extract_grade(gradename_series):
    return (
        gradename_series.astype(str)
        .str.extract(r"(\d)", expand=False)
        .astype(float)
    )


# ═════════════════════════════════════════════════════════════════════════════
# 1. LOAD PLACEMENT FILE (authoritative source for treatment assignment)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading placement file (treatment truth) ---")
pl = pd.read_excel(cfg["FILE_PLACEMENT"])
pl = pl.drop_duplicates(subset=["AcademyCode", "StudyID"])
pl = pl.rename(columns={"AcademyCode": "academycode", "StudyID": "studyid",
                         "Treatment": "treat", "Grade": "grade_pl",
                         "Group": "group_raw"})

# Clean group labels: Red 1, Red 2 → Red; Blue, Blue 3 → Blue
pl["group"] = (pl["group_raw"]
               .str.replace(r"\s*\d+", "", regex=True)
               .str.strip())

rct_academies = set(pl["academycode"].unique())
treat_map = pl.drop_duplicates("academycode")[["academycode", "treat"]]
n_t = (treat_map["treat"] == 1).sum()
n_c = (treat_map["treat"] == 0).sum()
print(f"  RCT academies: {len(rct_academies)} ({n_t} treatment, {n_c} control)")
print(f"  Placement students: {len(pl):,d}")
print(f"  Groups: {pl['group'].value_counts().to_dict()}")


# ═════════════════════════════════════════════════════════════════════════════
# 2. LOAD ASSESSMENT DATA
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading assessment files ---")

# 2a. Baseline: T1 ETE Maths (Dec 2020, pre-intervention)
bl = pd.read_excel(cfg["FILE_BL"])
bl.columns = bl.columns.str.strip()
bl = bl.rename(columns={"AcademyCode": "academycode", "StudyID": "studyid",
                         "Score": "score_bl", "MaxScore": "maxscore_bl",
                         "GradeName": "gradename", "Constituency1": "constituency",
                         "County": "county", "Stream": "stream",
                         "Enrolled_Date": "enrolled_date"})
bl["grade"] = extract_grade(bl["gradename"])
bl["score_bl"] = pd.to_numeric(bl["score_bl"], errors="coerce")
bl = bl[bl["academycode"].isin(rct_academies)].copy()
print(f"  Baseline (T1 ETE Maths): {len(bl):,d} rows, "
      f"{bl['academycode'].nunique()} academies, "
      f"{bl['score_bl'].notna().sum():,d} scored")

# 2b. Endline: T3 ETE Numeracy (Jul 2021, primary outcome)
el_num = pd.read_excel(cfg["FILE_EL_NUM"])
el_num.columns = el_num.columns.str.strip()
el_num = el_num.rename(columns={"AcademyCode": "academycode", "StudyID": "studyid",
                                 "Score": "score_el", "MaxScore": "maxscore_el",
                                 "GradeName": "gradename"})
el_num["score_el"] = pd.to_numeric(el_num["score_el"], errors="coerce")
el_num = el_num[el_num["academycode"].isin(rct_academies)].copy()
print(f"  Endline numeracy (T3 ETE): {len(el_num):,d} rows, "
      f"{el_num['score_el'].notna().sum():,d} scored")

# 2c. Endline: T3 ETE Maths (Jul 2021, secondary/spillover outcome)
el_math = pd.read_excel(cfg["FILE_EL_MATH"])
el_math.columns = el_math.columns.str.strip()
el_math = el_math.rename(columns={"AcademyCode": "academycode", "StudyID": "studyid",
                                    "Score": "score_el_math", "MaxScore": "maxscore_el_math",
                                    "GradeName": "gradename"})
el_math["score_el_math"] = pd.to_numeric(el_math["score_el_math"], errors="coerce")
el_math = el_math[el_math["academycode"].isin(rct_academies)].copy()
print(f"  Endline maths (T3 ETE): {len(el_math):,d} rows, "
      f"{el_math['score_el_math'].notna().sum():,d} scored")

# 2d. Roster (has PlacementExamScore, Gender)
roster = pd.read_excel(cfg["FILE_ROSTER"])
roster.columns = roster.columns.str.strip()
roster = roster.rename(columns={"AcademyCode": "academycode", "StudyID": "studyid",
                                 "PlacementExamScore": "placement_score",
                                 "Gender": "gender", "GradeName": "gradename"})
roster = roster[roster["academycode"].isin(rct_academies)].copy()
print(f"  Roster T2: {len(roster):,d} rows, "
      f"{roster['placement_score'].notna().sum():,d} with placement score")


# ═════════════════════════════════════════════════════════════════════════════
# 3. MERGE
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Merging ---")

# Start from BL universe in RCT academies
df = bl[["academycode", "studyid", "grade", "score_bl", "maxscore_bl",
         "constituency", "county", "stream", "enrolled_date"]].copy()

# Merge endline numeracy
df = df.merge(el_num[["studyid", "score_el", "maxscore_el"]].drop_duplicates("studyid"),
              on="studyid", how="outer", indicator="_mel_num")
df["in_bl"] = df["_mel_num"] != "right_only"
df["in_el"] = df["_mel_num"] != "left_only"
df.drop(columns=["_mel_num"], inplace=True)

# Merge endline maths
df = df.merge(el_math[["studyid", "score_el_math", "maxscore_el_math"]].drop_duplicates("studyid"),
              on="studyid", how="left")

# Merge roster (for placement score, gender)
df = df.merge(roster[["studyid", "placement_score", "gender"]].drop_duplicates("studyid"),
              on="studyid", how="left")

# Merge placement group assignments
pl_grp = pl[["studyid", "group"]].drop_duplicates("studyid")
df = df.merge(pl_grp, on="studyid", how="left")

# Fill academy code from other sources for EL-only students
if df["academycode"].isna().any():
    el_acad = el_num[["studyid", "academycode"]].drop_duplicates("studyid")
    fill = df["academycode"].isna()
    df.loc[fill, "academycode"] = df.loc[fill, "studyid"].map(
        el_acad.set_index("studyid")["academycode"])

# Fill grade from EL file for students missing BL grade
if df["grade"].isna().any():
    el_grade = el_num[["studyid", "gradename"]].drop_duplicates("studyid")
    el_grade["grade_el"] = extract_grade(el_grade["gradename"])
    fill = df["grade"].isna()
    df.loc[fill, "grade"] = df.loc[fill, "studyid"].map(
        el_grade.set_index("studyid")["grade_el"])

# Merge correct treatment from placement file
df = df.drop(columns=["treat"], errors="ignore")
df = df.merge(treat_map, on="academycode", how="left")

# Fill constituency from EL file
if df["constituency"].isna().any():
    el_const = el_num[["studyid", "Constituency1"]].rename(
        columns={"Constituency1": "constituency_el"}).drop_duplicates("studyid")
    fill = df["constituency"].isna()
    if "constituency_el" not in df.columns:
        df = df.merge(el_const, on="studyid", how="left")
        df["constituency"] = df["constituency"].fillna(df["constituency_el"])
        df.drop(columns=["constituency_el"], inplace=True)

print(f"  After merge: {len(df):,d} rows, {df['academycode'].nunique()} academies")


# ═════════════════════════════════════════════════════════════════════════════
# 4. SAMPLE RESTRICTIONS
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Sample restriction log ---")
print_sample_log("Starting merged dataset", len(df))

# Keep only RCT academies
df = df[df["academycode"].isin(rct_academies)].copy()
print_sample_log("RCT academies only", len(df))

df = df[df["grade"].isin([1, 2, 3])].copy()
print_sample_log("Valid grade (P1-P3)", len(df))

df = df[df["treat"].notna()].copy()
print_sample_log("Non-missing treatment", len(df))

# Drop Stream B if present
if "stream" in df.columns:
    df = df[~(df["stream"] == "B")].copy()
    print_sample_log("Drop Stream B", len(df))

# g12 indicator (for pipeline compatibility)
df["g12"] = (df["grade"].isin([1, 2])).astype(int)

# ggroup: treatment at academy level
df["ggroup"] = df.groupby("academycode").ngroup()

# Drop single-grade academies
grade_counts = df.groupby("academycode")["grade"].nunique()
single_grade_acads = grade_counts[grade_counts == 1].index
df = df[~df["academycode"].isin(single_grade_acads)].copy()
print_sample_log("Drop single-grade academies", len(df))

# Need BL scores in academy
bl_by_acad = df.groupby("academycode")["score_bl"].transform(lambda x: x.notna().sum())
df = df[bl_by_acad > 0].copy()
print_sample_log("BL scores exist in academy", len(df))

# Drop duplicates
dup_mask = df.duplicated(subset=["studyid"], keep=False)
dup_acad = df[dup_mask].groupby("studyid")["academycode"].nunique()
movers = dup_acad[dup_acad > 1].index
if len(movers) > 0:
    df = df[~df["studyid"].isin(movers)].copy()
    print_sample_log(f"Drop {len(movers)} students who switched academies", len(df))
df = df.drop_duplicates(subset=["studyid"], keep="first")
print_sample_log("Deduplicated by studyid", len(df))

# Sample flags
df["has_bl"] = df["score_bl"].notna()
df["has_el"] = df["score_el"].notna()

bl_counts = df.groupby("ggroup")["score_bl"].transform(lambda x: x.notna().sum())
df["finsamp"] = df["has_bl"] & (bl_counts > 1)
print_sample_log("Final sample (has BL, ≥2 BL in academy)", df["finsamp"].sum())
print_sample_log("  ... of whom have endline (numeracy)", (df["finsamp"] & df["has_el"]).sum())
print_sample_log("  ... of whom have endline (maths)",
                 (df["finsamp"] & df["score_el_math"].notna()).sum())


# ═════════════════════════════════════════════════════════════════════════════
# 5. CONSTRUCT VARIABLES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Constructing variables ---")

# Strata: by constituency
df["constituency"] = df["constituency"].fillna("Unknown").str.strip()
df["strata"] = df.groupby("constituency").ngroup()

# Propensity score: fraction treated within strata
acad_treat = df.drop_duplicates("academycode")[["academycode", "treat", "strata"]]
strata_pt = acad_treat.groupby("strata")["treat"].mean()
df["P_t"] = df["strata"].map(strata_pt)
df["P_c"] = 1 - df["P_t"]
print(f"  Propensity (P_t): mean={df['P_t'].mean():.3f}, "
      f"range=[{df['P_t'].min():.3f}, {df['P_t'].max():.3f}]")

# Ability group assignment (std_grp)
# Treatment schools: Red=1, Blue=2, Yellow=3
# Control schools: each grade is its own "group"
group_map = {"Red": 1, "Blue": 2, "Yellow": 3}
df["std_grp"] = df["group"].map(group_map)

# For students without placement group data, assign based on BL score tercile
missing_grp = df["std_grp"].isna() & df["score_bl"].notna()
for g in [1, 2, 3]:
    g_mask = missing_grp & (df["grade"] == g)
    if g_mask.sum() > 0:
        scores = df.loc[g_mask, "score_bl"]
        try:
            df.loc[g_mask, "std_grp"] = pd.qcut(
                scores, q=3, labels=[1, 2, 3], duplicates="drop"
            ).astype(float)
        except ValueError:
            df.loc[g_mask, "std_grp"] = 1.0

# Remaining missing → group 1
df["std_grp"] = df["std_grp"].fillna(1.0).astype(int)

# upper_group: Yellow (top group) = 1, Red/Blue = 0
df["upper_group"] = (df["std_grp"] == 3).astype(float)

print(f"  Group assignments: {df['std_grp'].value_counts().sort_index().to_dict()}")

# Standardise scores (control-group normalised)
ctrl = df["treat"] == 0
df["std_score_bl"] = standardise_by_grade(df, "score_bl", ctrl)
df["std_score_el"] = standardise_by_grade(df, "score_el", ctrl)
print("  Standardised BL/EL numeracy scores")

# ── Reliability estimation ──
# The standard BL→EL r² is cross-subject (maths→numeracy) and severely attenuated.
# Instead, estimate reliability from the placement test's group assignment in the
# control group: R²(Group → EL Num | within-grade), corrected for discretization
# (3-category ordinal → continuous latent via Monte Carlo polyserial).
# See nigeria_reliability.py for full derivation.

r2_diag = {}
for g in [1, 2, 3]:
    mask = ctrl & (df["grade"] == g) & df["score_bl"].notna() & df["score_el"].notna()
    if mask.sum() > 10:
        r2_diag[g] = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
    else:
        r2_diag[g] = 0.0
print("  Diagnostic r² = R²(BL_maths→EL_num) by grade (cross-subject, attenuated): "
      + ", ".join(f"G{g}={v:.4f}" for g, v in sorted(r2_diag.items())))

from scipy.stats import norm, pearsonr  # noqa: E402

r2_by_grade = {}
for g in [2, 3]:
    g_ctrl = ctrl & (df["grade"] == g) & df["std_grp"].notna() & df["score_el"].notna()
    if g_ctrl.sum() > 20:
        r_obs = pearsonr(df.loc[g_ctrl, "std_grp"], df.loc[g_ctrl, "score_el"])[0]
        # Discretization correction via Monte Carlo
        freq = df.loc[g_ctrl, "std_grp"].value_counts(normalize=True).sort_index()
        p1g = freq.get(1, 0)
        p2g = freq.get(2, 0)
        c1 = norm.ppf(p1g) if p1g < 1 else 3.0
        c2 = norm.ppf(p1g + p2g) if (p1g + p2g) < 1 else 3.0
        rng = np.random.default_rng(42)
        z = rng.standard_normal(200_000)
        z_cat = np.where(z < c1, 1, np.where(z < c2, 2, 3)).astype(float)
        d_factor = np.corrcoef(z, z_cat)[0, 1]
        r2_corrected = r_obs**2 / max(d_factor**2, 0.01)
        r2_by_grade[g] = min(r2_corrected, 0.95)
        print(f"  P{g}: r(grp,EL)={r_obs:.3f}, d={d_factor:.3f}, "
              f"corrected r²={r2_by_grade[g]:.3f}  [N={g_ctrl.sum()}]")
    else:
        r2_by_grade[g] = r2_diag.get(g, 0.05)

# P1 has almost no sorting variation (nearly all Red), use BL→EL fallback
r2_by_grade[1] = max(r2_diag.get(1, 0.05), 0.05)
print(f"  P1: using BL→EL fallback r²={r2_by_grade[1]:.3f} (minimal sorting variation)")
print("  Reliability r² for EB shrinkage: "
      + ", ".join(f"G{g}={v:.3f}" for g, v in sorted(r2_by_grade.items())))

# EB ability
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

# Experiment indicators
df["exp0"] = 1   # stacked (all)
df["exp1"] = 0   # no separate sub-experiment
df["exp2"] = 1   # all grades (for compatibility)
for g in [1, 2, 3]:
    df[f"g{g}"] = (df["grade"] == g).astype(int)
df["g4"] = 0


# ═════════════════════════════════════════════════════════════════════════════
# 6. PEER VARIABLES (Borusyak-Hull)
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

# Distance from median instruction
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    med = df.groupby(["academycode", grp_type])["std_eb"].transform("median")
    df[f"dist_med_{suffix}"] = (df["std_eb"] - med).abs()

df["exp_dist_med"] = df["P_t"] * df["dist_med_treat"] + df["P_c"] * df["dist_med_ctrl"]
df["dist_med"] = np.where(df["treat"] == 1, df["dist_med_treat"], df["dist_med_ctrl"])

# Within-class dispersion (endline)
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_score_el"].transform("mean")
    df[f"dev_el_{suffix}"] = (df["std_score_el"] - mn).abs()
df["dev_el"] = np.where(df["treat"] == 1, df["dev_el_treat"], df["dev_el_ctrl"])

# Within-class dispersion (EB ability)
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_eb"].transform("mean")
    df[f"dev_eb_{suffix}"] = (df["std_eb"] - mn).abs()
df["dev_eb"] = np.where(df["treat"] == 1, df["dev_eb_treat"], df["dev_eb_ctrl"])
df["exp_dev_eb"] = df["P_t"] * df["dev_eb_treat"] + df["P_c"] * df["dev_eb_ctrl"]
print("  Distance and dispersion variables computed")

# Class size
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    df[f"csize_{suffix}"] = df.groupby(["academycode", grp_type])["studyid"].transform("count")
df["exp_csize"] = df["P_t"] * df["csize_treat"] + df["P_c"] * df["csize_ctrl"]
df["csize"] = np.where(df["treat"] == 1, df["csize_treat"], df["csize_ctrl"])
print("  Class sizes computed")

# Baseline deciles, misfit, distance from cutoff
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
for g, cutoff in cfg["cutoffs"].items():
    mask = (df["grade"] == g) & df["score_bl"].notna()
    df.loc[mask, "dist_from_cutoff"] = (df.loc[mask, "score_bl"] - cutoff).abs()
print("  Baseline deciles, misfit, distance-from-cutoff computed")


# ═════════════════════════════════════════════════════════════════════════════
# 7. MERGE ACADEMY-GRADE COVARIATES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Merging covariates ---")

# Teacher attendance
try:
    tch = pd.read_excel(cfg["FILE_TCH"])
    tch.columns = tch.columns.str.strip()
    tch = tch.rename(columns={"academycode": "academycode",
                               "GradeName": "gradename",
                               "attendance_grade_average": "tch_attn"})
    tch["grade"] = extract_grade(tch["gradename"])
    tch = tch[["academycode", "grade", "tch_attn"]].dropna(subset=["academycode", "grade"])
    df = df.merge(tch, on=["academycode", "grade"], how="left")
    print(f"  Teacher attendance merged ({df['tch_attn'].notna().sum():,d} non-missing)")
except Exception as e:
    print(f"  WARNING: Teacher attendance merge failed ({e})")
    df["tch_attn"] = np.nan

# Fill missing covariates for pipeline compatibility
for col in ["score_ml", "std_score_ml", "maxscore_ml", "maxscore_el",
            "in_ml", "acad_year", "pupilattendance", "lp_comp", "lp_opened"]:
    if col not in df.columns:
        df[col] = np.nan
df["in_ml"] = False


# ═════════════════════════════════════════════════════════════════════════════
# 8. SAVE
# ═════════════════════════════════════════════════════════════════════════════

keep_cols = [
    "academycode", "studyid", "grade", "stream", "county", "constituency",
    "ggroup", "strata", "acad_year", "g12",
    "treat", "P_t", "P_c",
    "upper_group", "std_grp",
    "score_bl", "score_ml", "score_el", "score_el_math",
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
    "has_bl", "has_el", "finsamp", "in_bl", "in_ml", "in_el",
    "placement_score", "gender", "group",
]
keep_cols = [c for c in keep_cols if c in df.columns]
df = df[keep_cols].copy()

df.to_parquet(cfg["ANALYSIS_FILE"], index=False)
print(f"\n{'='*70}")
print(f"  Nigeria dataset saved to {cfg['ANALYSIS_FILE']}")
print(f"  {len(df):,d} rows, {len(df.columns)} columns")
print(f"  Final sample (finsamp): {df['finsamp'].sum():,d}")
print(f"  Final sample with endline (numeracy): {(df['finsamp'] & df['has_el']).sum():,d}")
print(f"  Final sample with endline (maths): {(df['finsamp'] & df['score_el_math'].notna()).sum():,d}")

print("\n--- Quick summary ---")
print(df.groupby(["grade", "treat"]).agg(
    n=("studyid", "count"),
    n_finsamp=("finsamp", "sum"),
    mean_bl=("score_bl", "mean"),
    mean_el=("score_el", "mean"),
    pct_has_el=("has_el", "mean"),
).round(3).to_string())

# Attrition check
print("\n--- Attrition ---")
for t in [0, 1]:
    sub = df[df["treat"] == t]
    bl_n = sub["has_bl"].sum()
    el_n = (sub["has_bl"] & sub["has_el"]).sum()
    rate = el_n / bl_n * 100 if bl_n > 0 else 0
    print(f"  T={t}: {bl_n:,d} with BL -> {el_n:,d} with EL ({rate:.1f}% retention)")
