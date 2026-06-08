#!/usr/bin/env python3
"""
01_reduced_form.py — Phase 1: Reduced-form ITT effects.

Bulletproof estimates that rely only on random assignment.
No structural assumptions, no peer variables — just Y = α + β T + controls.

Produces:
  output/table1_itt.txt          — main ITT table
  output/table1_itt_upper.txt    — effects by upper/lower group
"""

import pandas as pd
import numpy as np
from config import ANALYSIS_FILE, OUT
from utils import ols_cluster, coef_str, se_str, stars

print("=" * 70)
print("Phase 1: Reduced-form ITT effects")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df = df[df["finsamp"] == True].copy()
print(f"Analysis sample: {len(df):,d} students")

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 1: Average treatment effects on endline scores
# ═════════════════════════════════════════════════════════════════════════════
#
# Specification:
#   std_score_el = α + β·treat + γ·std_eb + δ·P_t + ε
#
# Stata equivalent:
#   reg std_score_el treat std_pred_eb P_t, vce(clus ggroup)

print("\n--- Table 1: ITT effects on standardised endline scores ---\n")

experiments = [
    ("Stacked",    "exp0"),
    ("Grades 3-4", "exp1"),
    ("Grades 1-2", "exp2"),
]

rows = []
for label, exp_col in experiments:
    sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()

    # Control mean
    ctrl_mean = sub.loc[sub["treat"] == 0, "std_score_el"].mean()
    ctrl_n = (sub["treat"] == 0).sum()

    # Regression
    X = sub[["treat", "std_eb", "P_t"]].copy()
    res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

    b = coef_str(res, "treat")
    se = se_str(res, "treat")
    N = len(sub)

    rows.append({
        "Sample": label,
        "Control mean": f"{ctrl_mean:.3f}",
        "Coef": b,
        "SE": se,
        "N": f"{N:,d}",
    })
    print(f"  {label:15s}  ctrl_mean={ctrl_mean:7.3f}  β={b:>10s}  {se:>10s}  N={N:,d}")

results_df = pd.DataFrame(rows)
results_df.to_csv(OUT / "table1_itt.txt", sep="\t", index=False)
print(f"\n  → Saved to {OUT / 'table1_itt.txt'}")

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 1b: Effects by upper / lower group placement
# ═════════════════════════════════════════════════════════════════════════════
#
# Specification:
#   std_score_el = α + β₁·treat + β₂·treat×upper + β₃·upper + δ·P_t + ε
#
# β₁ = effect on lower group
# β₁ + β₂ = effect on upper group (test: lincom treat + treat×upper)

print("\n--- Table 1b: Effects by upper/lower group ---\n")

rows2 = []
for label, exp_col in experiments:
    sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
    sub["treat_x_upper"] = sub["treat"] * sub["upper_group"]

    X = sub[["treat", "treat_x_upper", "upper_group", "std_eb", "P_t"]].copy()
    res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

    # Linear combination: treat + treat_x_upper = effect on upper group
    b_upper = res.params["treat"] + res.params["treat_x_upper"]
    se_upper = np.sqrt(
        res.cov_params().loc["treat", "treat"] +
        res.cov_params().loc["treat_x_upper", "treat_x_upper"] +
        2 * res.cov_params().loc["treat", "treat_x_upper"]
    )
    t_upper = b_upper / se_upper
    p_upper = 2 * (1 - __import__("scipy").stats.t.cdf(abs(t_upper), res.df_resid))

    row = {
        "Sample": label,
        "Treatment": coef_str(res, "treat"),
        "SE(Treatment)": se_str(res, "treat"),
        "Treat × Upper": coef_str(res, "treat_x_upper"),
        "SE(Treat × Upper)": se_str(res, "treat_x_upper"),
        "Upper group": coef_str(res, "upper_group"),
        "SE(Upper)": se_str(res, "upper_group"),
        "Effect on upper (p)": f"{p_upper:.3f}",
        "N": f"{len(sub):,d}",
    }
    rows2.append(row)
    print(f"  {label:15s}  treat={coef_str(res, 'treat'):>10s}  "
          f"treat×upper={coef_str(res, 'treat_x_upper'):>10s}  "
          f"upper_effect={b_upper:.3f} (p={p_upper:.3f})")

pd.DataFrame(rows2).to_csv(OUT / "table1_itt_upper.txt", sep="\t", index=False)
print(f"\n  → Saved to {OUT / 'table1_itt_upper.txt'}")

print("\n✓ Phase 1 complete")
