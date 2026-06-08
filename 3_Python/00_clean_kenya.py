#!/usr/bin/env python3
"""
00_clean_kenya.py — Build analysis dataset from raw Kenya CSVs.

Kenya experiment: Grades 1-2, cross-grade ability grouping.
Baseline = T2 Midterm (Literacy + English Language composite).
Endline = T3 Endterm (same composite).
Treatment at academy level, stratified by constituency.
Reading group cutoff: comp > 40 (G1), comp > 35 (G2) → upper ("purple").

Produces: output/analysis_kenya.parquet
"""

import numpy as np
import pandas as pd
from config import get_config, OUT
from utils import (standardise_by_grade, leave_self_out_mean,
                   print_sample_log)

pd.set_option("display.max_columns", 40)
cfg = get_config("kenya")

print("=" * 70)
print("00_clean_kenya.py — Building Kenya analysis dataset from raw CSVs")
print("=" * 70)


def load_score_file(path, grade, wave_prefix):
    """Load a Kenya score CSV, extract key columns."""
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
        "Title": "title",
    })
    df["grade"] = grade
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df.loc[df["score"] == -1, "score"] = np.nan
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 1. LOAD AND MERGE BASELINE (T2 Midterm: Literacy + English)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading baseline (T2 Midterm) ---")

bl_parts = []
for grade, lit_file, eng_file in [
    (1, cfg["FILE_G1_BL_LIT"], cfg["FILE_G1_BL_ENG"]),
    (2, cfg["FILE_G2_BL_LIT"], cfg["FILE_G2_BL_ENG"]),
]:
    lit = load_score_file(lit_file, grade, "bl")
    eng = load_score_file(eng_file, grade, "bl")

    # Merge literacy and English on (academy, student)
    lit = lit.rename(columns={"score": "score_bl_lit", "maxscore": "max_bl_lit"})
    eng = eng.rename(columns={"score": "score_bl_eng", "maxscore": "max_bl_eng"})

    keep_lit = ["academycode", "studyid", "grade", "score_bl_lit", "max_bl_lit",
                "treatmentassignment", "constituency", "county",
                "demographiclocation", "academy_cohort", "enrolled_date",
                "stream"]
    keep_eng = ["academycode", "studyid", "score_bl_eng", "max_bl_eng"]

    merged = lit[keep_lit].merge(eng[keep_eng], on=["academycode", "studyid"],
                                  how="outer")
    bl_parts.append(merged)
    print(f"  Grade {grade}: {len(merged):,d} students "
          f"(lit={lit['score_bl_lit'].notna().sum()}, eng={eng['score_bl_eng'].notna().sum()})")

bl = pd.concat(bl_parts, ignore_index=True)
n_both_bl = (bl["score_bl_lit"].notna() & bl["score_bl_eng"].notna()).sum()
n_one_bl = ((bl["score_bl_lit"].notna() ^ bl["score_bl_eng"].notna())).sum()
bl["score_bl"] = bl["score_bl_lit"] + bl["score_bl_eng"]  # NaN if either missing
print(f"  Total baseline: {len(bl):,d} students, "
      f"{bl['academycode'].nunique()} academies")
print(f"  Both subjects: {n_both_bl:,d}  |  Only one subject (→ NaN): {n_one_bl:,d}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. LOAD AND MERGE ENDLINE (T3 Endterm: Literacy + English)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Loading endline (T3 Endterm) ---")

