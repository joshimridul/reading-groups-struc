"""
Estimate the reliability of the Nigeria placement test instrument.

The numeracy MTE (MaxScore 30) and ETE (MaxScore 50) are different tests,
not parallel forms. So disattenuation via MTE↔ETE breaks.

Better approach:
  1. Predictive R²: Group → EL numeracy in control (lower bound on reliability)
  2. Ratio method: Compare group's predictive power to BL maths' predictive power
  3. Discretization correction: 3-category ordinal → continuous latent
  4. Cross-validation with multiple post-tests
"""

import pandas as pd
import numpy as np
from scipy.stats import norm, pearsonr, spearmanr
from pathlib import Path
import statsmodels.api as sm

BASE = Path("/Users/mriduljoshi/Github/AbilityGrouping/2_Data/1_Raw/P123 Numeracy Groups")

# ── 1. Load placement file ──
pl = pd.read_excel(BASE / "[Data Entry] Numeracy Groups Placement - 2020-2021.xlsx")
pl["grade_clean"] = (
    pl["Grade"]
    .str.replace("Primay", "Primary")
    .str.replace("Primary3", "Primary 3")
    .str.strip()
)
pl["group_clean"] = pl["Group"].str.strip().str.replace(r"\s*\d+$", "", regex=True)
grp_map = {"Red": 1, "Blue": 2, "Yellow": 3}
pl["grp_ord"] = pl["group_clean"].map(grp_map)

treat_map = pl.groupby("AcademyCode")["Treatment"].first().reset_index()
treat_map.columns = ["AcademyCode", "treat"]
rct_acads = set(treat_map["AcademyCode"])
student_grp = pl[pl["StudyID"] > 0][["StudyID", "grp_ord", "group_clean"]].drop_duplicates("StudyID")


# ── 2. Load assessment scores ──
def load_assess(rel_path, label):
    df = pd.read_excel(BASE / rel_path)
    df = df[df["AcademyCode"].isin(rct_acads)].copy()
    df["grade"] = df["GradeName"].str.extract(r"(\d)")[0].astype(float)
    df = df.rename(columns={"Score": f"score_{label}"})
    return df[["StudyID", "AcademyCode", "grade", f"score_{label}"]].dropna(
        subset=[f"score_{label}"]
    )


print("Loading assessment files...")
bl = load_assess("term 2/Assessment Scores by Pupil - MASTER v2 (P123 T1 ETE Maths).xlsx", "bl")
t3_num = load_assess("term 3/Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Numeracy).xlsx", "el_num")
t3_math = load_assess("term 3/Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Maths).xlsx", "el_math")
t2_num = load_assess("term 2/Assessment Scores by Pupil - MASTER v2 (P123 T2 ETE Numeracy).xlsx", "t2_num")
t2_math = load_assess("term 2/Assessment Scores by Pupil - MASTER v2 (P123 T2 ETE Maths).xlsx", "t2_math")

# ── 3. Merge ──
df = bl.copy()
for d in [t3_num, t3_math, t2_num, t2_math]:
    sc = [c for c in d.columns if c.startswith("score_")][0]
    df = df.merge(d[["StudyID", sc]], on="StudyID", how="outer")

for d in [bl, t3_num, t3_math]:
    for col in ["grade", "AcademyCode"]:
        if col in d.columns:
            mask = df[col].isna()
            if mask.sum() > 0:
                fill = d.drop_duplicates("StudyID").set_index("StudyID")[col]
                df.loc[mask, col] = df.loc[mask, "StudyID"].map(fill)

df = df.merge(student_grp, on="StudyID", how="left")
df = df.merge(treat_map, on="AcademyCode", how="left")
df = df.dropna(subset=["treat", "grp_ord"])

# ── 4. Control P2+P3 ──
ctrl = df[(df["treat"] == 0) & (df["grade"].isin([2, 3]))].copy()

print(f"\n{'='*70}")
print(f"SAMPLE: Control P2+P3, N = {len(ctrl)}")
print(f"{'='*70}")
print(f"\nGroup distribution:")
print(ctrl.groupby(["grade", "group_clean"]).size().unstack(fill_value=0))

# Standardize scores within grade
for c in [col for col in ctrl.columns if col.startswith("score_")]:
    for g in [2, 3]:
        mask = ctrl["grade"] == g
        vals = ctrl.loc[mask, c]
        if vals.notna().sum() > 10:
            ctrl.loc[mask, c] = (vals - vals.mean()) / vals.std()

# Also standardize group ordinal within grade
for g in [2, 3]:
    mask = ctrl["grade"] == g
    vals = ctrl.loc[mask, "grp_ord"]
    ctrl.loc[mask, "grp_std"] = (vals - vals.mean()) / vals.std()

