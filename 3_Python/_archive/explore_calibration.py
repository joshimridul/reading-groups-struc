#!/usr/bin/env python3
"""
Diagnostic script: why does the calibration chain break?

Core problem: λ (return to match) is often negative, meaning students
farther from their class mean do BETTER.  This violates the model and
breaks ρ = 2√(λ·(-τ)).

Hypotheses:
  H1: Quadratic ability-outcome confounding.
      misfit = (θ̂ - Ī)² picks up the non-linear ability-outcome
      relationship when we only control for θ̂ linearly.
  H2: EB shrinkage destroys variation.
      With r² ≈ 0.05 in Liberia, θ̂ ≈ μ for everyone, so misfit
      has negligible structural variation.
  H3: Wrong "classroom" for misfit.
      We compute class_mean from the realized classroom, but the
      relevant instruction level under scripted instruction is
      fixed by track, not by composition.
  H4: Pooling across grades helps power.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from config import get_config, OUT
from utils import ols_cluster

np.set_printoptions(precision=4)


def run_diagnostics(country):
    cfg = get_config(country)
    label = cfg["label"]
    print("\n" + "=" * 70)
    print(f"  CALIBRATION DIAGNOSTICS — {label}")
    print("=" * 70)

    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    df = df[df["finsamp"] == True].copy()
    ctrl = df["treat"] == 0
    grades = sorted(df["grade"].dropna().unique())

    sub = df[df["std_score_el"].notna() & df["misfit"].notna()].copy()

    # ─── 0. Descriptives: what does misfit look like? ────────────────────
    print(f"\n{'─'*50}")
    print("0. Misfit descriptives")
    print(f"{'─'*50}")

    for g in grades:
        g_sub = sub[sub["grade"] == g]
        for t_val, t_lab in [(0, "Control"), (1, "Treatment")]:
            s = g_sub.loc[g_sub["treat"] == t_val, "misfit"]
            if len(s) > 0:
                print(f"  G{int(g)} {t_lab:9s}: mean={s.mean():.4f}  "
                      f"sd={s.std():.4f}  median={s.median():.4f}  N={len(s)}")

    print(f"\n  std_eb vs std_score_bl correlation: "
          f"{sub['std_eb'].corr(sub['std_score_bl']):.4f}")
    print(f"  (If ≈1.0, EB shrinkage is so heavy that std_eb ≈ std_bl)")

    # ─── 1. Current spec: Y = -λ·misfit + γ·θ_eb + ε ───────────────────
    print(f"\n{'─'*50}")
    print("1. Current specification (linear ability control)")
    print(f"{'─'*50}")

    for g in grades:
        g_sub = sub[sub["grade"] == g]
        res = ols_cluster(g_sub["std_score_el"],
                           g_sub[["misfit", "std_eb"]], g_sub["ggroup"])
        print(f"  Grade {int(g)}: misfit={res.params['misfit']:+.4f} "
              f"(t={res.tvalues['misfit']:.2f})  "
              f"std_eb={res.params['std_eb']:+.4f}  N={len(g_sub)}")

    res_pool = ols_cluster(sub["std_score_el"],
                            sub[["misfit", "std_eb"]], sub["ggroup"])
    print(f"  Pooled:   misfit={res_pool.params['misfit']:+.4f} "
          f"(t={res_pool.tvalues['misfit']:.2f})  N={len(sub)}")

    # ─── 2. FIX H1: Add quadratic ability control ───────────────────────
    print(f"\n{'─'*50}")
    print("2. Fix H1: Add std_eb² (quadratic ability control)")
    print(f"{'─'*50}")

    sub["std_eb_sq"] = sub["std_eb"] ** 2
    for g in grades:
        g_sub = sub[sub["grade"] == g]
        res = ols_cluster(g_sub["std_score_el"],
                           g_sub[["misfit", "std_eb", "std_eb_sq"]], g_sub["ggroup"])
        print(f"  Grade {int(g)}: misfit={res.params['misfit']:+.4f} "
              f"(t={res.tvalues['misfit']:.2f})  "
              f"std_eb²={res.params['std_eb_sq']:+.4f}  N={len(g_sub)}")

    res_pool = ols_cluster(sub["std_score_el"],
                            sub[["misfit", "std_eb", "std_eb_sq"]], sub["ggroup"])
    print(f"  Pooled:   misfit={res_pool.params['misfit']:+.4f} "
          f"(t={res_pool.tvalues['misfit']:.2f})  "
          f"std_eb²={res_pool.params['std_eb_sq']:+.4f}")

    # ─── 3. FIX H2: Use raw BL scores instead of EB ─────────────────────
    print(f"\n{'─'*50}")
    print("3. Fix H2: Raw BL-based misfit (no EB shrinkage)")
    print(f"{'─'*50}")

    for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
        cm = sub.groupby(["academycode", grp_type])["std_score_bl"].transform("mean")
        sub[f"cm_bl_{suffix}"] = cm
    sub["class_mean_bl"] = np.where(sub["treat"] == 1,
                                     sub["cm_bl_treat"], sub["cm_bl_ctrl"])
    sub["misfit_bl"] = (sub["std_score_bl"] - sub["class_mean_bl"]) ** 2
    sub["std_bl_sq"] = sub["std_score_bl"] ** 2

    for g in grades:
        g_sub = sub[sub["grade"] == g].dropna(subset=["misfit_bl"])
        if len(g_sub) < 30:
            continue
        res = ols_cluster(g_sub["std_score_el"],
                           g_sub[["misfit_bl", "std_score_bl", "std_bl_sq"]],
                           g_sub["ggroup"])
        print(f"  Grade {int(g)}: misfit_bl={res.params['misfit_bl']:+.4f} "
              f"(t={res.tvalues['misfit_bl']:.2f})  N={len(g_sub)}")

    g_sub = sub.dropna(subset=["misfit_bl"])
    res_pool = ols_cluster(g_sub["std_score_el"],
                            g_sub[["misfit_bl", "std_score_bl", "std_bl_sq"]],
                            g_sub["ggroup"])
    print(f"  Pooled:   misfit_bl={res_pool.params['misfit_bl']:+.4f} "
          f"(t={res_pool.tvalues['misfit_bl']:.2f})  N={len(g_sub)}")

    # ─── 4. FIX H3: Control-group only λ ────────────────────────────────
    print(f"\n{'─'*50}")
    print("4. Fix H3: Estimate λ from CONTROL group only")
    print(f"   (In control, misfit = distance from grade instruction)")
    print(f"{'─'*50}")

    ctrl_sub = sub[sub["treat"] == 0].copy()
    for g in grades:
        g_sub = ctrl_sub[ctrl_sub["grade"] == g]
        if len(g_sub) < 30:
            continue
        res = ols_cluster(g_sub["std_score_el"],
                           g_sub[["misfit", "std_eb", "std_eb_sq"]],
                           g_sub["ggroup"])
        print(f"  Grade {int(g)}: misfit={res.params['misfit']:+.4f} "
              f"(t={res.tvalues['misfit']:.2f})  N={len(g_sub)}")

    if len(ctrl_sub) >= 30:
        res_pool = ols_cluster(ctrl_sub["std_score_el"],
                                ctrl_sub[["misfit", "std_eb", "std_eb_sq"]],
                                ctrl_sub["ggroup"])
        print(f"  Pooled:   misfit={res_pool.params['misfit']:+.4f} "
              f"(t={res_pool.tvalues['misfit']:.2f})")

    # ─── 5. Alternative: Variance decomposition approach ─────────────────
    print(f"\n{'─'*50}")
    print("5. Alternative: Direct variance decomposition")
    print(f"   (More robust than structural calibration)")
    print(f"{'─'*50}")

    for g in grades:
        g_df = sub[sub["grade"] == g]
        g_ctrl = g_df[g_df["treat"] == 0]
        g_treat = g_df[g_df["treat"] == 1]

        if len(g_ctrl) < 10 or len(g_treat) < 10:
            continue

        var_ctrl_eb = _within_class_var(g_ctrl, "std_eb",
                                          "academycode", "grade")
        var_treat_eb = _within_class_var(g_treat, "std_eb",
                                           "academycode", "std_grp")
        var_ctrl_el = _within_class_var(g_ctrl, "std_score_el",
                                          "academycode", "grade")
        var_treat_el = _within_class_var(g_treat, "std_score_el",
                                           "academycode", "std_grp")

        delta_eb = var_ctrl_eb - var_treat_eb
        delta_el = var_ctrl_el - var_treat_el

        r2_g = g_ctrl["score_bl"].corr(g_ctrl["score_el"]) ** 2 if len(
            g_ctrl.dropna(subset=["score_bl", "score_el"])) > 10 else np.nan

        print(f"  Grade {int(g)}:")
        print(f"    Within-class Var(EB):  ctrl={var_ctrl_eb:.4f}  "
              f"treat={var_treat_eb:.4f}  ΔV={delta_eb:+.4f}")
        print(f"    Within-class Var(EL):  ctrl={var_ctrl_el:.4f}  "
              f"treat={var_treat_el:.4f}  ΔV={delta_el:+.4f}")
        print(f"    r²={r2_g:.4f}  "
              f"{'Tracking REDUCES dispersion' if delta_eb > 0 else 'Tracking INCREASES dispersion'}")

    # Overall
    g_ctrl_all = sub[sub["treat"] == 0]
    g_treat_all = sub[sub["treat"] == 1]
    var_ctrl_eb_all = _within_class_var(g_ctrl_all, "std_eb",
                                          "academycode", "grade")
    var_treat_eb_all = _within_class_var(g_treat_all, "std_eb",
                                           "academycode", "std_grp")
    var_ctrl_el_all = _within_class_var(g_ctrl_all, "std_score_el",
                                          "academycode", "grade")
    var_treat_el_all = _within_class_var(g_treat_all, "std_score_el",
                                           "academycode", "std_grp")
    print(f"  Overall:")
    print(f"    Within-class Var(EB):  ctrl={var_ctrl_eb_all:.4f}  "
          f"treat={var_treat_eb_all:.4f}  "
          f"ΔV={var_ctrl_eb_all - var_treat_eb_all:+.4f}")
    print(f"    Within-class Var(EL):  ctrl={var_ctrl_el_all:.4f}  "
          f"treat={var_treat_el_all:.4f}  "
          f"ΔV={var_ctrl_el_all - var_treat_el_all:+.4f}")

    # ─── 6. Full calibration with best fixes applied ─────────────────────
    print(f"\n{'─'*50}")
    print("6. Full calibration chain WITH fixes")
    print(f"   (Quadratic ability + raw BL misfit + pooled)")
    print(f"{'─'*50}")

    full = sub.dropna(subset=["misfit_bl", "std_score_bl"]).copy()

    # Step 1: λ from Y = -λ·misfit_bl + γ·s + δ·s² + ε
    res1 = ols_cluster(full["std_score_el"],
                        full[["misfit_bl", "std_score_bl", "std_bl_sq"]],
                        full["ggroup"])
    lambda_hat = -res1.params["misfit_bl"]
    print(f"  Step 1: λ = {lambda_hat:+.4f} "
          f"(t={-res1.tvalues['misfit_bl']:.2f})")

    # Step 2: add treatment
    res2 = ols_cluster(full["std_score_el"],
                        full[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                        full["ggroup"])
    lambda_hat2 = -res2.params["misfit_bl"]
    tau_hat = res2.params["treat"]
    print(f"  Step 2: λ = {lambda_hat2:+.4f}  τ = {tau_hat:+.4f}")

    # Step 3: ρ
    if tau_hat < 0 and lambda_hat2 > 0:
        rho_hat = 2 * np.sqrt(lambda_hat2 * (-tau_hat))
        print(f"  Step 3: ρ = {rho_hat:.4f}")
    else:
        rho_hat = np.nan
        reasons = []
        if lambda_hat2 <= 0:
            reasons.append(f"λ={lambda_hat2:.4f} ≤ 0")
        if tau_hat >= 0:
            reasons.append(f"τ={tau_hat:.4f} ≥ 0")
        print(f"  Step 3: ρ undefined ({'; '.join(reasons)})")

    # Step 4: threshold by grade
    for g in grades:
        g_ctrl = ctrl & (df["grade"] == g) & df["score_bl"].notna()
        sigma2 = df.loc[g_ctrl, "std_score_bl"].var()
        mask_r2 = g_ctrl & df["score_el"].notna()
        r2_obs = (df.loc[mask_r2, "score_bl"].corr(
                   df.loc[mask_r2, "score_el"]) ** 2
                  if mask_r2.sum() > 10 else np.nan)
        if pd.notna(rho_hat) and lambda_hat2 > 0 and sigma2 > 0:
            r2_star = rho_hat ** 2 / (4 * lambda_hat2 ** 2 * sigma2)
            verdict = "FAIL" if r2_obs < r2_star else "PASS"
            print(f"  Grade {int(g)}: r²_obs={r2_obs:.4f}  "
                  f"σ²={sigma2:.4f}  r²*={r2_star:.4f}  → {verdict}")
        else:
            print(f"  Grade {int(g)}: r²_obs={r2_obs:.4f}  "
                  f"σ²={sigma2:.4f}  r²*=NA")

    # ─── 7. EB sensitivity: what if we used different r²? ────────────────
    print(f"\n{'─'*50}")
    print("7. EB sensitivity (varying the shrinkage weight)")
    print(f"{'─'*50}")

    for r2_test in [0.01, 0.05, 0.10, 0.20, 0.50]:
        test_sub = sub.copy()
        for g in grades:
            g_ctrl_mask = ctrl & (sub["grade"] == g)
            mu_g = sub.loc[g_ctrl_mask, "score_bl"].mean()
            g_mask = sub["grade"] == g
            has_bl = g_mask & sub["score_bl"].notna()
            test_sub.loc[has_bl, "_eb_test"] = (
                mu_g + r2_test * (sub.loc[has_bl, "score_bl"] - mu_g))
            test_sub.loc[g_mask & ~has_bl, "_eb_test"] = mu_g
            ctrl_mean = test_sub.loc[g_ctrl_mask, "_eb_test"].mean()
            ctrl_sd = test_sub.loc[g_ctrl_mask, "_eb_test"].std()
            if ctrl_sd > 0:
                test_sub.loc[g_mask, "_seb_test"] = (
                    (test_sub.loc[g_mask, "_eb_test"] - ctrl_mean) / ctrl_sd)

        for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
            cm = test_sub.groupby(["academycode", grp_type]
                                   )["_seb_test"].transform("mean")
            test_sub[f"_cm_{suffix}"] = cm
        test_sub["_cm"] = np.where(test_sub["treat"] == 1,
                                    test_sub["_cm_treat"], test_sub["_cm_ctrl"])
        test_sub["_misfit_test"] = (test_sub["_seb_test"] - test_sub["_cm"]) ** 2
        test_sub["_seb2"] = test_sub["_seb_test"] ** 2

        valid = test_sub.dropna(subset=["_misfit_test", "_seb_test"])
        try:
            res = ols_cluster(valid["std_score_el"],
                               valid[["_misfit_test", "_seb_test", "_seb2"]],
                               valid["ggroup"])
            lam = -res.params["_misfit_test"]
            print(f"  r²={r2_test:.2f}:  λ={lam:+.4f} "
                  f"(t={-res.tvalues['_misfit_test']:.2f})  N={len(valid)}")
        except Exception as e:
            print(f"  r²={r2_test:.2f}:  FAILED ({e})")

    print(f"\n✓ Diagnostics complete for {label}")


def _within_class_var(df_sub, var, acad_col, class_col):
    """Weighted-mean within-classroom variance."""
    groups = df_sub.groupby([acad_col, class_col])[var]
    var_within = groups.transform("var")
    return var_within.mean()


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "both"
    if target == "both":
        for c in ["liberia", "kenya"]:
            try:
                run_diagnostics(c)
            except Exception as e:
                print(f"\n⚠ {c}: {e}")
                import traceback; traceback.print_exc()
    else:
        run_diagnostics(target)