el_parts = []
for grade, lit_file, eng_file in [
    (1, cfg["FILE_G1_EL_LIT"], cfg["FILE_G1_EL_ENG"]),
    (2, cfg["FILE_G2_EL_LIT"], cfg["FILE_G2_EL_ENG"]),
]:
    lit = load_score_file(lit_file, grade, "el")
    eng = load_score_file(eng_file, grade, "el")

    lit = lit.rename(columns={"score": "score_el_lit", "maxscore": "max_el_lit"})
    eng = eng.rename(columns={"score": "score_el_eng", "maxscore": "max_el_eng"})

    keep_lit = ["academycode", "studyid", "grade", "score_el_lit", "max_el_lit"]
    keep_eng = ["academycode", "studyid", "score_el_eng", "max_el_eng"]

    merged = lit[keep_lit].merge(eng[keep_eng], on=["academycode", "studyid"],
                                  how="outer")
    el_parts.append(merged)
    print(f"  Grade {grade}: {len(merged):,d} students")

el = pd.concat(el_parts, ignore_index=True)
n_both_el = (el["score_el_lit"].notna() & el["score_el_eng"].notna()).sum()
n_one_el = ((el["score_el_lit"].notna() ^ el["score_el_eng"].notna())).sum()
el["score_el"] = el["score_el_lit"] + el["score_el_eng"]  # NaN if either missing
print(f"  Total endline: {len(el):,d} students")
print(f"  Both subjects: {n_both_el:,d}  |  Only one subject (→ NaN): {n_one_el:,d}")

# ═════════════════════════════════════════════════════════════════════════════
# 3. MERGE BL + EL
# ═════════════════════════════════════════════════════════════════════════════

df = bl.merge(el[["academycode", "studyid", "score_el", "score_el_lit",
                   "score_el_eng", "max_el_lit", "max_el_eng"]],
              on=["academycode", "studyid"], how="outer", indicator="_mel")

df["in_bl"] = df["_mel"] != "right_only"
df["in_el"] = df["_mel"] != "left_only"
df.drop(columns=["_mel"], inplace=True)
print(f"\nAfter BL-EL merge: {len(df):,d} rows")

# Treatment
df["treat"] = (df["treatmentassignment"] == "Treatment").astype(float)
df.loc[df["treatmentassignment"].isna(), "treat"] = np.nan

# Design-based school assignment probabilities from the vetted legacy
# Kenya cleaning pipeline, which preserves the full year-1 school roster.
legacy_parent = ROOT / "2_Data" / "2_Cleaned" / "Kenya" / "0_K_AG_parent.dta"
design = pd.read_stata(
    legacy_parent,
    columns=["academycode", "constituency", "treat"],
    convert_categoricals=False,
)
design["constituency_design"] = design["constituency"].astype("string").str.strip()
design = design.groupby("academycode", as_index=False).agg(
    treat=("treat", "max"),
    constituency_design=("constituency_design", "last"),
)
assert design["constituency_design"].notna().all()
design["P_t_design"] = design.groupby("constituency_design")["treat"].transform("mean")

# Grade (prefer BL, fill from where available)
df["grade"] = df["grade"].fillna(
    df.merge(el[["academycode", "studyid", "grade"]],
             on=["academycode", "studyid"], how="left", suffixes=("", "_el"))
    .get("grade_el", pd.Series(dtype=float))
)

# Stream
df["stream"] = df["stream"].str.strip()

# Location
df["locationtype"] = df["demographiclocation"].str.strip()

# Constituency (clean)
df["constituency"] = df["constituency"].str.strip()
df["county"] = df["county"].str.strip()


# ═════════════════════════════════════════════════════════════════════════════
# 4. SAMPLE RESTRICTIONS
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Sample restriction log ---")
print_sample_log("Starting merged dataset", len(df))

df = df[df["grade"].isin([1, 2])].copy()
print_sample_log("Valid grade (1-2)", len(df))

df = df[df["treat"].notna()].copy()
print_sample_log("Non-missing treatment", len(df))

# Drop Stream B
df = df[~(df["stream"] == "B")].copy()
print_sample_log("Drop Stream B", len(df))

# g12 indicator (all are g12 in Kenya)
df["g12"] = 1

# ggroup: in Kenya, treatment is at academy level (both grades treated together)
# Stata: egen ggroup = group(academycode)
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