# ── 5. Method 1: Predictive R² ──
print(f"\n{'='*70}")
print("METHOD 1: Predictive R² (Group → Outcome, with grade FE)")
print(f"{'='*70}")

outcomes = {
    "T3 ETE Numeracy (primary EL)": "score_el_num",
    "T3 ETE Maths (spillover EL)": "score_el_math",
    "BL Maths (pre-placement)": "score_bl",
    "T2 ETE Numeracy (midterm)": "score_t2_num",
    "T2 ETE Maths (midterm)": "score_t2_math",
}

for label, col in outcomes.items():
    valid = ctrl[["grp_ord", col, "grade"]].dropna()
    if len(valid) < 30:
        continue
    grade_dum = pd.get_dummies(valid["grade"], prefix="g", drop_first=True, dtype=float)
    X = sm.add_constant(pd.concat([valid[["grp_ord"]].reset_index(drop=True), grade_dum.reset_index(drop=True)], axis=1))
    y = valid[col].reset_index(drop=True)
    r_full = sm.OLS(y.astype(float), X.astype(float)).fit()

    X0 = sm.add_constant(grade_dum.reset_index(drop=True).astype(float))
    r_base = sm.OLS(y.astype(float), X0.astype(float)).fit()

    partial_r2 = 1 - (1 - r_full.rsquared) / (1 - r_base.rsquared)
    r_corr, _ = pearsonr(valid["grp_ord"], valid[col])
    print(f"\n  {label}:")
    print(f"    r(group, outcome) = {r_corr:.3f}")
    print(f"    R²(group | grade FE) = {partial_r2:.3f}   [N={len(valid)}]")

# ── 6. Method 2: Comparison with BL Maths ──
print(f"\n{'='*70}")
print("METHOD 2: Group vs BL Maths as predictors of EL Numeracy")
print(f"{'='*70}")

valid = ctrl[["grp_ord", "score_bl", "score_el_num", "grade"]].dropna().reset_index(drop=True)
print(f"N = {len(valid)}")

grade_dum = pd.get_dummies(valid["grade"], prefix="g", drop_first=True, dtype=float)
y = valid["score_el_num"].astype(float)

# BL only
X_bl = sm.add_constant(pd.concat([valid[["score_bl"]], grade_dum], axis=1).astype(float))
r_bl = sm.OLS(y, X_bl).fit()

# Group only
X_gr = sm.add_constant(pd.concat([valid[["grp_ord"]], grade_dum], axis=1).astype(float))
r_gr = sm.OLS(y, X_gr).fit()

# Both
X_both = sm.add_constant(pd.concat([valid[["score_bl", "grp_ord"]], grade_dum], axis=1).astype(float))
r_both = sm.OLS(y, X_both).fit()

# Grade only
X_g0 = sm.add_constant(grade_dum.astype(float))
r_g0 = sm.OLS(y, X_g0).fit()

pr2_bl = 1 - (1 - r_bl.rsquared) / (1 - r_g0.rsquared)
pr2_gr = 1 - (1 - r_gr.rsquared) / (1 - r_g0.rsquared)
pr2_both = 1 - (1 - r_both.rsquared) / (1 - r_g0.rsquared)
incr_bl = pr2_both - pr2_gr
incr_gr = pr2_both - pr2_bl

print(f"\n  Partial R² (controlling for grade FE):")
print(f"    BL Maths alone:       {pr2_bl:.3f}")
print(f"    Group alone:          {pr2_gr:.3f}")
print(f"    BL + Group together:  {pr2_both:.3f}")
print(f"    Incremental R² of Group over BL: {incr_gr:.3f}")
print(f"    Incremental R² of BL over Group: {incr_bl:.3f}")
print(f"\n  → Group explains {pr2_gr/pr2_bl:.1f}x as much EL variance as BL maths")
print(f"  → Group adds {incr_gr:.3f} beyond what BL maths captures")

# ── 7. Method 3: Discretization correction ──
print(f"\n{'='*70}")
print("METHOD 3: Correct for discretization (3-category → continuous)")
print(f"{'='*70}")

freq = ctrl["grp_ord"].value_counts(normalize=True).sort_index()
p1, p2, p3 = freq.get(1, 0), freq.get(2, 0), freq.get(3, 0)
print(f"\n  Marginal frequencies: Red={p1:.3f}, Blue={p2:.3f}, Yellow={p3:.3f}")

c1 = norm.ppf(p1) if p1 < 1 else 3
c2 = norm.ppf(p1 + p2) if (p1 + p2) < 1 else 3
print(f"  Normal cut points: z₁={c1:.2f}, z₂={c2:.2f}")

