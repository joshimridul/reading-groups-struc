#!/usr/bin/env python3
"""
00_clean.py — Build analysis dataset from raw Liberia CSVs.

Produces: output/analysis.parquet

Every sample restriction is logged so decisions are transparent.
No dependency on old .dta files.
"""

import numpy as np
import pandas as pd
from config import get_config, OUT
from utils import standardise_by_grade, leave_self_out_mean, print_sample_log

cfg = get_config("liberia")
FILE_BL = cfg["FILE_BL"]
FILE_ML = cfg["FILE_ML"]
FILE_EL = cfg["FILE_EL"]
FILE_LOC = cfg["FILE_LOC"]
FILE_ATTN = cfg["FILE_ATTN"]
FILE_LP = cfg["FILE_LP"]
FILE_TCH = cfg["FILE_TCH"]
FILE_MGR = cfg["FILE_MGR"]
CUTOFF_G12 = cfg["cutoff_g12"]
CUTOFF_G34 = cfg["cutoff_g34"]
COHORT_THRESHOLD = cfg["cohort_threshold"]
ANALYSIS_FILE = cfg["ANALYSIS_FILE"]

pd.set_option("display.max_columns", 40)


def extract_grade(gradename_series):
    """
    Pull numeric grade from strings like 'Grade 1', 'GRADE 4'.
    Stata: gen grade = real(substr(gradename,-1,1))
    """
    return (
        gradename_series.astype(str)
        .str.extract(r"(\d)", expand=False)
        .astype(float)
    )


def clean_treatment(col):
    """Convert treatment columns: 'na' → NaN, then float."""
    return pd.to_numeric(col.replace("na", np.nan), errors="coerce")


# ═════════════════════════════════════════════════════════════════════════════
# 1. LOAD RAW DATA
# ═════════════════════════════════════════════════════════════════════════════

print("=" * 70)
print("00_clean.py — Building analysis dataset from raw CSVs")
print("=" * 70)

# ── 1a. Baseline (student level) ─────────────────────────────────────────────
# Stata: import delimited using "LR_G1234_S1_BaselineData_Blinded.csv", clear
bl = pd.read_csv(FILE_BL)
bl.columns = bl.columns.str.strip().str.lower()
bl["grade_bl"] = extract_grade(bl["gradename"])
bl["treat_g12_bl"] = clean_treatment(bl["treatmentassignment_g12"])
bl["treat_g34_bl"] = clean_treatment(bl["treatmentassignment_g34"])
bl = bl.rename(columns={"baselinescore": "score_bl"})
bl = bl[["academycode", "studyid", "grade_bl", "score_bl",
         "treat_g12_bl", "treat_g34_bl"]]
print(f"\nBaseline loaded: {len(bl):,d} rows, "
      f"{bl['academycode'].nunique()} academies")

# ── 1b. Midline (student level) ─────────────────────────────────────────────
# Stata: import delimited using "LR_G1234_S1_ETE_Blinded.csv", clear
ml = pd.read_csv(FILE_ML)
ml.columns = ml.columns.str.strip().str.lower()
ml["grade_ml"] = extract_grade(ml["gradename"])
ml["treat_g12_ml"] = clean_treatment(ml["treatmentassignment_g12"])
ml["treat_g34_ml"] = clean_treatment(ml["treatmentassignment_g34"])
# Score of -1 = absent → missing
ml["score_ml"] = ml["midlinescore"].where(ml["midlinescore"] >= 0)
ml["maxscore_ml"] = ml["midlinemaxscore"]
ml["stream_ml"] = ml["stream"].str.strip()
ml["county_ml"] = ml["county"].str.strip()
ml = ml[["academycode", "studyid", "grade_ml", "score_ml", "maxscore_ml",
         "stream_ml", "county_ml", "treat_g12_ml", "treat_g34_ml"]]
# Deduplicate: keep first occurrence per (academy, student)
ml = ml.drop_duplicates(subset=["academycode", "studyid"], keep="first")
print(f"Midline loaded:  {len(ml):,d} rows")

