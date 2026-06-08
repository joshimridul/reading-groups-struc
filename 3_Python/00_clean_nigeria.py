#!/usr/bin/env python3
"""
Build canonical Nigeria analysis dataset from P123 Numeracy Groups raw files.

Output:
  3_Python/output/analysis_nigeria.parquet
  3_Python/output/ng_cleaning_audit.csv
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, pearsonr

from config import get_config, OUT
from utils import leave_self_out_mean, print_sample_log, standardise_by_grade


pd.set_option("display.max_columns", 60)
cfg = get_config("nigeria")


def extract_grade(gradename_series: pd.Series) -> pd.Series:
    return gradename_series.astype(str).str.extract(r"(\d)", expand=False).astype(float)


def _mode_or_nan(s: pd.Series):
    s = s.dropna()
    if s.empty:
        return np.nan
    m = s.mode()
    return m.iloc[0] if not m.empty else np.nan


def _read_assessment(path, rename_map):
    df = pd.read_excel(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns=rename_map)
    return df


def main():
    print("=" * 72)
    print("00_clean_nigeria.py — canonical Nigeria analysis build")
    print("=" * 72)

    # 1) Placement file is canonical source of treatment and treated-group labels.
    pl = pd.read_excel(cfg["FILE_PLACEMENT"])
    pl = pl.drop_duplicates(subset=["AcademyCode", "StudyID"])
    pl = pl.rename(
        columns={
            "AcademyCode": "academycode",
            "StudyID": "studyid",
            "Treatment": "treat",
            "Grade": "grade_pl",
            "Group": "group_raw",
        }
    )
    pl["group"] = pl["group_raw"].astype(str).str.replace(r"\s*\d+", "", regex=True).str.strip()
    pl["treat"] = pd.to_numeric(pl["treat"], errors="coerce")
    pl["academycode"] = pd.to_numeric(pl["academycode"], errors="coerce")
    pl["studyid"] = pd.to_numeric(pl["studyid"], errors="coerce")
    pl = pl.dropna(subset=["academycode", "studyid", "treat"])

    treat_map = pl.drop_duplicates("academycode")[["academycode", "treat"]]
    rct_academies = set(treat_map["academycode"].unique())

    # 2) Core files.
    bl = _read_assessment(
        cfg["FILE_BL"],
        {
            "AcademyCode": "academycode",
            "StudyID": "studyid",
            "Score": "score_bl",
            "MaxScore": "maxscore_bl",
            "GradeName": "gradename",
            "Constituency1": "constituency",
            "County": "county",
            "Stream": "stream",
            "Enrolled_Date": "enrolled_date",
        },
    )
    bl["grade"] = extract_grade(bl["gradename"])
    bl["academycode"] = pd.to_numeric(bl["academycode"], errors="coerce")
    bl["studyid"] = pd.to_numeric(bl["studyid"], errors="coerce")
    bl["score_bl"] = pd.to_numeric(bl["score_bl"], errors="coerce")
    bl = bl[bl["academycode"].isin(rct_academies)].copy()

    el_num = _read_assessment(
        cfg["FILE_EL_NUM"],
        {
            "AcademyCode": "academycode",
            "StudyID": "studyid",
            "Score": "score_el",
            "MaxScore": "maxscore_el",
            "GradeName": "gradename",
            "Constituency1": "constituency",
            "County": "county",
        },
    )
    el_num["academycode"] = pd.to_numeric(el_num["academycode"], errors="coerce")
    el_num["studyid"] = pd.to_numeric(el_num["studyid"], errors="coerce")
    el_num["score_el"] = pd.to_numeric(el_num["score_el"], errors="coerce")
    el_num = el_num[el_num["academycode"].isin(rct_academies)].copy()

    el_math = _read_assessment(
        cfg["FILE_EL_MATH"],
        {
            "AcademyCode": "academycode",
            "StudyID": "studyid",
            "Score": "score_el_math",
            "MaxScore": "maxscore_el_math",
        },
    )
    el_math["academycode"] = pd.to_numeric(el_math["academycode"], errors="coerce")
    el_math["studyid"] = pd.to_numeric(el_math["studyid"], errors="coerce")
    el_math["score_el_math"] = pd.to_numeric(el_math["score_el_math"], errors="coerce")
    el_math = el_math[el_math["academycode"].isin(rct_academies)].copy()

    roster = pd.read_excel(cfg["FILE_ROSTER"])
    roster.columns = roster.columns.str.strip()
    roster = roster.rename(
        columns={
            "AcademyCode": "academycode",
            "StudyID": "studyid",
            "PlacementExamScore": "placement_score",
            "Gender": "gender",
            "GradeName": "gradename",
        }
    )
    roster["academycode"] = pd.to_numeric(roster["academycode"], errors="coerce")
    roster["studyid"] = pd.to_numeric(roster["studyid"], errors="coerce")
    roster["placement_score"] = pd.to_numeric(roster["placement_score"], errors="coerce")
    roster = roster[roster["academycode"].isin(rct_academies)].copy()

    # 3) Merge baseline-centric universe.
    df = bl[
        [
            "academycode",
            "studyid",
            "grade",
            "score_bl",
            "maxscore_bl",
            "constituency",
            "county",
            "stream",
            "enrolled_date",
        ]
    ].copy()

    df = df.merge(
        el_num[["studyid", "academycode", "score_el", "maxscore_el", "constituency", "county"]].drop_duplicates("studyid"),
        on="studyid",
        how="outer",
        suffixes=("", "_el"),
        indicator="_mel_num",
    )
    df["in_bl"] = df["_mel_num"] != "right_only"
    df["in_el"] = df["_mel_num"] != "left_only"
    df.drop(columns=["_mel_num"], inplace=True)

    # fill academy/geography from endline if needed
    df["academycode"] = df["academycode"].fillna(df["academycode_el"])
    df["constituency"] = df["constituency"].fillna(df["constituency_el"])
    df["county"] = df["county"].fillna(df["county_el"])
    df = df.drop(columns=["academycode_el", "constituency_el", "county_el"], errors="ignore")

    df = df.merge(el_math[["studyid", "score_el_math", "maxscore_el_math"]].drop_duplicates("studyid"), on="studyid", how="left")
    df = df.merge(roster[["studyid", "placement_score", "gender"]].drop_duplicates("studyid"), on="studyid", how="left")
    df = df.merge(pl[["studyid", "group"]].drop_duplicates("studyid"), on="studyid", how="left")
    df = df.merge(treat_map, on="academycode", how="left")

    # fill grade from endline gradename if baseline missing
    if df["grade"].isna().any():
        el_grade = el_num[["studyid", "gradename"]].drop_duplicates("studyid").copy()
        el_grade["grade_el"] = extract_grade(el_grade["gradename"])
        df["grade"] = df["grade"].fillna(df["studyid"].map(el_grade.set_index("studyid")["grade_el"]))

    # 4) Restrictions.
    print("\n--- Sample restriction log ---")
    print_sample_log("Starting merged dataset", len(df))

    df = df[df["academycode"].isin(rct_academies)].copy()
    print_sample_log("RCT academies only", len(df))

    df = df[df["grade"].isin([1, 2, 3])].copy()
    print_sample_log("Valid grade (P1-P3)", len(df))

    df = df[df["treat"].notna()].copy()
    print_sample_log("Non-missing treatment", len(df))

    if "stream" in df.columns:
        df = df[~(df["stream"] == "B")].copy()
        print_sample_log("Drop stream B", len(df))

    # Remove movers across academies.
    dup_mask = df.duplicated(subset=["studyid"], keep=False)
    dup_acad = df[dup_mask].groupby("studyid")["academycode"].nunique()
    movers = dup_acad[dup_acad > 1].index
    if len(movers) > 0:
        df = df[~df["studyid"].isin(movers)].copy()
        print_sample_log(f"Drop academy movers ({len(movers)})", len(df))
    df = df.drop_duplicates(subset=["studyid"], keep="first")
    print_sample_log("Deduplicated by studyid", len(df))

    # ensure treatment consistent at academy level
    mode_t = df.dropna(subset=["academycode", "treat"]).groupby("academycode")["treat"].agg(_mode_or_nan)
    df["treat"] = df["academycode"].map(mode_t).fillna(df["treat"])

    # 5) Construct analysis variables.
    df["has_bl"] = df["score_bl"].notna()
    df["has_el"] = df["score_el"].notna()
    df["g12"] = df["grade"].isin([1, 2]).astype(int)
    df["ggroup"] = df.groupby("academycode").ngroup()

    bl_counts = df.groupby("ggroup")["score_bl"].transform(lambda x: x.notna().sum())
    df["finsamp"] = df["has_bl"] & (bl_counts > 1)

    df["constituency"] = df["constituency"].fillna("Unknown").astype(str).str.strip()
    df["strata"] = df.groupby("constituency").ngroup()

    acad_treat = df.drop_duplicates("academycode")[["academycode", "treat", "strata"]]
    strata_pt = acad_treat.groupby("strata")["treat"].mean()
    df["P_t"] = df["strata"].map(strata_pt)
    df["P_c"] = 1 - df["P_t"]

    group_map = {"Red": 1, "Blue": 2, "Yellow": 3}
    df["std_grp"] = df["group"].map(group_map)
    missing_grp = df["std_grp"].isna() & df["score_bl"].notna()
    for g in [1, 2, 3]:
        g_mask = missing_grp & (df["grade"] == g)
        if g_mask.sum() > 0:
            scores = df.loc[g_mask, "score_bl"]
            try:
                df.loc[g_mask, "std_grp"] = pd.qcut(scores, q=3, labels=[1, 2, 3], duplicates="drop").astype(float)
            except ValueError:
                df.loc[g_mask, "std_grp"] = 1.0
    df["std_grp"] = df["std_grp"].fillna(1.0).astype(int)
    df["upper_group"] = (df["std_grp"] == 3).astype(float)

    ctrl = df["treat"] == 0
    df["std_score_bl"] = standardise_by_grade(df, "score_bl", ctrl)
    df["std_score_el"] = standardise_by_grade(df, "score_el", ctrl)
    df["std_score_el_math"] = standardise_by_grade(df, "score_el_math", ctrl)

    # Reliability and EB.
    r2_diag = {}
    for g in [1, 2, 3]:
        mask = ctrl & (df["grade"] == g) & df["score_bl"].notna() & df["score_el"].notna()
        if mask.sum() > 10:
            r2_diag[g] = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
        else:
            r2_diag[g] = 0.0

    r2_by_grade = {}
    for g in [2, 3]:
        g_ctrl = ctrl & (df["grade"] == g) & df["std_grp"].notna() & df["score_el"].notna()
        if g_ctrl.sum() > 20:
            r_obs = pearsonr(df.loc[g_ctrl, "std_grp"], df.loc[g_ctrl, "score_el"])[0]
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
        else:
            r2_by_grade[g] = r2_diag.get(g, 0.05)
    r2_by_grade[1] = max(r2_diag.get(1, 0.05), 0.05)

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

    # Peer and mechanism variables.
    df["peer_bl_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_score_bl")
    df["peer_bl_ctrl"] = leave_self_out_mean(df, ["academycode", "grade"], "std_score_bl")
    df["peer_eb_treat"] = leave_self_out_mean(df, ["academycode", "std_grp"], "std_eb")
    df["peer_eb_ctrl"] = leave_self_out_mean(df, ["academycode", "grade"], "std_eb")
    df["exp_peer_bl"] = df["P_t"] * df["peer_bl_treat"] + df["P_c"] * df["peer_bl_ctrl"]
    df["exp_peer_eb"] = df["P_t"] * df["peer_eb_treat"] + df["P_c"] * df["peer_eb_ctrl"]
    df["peer_bl"] = np.where(df["treat"] == 1, df["peer_bl_treat"], df["peer_bl_ctrl"])
    df["peer_eb"] = np.where(df["treat"] == 1, df["peer_eb_treat"], df["peer_eb_ctrl"])

    for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
        med = df.groupby(["academycode", grp_type])["std_eb"].transform("median")
        df[f"dist_med_{suffix}"] = (df["std_eb"] - med).abs()
        mn_eb = df.groupby(["academycode", grp_type])["std_eb"].transform("mean")
        df[f"dev_eb_{suffix}"] = (df["std_eb"] - mn_eb).abs()
        mn_el = df.groupby(["academycode", grp_type])["std_score_el"].transform("mean")
        df[f"dev_el_{suffix}"] = (df["std_score_el"] - mn_el).abs()
        df[f"csize_{suffix}"] = df.groupby(["academycode", grp_type])["studyid"].transform("count")
    df["dist_med"] = np.where(df["treat"] == 1, df["dist_med_treat"], df["dist_med_ctrl"])
    df["exp_dist_med"] = df["P_t"] * df["dist_med_treat"] + df["P_c"] * df["dist_med_ctrl"]
    df["dev_eb"] = np.where(df["treat"] == 1, df["dev_eb_treat"], df["dev_eb_ctrl"])
    df["exp_dev_eb"] = df["P_t"] * df["dev_eb_treat"] + df["P_c"] * df["dev_eb_ctrl"]
    df["dev_el"] = np.where(df["treat"] == 1, df["dev_el_treat"], df["dev_el_ctrl"])
    df["csize"] = np.where(df["treat"] == 1, df["csize_treat"], df["csize_ctrl"])
    df["exp_csize"] = df["P_t"] * df["csize_treat"] + df["P_c"] * df["csize_ctrl"]

    # Baseline decile and mismatch.
    df["bl_decile"] = np.nan
    for g in [1, 2, 3]:
        mask = (df["grade"] == g) & df["score_bl"].notna()
        if mask.sum() > 10:
            df.loc[mask, "bl_decile"] = pd.qcut(df.loc[mask, "score_bl"], q=10, labels=False, duplicates="drop") + 1
    has_bl = df["score_bl"].notna()
    eb_for_mean = df["std_eb"].where(has_bl)
    class_mean_treat = df.assign(_eb=eb_for_mean).groupby(["academycode", "std_grp"])["_eb"].transform("mean")
    class_mean_ctrl = df.assign(_eb=eb_for_mean).groupby(["academycode", "grade"])["_eb"].transform("mean")
    df["class_mean_eb"] = np.where(df["treat"] == 1, class_mean_treat, class_mean_ctrl)
    df["misfit"] = (df["std_eb"] - df["class_mean_eb"]) ** 2

    df["dist_from_cutoff"] = np.nan
    for g, cutoff in cfg["cutoffs"].items():
        mask = (df["grade"] == g) & df["score_bl"].notna()
        df.loc[mask, "dist_from_cutoff"] = (df.loc[mask, "score_bl"] - cutoff).abs()

    # Compatibility fields for shared scripts.
    df["exp0"] = 1
    df["exp1"] = 0
    df["exp2"] = 1
    df["g1"] = (df["grade"] == 1).astype(int)
    df["g2"] = (df["grade"] == 2).astype(int)
    df["g3"] = (df["grade"] == 3).astype(int)
    df["g4"] = 0
    df["in_ml"] = False
    for col in ["score_ml", "std_score_ml", "maxscore_ml", "acad_year", "pupilattendance", "lp_comp", "lp_opened", "tch_attn"]:
        if col not in df.columns:
            df[col] = np.nan

    # Save.
    keep_cols = [
        "academycode", "studyid", "grade", "stream", "county", "constituency", "ggroup", "strata", "acad_year", "g12",
        "treat", "P_t", "P_c", "upper_group", "std_grp", "score_bl", "score_ml", "score_el", "score_el_math",
        "maxscore_ml", "maxscore_el", "std_score_bl", "std_score_ml", "std_score_el", "std_score_el_math",
        "eb_ability", "std_eb", "peer_bl", "peer_bl_treat", "peer_bl_ctrl", "exp_peer_bl",
        "peer_eb", "peer_eb_treat", "peer_eb_ctrl", "exp_peer_eb",
        "dist_med", "dist_med_treat", "dist_med_ctrl", "exp_dist_med",
        "dev_el", "dev_el_treat", "dev_el_ctrl", "dev_eb", "dev_eb_treat", "dev_eb_ctrl", "exp_dev_eb",
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

    audit = pd.DataFrame(
        [
            {"metric": "rows", "value": len(df)},
            {"metric": "schools", "value": df["academycode"].nunique()},
            {"metric": "students", "value": df["studyid"].nunique()},
            {"metric": "final_sample_finsamp", "value": int(df["finsamp"].sum())},
            {"metric": "finsamp_with_endline_numeracy", "value": int((df["finsamp"] & df["has_el"]).sum())},
            {"metric": "finsamp_with_endline_math", "value": int((df["finsamp"] & df["score_el_math"].notna()).sum())},
            {"metric": "treated_schools", "value": int(df.loc[df["treat"] == 1, "academycode"].nunique())},
            {"metric": "control_schools", "value": int(df.loc[df["treat"] == 0, "academycode"].nunique())},
        ]
    )
    audit.to_csv(OUT / "ng_cleaning_audit.csv", index=False)

    print("\nSaved:")
    print(f"  {cfg['ANALYSIS_FILE']}")
    print(f"  {OUT / 'ng_cleaning_audit.csv'}")
    print(f"Rows={len(df):,}, cols={len(df.columns)}")


if __name__ == "__main__":
    main()