np.random.seed(42)
z = np.random.randn(500_000)
z_cat = np.where(z < c1, 1, np.where(z < c2, 2, 3))
d_factor = pearsonr(z, z_cat)[0]
print(f"  Discretization attenuation: d = {d_factor:.3f}  (d² = {d_factor**2:.3f})")

# Grade-specific
for g in [2, 3]:
    sub = ctrl[ctrl["grade"] == g]
    freq_g = sub["grp_ord"].value_counts(normalize=True).sort_index()
    p1g, p2g, p3g = freq_g.get(1, 0), freq_g.get(2, 0), freq_g.get(3, 0)
    c1g = norm.ppf(p1g) if p1g < 1 else 3
    c2g = norm.ppf(p1g + p2g) if (p1g + p2g) < 1 else 3
    z_catg = np.where(z < c1g, 1, np.where(z < c2g, 2, 3))
    dg = pearsonr(z, z_catg)[0]
    print(f"  P{g}: freq=({p1g:.2f},{p2g:.2f},{p3g:.2f}), d={dg:.3f}")

print(f"\n  Corrected R²_placement = R²_observed / d² = {pr2_gr:.3f} / {d_factor**2:.3f} = {pr2_gr / d_factor**2:.3f}")

# ── 8. Method 4: Within-grade analysis ──
print(f"\n{'='*70}")
print("METHOD 4: Within-grade estimates (avoid pooling artifacts)")
print(f"{'='*70}")

for g in [2, 3]:
    sub = ctrl[ctrl["grade"] == g].copy()
    n_grps = sub["grp_ord"].nunique()
    freq_g = sub["grp_ord"].value_counts(normalize=True).sort_index()
    
    print(f"\n  ── P{g} (N={len(sub)}, groups={n_grps}: {freq_g.to_dict()}) ──")
    
    for label, col in [("T3 ETE Numeracy", "score_el_num"), 
                       ("T3 ETE Maths", "score_el_math"),
                       ("BL Maths", "score_bl")]:
        v = sub[["grp_ord", col]].dropna()
        if len(v) > 20:
            r, p = pearsonr(v["grp_ord"], v[col])
            print(f"    r(group, {label}) = {r:.3f}  (R²={r**2:.3f}, p={p:.4f}, N={len(v)})")
    
    # Group means on EL numeracy
    v = sub[["grp_ord", "group_clean", "score_el_num"]].dropna()
    if len(v) > 20:
        print(f"    Group means on T3 ETE Numeracy (standardized within grade):")
        gm = v.groupby("group_clean")["score_el_num"].agg(["mean", "std", "count"])
        for idx, row in gm.iterrows():
            print(f"      {idx}: mean={row['mean']:.3f}, sd={row['std']:.3f}, n={int(row['count'])}")

# ── 9. Method 5: Upper/lower bound via ratio method ──
print(f"\n{'='*70}")
print("METHOD 5: Bound placement reliability via ratio to BL maths")
print(f"{'='*70}")

print("""
  Logic (classical test theory, all variables standardized within grade):
    BL     = θ + ε_BL       reliability r_BL = Var(θ)/Var(BL)
    P_cont = θ + ε_P        reliability r_P  = Var(θ)/Var(P_cont)
    EL     = θ + ε_EL       reliability r_EL = Var(θ)/Var(EL)
    Group  = discretize(P_cont)
    
    Corr(BL, EL)    = √(r_BL × r_EL)
    Corr(Group, EL) = √(r_P × r_EL) × d
    
    ⟹ r_P = [Corr(Group, EL) / d]² × r_BL / Corr(BL, EL)²
    
    But we need r_BL. Use same-subject comparison:
    Corr(BL_math, EL_math) = √(r_BL_math × r_EL_math) for same-construct
    Corr(BL_math, EL_num)  = √(r_BL_math × r_EL_num) × ρ(math, num)
    
    From EL tests: Corr(EL_num, EL_math) ≈ √(r_EL_num × r_EL_math) × ρ(math,num)
""")

v = ctrl[["score_bl", "score_el_num", "score_el_math", "grp_ord"]].dropna()
r_bl_elnum = pearsonr(v["score_bl"], v["score_el_num"])[0]
r_bl_elmath = pearsonr(v["score_bl"], v["score_el_math"])[0]
r_elnum_elmath = pearsonr(v["score_el_num"], v["score_el_math"])[0]
r_grp_elnum = pearsonr(v["grp_ord"], v["score_el_num"])[0]
r_grp_elmath = pearsonr(v["grp_ord"], v["score_el_math"])[0]
r_grp_bl = pearsonr(v["grp_ord"], v["score_bl"])[0]