# ── 1c. Endline (student level) ─────────────────────────────────────────────
el = pd.read_csv(FILE_EL)
el.columns = el.columns.str.strip().str.lower()
el["grade_el"] = extract_grade(el["gradename"])
el["treat_g12_el"] = clean_treatment(el["treatmentassignment_g12"])
el["treat_g34_el"] = clean_treatment(el["treatmentassignment_g34"])
el["score_el"] = el["endlinescore"].where(el["endlinescore"] >= 0)
el["maxscore_el"] = el["endlinemaxscore"]
el["stream_el"] = el["stream"].str.strip()
el["county_el"] = el["county"].str.strip()
el["demographic_el"] = el.get("demographiclocation", pd.Series(dtype=str))
el = el[["academycode", "studyid", "grade_el", "score_el", "maxscore_el",
         "stream_el", "county_el", "treat_g12_el", "treat_g34_el"]]
el = el.drop_duplicates(subset=["academycode", "studyid"], keep="first")
print(f"Endline loaded:  {len(el):,d} rows")

# ── 1d. Academy locations ───────────────────────────────────────────────────
loc = pd.read_excel(FILE_LOC)
loc.columns = loc.columns.str.strip().str.lower()
loc = loc.rename(columns={"county": "county_loc", "constituency": "constituency",
                           "cohort": "cohort_raw"})
loc = loc[["academycode", "county_loc", "constituency", "cohort_raw"]]
print(f"Locations loaded: {len(loc)} academies")


# ═════════════════════════════════════════════════════════════════════════════
# 2. MERGE STUDENT-LEVEL DATA
# ═════════════════════════════════════════════════════════════════════════════

# Stata: merge 1:1 academycode studyid using `ml', gen(_mml)
df = bl.merge(ml, on=["academycode", "studyid"], how="outer", indicator="_mml")
df = df.merge(el, on=["academycode", "studyid"], how="outer", indicator="_mel")
print(f"\nAfter three-way merge: {len(df):,d} rows")

# Merge flags
df["in_bl"] = df["_mml"] != "right_only"
df["in_ml"] = df["_mml"] != "left_only"
df["in_el"] = df["_mel"] != "right_only"
df.drop(columns=["_mml", "_mel"], inplace=True)

# ── Resolve grade ────────────────────────────────────────────────────────────
# Priority: EL grade (latest), then ML, then BL
df["grade"] = df["grade_el"].fillna(df["grade_ml"]).fillna(df["grade_bl"])

# ── Resolve stream ───────────────────────────────────────────────────────────
df["stream"] = df["stream_el"].fillna(df["stream_ml"])

# ── Resolve treatment assignment ─────────────────────────────────────────────
for suffix in ["g12", "g34"]:
    cols = [f"treat_{suffix}_{w}" for w in ["bl", "ml", "el"]]
    existing = [c for c in cols if c in df.columns]
    if len(existing) == 0:
        continue
    wave_vals = df[existing]
    row_min = wave_vals.min(axis=1)
    row_max = wave_vals.max(axis=1)
    disagree = (row_min != row_max) & wave_vals.notna().sum(axis=1).gt(1)
    n_disagree = disagree.sum()
    if n_disagree > 0:
        print(f"  WARNING: {n_disagree} students have conflicting treat_{suffix} "
              f"across waves — using modal value (ties→NaN)")
    modal = wave_vals.mode(axis=1)[0]
    df[f"treat_{suffix}"] = np.where(disagree, modal, row_min)

# Assign treatment: g12 for grades 1-2, g34 for grades 3-4
df["treat"] = np.where(df["grade"].isin([1, 2]), df["treat_g12"],
              np.where(df["grade"].isin([3, 4]), df["treat_g34"], np.nan))

# ── Merge academy locations ─────────────────────────────────────────────────
df = df.merge(loc, on="academycode", how="left")

# Parse cohort date
df["cohort_date"] = pd.to_datetime(df["cohort_raw"], format="mixed",
                                    dayfirst=True, errors="coerce")
df["acad_year"] = np.where(df["cohort_date"] < pd.Timestamp(COHORT_THRESHOLD),
                           1, 2)

# County: prefer location file, fall back to EL/ML
df["county"] = df["county_loc"].fillna(df["county_el"]).fillna(df["county_ml"])


# ═════════════════════════════════════════════════════════════════════════════
# 3. SAMPLE RESTRICTIONS (every step logged)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Sample restriction log ---")
print_sample_log("Starting merged dataset", len(df))

