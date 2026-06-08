#!/usr/bin/env python3
"""
run_analysis.py — Run all 6 analysis phases for a given country.

Aligned with cursor_handoff specifications:
  - Strata FE as main spec (absorb(strata))
  - Borusyak-Hull with decile×T FE (β_P only; M absorbed)
  - Calibration: λ → ρ → threshold chain

Usage:
    python run_analysis.py liberia
    python run_analysis.py kenya
    python run_analysis.py both
"""

import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as scipy_stats

from config import get_config, OUT, SEED
from utils import (ols_cluster, coef_str, se_str, stars,
                   leave_self_out_mean, standardise_by_grade,
                   strata_fe, decile_treat_fe)

np.random.seed(SEED)


def run_all(country, matched_only=False):
    cfg = get_config(country)
    label = cfg["label"]
    prefix = cfg["OUT_PREFIX"]

    if matched_only:
        label += " (matched only)"
        prefix += "m_"

    print("\n" + "=" * 70)
    print(f"  FULL ANALYSIS PIPELINE — {label}")
    print("=" * 70)

    df_full = pd.read_parquet(cfg["ANALYSIS_FILE"])
    df = df_full[df_full["finsamp"] == True].copy()

    if matched_only and "matched_grp" in df.columns:
        n_before = len(df)
        df = df[df["matched_grp"] == True].copy()
        print(f"Matched-only filter: {n_before:,d} → {len(df):,d} "
              f"(dropped {n_before - len(df):,d} inferred-assignment students)")

    print(f"Analysis sample: {len(df):,d} students "
          f"({df['has_el'].sum():,d} with endline)")

    if country == "kenya":
        experiments = [("Stacked (G1-2)", "exp0")]
    elif country == "kenya2":
        experiments = [
            ("Stacked (G1-3)", "exp0"),
            ("Grades 1-2",     "exp2"),
        ]
    elif country == "nigeria":
        experiments = [("Stacked (P1-P3)", "exp0")]
    else:
        experiments = [
            ("Stacked",    "exp0"),
            ("Grades 3-4", "exp1"),
            ("Grades 1-2", "exp2"),
        ]

    ctrl = df["treat"] == 0
    grades = sorted(df["grade"].dropna().unique())

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1: Reduced-form ITT  (strata FE)
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 1: ITT effects ({label})")
    print(f"{'─'*50}")

    itt_rows = []
    for exp_label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
        ctrl_mean = sub.loc[sub["treat"] == 0, "std_score_el"].mean()
        s_dum = strata_fe(sub["strata"])
        X = pd.concat([sub[["treat", "std_eb"]], s_dum], axis=1)
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        itt_rows.append({
            "Sample": exp_label,
            "Control mean": f"{ctrl_mean:.3f}",
            "Coef": coef_str(res, "treat"),
            "SE": se_str(res, "treat"),
            "N": f"{len(sub):,d}",
        })
        print(f"  {exp_label:20s}  β={coef_str(res, 'treat'):>10s}  "
              f"{se_str(res, 'treat'):>10s}  N={len(sub):,d}")

    pd.DataFrame(itt_rows).to_csv(OUT / f"{prefix}table1_itt.txt",
                                   sep="\t", index=False)

    # Upper/lower interaction
    print(f"\n  Effects by upper/lower group:")
    int_rows = []
    for exp_label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
        sub["treat_x_upper"] = sub["treat"] * sub["upper_group"]
        s_dum = strata_fe(sub["strata"])
        X = pd.concat([sub[["treat", "treat_x_upper", "upper_group", "std_eb"]],
                        s_dum], axis=1)
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

        b_upper = res.params["treat"] + res.params["treat_x_upper"]
        se_upper = np.sqrt(
            res.cov_params().loc["treat", "treat"] +
            res.cov_params().loc["treat_x_upper", "treat_x_upper"] +
            2 * res.cov_params().loc["treat", "treat_x_upper"]
        )
        t_upper = b_upper / se_upper
        p_upper = 2 * (1 - scipy_stats.t.cdf(abs(t_upper), res.df_resid))

        int_rows.append({
            "Sample": exp_label,
            "Lower group": coef_str(res, "treat"),
            "SE(lower)": se_str(res, "treat"),
            "Treat x Upper": coef_str(res, "treat_x_upper"),
            "SE(TxU)": se_str(res, "treat_x_upper"),
            "Upper effect": f"{b_upper:.3f}{stars(p_upper)}",
            "p(upper)": f"{p_upper:.3f}",
            "N": f"{len(sub):,d}",
        })
        print(f"  {exp_label:20s}  lower={coef_str(res, 'treat'):>10s}  "
              f"TxU={coef_str(res, 'treat_x_upper'):>10s}  "
              f"upper={b_upper:.3f} (p={p_upper:.3f})")

    pd.DataFrame(int_rows).to_csv(OUT / f"{prefix}table1_itt_upper.txt",
                                   sep="\t", index=False)

    # Within-class dispersion
    print(f"\n  Within-class dispersion:")
    disp_rows = []
    for out_label, out_var in [("EB ability", "dev_eb"), ("Endline", "dev_el")]:
        for exp_label, exp_col in experiments:
            sub = df[(df[exp_col] == 1) & df[out_var].notna()].copy()
            s_dum = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat", "std_eb"]], s_dum], axis=1)
            res = ols_cluster(sub[out_var], X, sub["ggroup"])
            c_mean = sub.loc[sub["treat"] == 0, out_var].mean()
            disp_rows.append({
                "Outcome": out_label, "Sample": exp_label,
                "Ctrl mean": f"{c_mean:.3f}",
                "Coef": coef_str(res, "treat"),
                "SE": se_str(res, "treat"),
            })
            print(f"    {out_label:12s} | {exp_label:20s}  "
                  f"ctrl={c_mean:.3f}  β={coef_str(res, 'treat'):>10s}")

    pd.DataFrame(disp_rows).to_csv(OUT / f"{prefix}table5_dispersion.txt",
                                    sep="\t", index=False)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2: Diagnostic reliability
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 2: Diagnostic reliability ({label})")
    print(f"{'─'*50}")

    rel_rows = []
    for g in grades:
        g_ctrl = ctrl & (df["grade"] == g)

        mask_be = g_ctrl & df["score_bl"].notna() & df["score_el"].notna()
        if mask_be.sum() > 10:
            corr_be = df.loc[mask_be, "score_bl"].corr(df.loc[mask_be, "score_el"])
            r2_be = corr_be ** 2
        else:
            corr_be, r2_be = np.nan, np.nan

        mask_bm = g_ctrl & df["score_bl"].notna() & df["score_ml"].notna()
        corr_bm = (df.loc[mask_bm, "score_bl"].corr(df.loc[mask_bm, "score_ml"])
                    if mask_bm.sum() > 10 else np.nan)

        sigma2 = df.loc[g_ctrl & df["score_bl"].notna(), "score_bl"].var()

        rel_rows.append({
            "Grade": int(g),
            "r²=R²(BL→EL)": round(r2_be, 4) if pd.notna(r2_be) else np.nan,
            "cor(BL,EL)": round(corr_be, 4) if pd.notna(corr_be) else np.nan,
            "cor(BL,ML)": round(corr_bm, 4) if pd.notna(corr_bm) else np.nan,
            "σ²(BL)": round(sigma2, 2),
            "N": mask_be.sum(),
        })
        print(f"  Grade {int(g)}: r²={r2_be:.4f}  σ²(BL)={sigma2:.2f}  "
              f"cor(BL,ML)={'NA' if pd.isna(corr_bm) else f'{corr_bm:.4f}'}  "
              f"N={mask_be.sum()}")

    rel_df = pd.DataFrame(rel_rows)
    rel_df.to_csv(OUT / f"{prefix}table2_reliability.txt", sep="\t", index=False)

    # Scatter plot
    ncols = len(grades)
    fig, axes = plt.subplots(1, ncols, figsize=(5 * ncols, 4.5), squeeze=False)
    for idx, g in enumerate(grades):
        ax = axes[0, idx]
        mask = ctrl & (df["grade"] == g) & df["std_score_bl"].notna() & df["std_score_el"].notna()
        x, y = df.loc[mask, "std_score_bl"], df.loc[mask, "std_score_el"]
        ax.scatter(x, y, alpha=0.15, s=8, color="steelblue")
        if len(x) > 2:
            z = np.polyfit(x.values, y.values, 1)
            xline = np.linspace(x.min(), x.max(), 100)
            ax.plot(xline, np.polyval(z, xline), color="darkred", lw=2)
        r2 = np.corrcoef(x, y)[0, 1] ** 2 if len(x) > 2 else 0
        ax.set_title(f"Grade {int(g)} (R²={r2:.3f}, N={mask.sum()})")
        ax.set_xlabel("Std. baseline"); ax.set_ylabel("Std. endline")
    fig.suptitle(f"BL→EL signal, control group ({label})", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / f"{prefix}fig2_scatter.pdf"); plt.close()

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3: τ(s) — Treatment Effect Heterogeneity
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 3: τ(s) ({label})")
    print(f"{'─'*50}")

    # 3.1 Decile-by-decile ITT (simple experimental estimate within each bin)
    dec_results = []
    for d in sorted(df["bl_decile"].dropna().unique()):
        sub = df[(df["bl_decile"] == d) & df["std_score_el"].notna()]
        if len(sub) < 20 or sub["treat"].nunique() < 2:
            continue
        try:
            res = ols_cluster(sub["std_score_el"], sub[["treat"]], sub["ggroup"])
            dec_results.append({"decile": d, "coef": res.params["treat"],
                                 "se": res.bse["treat"], "N": len(sub)})
            print(f"  Decile {d:2.0f}: β={res.params['treat']:7.3f} "
                  f"({res.bse['treat']:.3f})  N={len(sub):,d}")
        except Exception as e:
            print(f"  Decile {d:2.0f}: SKIPPED ({e})")

    dec_df = pd.DataFrame(dec_results)
    dec_df.to_csv(OUT / f"{prefix}table3_tau_s.txt", sep="\t", index=False)

    if len(dec_df) > 0:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.errorbar(dec_df["decile"], dec_df["coef"], yerr=1.96 * dec_df["se"],
                    fmt="o-", color="steelblue", capsize=4, lw=2, markersize=6)
        ax.axhline(0, color="gray", ls="--", lw=1)
        ax.set_xlabel("Baseline score decile (within grade)")
        ax.set_ylabel("Treatment effect (std. endline)")
        ax.set_title(f"τ(s): Treatment effect by baseline ability ({label})")
        fig.tight_layout()
        fig.savefig(OUT / f"{prefix}fig2_tau_s.pdf"); plt.close()

    # 3.2 Cutoff proximity test (model predicts τ(s) most negative near cutoff)
    print(f"\n  Cutoff proximity test:")
    sub_cut = df[df["std_score_el"].notna() & df["dist_from_cutoff"].notna()].copy()
    sub_cut["treat_x_dist"] = sub_cut["treat"] * sub_cut["dist_from_cutoff"]
    s_dum = strata_fe(sub_cut["strata"])
    X_cut = pd.concat([sub_cut[["treat", "treat_x_dist", "dist_from_cutoff", "std_eb"]],
                        s_dum], axis=1)
    try:
        res_cut = ols_cluster(sub_cut["std_score_el"], X_cut, sub_cut["ggroup"])
        print(f"    T:          {coef_str(res_cut, 'treat'):>10s}  {se_str(res_cut, 'treat')}")
        print(f"    T×|s-c|:    {coef_str(res_cut, 'treat_x_dist'):>10s}  "
              f"{se_str(res_cut, 'treat_x_dist')}")
        print(f"    (Positive T×|s-c| = effect improves away from cutoff)")
    except Exception as e:
        print(f"    FAILED: {e}")

    # 3.3 ΔP(s), ΔM(s), ΔY(s) experimental contrasts
    print(f"\n  ΔP(s), ΔM(s), ΔY(s) by decile:")
    delta_rows = []
    for d in sorted(df["bl_decile"].dropna().unique()):
        sub = df[df["bl_decile"] == d].copy()
        t_mask = sub["treat"] == 1
        c_mask = sub["treat"] == 0
        row = {"decile": d}
        for v, vname in [("peer_eb", "ΔP"), ("misfit", "ΔM"), ("std_score_el", "ΔY")]:
            t_m = sub.loc[t_mask, v].mean()
            c_m = sub.loc[c_mask, v].mean()
            row[vname] = t_m - c_m if pd.notna(t_m) and pd.notna(c_m) else np.nan
        delta_rows.append(row)
        if pd.notna(row.get("ΔY")):
            print(f"    Decile {d:2.0f}:  ΔP={row['ΔP']:+.3f}  "
                  f"ΔM={row['ΔM']:+.3f}  ΔY={row['ΔY']:+.3f}")

    delta_df = pd.DataFrame(delta_rows).dropna()
    if len(delta_df) > 0:
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
        for ax, col, title in zip(axes, ["ΔP", "ΔM", "ΔY"],
                                    ["ΔP(s): Peer ability", "ΔM(s): Misfit",
                                     "ΔY(s): Outcome"]):
            ax.bar(delta_df["decile"], delta_df[col], color="steelblue", alpha=0.7)
            ax.axhline(0, color="gray", ls="--", lw=1)
            ax.set_xlabel("BL decile")
            ax.set_title(title)
        fig.suptitle(f"Experimental contrasts by baseline score ({label})", fontsize=14)
        fig.tight_layout(rect=[0, 0, 1, 0.93])
        fig.savefig(OUT / f"{prefix}fig3_delta.pdf"); plt.close()

    # 3.4 Quartile effects
    df["bl_quartile"] = np.nan
    for g in grades:
        mask = (df["grade"] == g) & df["std_score_bl"].notna()
        df.loc[mask, "bl_quartile"] = pd.qcut(
            df.loc[mask, "std_score_bl"], q=4, labels=False, duplicates="drop") + 1

    print("\n  By quartile:")
    q_rows = []
    for q in sorted(df["bl_quartile"].dropna().unique()):
        sub = df[(df["bl_quartile"] == q) & df["std_score_el"].notna()]
        if len(sub) < 20:
            continue
        try:
            s_dum = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat", "std_eb"]], s_dum], axis=1)
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            q_rows.append({"Q": f"Q{int(q)}", "Coef": coef_str(res, "treat"),
                            "SE": se_str(res, "treat"), "N": f"{len(sub):,d}"})
            print(f"    Q{int(q)}: β={coef_str(res, 'treat'):>10s}  "
                  f"{se_str(res, 'treat'):>10s}  N={len(sub):,d}")
        except Exception as e:
            print(f"    Q{int(q)}: SKIPPED ({e})")
    pd.DataFrame(q_rows).to_csv(OUT / f"{prefix}table3_quartiles.txt",
                                 sep="\t", index=False)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 4: Mechanism Analysis (Borusyak-Hull)
    #
    #   Y = β_P·P + decile×T FE + strata FE + ε
    #
    #   Under scripted instruction, M is absorbed by decile×T FE.
    #   Identifying variation: cross-school differences in P within
    #   (decile, treatment) cells.
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 4: Mechanisms — Borusyak-Hull ({label})")
    print(f"{'─'*50}")

    mech_rows = []
    for exp_label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()
                  & df["bl_decile"].notna() & df["peer_eb"].notna()].copy()

        n_cells = sub.groupby(["bl_decile", "treat"]).ngroups
        print(f"  {exp_label}: {len(sub):,d} obs, {n_cells} decile×T cells")

        s_dum = strata_fe(sub["strata"])
        dt_dum = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_eb"]], dt_dum, s_dum], axis=1)

        try:
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            row = {"Sample": exp_label,
                   "β_P": coef_str(res, "peer_eb"),
                   "SE(β_P)": se_str(res, "peer_eb"),
                   "N": f"{len(sub):,d}",
                   "Cells": n_cells}
            mech_rows.append(row)
            print(f"    β_P = {coef_str(res, 'peer_eb'):>10s}  "
                  f"{se_str(res, 'peer_eb'):>10s}")
        except Exception as e:
            print(f"    FAILED: {e}")

    pd.DataFrame(mech_rows).to_csv(OUT / f"{prefix}table6_mechanism.txt",
                                    sep="\t", index=False)

    # Robustness: raw BL peer mean
    print(f"\n  Robustness: raw BL peer mean")
    for exp_label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()
                  & df["bl_decile"].notna() & df["peer_bl"].notna()].copy()
        s_dum = strata_fe(sub["strata"])
        dt_dum = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_bl"]], dt_dum, s_dum], axis=1)
        try:
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            print(f"    {exp_label:20s}  β_P(raw)={coef_str(res, 'peer_bl'):>10s}  "
                  f"{se_str(res, 'peer_bl'):>10s}")
        except Exception as e:
            print(f"    {exp_label:20s}  FAILED: {e}")

    # Robustness: add class size
    print(f"\n  Robustness: with class size control")
    for exp_label, exp_col in experiments:
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()
                  & df["bl_decile"].notna() & df["peer_eb"].notna()
                  & df["csize"].notna()].copy()
        s_dum = strata_fe(sub["strata"])
        dt_dum = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_eb", "csize"]], dt_dum, s_dum], axis=1)
        try:
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            print(f"    {exp_label:20s}  β_P={coef_str(res, 'peer_eb'):>10s}  "
                  f"β_C={coef_str(res, 'csize'):>10s}")
        except Exception as e:
            print(f"    {exp_label:20s}  FAILED: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 5: Model Calibration
    #
    # 5A. Variance decomposition (model-free, purely experimental)
    # 5B. Structural calibration (λ → ρ → threshold)
    #     KEY FIX: control for std_eb² to separate the quadratic
    #     ability-outcome relationship from the misfit penalty.
    #     Use raw BL misfit to avoid EB shrinkage artifacts.
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 5A: Variance decomposition ({label})")
    print(f"{'─'*50}")

    def _within_class_var(d, var, acad_col, class_col):
        return d.groupby([acad_col, class_col])[var].transform("var").mean()

    decomp_rows = []
    for g in grades:
        g_df = df[(df["grade"] == g) & df["std_score_el"].notna()]
        g_c = g_df[g_df["treat"] == 0]
        g_t = g_df[g_df["treat"] == 1]
        if len(g_c) < 10 or len(g_t) < 10:
            continue

        v_c_eb = _within_class_var(g_c, "std_eb", "academycode", "grade")
        v_t_eb = _within_class_var(g_t, "std_eb", "academycode", "std_grp")
        v_c_el = _within_class_var(g_c, "std_score_el", "academycode", "grade")
        v_t_el = _within_class_var(g_t, "std_score_el", "academycode", "std_grp")

        g_ctrl_mask = ctrl & (df["grade"] == g)
        mask_r2 = g_ctrl_mask & df["score_bl"].notna() & df["score_el"].notna()
        r2_g = (df.loc[mask_r2, "score_bl"].corr(df.loc[mask_r2, "score_el"]) ** 2
                if mask_r2.sum() > 10 else np.nan)

        decomp_rows.append({
            "Grade": int(g), "r²": round(r2_g, 4),
            "Var_EB_ctrl": round(v_c_eb, 4), "Var_EB_treat": round(v_t_eb, 4),
            "ΔV_EB": round(v_c_eb - v_t_eb, 4),
            "Var_EL_ctrl": round(v_c_el, 4), "Var_EL_treat": round(v_t_el, 4),
            "ΔV_EL": round(v_c_el - v_t_el, 4),
        })
        dv_eb = v_c_eb - v_t_eb
        dv_el = v_c_el - v_t_el
        print(f"  Grade {int(g)}: r²={r2_g:.4f}  "
              f"ΔV(EB)={dv_eb:+.4f}  ΔV(EL)={dv_el:+.4f}  "
              f"{'sort helps' if dv_el > 0 else 'sort hurts'}")

    pd.DataFrame(decomp_rows).to_csv(OUT / f"{prefix}table7a_variance_decomp.txt",
                                      sep="\t", index=False)

    # ── 5B. Structural calibration (pooled, with quadratic fix) ──────────
    print(f"\n{'─'*50}")
    print(f"Phase 5B: Structural calibration ({label})")
    print(f"{'─'*50}")

    # Build raw-BL misfit (avoids EB shrinkage issues, since std_eb ≈ std_bl)
    sub_cal = df[df["std_score_el"].notna() & df["std_score_bl"].notna()].copy()
    for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
        cm = sub_cal.groupby(["academycode", grp_type]
                              )["std_score_bl"].transform("mean")
        sub_cal[f"_cm_{suffix}"] = cm
    sub_cal["_cm"] = np.where(sub_cal["treat"] == 1,
                               sub_cal["_cm_treat"], sub_cal["_cm_ctrl"])
    sub_cal["misfit_bl"] = (sub_cal["std_score_bl"] - sub_cal["_cm"]) ** 2
    sub_cal["std_bl_sq"] = sub_cal["std_score_bl"] ** 2

    cal_rows = []

    # Step 1: Y = -λ·misfit + γ·s + δ·s² + ε  (quadratic control fixes λ sign)
    res1 = ols_cluster(sub_cal["std_score_el"],
                        sub_cal[["misfit_bl", "std_score_bl", "std_bl_sq"]],
                        sub_cal["ggroup"])
    lambda_hat = -res1.params["misfit_bl"]
    print(f"  Step 1 (pooled): λ = {lambda_hat:+.4f} "
          f"(t={-res1.tvalues['misfit_bl']:.2f}, N={len(sub_cal)})")

    # Step 2: add treatment
    res2 = ols_cluster(sub_cal["std_score_el"],
                        sub_cal[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                        sub_cal["ggroup"])
    lambda_hat2 = -res2.params["misfit_bl"]
    tau_hat = res2.params["treat"]
    print(f"  Step 2 (pooled): λ = {lambda_hat2:+.4f}  τ = {tau_hat:+.4f} "
          f"(t_τ={res2.tvalues['treat']:.2f})")

    # Step 3: ρ
    if tau_hat < 0 and lambda_hat2 > 0:
        rho_hat = 2 * np.sqrt(lambda_hat2 * (-tau_hat))
        print(f"  Step 3: ρ = {rho_hat:.4f}")
    elif tau_hat >= 0:
        rho_hat = np.nan
        print(f"  Step 3: τ ≥ 0 → tracking has NET BENEFIT beyond matching. "
              f"Distortion term Ω ≤ 0; ρ not applicable.")
    else:
        rho_hat = np.nan
        print(f"  Step 3: λ ≤ 0 → model structure not supported. ρ undefined.")

    # Step 4: threshold by grade (using standardized σ² ≈ 1)
    for g in grades:
        g_ctrl_mask = ctrl & (df["grade"] == g) & df["score_bl"].notna()
        sigma2 = df.loc[g_ctrl_mask, "std_score_bl"].var()
        mask_r2 = g_ctrl_mask & df["score_el"].notna()
        r2_obs = (df.loc[mask_r2, "score_bl"].corr(
                   df.loc[mask_r2, "score_el"]) ** 2
                  if mask_r2.sum() > 10 else np.nan)

        if pd.notna(rho_hat) and lambda_hat2 > 0 and sigma2 > 0:
            r2_star = rho_hat ** 2 / (4 * lambda_hat2 ** 2 * sigma2)
            verdict = "FAIL" if r2_obs < r2_star else "PASS"
        else:
            r2_star = np.nan
            verdict = "τ>0 → PASS" if tau_hat >= 0 else "NA"

        cal_rows.append({
            "Grade": int(g), "r²_obs": round(r2_obs, 4) if pd.notna(r2_obs) else np.nan,
            "σ²": round(sigma2, 4), "λ": round(lambda_hat2, 4),
            "τ": round(tau_hat, 4),
            "ρ": round(rho_hat, 4) if pd.notna(rho_hat) else np.nan,
            "r²*": round(r2_star, 4) if pd.notna(r2_star) else np.nan,
            "Verdict": verdict, "N": len(sub_cal),
        })
        r2t_str = f"{r2_star:.4f}" if pd.notna(r2_star) else "NA"
        print(f"  Grade {int(g)}: r²_obs={r2_obs:.4f}  σ²={sigma2:.4f}  "
              f"r²*={r2t_str}  → {verdict}")

    pd.DataFrame(cal_rows).to_csv(OUT / f"{prefix}table7b_calibration.txt",
                                   sep="\t", index=False)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 6: Robustness
    # ═══════════════════════════════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print(f"Phase 6: Robustness ({label})")
    print(f"{'─'*50}")

    sub = df[df["std_score_el"].notna()].copy()
    s_dum = strata_fe(sub["strata"])

    rob_rows = []
    specs = [
        ("(A) EB + strata FE",
         pd.concat([sub[["treat", "std_eb"]], s_dum], axis=1)),
        ("(B) Raw BL + strata FE",
         pd.concat([sub[["treat", "std_score_bl"]], s_dum], axis=1)),
        ("(C) No BL + strata FE",
         pd.concat([sub[["treat"]], s_dum], axis=1)),
        ("(D) EB + linear P_t",
         sub[["treat", "std_eb", "P_t"]].copy()),
    ]
    for spec_label, X in specs:
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        rob_rows.append({"Spec": spec_label, "Coef": coef_str(res, "treat"),
                          "SE": se_str(res, "treat"), "N": f"{len(sub):,d}"})
        print(f"  {spec_label:30s}  β={coef_str(res, 'treat'):>10s}  "
              f"{se_str(res, 'treat'):>10s}")

    pd.DataFrame(rob_rows).to_csv(OUT / f"{prefix}table8_robustness.txt",
                                   sep="\t", index=False)

    # Balance
    print(f"\n  Balance:")
    for v in ["score_bl", "has_el", "upper_group"]:
        t_vals = df.loc[df["treat"] == 1, v].dropna()
        c_vals = df.loc[df["treat"] == 0, v].dropna()
        if len(t_vals) > 5 and len(c_vals) > 5:
            _, p = scipy_stats.ttest_ind(t_vals, c_vals, equal_var=False)
        else:
            p = np.nan
        print(f"    {v:15s}  T={t_vals.mean():.3f}  C={c_vals.mean():.3f}  p={p:.3f}")

    # Attrition
    print(f"\n  Attrition:")
    df_att = df_full[df_full["treat"].notna()].copy()
    df_att["attrited"] = (~df_att["has_el"]).astype(float)
    att_t = df_att.loc[df_att["treat"] == 1, "attrited"].mean()
    att_c = df_att.loc[df_att["treat"] == 0, "attrited"].mean()
    s_dum_att = strata_fe(df_att["strata"])
    X_att = pd.concat([df_att[["treat"]], s_dum_att], axis=1)
    res_att = ols_cluster(df_att["attrited"], X_att, df_att["ggroup"])
    print(f"    T={att_t:.3f}  C={att_c:.3f}  "
          f"diff={coef_str(res_att, 'treat'):>10s}  {se_str(res_att, 'treat')}")

    # Permutation inference (within strata)
    N_PERMS = 999
    print(f"\n  Permutation inference ({N_PERMS} iters, within-strata):")
    sub = df[df["std_score_el"].notna()].copy()
    s_dum = strata_fe(sub["strata"])
    X_real = pd.concat([sub[["treat", "std_eb"]], s_dum], axis=1)
    res_real = ols_cluster(sub["std_score_el"], X_real, sub["ggroup"])
    t_real = res_real.tvalues["treat"]

    ggroup_info = sub.drop_duplicates("ggroup")[["ggroup", "treat", "strata"]].copy()
    t_perms = []
    for _ in range(N_PERMS):
        pi = ggroup_info.copy()
        pi["treat_perm"] = pi.groupby("strata")["treat"].transform(
            lambda x: x.sample(frac=1, replace=False).values)
        pmap = dict(zip(pi["ggroup"], pi["treat_perm"]))
        sub["tp"] = sub["ggroup"].map(pmap)
        Xp = pd.concat([sub[["tp", "std_eb"]].rename(columns={"tp": "treat"}),
                          s_dum], axis=1)
        try:
            rp = ols_cluster(sub["std_score_el"], Xp, sub["ggroup"])
            t_perms.append(rp.tvalues["treat"])
        except Exception as e:
            if i < 3:
                print(f"    Perm {i}: FAILED ({e})")

    t_perms = np.array(t_perms)
    p_perm = (np.abs(t_perms) >= np.abs(t_real)).mean()
    print(f"    t-stat={t_real:.3f}  permutation p={p_perm:.3f}")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(t_perms, bins=30, color="steelblue", alpha=0.7, density=True)
    ax.axvline(t_real, color="darkred", lw=2, ls="--",
               label=f"Observed (t={t_real:.2f})")
    ax.set_title(f"Permutation inference — {label} (p={p_perm:.3f})")
    ax.legend(); fig.tight_layout()
    fig.savefig(OUT / f"{prefix}fig6_permutation.pdf"); plt.close()

    print(f"\n✓ All phases complete for {label}")
    return df


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "both"

    if target == "both":
        for c in ["liberia", "kenya", "kenya2", "nigeria"]:
            try:
                run_all(c)
            except FileNotFoundError as e:
                print(f"\n⚠ Skipping {c}: {e}")
        try:
            run_all("kenya2", matched_only=True)
        except FileNotFoundError as e:
            print(f"\n⚠ Skipping kenya2 matched-only: {e}")
    elif target == "kenya2":
        run_all("kenya2")
        run_all("kenya2", matched_only=True)
    else:
        run_all(target)