print(f"  Observed correlations (N={len(v)}):")
print(f"    Corr(BL, EL_num)  = {r_bl_elnum:.3f}")
print(f"    Corr(BL, EL_math) = {r_bl_elmath:.3f}")
print(f"    Corr(EL_num, EL_math) = {r_elnum_elmath:.3f}")
print(f"    Corr(Group, EL_num)   = {r_grp_elnum:.3f}")
print(f"    Corr(Group, EL_math)  = {r_grp_elmath:.3f}")
print(f"    Corr(Group, BL)       = {r_grp_bl:.3f}")

# Ratio of predictive power: placement vs BL
ratio_num = (r_grp_elnum / d_factor)**2 / r_bl_elnum**2
ratio_math = (r_grp_elmath / d_factor)**2 / r_bl_elmath**2

print(f"\n  r_P / r_BL (via EL numeracy) = [{r_grp_elnum:.3f}/{d_factor:.3f}]² / {r_bl_elnum:.3f}² = {ratio_num:.2f}")
print(f"  r_P / r_BL (via EL maths)    = [{r_grp_elmath:.3f}/{d_factor:.3f}]² / {r_bl_elmath:.3f}² = {ratio_math:.2f}")

# Geometric mean of the two
ratio_avg = np.sqrt(ratio_num * ratio_math)
print(f"  Geometric mean ratio: {ratio_avg:.2f}")
print(f"\n  ⟹ The placement test is ~{ratio_avg:.1f}x more reliable than the BL maths test")
print(f"     for predicting future numeracy/maths performance.")

# Use BL math test-retest to bound r_BL
# BL math ↔ T2 ETE math (same subject, 4 months apart)
v2 = ctrl[["score_bl", "score_t2_math"]].dropna()
r_bl_t2m = pearsonr(v2.iloc[:, 0], v2.iloc[:, 1])[0] if len(v2) > 20 else np.nan
# BL math ↔ T3 ETE math (same subject, 7 months apart)
v3 = ctrl[["score_bl", "score_el_math"]].dropna()
r_bl_t3m = pearsonr(v3.iloc[:, 0], v3.iloc[:, 1])[0] if len(v3) > 20 else np.nan

print(f"\n  BL maths test-retest correlations:")
print(f"    BL → T2 ETE Maths (4mo): r = {r_bl_t2m:.3f}")
print(f"    BL → T3 ETE Maths (7mo): r = {r_bl_t3m:.3f}")
print(f"    These equal √(r_BL × r_other). With r_other ≤ 1:")
print(f"    Lower bound r_BL ≥ {r_bl_t2m**2:.3f} (from T2)")
print(f"    Lower bound r_BL ≥ {r_bl_t3m**2:.3f} (from T3)")

r_bl_est = r_bl_t2m**2  # conservative lower bound
r_p_est = ratio_num * r_bl_est
r_p_est2 = ratio_math * r_bl_est

print(f"\n  Using conservative r_BL ≈ {r_bl_est:.3f}:")
print(f"    r_placement (via numeracy) ≈ {ratio_num:.2f} × {r_bl_est:.3f} = {r_p_est:.3f}")
print(f"    r_placement (via maths)    ≈ {ratio_math:.2f} × {r_bl_est:.3f} = {r_p_est2:.3f}")

# ── 10. Summary ──
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"""
  In the control group (P2+P3, N≈{len(ctrl)}), where grouping didn't affect
  instruction, we estimate the placement test's reliability:

  ┌─────────────────────────────────────────────────────────────────┐
  │ Measure                                          │   Estimate  │
  ├─────────────────────────────────────────────────────────────────┤
  │ Raw R²(Group → EL Num | grade FE)                │   {pr2_gr:.3f}     │
  │ Discretization-corrected R²                       │   {pr2_gr / d_factor**2:.3f}     │
  │ Ratio r_placement / r_BL (via EL Num)             │   {ratio_num:.1f}x       │
  │ Ratio r_placement / r_BL (via EL Math)            │   {ratio_math:.1f}x       │
  │ Absolute r²_placement (conservative bound)        │   {(r_p_est + r_p_est2)/2:.3f}     │
  │ For comparison: R²(BL → EL Num | grade FE)       │   {pr2_bl:.3f}     │
  └─────────────────────────────────────────────────────────────────┘

  Interpretation: The placement test's group assignments explain 
  {pr2_gr:.0%} of EL numeracy variance (raw) or ~{pr2_gr/d_factor**2:.0%} after 
  correcting for discretization. This is {pr2_gr/pr2_bl:.1f}x the BL maths 
  R² ({pr2_bl:.0%}), confirming the "better placement test" used in Nigeria 
  was substantially more predictive than the standard maths assessment.
  
  Recommended r² for pipeline: {min(pr2_gr / d_factor**2, 0.99):.2f}
""")