# 3a. Must have a valid grade
df = df[df["grade"].isin([1, 2, 3, 4])].copy()
print_sample_log("Valid grade (1-4)", len(df))

# 3b. Must be in the experiment (non-missing treatment)
df = df[df["treat"].notna()].copy()
print_sample_log("Non-missing treatment assignment", len(df))

# 3c. Drop Stream B (only 1 academy had a second stream)
df = df[~(df["stream"] == "B")].copy()
print_sample_log("Drop Stream B", len(df))

# 3d. Grade group and identifiers
# Stata: gen g12 = inlist(grade, 1, 2)
df["g12"] = df["grade"].isin([1, 2]).astype(int)
# ggroup = unique (academy × grade-group) identifier — the clustering unit
# Stata: egen ggroup = group(g12 academycode)
df["ggroup"] = df.groupby(["g12", "academycode"]).ngroup()

# 3e. Drop single-grade academies (only one grade present in the grade pair)
# Stata: bys academycode g12: egen grade_mean = mean(grade)
#        gen single_grade = inlist(grade_mean,1,2,3,4)
grade_counts = df.groupby(["academycode", "g12"])["grade"].nunique()
single_grade_keys = grade_counts[grade_counts == 1].index
df["single_grade"] = df.set_index(["academycode", "g12"]).index.isin(single_grade_keys)
df = df[~df["single_grade"]].copy()
print_sample_log("Drop single-grade academies", len(df))

# 3f. Need at least some BL scores in the academy-grade group
# Stata: bys academycode ggroup: egen max_gr_bl = max(mean_gr_bl)
#        drop if max_gr_bl == .
bl_by_ggroup = (df.groupby("ggroup")["score_bl"]
                .transform(lambda x: x.notna().sum()))
df = df[bl_by_ggroup > 0].copy()
print_sample_log("BL scores exist in academy-grade group", len(df))

# 3g. Drop duplicate student-within-academy rows (keep first occurrence)
dup_mask = df.duplicated(subset=["academycode", "studyid"], keep="first")
n_dups = dup_mask.sum()
if n_dups > 0:
    df = df[~dup_mask].copy()
    print_sample_log(f"Drop {n_dups} duplicate academy-student rows", len(df))

# 3h. Handle cross-academy duplicate studyids
#     Same student appearing in multiple academies — keep the row with most data
n_before = len(df)
dup_sid = df.duplicated(subset=["studyid"], keep=False)
if dup_sid.any():
    df["_data_score"] = df[["score_bl", "score_ml", "score_el"]].notna().sum(axis=1)
    df = df.sort_values("_data_score", ascending=False).drop_duplicates(
        subset=["studyid"], keep="first").drop(columns=["_data_score"])
    print_sample_log(f"Drop cross-academy duplicate studyids (kept most complete)", len(df))

# 3i. Flag: has baseline score (for final analytical sample)
df["has_bl"] = df["score_bl"].notna()
df["has_el"] = df["score_el"].notna()

# 3j. Final analytical sample flag
# Students who have a baseline score and at least one peer with a BL score
bl_counts = df.groupby("ggroup")["score_bl"].transform(
    lambda x: x.notna().sum())
df["finsamp"] = df["has_bl"] & (bl_counts > 1)
print_sample_log("Final sample (has BL, ≥2 BL in group)", df["finsamp"].sum())
print_sample_log("  ... of whom have endline", (df["finsamp"] & df["has_el"]).sum())


# ═════════════════════════════════════════════════════════════════════════════
# 4. CONSTRUCT VARIABLES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Constructing variables ---")

# ── 4a. Strata and propensity score ──────────────────────────────────────────
# Stata: egen strata = group(acad_year g12)
df["strata"] = df.groupby(["acad_year", "g12"]).ngroup()

# Propensity: fraction treated within strata (at ggroup level)
# Stata: collapse treat, by(academycode acad_year g12)
#        bys acad_year g12: egen P_t = mean(treat)
ggroup_treat = df.drop_duplicates("ggroup")[["ggroup", "treat", "strata"]]
strata_pt = ggroup_treat.groupby("strata")["treat"].mean()
df["P_t"] = df["strata"].map(strata_pt)
df["P_c"] = 1 - df["P_t"]
print(f"  Propensity scores (P_t): {df['P_t'].describe().to_dict()}")

