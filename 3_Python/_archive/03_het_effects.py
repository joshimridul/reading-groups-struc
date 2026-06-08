#!/usr/bin/env python3
"""
03_het_effects.py — Phase 3: Treatment effect heterogeneity τ(s).

How does the ITT vary with baseline score? This is the key plot.

Produces:
  output/fig3_tau_s.pdf               — τ(s) by decile, with CIs
  output/fig3_tau_s_by_experiment.pdf  — same, separate panels for G12/G34
  output/table3_quartile_effects.txt  — effects by quartile
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from config import ANALYSIS_FILE, OUT
from utils import ols_cluster, coef_str, se_str

print("=" * 70)
print("Phase 3: Treatment effect heterogeneity τ(s)")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df = df[df["finsamp"] == True].copy()

# ═════════════════════════════════════════════════════════════════════════════
# 1. NON-PARAMETRIC: τ(s) by decile
# ═════════════════════════════════════════════════════════════════════════════
#
# Within each grade, split students into deciles of baseline score.
# Estimate ITT within each decile.

print("\n--- τ(s) by decile (within grade) ---\n")

# Create within-grade deciles
# Stata: bys grade: xtile bl_q = std_score_bl, nq(10)
df["bl_decile"] = np.nan
for g in [1, 2, 3, 4]:
    mask = (df["grade"] == g) & df["std_score_bl"].notna()
    df.loc[mask, "bl_decile"] = pd.qcut(
        df.loc[mask, "std_score_bl"], q=10, labels=False, duplicates="drop"
    ) + 1  # 1-indexed

# Estimate ITT by decile (stacked)
decile_results = []
for d in sorted(df["bl_decile"].dropna().unique()):
    sub = df[(df["bl_decile"] == d) & df["std_score_el"].notna()].copy()
    if len(sub) < 20 or sub["treat"].nunique() < 2:
        continue
    X = sub[["treat", "P_t"]].copy()
    try:
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        decile_results.append({
            "decile": d,
            "coef": res.params["treat"],
            "se": res.bse["treat"],
            "ci_lo": res.params["treat"] - 1.96 * res.bse["treat"],
            "ci_hi": res.params["treat"] + 1.96 * res.bse["treat"],
            "N": len(sub),
            "mean_bl": sub["std_score_bl"].mean(),
        })
        print(f"  Decile {d:2.0f}: β={res.params['treat']:7.3f} "
              f"({res.bse['treat']:.3f})  N={len(sub):,d}")
    except Exception as e:
        print(f"  Decile {d:2.0f}: FAILED — {e}")

dec_df = pd.DataFrame(decile_results)

# ── Plot: τ(s) ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.errorbar(dec_df["decile"], dec_df["coef"],
            yerr=1.96 * dec_df["se"],
            fmt="o-", color="steelblue", capsize=4, lw=2, markersize=6)
ax.axhline(0, color="gray", ls="--", lw=1)
ax.set_xlabel("Baseline score decile (within grade)")
ax.set_ylabel("Treatment effect (std. endline score)")
ax.set_title("τ(s): Treatment effect by baseline ability")
ax.set_xticks(dec_df["decile"].values)
fig.tight_layout()
fig.savefig(OUT / "fig3_tau_s.pdf")
plt.close()
print(f"\n  → Figure saved to {OUT / 'fig3_tau_s.pdf'}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. τ(s) by experiment (G3-4 and G1-2 separately)
# ═════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for idx, (label, exp_col) in enumerate([("Grades 3-4", "exp1"), ("Grades 1-2", "exp2")]):
    ax = axes[idx]
    sub_exp = df[(df[exp_col] == 1)].copy()

    # Deciles within this experiment
    sub_exp["dec"] = np.nan
    for g in sub_exp["grade"].unique():
        mask = (sub_exp["grade"] == g) & sub_exp["std_score_bl"].notna()
        sub_exp.loc[mask, "dec"] = pd.qcut(
            sub_exp.loc[mask, "std_score_bl"], q=10, labels=False, duplicates="drop"
        ) + 1

    exp_results = []
    for d in sorted(sub_exp["dec"].dropna().unique()):
        sub = sub_exp[(sub_exp["dec"] == d) & sub_exp["std_score_el"].notna()]
        if len(sub) < 15 or sub["treat"].nunique() < 2:
            continue
        X = sub[["treat", "P_t"]].copy()
        try:
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            exp_results.append({
                "decile": d,
                "coef": res.params["treat"],
                "se": res.bse["treat"],
            })
        except Exception:
            pass

    if exp_results:
        edf = pd.DataFrame(exp_results)
        ax.errorbar(edf["decile"], edf["coef"], yerr=1.96 * edf["se"],
                    fmt="o-", color="steelblue", capsize=4, lw=2, markersize=5)
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Baseline score decile")
    ax.set_title(label)
    ax.set_ylabel("Treatment effect (std. EL)")

fig.suptitle("τ(s) by experiment", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT / "fig3_tau_s_by_experiment.pdf")
plt.close()
print(f"  → Figure saved to {OUT / 'fig3_tau_s_by_experiment.pdf'}")

# ═════════════════════════════════════════════════════════════════════════════
# 3. TABLE: Effects by quartile (parametric)
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Effects by baseline quartile ---\n")

df["bl_quartile"] = np.nan
for g in [1, 2, 3, 4]:
    mask = (df["grade"] == g) & df["std_score_bl"].notna()
    df.loc[mask, "bl_quartile"] = pd.qcut(
        df.loc[mask, "std_score_bl"], q=4, labels=False, duplicates="drop"
    ) + 1

q_rows = []
for q in [1, 2, 3, 4]:
    sub = df[(df["bl_quartile"] == q) & df["std_score_el"].notna()].copy()
    if len(sub) < 20:
        continue
    X = sub[["treat", "std_eb", "P_t"]].copy()
    try:
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        q_rows.append({
            "Quartile": f"Q{q}",
            "Coef": coef_str(res, "treat"),
            "SE": se_str(res, "treat"),
            "N": f"{len(sub):,d}",
        })
        print(f"  Q{q}: β={coef_str(res, 'treat'):>10s}  "
              f"{se_str(res, 'treat'):>10s}  N={len(sub):,d}")
    except Exception as e:
        print(f"  Q{q}: FAILED — {e}")

pd.DataFrame(q_rows).to_csv(OUT / "table3_quartile_effects.txt",
                             sep="\t", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# 4. INTERACTION TEST: are effects heterogeneous?
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Interaction test (quartile × treatment) ---")
sub = df[df["std_score_el"].notna() & df["bl_quartile"].notna()].copy()
for q in [2, 3, 4]:
    sub[f"treat_x_q{q}"] = sub["treat"] * (sub["bl_quartile"] == q).astype(float)
    sub[f"q{q}"] = (sub["bl_quartile"] == q).astype(float)

X = sub[["treat", "treat_x_q2", "treat_x_q3", "treat_x_q4",
         "q2", "q3", "q4", "std_eb", "P_t"]].copy()
res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
# Joint test of interactions
from scipy import stats
F_stat = res.f_test("treat_x_q2 = treat_x_q3 = treat_x_q4 = 0")
fval = float(np.squeeze(F_stat.fvalue))
pval = float(np.squeeze(F_stat.pvalue))
print(f"  Joint F-test (interactions = 0): F={fval:.3f}, p={pval:.3f}")

print("\n✓ Phase 3 complete")
