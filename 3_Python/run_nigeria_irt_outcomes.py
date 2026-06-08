from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path("/Users/mriduljoshi/Github/AbilityGrouping")
RAW = ROOT / "2_Data/1_Raw/P123 Numeracy Groups"
OUT = ROOT / "2_Data/2_Cleaned/Nigeria"


def logistic(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


def parse_gender_to_female(s: pd.Series) -> pd.Series:
    sval = s.astype(str).str.strip().str.lower()
    return np.where(sval.str.startswith("f"), 1.0, np.where(s.isna(), np.nan, 0.0))


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    sd = s.std(skipna=True)
    if pd.isna(sd) or sd == 0:
        return s * 0
    return (s - s.mean(skipna=True)) / sd


def ability_from_score(score: float, b: np.ndarray, lo: float = -6.0, hi: float = 6.0) -> float:
    if np.isnan(score):
        return np.nan
    n_items = b.shape[0]
    if score <= 0:
        return lo
    if score >= n_items:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        expected = logistic(mid - b).sum()
        if expected > score:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Item-level T3 ETE numeracy data
    item_path = OUT / "ng_itemlevel_t3_ete_numeracy.dta"
    item = pd.read_stata(item_path, convert_categoricals=False)
    item.columns = [c.strip().lower() for c in item.columns]
    item["studyid"] = pd.to_numeric(item["studyid"], errors="coerce")
    item["academycode"] = pd.to_numeric(item["academycode"], errors="coerce")
    item["treatment"] = pd.to_numeric(item["treatment"], errors="coerce")

    item_cols = [c for c in item.columns if c.startswith("q") and c.endswith("_a")]
    item[item_cols] = item[item_cols].apply(pd.to_numeric, errors="coerce")

    # Use control group to calibrate item difficulty (Rasch 1PL anchor)
    ctrl = item[item["treatment"] == 0].copy()
    p_j = ctrl[item_cols].mean(axis=0, skipna=True).clip(0.01, 0.99)
    b_j = -np.log(p_j / (1.0 - p_j)).to_numpy()

    # Person total scores on observed items and latent ability
    item["n_answered"] = item[item_cols].notna().sum(axis=1)
    item["raw_total"] = item[item_cols].sum(axis=1, skipna=True)
    # Rescale partial completion to 50-item equivalent score before inversion.
    item["raw_total_eq50"] = np.where(
        item["n_answered"] > 0,
        item["raw_total"] * (len(item_cols) / item["n_answered"]),
        np.nan,
    )
    item["theta_irt"] = item["raw_total_eq50"].apply(lambda s: ability_from_score(float(s), b_j))

    # Standardize IRT ability relative to control group
    m0 = item.loc[item["treatment"] == 0, "theta_irt"].mean(skipna=True)
    sd0 = item.loc[item["treatment"] == 0, "theta_irt"].std(skipna=True)
    item["theta_irt_z"] = (item["theta_irt"] - m0) / sd0

    # Bring covariates from master T3 ETE numeracy
    t3 = pd.read_excel(RAW / "term 3/Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Numeracy).xlsx")
    t3.columns = [c.strip().lower() for c in t3.columns]
    t3 = t3.rename(columns={"constituency1": "constituency", "gradename": "gradename"})
    t3["studyid"] = pd.to_numeric(t3["studyid"], errors="coerce")
    t3["academycode"] = pd.to_numeric(t3["academycode"], errors="coerce")
    t3["treatment"] = pd.to_numeric(t3["treatment"], errors="coerce")
    keep = ["studyid", "academycode", "treatment", "constituency", "county", "gradename"]
    t3 = t3[keep].dropna(subset=["studyid"]).sort_values("studyid").drop_duplicates("studyid")

    # Baseline precision controls
    bl = pd.read_excel(RAW / "term 2/Assessment Scores by Pupil - MASTER v2 (P123 T1 ETE Maths).xlsx")
    bl.columns = [c.strip().lower() for c in bl.columns]
    bl["studyid"] = pd.to_numeric(bl["studyid"], errors="coerce")
    bl["score_bl"] = pd.to_numeric(bl["score"], errors="coerce")
    bl = bl[["studyid", "score_bl"]].dropna(subset=["studyid"]).sort_values("studyid").drop_duplicates("studyid")
    bl["score_bl_z"] = zscore(bl["score_bl"])

    r2 = pd.read_excel(RAW / "term 2/Roster of Pupils (P123 T2).xlsx")
    r3 = pd.read_excel(RAW / "term 3/Roster of Pupils (P123 T3).xlsx")
    for r in (r2, r3):
        r.columns = [c.strip().lower() for c in r.columns]
        r["studyid"] = pd.to_numeric(r["studyid"], errors="coerce")
        r["placement_score"] = pd.to_numeric(r["placementexamscore"], errors="coerce")
    ros = pd.concat(
        [
            r2[["studyid", "placement_score", "gender"]],
            r3[["studyid", "placement_score", "gender"]],
        ],
        ignore_index=True,
    )
    ros = (
        ros.sort_values("studyid")
        .groupby("studyid", as_index=False)
        .agg(
            placement_score=("placement_score", lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan),
            gender=("gender", lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan),
        )
    )
    ros["placement_score_z"] = zscore(ros["placement_score"])
    ros["female"] = parse_gender_to_female(ros["gender"])

    df = (
        item[["studyid", "academycode", "treatment", "n_answered", "raw_total", "raw_total_eq50", "theta_irt", "theta_irt_z"]]
        .merge(t3, on=["studyid", "academycode", "treatment"], how="inner")
        .merge(bl[["studyid", "score_bl_z"]], on="studyid", how="left")
        .merge(ros[["studyid", "placement_score_z", "female"]], on="studyid", how="left")
    )

    # Save student-level IRT outcome file
    out_students = OUT / "ng_t3_ete_numeracy_irt_student.csv"
    df.to_csv(out_students, index=False)

    # Treatment effect regressions
    rows: list[dict[str, float | str | int]] = []

    d1 = df.dropna(subset=["theta_irt_z", "treatment", "academycode"])
    m1 = smf.ols("theta_irt_z ~ treatment + C(constituency) + C(gradename)", data=d1).fit(
        cov_type="cluster", cov_kwds={"groups": d1["academycode"]}
    )
    rows.append(
        {
            "spec": "irt_t3_treat_fe",
            "coef_term": "treatment",
            "coef": float(m1.params["treatment"]),
            "se": float(m1.bse["treatment"]),
            "p_value": float(m1.pvalues["treatment"]),
            "n_rows": int(len(d1)),
            "n_students": int(d1["studyid"].nunique()),
            "n_schools": int(d1["academycode"].nunique()),
        }
    )

    d2 = df.dropna(subset=["theta_irt_z", "treatment", "academycode", "score_bl_z", "placement_score_z", "female"])
    m2 = smf.ols(
        "theta_irt_z ~ treatment + score_bl_z + placement_score_z + female + C(constituency) + C(gradename)",
        data=d2,
    ).fit(cov_type="cluster", cov_kwds={"groups": d2["academycode"]})
    rows.append(
        {
            "spec": "irt_t3_treat_fe_precision",
            "coef_term": "treatment",
            "coef": float(m2.params["treatment"]),
            "se": float(m2.bse["treatment"]),
            "p_value": float(m2.pvalues["treatment"]),
            "n_rows": int(len(d2)),
            "n_students": int(d2["studyid"].nunique()),
            "n_schools": int(d2["academycode"].nunique()),
        }
    )

    out_reg = OUT / "ng_irt_regressions_t3_ete_numeracy.csv"
    pd.DataFrame(rows).to_csv(out_reg, index=False)

    out_note = OUT / "ng_irt_regressions_t3_ete_numeracy_note.md"
    with open(out_note, "w", encoding="utf-8") as f:
        f.write("# Nigeria T3 ETE Numeracy IRT outcomes\n\n")
        f.write("- Outcome uses a Rasch-style 1PL IRT score built from 50 item indicators (`q*_a`).\n")
        f.write("- Item difficulties are calibrated on the control group, then person ability is standardized by control-group mean/SD.\n")
        f.write("- SEs are clustered at academy level.\n\n")
        for r in rows:
            f.write(
                f"- {r['spec']}: coef={r['coef']:.4f}, se={r['se']:.4f}, p={r['p_value']:.4f}, "
                f"N={r['n_rows']}, students={r['n_students']}, schools={r['n_schools']}\n"
            )

    print("Wrote:", out_students)
    print("Wrote:", out_reg)
    print("Wrote:", out_note)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