# Sample flags
df["has_bl"] = df["score_bl"].notna()
df["has_el"] = df["score_el"].notna()

bl_counts = df.groupby("ggroup")["score_bl"].transform(lambda x: x.notna().sum())
df["finsamp"] = df["has_bl"] & (bl_counts > 1)
print_sample_log("Final sample (has BL, ≥2 BL in academy)", df["finsamp"].sum())
print_sample_log("  ... of whom have endline", (df["finsamp"] & df["has_el"]).sum())


# ═════════════════════════════════════════════════════════════════════════════
# 5. CONSTRUCT VARIABLES
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Constructing variables ---")

# Strata and propensity: merge design-based school roster.
design_map = design.set_index("academycode")
df["constituency"] = df["academycode"].map(design_map["constituency_design"])
df["P_t"] = df["academycode"].map(design_map["P_t_design"])
assert df["constituency"].notna().all()
assert df["P_t"].notna().all()
df["strata"] = df.groupby("constituency").ngroup()
df["P_c"] = 1 - df["P_t"]
print(f"  Propensity (P_t): mean={df['P_t'].mean():.3f}, "
      f"range=[{df['P_t'].min():.3f}, {df['P_t'].max():.3f}]")

# Upper group (reading group assignment under treatment)
# G1: comp > 40 → purple. G2: comp > 35 → purple.
df["upper_group"] = np.nan
for g, cutoff in cfg["cutoffs"].items():
    mask = (df["grade"] == g) & df["score_bl"].notna()
    df.loc[mask, "upper_group"] = (df.loc[mask, "score_bl"] > cutoff).astype(float)
df.loc[df["score_bl"].isna() & df["treat"].notna(), "upper_group"] = 0.0

# std_grp (reading group label): 1=lower, 2=upper (both grades mixed)
df["std_grp"] = np.where(df["upper_group"] == 1, 2, 1)

# Standardise composite scores by grade, control-group normalised
ctrl = df["treat"] == 0
df["std_score_bl"] = standardise_by_grade(df, "score_bl", ctrl)
df["std_score_el"] = standardise_by_grade(df, "score_el", ctrl)
print("  Standardised BL/EL composite scores")

# Reliability r² = R²(BL→EL) in control, by grade
# EB shrinkage: θ̂ = μ_g + r²_g × (s_i - μ_g)
r2_by_grade = {}
for g in [1, 2]:
    mask = ctrl & (df["grade"] == g) & df["score_bl"].notna() & df["score_el"].notna()
    if mask.sum() > 10:
        r2_by_grade[g] = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
    else:
        r2_by_grade[g] = 0.05
print("  Diagnostic reliability r² = R²(BL→EL) by grade: "
      + ", ".join(f"G{g}={v:.4f}" for g, v in sorted(r2_by_grade.items())))

df["eb_ability"] = np.nan
for g in [1, 2]:
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
df["exp1"] = 0   # no G3-4 in Kenya
df["exp2"] = 1   # all are G1-2
for g in [1, 2]:
    df[f"g{g}"] = (df["grade"] == g).astype(int)
df["g3"] = 0
df["g4"] = 0


# ═════════════════════════════════════════════════════════════════════════════
# 6. PEER VARIABLES (Borusyak-Hull)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Computing peer variables ---")

# Treatment peers: same reading group (std_grp) at academy
# Control peers: same grade at academy
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

# Within-class dispersion (EB ability — pre-treatment)
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
for g in [1, 2]:
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
# 7. SAVE
# ═════════════════════════════════════════════════════════════════════════════

# No midline in Kenya's main experiment
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
    "has_bl", "has_el", "finsamp", "in_bl", "in_ml", "in_el",
]
keep_cols = [c for c in keep_cols if c in df.columns]
df = df[keep_cols].copy()

df.to_parquet(cfg["ANALYSIS_FILE"], index=False)
print(f"\n✓ Kenya dataset saved to {cfg['ANALYSIS_FILE']}")
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
