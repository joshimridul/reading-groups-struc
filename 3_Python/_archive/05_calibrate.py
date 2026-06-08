#!/usr/bin/env python3
"""
05_calibrate.py — Phase 5: Calibrate the model.

Back out ρ (reliability of the baseline diagnostic) and compare to the
threshold ρ* below which tracking harms students.

Key idea:
  - Tracking helps only if the diagnostic is informative enough.
  - With perfect tests (ρ=1), tracking always reduces mismatch.
  - With pure noise (ρ=0), tracking randomly reshuffles students → no gain
    but disruption and new peer groups.
  - There is a threshold ρ* where the benefits balance the costs.

Produces:
  output/table5_calibration.txt     — ρ estimates and threshold
  output/fig5_rho_threshold.pdf     — ρ vs ρ* diagram
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from config import ANALYSIS_FILE, OUT, CUTOFF_G12, CUTOFF_G34
from utils import ols_cluster

print("=" * 70)
print("Phase 5: Model calibration")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df = df[df["finsamp"] == True].copy()
ctrl = df["treat"] == 0

# ═════════════════════════════════════════════════════════════════════════════
# 1. ESTIMATE ρ — reliability of the baseline diagnostic
# ═════════════════════════════════════════════════════════════════════════════
#
# Method 1: Test-retest R² — cor(BL, ML)² in control group
# Method 2: Correlation coefficient cor(BL, ML) as ρ (assumes equal reliability)
# Method 3: Regression BL on ML, adjusted for measurement error
#
# The "true" ρ = Var(θ)/Var(s). Under classical measurement error with
# s = θ + u, ρ = 1 - σ²_u/σ²_s. The BL-ML correlation gives:
#   cor(BL, ML) = σ²_θ / (σ²_s_BL × σ²_s_ML)^{1/2}
# If BL and ML have similar noise levels, cor(BL,ML) ≈ ρ.

print("\n--- Estimating ρ by grade ---\n")

rho_rows = []
for g in [1, 2, 3, 4]:
    g_ctrl = ctrl & (df["grade"] == g)

    # Method 1: BL-EL R²
    mask = g_ctrl & df["score_bl"].notna() & df["score_el"].notna()
    if mask.sum() > 10:
        r2_bl_el = df.loc[mask, "score_bl"].corr(df.loc[mask, "score_el"]) ** 2
    else:
        r2_bl_el = np.nan

    # Method 2: BL-ML correlation
    mask_ml = g_ctrl & df["score_bl"].notna() & df["score_ml"].notna()
    if mask_ml.sum() > 10:
        rho_bl_ml = df.loc[mask_ml, "score_bl"].corr(df.loc[mask_ml, "score_ml"])
    else:
        rho_bl_ml = np.nan

    # Method 3: Disattenuated correlation
    # If cor(BL, ML) ≈ ρ_BL × ρ_ML under equal noise, then ρ ≈ sqrt(cor(BL,ML))
    # is an approximation when one test is noisier than the other.
    # But cor(BL,ML) is already a reasonable lower bound on ρ.
    rho_disattn = np.sqrt(abs(rho_bl_ml)) if not np.isnan(rho_bl_ml) else np.nan

    rho_rows.append({
        "Grade": g,
        "R²(BL→EL)": r2_bl_el,
        "cor(BL,ML) [ρ̂ lower bound]": rho_bl_ml,
        "√cor(BL,ML) [ρ̂ geometric]": rho_disattn,
        "N_ctrl": mask.sum(),
    })
    print(f"  Grade {g}: R²(BL→EL)={r2_bl_el:.4f}  "
          f"cor(BL,ML)={rho_bl_ml:.4f}  "
          f"ρ_geom={rho_disattn:.4f}")

rho_df = pd.DataFrame(rho_rows)

# Overall ρ (pooled across grades)
mask_all = ctrl & df["score_bl"].notna() & df["score_ml"].notna()
rho_pooled = df.loc[mask_all, "std_score_bl"].corr(df.loc[mask_all, "std_score_ml"])
print(f"\n  Pooled cor(std_BL, std_ML): {rho_pooled:.4f}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. ESTIMATE ρ* — threshold reliability
# ═════════════════════════════════════════════════════════════════════════════
#
# Under the theoretical model (see SPECIFICATIONS.md, Phase 5):
# Tracking is beneficial when it reduces total mismatch.
#
# A simple calibration:
# Mismatch reduction ∝ ρ × Var(between-group ability) - (1-ρ) × Var(misclassification)
# Tracking helps when ρ > ρ* where:
#   ρ* ≈ 1 - (Var_between / Var_total) under certain assumptions
#
# We compute this from the data.

print("\n--- Threshold calibration ---")

# Between-group variance as fraction of total
# Under treatment, groups are split at the cutoff
# Variance decomposition: Var(s) = Var_between(groups) + Var_within(groups)
for exp_name, exp_col, cutoff in [("G3-4", "exp1", CUTOFF_G34),
                                   ("G1-2", "exp2", CUTOFF_G12)]:
    sub = df[(df[exp_col] == 1) & df["score_bl"].notna()].copy()
    var_total = sub["score_bl"].var()
    group_means = sub.groupby("upper_group")["score_bl"].mean()
    group_sizes = sub.groupby("upper_group")["score_bl"].count()
    grand_mean = sub["score_bl"].mean()
    var_between = sum(group_sizes[g] * (group_means[g] - grand_mean)**2
                      for g in group_means.index) / len(sub)
    var_within = var_total - var_between
    share_between = var_between / var_total

    # rho* ≈ share_within (tracking helps when ρ > var_within/var_total)
    rho_star = var_within / var_total

    rho_hat = rho_df.loc[rho_df["Grade"].isin([3, 4] if exp_name == "G3-4" else [1, 2]),
                         "cor(BL,ML) [ρ̂ lower bound]"].mean()

    print(f"  {exp_name}: Var_between/Var_total={share_between:.3f}  "
          f"ρ*={rho_star:.3f}  ρ̂={rho_hat:.3f}  "
          f"{'ρ < ρ* → tracking HURTS' if rho_hat < rho_star else 'ρ > ρ* → tracking helps'}")

# ═════════════════════════════════════════════════════════════════════════════
# 3. ACCOUNTING DECOMPOSITION
# ═════════════════════════════════════════════════════════════════════════════
#
# Check: does β_P·ΔP + β_M·ΔM + β_C·ΔC ≈ β_ITT?
# (This was also done in Phase 4; here we add ρ-based interpretation.)

print("\n--- Effect decomposition with reliability interpretation ---")

for label, exp_col in [("Stacked", "exp0"), ("G3-4", "exp1"), ("G1-2", "exp2")]:
    sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
    sub = sub.dropna(subset=["peer_eb", "dist_med", "csize",
                              "exp_peer_eb", "exp_dist_med", "exp_csize",
                              "std_eb", "P_t"])

    X = sub[["peer_eb", "dist_med", "csize",
             "exp_peer_eb", "exp_dist_med", "exp_csize",
             "std_eb", "P_t"]].copy()
    res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

    t = sub["treat"] == 1
    contrib_P = res.params["peer_eb"] * (sub.loc[t, "peer_eb"].mean() - sub.loc[~t, "peer_eb"].mean())
    contrib_M = res.params["dist_med"] * (sub.loc[t, "dist_med"].mean() - sub.loc[~t, "dist_med"].mean())
    contrib_C = res.params["csize"] * (sub.loc[t, "csize"].mean() - sub.loc[~t, "csize"].mean())
    total = contrib_P + contrib_M + contrib_C

    print(f"  {label:15s}  peers={contrib_P:+.3f}  "
          f"mismatch={contrib_M:+.3f}  size={contrib_C:+.3f}  "
          f"total={total:+.3f}")

# Save calibration table
rho_df.to_csv(OUT / "table5_calibration.txt", sep="\t", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 5: ρ vs ρ* diagram
# ═════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(7, 5))

grades = [1, 2, 3, 4]
rho_vals = rho_df["cor(BL,ML) [ρ̂ lower bound]"].values
ax.bar(grades, rho_vals, color="steelblue", alpha=0.7, label="Estimated ρ")

# Add ρ* lines
for exp_col, cutoff, grades_in, color in [
    ("exp1", CUTOFF_G34, [3, 4], "darkred"),
    ("exp2", CUTOFF_G12, [1, 2], "darkorange"),
]:
    sub = df[(df[exp_col] == 1) & df["score_bl"].notna()]
    var_total = sub["score_bl"].var()
    var_within = sub.groupby("upper_group")["score_bl"].transform(
        lambda x: (x - x.mean())**2).mean()
    rho_star = var_within / var_total
    for g in grades_in:
        ax.axhline(rho_star, xmin=(g - 0.6) / 5, xmax=(g + 0.4) / 5,
                    color=color, ls="--", lw=2)
    ax.plot([], [], color=color, ls="--", lw=2,
            label=f"ρ* (G{grades_in[0]}-{grades_in[1]})")

ax.set_xlabel("Grade")
ax.set_ylabel("Reliability")
ax.set_title("Baseline test reliability ρ̂ vs threshold ρ*")
ax.set_xticks(grades)
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "fig5_rho_threshold.pdf")
plt.close()
print(f"\n  → Figure saved to {OUT / 'fig5_rho_threshold.pdf'}")

print("\n✓ Phase 5 complete")
