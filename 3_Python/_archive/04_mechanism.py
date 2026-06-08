#!/usr/bin/env python3
"""
04_mechanism.py — Phase 4: Borusyak-Hull mechanism analysis.

The key identification insight:
  Selection into tracks operates through observed scores s, not true ability θ.
  We condition on E[P|s, T], which is computable from the assignment mechanism.
  Under scripted instruction, mismatch M is absorbed by controls.
  This lets us identify peer effects β_P separately.

Specification:
  Y_i = α + β_P·P_i + β_M·M_i + β_C·C_i
        + γ_P·E[P_i] + γ_M·E[M_i] + γ_C·E[C_i]
        + δ·θ̂_i^EB + λ·p_t + ε_i

where E[·] conditions on (s_i, academy, grade) — computed in 00_clean.py.

Produces:
  output/table4_mechanism.txt          — main mechanism table
  output/table4_mechanism_separate.txt — one channel at a time
  output/table4_dispersion.txt         — effect on within-class dispersion
"""

import pandas as pd
import numpy as np
from config import ANALYSIS_FILE, OUT
from utils import ols_cluster, coef_str, se_str

print("=" * 70)
print("Phase 4: Borusyak-Hull mechanism analysis")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df = df[df["finsamp"] == True].copy()

experiments = [
    ("Stacked",    "exp0"),
    ("Grades 3-4", "exp1"),
    ("Grades 1-2", "exp2"),
]

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 4a: Full structural model (all three channels)
# ═════════════════════════════════════════════════════════════════════════════
#
# Y = β_P·P + β_M·M + β_C·C + γ_P·E[P] + γ_M·E[M] + γ_C·E[C] + δ·θ̂ + λ·p_t
#
# P  = realised peer EB ability (leave-self-out mean)
# M  = realised distance from median instruction (|θ̂ - median(θ̂) in group|)
# C  = realised class size
# E[·] = Borusyak-Hull conditioning: expected value under the assignment mechanism

print("\n--- Table 4a: Full structural model ---\n")

full_rows = []
for label, exp_col in experiments:
    sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()

    # Drop rows where mechanism variables are missing
    mech_vars = ["peer_eb", "dist_med", "csize",
                 "exp_peer_eb", "exp_dist_med", "exp_csize",
                 "std_eb", "P_t"]
    sub = sub.dropna(subset=mech_vars + ["std_score_el"])

    X = sub[mech_vars].copy()
    res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

    row = {"Sample": label, "N": f"{len(sub):,d}"}
    for v in ["peer_eb", "dist_med", "csize"]:
        row[f"β({v})"] = coef_str(res, v)
        row[f"se({v})"] = se_str(res, v)

    full_rows.append(row)
    print(f"  {label:15s}  β_P={coef_str(res, 'peer_eb'):>10s}  "
          f"β_M={coef_str(res, 'dist_med'):>10s}  "
          f"β_C={coef_str(res, 'csize'):>10s}  N={len(sub):,d}")

pd.DataFrame(full_rows).to_csv(OUT / "table4_mechanism.txt", sep="\t", index=False)
print(f"\n  → Saved to {OUT / 'table4_mechanism.txt'}")

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 4b: One channel at a time (to check sensitivity)
# ═════════════════════════════════════════════════════════════════════════════
#
# Run the Borusyak-Hull specification with each channel individually.
# This shows whether results change when we include/exclude other channels.

print("\n--- Table 4b: Channels separately ---\n")

channels = [
    ("Peer ability",         "peer_eb",  "exp_peer_eb"),
    ("Distance from median", "dist_med", "exp_dist_med"),
    ("Class size",           "csize",    "exp_csize"),
]

sep_rows = []
for ch_label, var, exp_var in channels:
    for label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
        sub = sub.dropna(subset=[var, exp_var, "std_eb", "P_t", "std_score_el"])

        X = sub[[var, exp_var, "std_eb", "P_t"]].copy()
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

        sep_rows.append({
            "Channel": ch_label,
            "Sample": label,
            "Coef": coef_str(res, var),
            "SE": se_str(res, var),
            "N": f"{len(sub):,d}",
        })
        print(f"  {ch_label:25s} | {label:15s}  β={coef_str(res, var):>10s}  "
              f"{se_str(res, var):>10s}")

pd.DataFrame(sep_rows).to_csv(OUT / "table4_mechanism_separate.txt",
                               sep="\t", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 4c: Effect on within-class dispersion
# ═════════════════════════════════════════════════════════════════════════════
#
# Outcome: |Y_i - Ȳ_group| = absolute deviation from classroom mean
# This tests whether tracking reduced or increased within-class heterogeneity.
# Two versions: using EB ability (pre-treatment) and actual endline (post-treatment).

print("\n--- Table 4c: Effect on within-class dispersion ---\n")

disp_outcomes = [
    ("Dispersion (EB ability)", "dev_eb"),
    ("Dispersion (endline)",    "dev_el"),
]

disp_rows = []
for out_label, out_var in disp_outcomes:
    for label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df[out_var].notna()].copy()
        sub = sub.dropna(subset=["P_t"])

        X = sub[["treat", "P_t"]].copy()
        res = ols_cluster(sub[out_var], X, sub["ggroup"])

        ctrl_mean = sub.loc[sub["treat"] == 0, out_var].mean()
        disp_rows.append({
            "Outcome": out_label,
            "Sample": label,
            "Control mean": f"{ctrl_mean:.3f}",
            "Coef": coef_str(res, "treat"),
            "SE": se_str(res, "treat"),
            "N": f"{len(sub):,d}",
        })
        print(f"  {out_label:30s} | {label:15s}  ctrl={ctrl_mean:.3f}  "
              f"β={coef_str(res, 'treat'):>10s}  {se_str(res, 'treat'):>10s}")

pd.DataFrame(disp_rows).to_csv(OUT / "table4_dispersion.txt", sep="\t", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# DECOMPOSITION CHECK: does β_P·ΔP + β_M·ΔM + β_C·ΔC ≈ β_ITT?
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Decomposition check ---")
for label, exp_col in experiments:
    sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
    sub = sub.dropna(subset=["peer_eb", "dist_med", "csize",
                              "exp_peer_eb", "exp_dist_med", "exp_csize",
                              "std_eb", "P_t"])

    # Structural estimates
    X = sub[["peer_eb", "dist_med", "csize",
             "exp_peer_eb", "exp_dist_med", "exp_csize",
             "std_eb", "P_t"]].copy()
    res_s = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

    # Mean change in each channel (treated - control)
    t = sub["treat"] == 1
    delta_P = sub.loc[t, "peer_eb"].mean() - sub.loc[~t, "peer_eb"].mean()
    delta_M = sub.loc[t, "dist_med"].mean() - sub.loc[~t, "dist_med"].mean()
    delta_C = sub.loc[t, "csize"].mean() - sub.loc[~t, "csize"].mean()

    # Predicted ITT from structural model
    predicted_itt = (res_s.params["peer_eb"] * delta_P +
                     res_s.params["dist_med"] * delta_M +
                     res_s.params["csize"] * delta_C)

    # Actual ITT
    X_rf = sub[["treat", "std_eb", "P_t"]].copy()
    res_rf = ols_cluster(sub["std_score_el"], X_rf, sub["ggroup"])
    actual_itt = res_rf.params["treat"]

    print(f"  {label:15s}  predicted={predicted_itt:7.3f}  "
          f"actual={actual_itt:7.3f}  "
          f"(ΔP={delta_P:.3f}  ΔM={delta_M:.3f}  ΔC={delta_C:.1f})")

print("\n✓ Phase 4 complete")