# ── 4b. Study groups (reading group assignment under treatment) ──────────────
# Stata: gen studygroup12 = 0 if inlist(grade,1,2) & score_bl <= 23
df["upper_group"] = np.nan
g12_mask = df["grade"].isin([1, 2]) & df["score_bl"].notna()
g34_mask = df["grade"].isin([3, 4]) & df["score_bl"].notna()
df.loc[g12_mask, "upper_group"] = (df.loc[g12_mask, "score_bl"] > CUTOFF_G12).astype(float)
df.loc[g34_mask, "upper_group"] = (df.loc[g34_mask, "score_bl"] > CUTOFF_G34).astype(float)
# Students with missing BL but valid treatment → lower group (can't be sorted)
missing_bl_treat = df["score_bl"].isna() & df["treat"].notna()
df.loc[missing_bl_treat, "upper_group"] = 0.0

# Reading group label (1=lower/yellow/blue, 2=upper/orange/purple)
# Under treatment, this is the assigned classroom
# Under control, the classroom is the grade
df["std_grp"] = np.nan
df.loc[df["grade"].isin([1, 2]) & (df["upper_group"] == 0), "std_grp"] = 1  # yellow
df.loc[df["grade"].isin([1, 2]) & (df["upper_group"] == 1), "std_grp"] = 2  # orange
df.loc[df["grade"].isin([3, 4]) & (df["upper_group"] == 0), "std_grp"] = 3  # blue
df.loc[df["grade"].isin([3, 4]) & (df["upper_group"] == 1), "std_grp"] = 4  # purple

# ── 4c. Standardise scores ──────────────────────────────────────────────────
ctrl = df["treat"] == 0
df["std_score_bl"] = standardise_by_grade(df, "score_bl", ctrl)
df["std_score_ml"] = standardise_by_grade(df, "score_ml", ctrl)
df["std_score_el"] = standardise_by_grade(df, "score_el", ctrl)
print("  Standardised BL/ML/EL scores (by grade, control-group normalised)")

# ── 4d. Empirical Bayes predicted ability ────────────────────────────────────
# Reliability r² = R²(BL→EL) in control group, by grade
# This is the predictive validity of the baseline diagnostic
# EB shrinkage: θ̂ = μ_g + r²_g × (s_i - μ_g)
r2_by_grade = {}
for g in [1, 2, 3, 4]:
    mask = ctrl & (df["grade"] == g) & df["score_bl"].notna() & df["score_el"].notna()
    if mask.sum() > 10:
        r2_by_grade[g] = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
    else:
        r2_by_grade[g] = 0.05

print("  Diagnostic reliability r² = R²(BL→EL) by grade: "
      + ", ".join(f"G{g}={v:.4f}" for g, v in sorted(r2_by_grade.items())))
for g, r2 in r2_by_grade.items():
    if r2 < 0.02:
        print(f"  ⚠ WARNING: Grade {g} has very low r²={r2:.4f}. "
              f"EB prediction nearly uninformative for this grade.")

df["eb_ability"] = np.nan
for g in [1, 2, 3, 4]:
    r2 = max(r2_by_grade.get(g, 0.05), 0.01)
    g_ctrl = ctrl & (df["grade"] == g)
    mu_g = df.loc[g_ctrl, "score_bl"].mean()
    g_mask = df["grade"] == g
    has_bl = g_mask & df["score_bl"].notna()
    no_bl = g_mask & df["score_bl"].isna()
    df.loc[has_bl, "eb_ability"] = mu_g + r2 * (df.loc[has_bl, "score_bl"] - mu_g)
    df.loc[no_bl, "eb_ability"] = mu_g

# Standardise EB ability
df["std_eb"] = standardise_by_grade(df, "eb_ability", ctrl)
print("  Empirical Bayes predicted ability constructed")

# ── 4e. Experiment indicators ────────────────────────────────────────────────
df["exp0"] = 1  # stacked
df["exp1"] = (1 - df["g12"]).astype(int)  # grades 3-4
df["exp2"] = df["g12"].astype(int)         # grades 1-2

# Grade dummies
for g in [1, 2, 3, 4]:
    df[f"g{g}"] = (df["grade"] == g).astype(int)


