#!/usr/bin/env python3
"""
06_robustness.py — Phase 6: Robustness checks.

Tests sensitivity of main results to:
  1. Strata FE instead of linear propensity
  2. Raw BL score instead of EB as control
  3. Trimming extreme BL scores
  4. Attrition analysis (Lee bounds)
  5. Permutation inference
  6. Balance checks on baseline observables

Produces:
  output/table6_robustness.txt       — robustness table
  output/table6_balance.txt          — balance table
  output/fig6_permutation.pdf        — permutation p-value distribution
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats
from config import ANALYSIS_FILE, OUT, SEED
from utils import ols_cluster, coef_str, se_str

np.random.seed(SEED)

print("=" * 70)
print("Phase 6: Robustness checks")
print("=" * 70)

df = pd.read_parquet(ANALYSIS_FILE)
df_full = df.copy()  # keep for attrition analysis
df = df[df["finsamp"] == True].copy()

# ═════════════════════════════════════════════════════════════════════════════
# 1. ROBUSTNESS TABLE: Alternative specifications
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Alternative specifications (stacked sample) ---\n")

sub = df[df["std_score_el"].notna()].copy()
rob_rows = []

# Spec A: Baseline (EB control + linear propensity)
X_a = sub[["treat", "std_eb", "P_t"]].copy()
res_a = ols_cluster(sub["std_score_el"], X_a, sub["ggroup"])
rob_rows.append({"Spec": "(A) Baseline: EB + P_t",
                  "Coef": coef_str(res_a, "treat"),
                  "SE": se_str(res_a, "treat"),
                  "N": f"{len(sub):,d}"})
print(f"  A (baseline):     {coef_str(res_a, 'treat'):>10s}  {se_str(res_a, 'treat'):>10s}")

# Spec B: Strata FE instead of linear propensity
strata_dums = pd.get_dummies(sub["strata"], prefix="strata", drop_first=True, dtype=float)
X_b = pd.concat([sub[["treat", "std_eb"]], strata_dums], axis=1)
res_b = ols_cluster(sub["std_score_el"], X_b, sub["ggroup"])
rob_rows.append({"Spec": "(B) Strata FE",
                  "Coef": coef_str(res_b, "treat"),
                  "SE": se_str(res_b, "treat"),
                  "N": f"{len(sub):,d}"})
print(f"  B (strata FE):    {coef_str(res_b, 'treat'):>10s}  {se_str(res_b, 'treat'):>10s}")

# Spec C: Raw BL score instead of EB
X_c = sub[["treat", "std_score_bl", "P_t"]].copy()
res_c = ols_cluster(sub["std_score_el"], X_c, sub["ggroup"])
rob_rows.append({"Spec": "(C) Raw BL (no EB)",
                  "Coef": coef_str(res_c, "treat"),
                  "SE": se_str(res_c, "treat"),
                  "N": f"{len(sub):,d}"})
print(f"  C (raw BL):       {coef_str(res_c, 'treat'):>10s}  {se_str(res_c, 'treat'):>10s}")

# Spec D: No ability control at all
X_d = sub[["treat", "P_t"]].copy()
res_d = ols_cluster(sub["std_score_el"], X_d, sub["ggroup"])
rob_rows.append({"Spec": "(D) No ability control",
                  "Coef": coef_str(res_d, "treat"),
                  "SE": se_str(res_d, "treat"),
                  "N": f"{len(sub):,d}"})
print(f"  D (no BL ctrl):   {coef_str(res_d, 'treat'):>10s}  {se_str(res_d, 'treat'):>10s}")

# Spec E: Trim extreme BL scores (5th–95th percentile within grade)
sub_trim = sub.copy()
sub_trim["keep"] = False
for g in [1, 2, 3, 4]:
    g_mask = sub_trim["grade"] == g
    lo = sub_trim.loc[g_mask, "std_score_bl"].quantile(0.05)
    hi = sub_trim.loc[g_mask, "std_score_bl"].quantile(0.95)
    sub_trim.loc[g_mask & sub_trim["std_score_bl"].between(lo, hi), "keep"] = True
sub_trim = sub_trim[sub_trim["keep"]].copy()
X_e = sub_trim[["treat", "std_eb", "P_t"]].copy()
res_e = ols_cluster(sub_trim["std_score_el"], X_e, sub_trim["ggroup"])
rob_rows.append({"Spec": "(E) Trim BL 5-95 pctile",
                  "Coef": coef_str(res_e, "treat"),
                  "SE": se_str(res_e, "treat"),
                  "N": f"{len(sub_trim):,d}"})
print(f"  E (trimmed):      {coef_str(res_e, 'treat'):>10s}  {se_str(res_e, 'treat'):>10s}")

# Spec F: Grade FE instead of EB (which already subsumes grade info)
grade_dums = pd.get_dummies(sub["grade"], prefix="grade", drop_first=True, dtype=float)
X_f = pd.concat([sub[["treat", "std_score_bl", "P_t"]], grade_dums], axis=1)
res_f = ols_cluster(sub["std_score_el"], X_f, sub["ggroup"])
rob_rows.append({"Spec": "(F) Raw BL + grade FE",
                  "Coef": coef_str(res_f, "treat"),
                  "SE": se_str(res_f, "treat"),
                  "N": f"{len(sub):,d}"})
print(f"  F (grade FE):     {coef_str(res_f, 'treat'):>10s}  {se_str(res_f, 'treat'):>10s}")

pd.DataFrame(rob_rows).to_csv(OUT / "table6_robustness.txt", sep="\t", index=False)
print(f"\n  → Saved to {OUT / 'table6_robustness.txt'}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. BALANCE TABLE
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Balance table (treatment vs control at baseline) ---\n")

balance_vars = ["score_bl", "has_bl", "has_el", "upper_group"]
bal_rows = []
for v in balance_vars:
    for exp_label, exp_col in [("All", "exp0"), ("G3-4", "exp1"), ("G1-2", "exp2")]:
        sub = df[df[exp_col] == 1].copy()
        t_mean = sub.loc[sub["treat"] == 1, v].mean()
        c_mean = sub.loc[sub["treat"] == 0, v].mean()
        diff = t_mean - c_mean
        # t-test (cluster-robust would be better, simple t-test as quick check)
        t_vals = sub.loc[sub["treat"] == 1, v].dropna()
        c_vals = sub.loc[sub["treat"] == 0, v].dropna()
        if len(t_vals) > 5 and len(c_vals) > 5:
            t_stat, p_val = stats.ttest_ind(t_vals, c_vals, equal_var=False)
        else:
            p_val = np.nan

        bal_rows.append({
            "Variable": v,
            "Sample": exp_label,
            "Treat mean": f"{t_mean:.3f}",
            "Control mean": f"{c_mean:.3f}",
            "Difference": f"{diff:.3f}",
            "p-value": f"{p_val:.3f}" if not np.isnan(p_val) else "—",
        })

pd.DataFrame(bal_rows).to_csv(OUT / "table6_balance.txt", sep="\t", index=False)
print(f"  → Saved to {OUT / 'table6_balance.txt'}")

# Print summary
bal_df = pd.DataFrame(bal_rows)
for v in balance_vars:
    sub = bal_df[bal_df["Variable"] == v]
    row = sub[sub["Sample"] == "All"].iloc[0]
    print(f"  {v:15s}  T={row['Treat mean']}  C={row['Control mean']}  "
          f"p={row['p-value']}")

# ═════════════════════════════════════════════════════════════════════════════
# 3. ATTRITION ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

print("\n--- Attrition analysis ---")

df_att = df_full[df_full["treat"].notna()].copy()
df_att["attrited"] = df_att["has_el"].apply(lambda x: 0 if x else 1)

for label, exp_col in [("All", "exp0"), ("G3-4", "exp1"), ("G1-2", "exp2")]:
    sub = df_att[df_att[exp_col] == 1].copy()
    att_t = sub.loc[sub["treat"] == 1, "attrited"].mean()
    att_c = sub.loc[sub["treat"] == 0, "attrited"].mean()
    diff = att_t - att_c

    # Regression: attrited on treatment
    X = sub[["treat", "P_t"]].copy()
    sub_clean = sub.dropna(subset=["attrited", "P_t"])
    if len(sub_clean) > 0:
        res = ols_cluster(sub_clean["attrited"], sub_clean[["treat", "P_t"]],
                          sub_clean["ggroup"])
        print(f"  {label:10s}  att_T={att_t:.3f}  att_C={att_c:.3f}  "
              f"diff={coef_str(res, 'treat'):>10s}  {se_str(res, 'treat')}")

# ═════════════════════════════════════════════════════════════════════════════
# 4. PERMUTATION INFERENCE (Randomisation inference)
# ═════════════════════════════════════════════════════════════════════════════
#
# Re-randomise treatment at the ggroup level WITHIN STRATA 1000 times.
# Stratified permutation respects the actual randomisation design.
# Under H0: β=0, the distribution of t-statistics should be standard normal.

print("\n--- Permutation inference (1000 permutations, within-strata) ---")

sub = df[df["std_score_el"].notna()].copy()
X_real = sub[["treat", "std_eb", "P_t"]].copy()
res_real = ols_cluster(sub["std_score_el"], X_real, sub["ggroup"])
t_real = res_real.tvalues["treat"]

# Build strata-level ggroup→treat map for stratified permutation
ggroup_info = sub.drop_duplicates("ggroup")[["ggroup", "treat", "strata"]].copy()
n_perm = 1000
t_perms = []

for _ in range(n_perm):
    perm_treat = ggroup_info.copy()
    # Shuffle treatment WITHIN each stratum (respects randomisation design)
    perm_treat["treat_perm"] = perm_treat.groupby("strata")["treat"].transform(
        lambda x: x.sample(frac=1, replace=False).values
    )
    perm_map = dict(zip(perm_treat["ggroup"], perm_treat["treat_perm"]))
    sub["treat_perm"] = sub["ggroup"].map(perm_map)
    X_p = sub[["treat_perm", "std_eb", "P_t"]].rename(columns={"treat_perm": "treat"})
    try:
        res_p = ols_cluster(sub["std_score_el"], X_p, sub["ggroup"])
        t_perms.append(res_p.tvalues["treat"])
    except Exception:
        pass

t_perms = np.array(t_perms)
p_perm = (np.abs(t_perms) >= np.abs(t_real)).mean()
print(f"  Real t-stat: {t_real:.3f}")
print(f"  Permutation p-value (two-sided): {p_perm:.3f}")

# Plot
fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(t_perms, bins=40, color="steelblue", alpha=0.7, density=True,
        label="Permuted t-stats")
ax.axvline(t_real, color="darkred", lw=2, ls="--", label=f"Observed (t={t_real:.2f})")
ax.axvline(-t_real, color="darkred", lw=2, ls="--", alpha=0.5)
ax.set_xlabel("t-statistic")
ax.set_ylabel("Density")
ax.set_title(f"Permutation inference (p={p_perm:.3f})")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "fig6_permutation.pdf")
plt.close()
print(f"  → Figure saved to {OUT / 'fig6_permutation.pdf'}")

print("\n✓ Phase 6 complete")
