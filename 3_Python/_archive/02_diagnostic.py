#!/usr/bin/env python3
"""
02_diagnostic.py — Phase 2: Diagnostic reliability of the baseline test.

Questions answered:
  1. How much signal does the baseline test carry? (R² by grade)
  2. What is the test–retest reliability ρ?
  3. How does EB shrinkage compare to raw scores?

Produces:
  output/table2_reliability.txt   — R² table
  output/fig2_bl_el_scatter.pdf   — BL vs EL scatter by grade (control)
  output/fig2_eb_vs_raw.pdf       — EB ability vs raw baseline
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from config import ANALYSIS_FILE, OUT

print("=" * 70)
print("Phase 2: Diagnostic reliability")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df = df[df["finsamp"] == True].copy()
ctrl = df["treat"] == 0

# ═════════════════════════════════════════════════════════════════════════════
# TABLE 2: R² from score regressions in control group
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- R² of baseline → endline (control group, by grade) ---\n")

rows = []
for g in [1, 2, 3, 4]:
    g_ctrl = ctrl & (df["grade"] == g)

    # BL → EL
    mask_bl_el = g_ctrl & df["score_bl"].notna() & df["score_el"].notna()
    n_bl_el = mask_bl_el.sum()
    if n_bl_el > 10:
        X = sm.add_constant(df.loc[mask_bl_el, "score_bl"])
        res_bl_el = sm.OLS(df.loc[mask_bl_el, "score_el"], X).fit()
        r2_bl_el = res_bl_el.rsquared
    else:
        r2_bl_el = np.nan

    # BL → ML
    mask_bl_ml = g_ctrl & df["score_bl"].notna() & df["score_ml"].notna()
    n_bl_ml = mask_bl_ml.sum()
    if n_bl_ml > 10:
        X = sm.add_constant(df.loc[mask_bl_ml, "score_bl"])
        res_bl_ml = sm.OLS(df.loc[mask_bl_ml, "score_ml"], X).fit()
        r2_bl_ml = res_bl_ml.rsquared
    else:
        r2_bl_ml = np.nan

    # ML → EL
    mask_ml_el = g_ctrl & df["score_ml"].notna() & df["score_el"].notna()
    n_ml_el = mask_ml_el.sum()
    if n_ml_el > 10:
        X = sm.add_constant(df.loc[mask_ml_el, "score_ml"])
        res_ml_el = sm.OLS(df.loc[mask_ml_el, "score_el"], X).fit()
        r2_ml_el = res_ml_el.rsquared
    else:
        r2_ml_el = np.nan

    # Correlation = proxy for reliability ρ
    corr_bl_ml = df.loc[mask_bl_ml, "score_bl"].corr(df.loc[mask_bl_ml, "score_ml"])

    rows.append({
        "Grade": g,
        "R²(BL→EL)": f"{r2_bl_el:.4f}" if not np.isnan(r2_bl_el) else "—",
        "R²(BL→ML)": f"{r2_bl_ml:.4f}" if not np.isnan(r2_bl_ml) else "—",
        "R²(ML→EL)": f"{r2_ml_el:.4f}" if not np.isnan(r2_ml_el) else "—",
        "cor(BL,ML)": f"{corr_bl_ml:.4f}" if not np.isnan(corr_bl_ml) else "—",
        "N(BL∩EL)": n_bl_el,
        "N(BL∩ML)": n_bl_ml,
    })
    print(f"  Grade {g}: R²(BL→EL)={r2_bl_el:.4f}  "
          f"R²(BL→ML)={r2_bl_ml:.4f}  "
          f"cor(BL,ML)={corr_bl_ml:.4f}  N={n_bl_el}")

# Pooled (all grades, with grade FE)
mask_pool = ctrl & df["score_bl"].notna() & df["score_el"].notna()
X_pool = pd.get_dummies(df.loc[mask_pool, "grade"], prefix="grade", drop_first=True, dtype=float)
X_pool["score_bl"] = df.loc[mask_pool, "score_bl"]
X_pool = sm.add_constant(X_pool)
res_pool = sm.OLS(df.loc[mask_pool, "score_el"], X_pool).fit()
print(f"\n  Pooled (with grade FE): R²={res_pool.rsquared:.4f}  N={mask_pool.sum()}")

rel_df = pd.DataFrame(rows)
rel_df.to_csv(OUT / "table2_reliability.txt", sep="\t", index=False)

# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 2a: Baseline vs Endline scatter (control group, by grade)
# ═════════════════════════════════════════════════════════════════════════════

fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=False, sharey=False)
for idx, g in enumerate([1, 2, 3, 4]):
    ax = axes.flat[idx]
    mask = ctrl & (df["grade"] == g) & df["std_score_bl"].notna() & df["std_score_el"].notna()
    x = df.loc[mask, "std_score_bl"]
    y = df.loc[mask, "std_score_el"]
    ax.scatter(x, y, alpha=0.15, s=8, color="steelblue")
    # Fit line
    z = np.polyfit(x.values, y.values, 1)
    xline = np.linspace(x.min(), x.max(), 100)
    ax.plot(xline, np.polyval(z, xline), color="darkred", lw=2)
    # R²
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    ax.set_title(f"Grade {g}  (R²={r2:.3f}, N={mask.sum()})")
    ax.set_xlabel("Std. baseline score")
    ax.set_ylabel("Std. endline score")

fig.suptitle("Baseline → Endline signal (control group only)", fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig(OUT / "fig2_bl_el_scatter.pdf")
plt.close()
print(f"\n  → Figure saved to {OUT / 'fig2_bl_el_scatter.pdf'}")

# ═════════════════════════════════════════════════════════════════════════════
# FIGURE 2b: EB predicted ability vs raw baseline
# ═════════════════════════════════════════════════════════════════════════════

fig, ax = plt.subplots(figsize=(6, 5))
mask = df["score_bl"].notna() & df["eb_ability"].notna()
ax.scatter(df.loc[mask, "std_score_bl"], df.loc[mask, "std_eb"],
           alpha=0.15, s=6, color="steelblue")
ax.plot([-3, 3], [-3, 3], "k--", alpha=0.4, lw=1, label="45° line")
ax.set_xlabel("Standardised baseline score (raw)")
ax.set_ylabel("Standardised EB predicted ability")
ax.set_title("Empirical Bayes shrinkage")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "fig2_eb_vs_raw.pdf")
plt.close()
print(f"  → Figure saved to {OUT / 'fig2_eb_vs_raw.pdf'}")

print("\n✓ Phase 2 complete")