# ═════════════════════════════════════════════════════════════════════════════
# 5. PEER VARIABLES (for Borusyak-Hull, Phase 4)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Computing peer variables ---")

# Under treatment: peers are in the same reading group (std_grp) at the academy
# Under control:   peers are in the same grade at the academy
# We compute BOTH counterfactual peer sets for every student.

# 5a. Peer mean score — treatment counterfactual (by reading group)
# Stata: bys academycode std_grp: egen total_t = total(std_score_bl)
df["peer_bl_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_score_bl")
df["peer_bl_ctrl"]  = leave_self_out_mean(df, ["academycode", "grade"],   "std_score_bl")

# Same for EB ability (standardised — so coefficients are comparable across grades)
df["peer_eb_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_eb")
df["peer_eb_ctrl"]  = leave_self_out_mean(df, ["academycode", "grade"],   "std_eb")

# 5b. Expected peer quality — Borusyak-Hull conditioning variable
# E[P|s,T] = P_t × P_treat + (1-P_t) × P_ctrl
df["exp_peer_bl"] = df["P_t"] * df["peer_bl_treat"] + df["P_c"] * df["peer_bl_ctrl"]
df["exp_peer_eb"] = df["P_t"] * df["peer_eb_treat"] + df["P_c"] * df["peer_eb_ctrl"]

# 5c. Realised peer quality
df["peer_bl"] = np.where(df["treat"] == 1, df["peer_bl_treat"], df["peer_bl_ctrl"])
df["peer_eb"] = np.where(df["treat"] == 1, df["peer_eb_treat"], df["peer_eb_ctrl"])

print("  Peer means computed (BL and EB, treatment/control/expected/realised)")

# 5d. Distance from median instruction (proxy: median ability in the group)
# Uses standardised EB so units are comparable across grades
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    med = df.groupby(["academycode", grp_type])["std_eb"].transform("median")
    df[f"dist_med_{suffix}"] = (df["std_eb"] - med).abs()

df["exp_dist_med"] = df["P_t"] * df["dist_med_treat"] + df["P_c"] * df["dist_med_ctrl"]
df["dist_med"] = np.where(df["treat"] == 1, df["dist_med_treat"], df["dist_med_ctrl"])

# 5e. Distance from mean instruction (for within-class dispersion analysis)
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_score_el"].transform("mean")
    df[f"dev_el_{suffix}"] = (df["std_score_el"] - mn).abs()

df["dev_el"] = np.where(df["treat"] == 1, df["dev_el_treat"], df["dev_el_ctrl"])

# Same for predicted ability (not contaminated by treatment)
# Uses standardised EB so units are comparable across grades
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    mn = df.groupby(["academycode", grp_type])["std_eb"].transform("mean")
    df[f"dev_eb_{suffix}"] = (df["std_eb"] - mn).abs()

df["dev_eb"] = np.where(df["treat"] == 1, df["dev_eb_treat"], df["dev_eb_ctrl"])
df["exp_dev_eb"] = df["P_t"] * df["dev_eb_treat"] + df["P_c"] * df["dev_eb_ctrl"]

print("  Distance-from-instruction variables computed")

# 5f. Class size
# Stata: bys academycode std_grp: egen csize_t = count(studyid) if has_bl
for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
    df[f"csize_{suffix}"] = df.groupby(["academycode", grp_type])["studyid"].transform("count")

df["exp_csize"] = df["P_t"] * df["csize_treat"] + df["P_c"] * df["csize_ctrl"]
df["csize"] = np.where(df["treat"] == 1, df["csize_treat"], df["csize_ctrl"])
print("  Class sizes computed")

# 5g. Baseline score deciles, misfit, distance from cutoff
df["bl_decile"] = np.nan
for g in [1, 2, 3, 4]:
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
g12_bl = df["grade"].isin([1, 2]) & df["score_bl"].notna()
g34_bl = df["grade"].isin([3, 4]) & df["score_bl"].notna()
df.loc[g12_bl, "dist_from_cutoff"] = (df.loc[g12_bl, "score_bl"] - CUTOFF_G12).abs()
df.loc[g34_bl, "dist_from_cutoff"] = (df.loc[g34_bl, "score_bl"] - CUTOFF_G34).abs()
print("  Baseline deciles, misfit, distance-from-cutoff computed")


# ═════════════════════════════════════════════════════════════════════════════
# 6. MERGE ACADEMY-GRADE COVARIATES
# ═════════════════════════════════════════════════════════════════════════════

# Pupil attendance
attn = pd.read_csv(FILE_ATTN)
attn.columns = attn.columns.str.strip().str.lower()
attn["grade"] = extract_grade(attn["gradename"])
attn = attn[["academycode", "grade", "pupilattendance"]].copy()

# Lesson completion
lp = pd.read_csv(FILE_LP)
lp.columns = lp.columns.str.strip().str.lower()
lp["grade"] = extract_grade(lp["gradename"])
lp = lp.rename(columns={"percentage_completed": "lp_comp",
                         "percentage_opened": "lp_opened"})
lp = lp[["academycode", "grade", "lp_comp", "lp_opened"]].copy()

# Teacher attendance
tch = pd.read_csv(FILE_TCH)
tch.columns = tch.columns.str.strip().str.lower()
tch["grade"] = extract_grade(tch["gradename"])
tch = tch.rename(columns={"teacherattendance": "tch_attn"})
tch = tch[["academycode", "grade", "tch_attn"]].copy()

# Merge covariates (academy-grade level) onto student data
covars = attn.merge(lp, on=["academycode", "grade"], how="outer")
covars = covars.merge(tch, on=["academycode", "grade"], how="outer")
df = df.merge(covars, on=["academycode", "grade"], how="left")
print(f"\nAcademy-grade covariates merged")


# ═════════════════════════════════════════════════════════════════════════════
# 7. SAVE
# ═════════════════════════════════════════════════════════════════════════════

# Select columns to keep (drop intermediate merge columns)
keep_cols = [
    # Identifiers
    "academycode", "studyid", "grade", "stream", "county", "constituency",
    "ggroup", "strata", "acad_year", "g12",
    # Treatment
    "treat", "P_t", "P_c",
    # Group assignment
    "upper_group", "std_grp",
    # Raw scores
    "score_bl", "score_ml", "score_el",
    "maxscore_ml", "maxscore_el",
    # Standardised scores
    "std_score_bl", "std_score_ml", "std_score_el",
    # EB predicted ability
    "eb_ability", "std_eb",
    # Peer variables (Borusyak-Hull)
    "peer_bl", "peer_bl_treat", "peer_bl_ctrl", "exp_peer_bl",
    "peer_eb", "peer_eb_treat", "peer_eb_ctrl", "exp_peer_eb",
    # Distance from instruction
    "dist_med", "dist_med_treat", "dist_med_ctrl", "exp_dist_med",
    # Within-class dispersion
    "dev_el", "dev_el_treat", "dev_el_ctrl",
    "dev_eb", "dev_eb_treat", "dev_eb_ctrl", "exp_dev_eb",
    # Calibration / mechanism
    "bl_decile", "class_mean_eb", "misfit", "dist_from_cutoff",
    # Class size
    "csize", "csize_treat", "csize_ctrl", "exp_csize",
    # Covariates
    "pupilattendance", "lp_comp", "lp_opened", "tch_attn",
    # Experiment indicators
    "exp0", "exp1", "exp2",
    "g1", "g2", "g3", "g4",
    # Sample flags
    "has_bl", "has_el", "finsamp",
    "in_bl", "in_ml", "in_el",
]
keep_cols = [c for c in keep_cols if c in df.columns]
df = df[keep_cols].copy()

df.to_parquet(ANALYSIS_FILE, index=False)
print(f"\n✓ Analysis dataset saved to {ANALYSIS_FILE}")
print(f"  {len(df):,d} rows, {len(df.columns)} columns")
print(f"  Final sample (finsamp): {df['finsamp'].sum():,d}")
print(f"  Final sample with endline: {(df['finsamp'] & df['has_el']).sum():,d}")

# Quick summary
print("\n--- Quick summary ---")
print(df.groupby(["g12", "treat"]).agg(
    n=("studyid", "count"),
    n_finsamp=("finsamp", "sum"),
    mean_bl=("score_bl", "mean"),
    mean_el=("score_el", "mean"),
    pct_has_el=("has_el", "mean"),
).round(3).to_string())
