#!/usr/bin/env python3
"""
Two investigations:
  A. Deep dive into Kenya β_P = -0.21** (negative peer effect)
  B. Cross-country pooled analysis (T × Country, T × r²)
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as scipy_stats

from config import get_config, OUT, SEED
from utils import (ols_cluster, coef_str, se_str, stars, leave_self_out_mean,
                   strata_fe, decile_treat_fe)

np.random.seed(SEED)


# ═════════════════════════════════════════════════════════════════════════════
# A. PEER EFFECT INVESTIGATION (Kenya)
# ═════════════════════════════════════════════════════════════════════════════

def investigate_peer_effect():
    cfg = get_config("kenya")
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    df = df[df["finsamp"] == True].copy()

    print("\n" + "=" * 70)
    print("  A. DEEP DIVE: Kenya β_P = -0.21**")
    print("=" * 70)

    sub = df[df["std_score_el"].notna() & df["bl_decile"].notna()
             & df["peer_eb"].notna()].copy()

    # ── A1. β_P by grade ─────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    print("A1. β_P by grade")
    print(f"{'─'*50}")

    for g in [1, 2]:
        g_sub = sub[sub["grade"] == g]
        s_dum = strata_fe(g_sub["strata"])
        dt_dum = decile_treat_fe(g_sub["bl_decile"], g_sub["treat"])
        X = pd.concat([g_sub[["peer_eb"]], dt_dum, s_dum], axis=1)
        try:
            res = ols_cluster(g_sub["std_score_el"], X, g_sub["ggroup"])
            print(f"  Grade {g}: β_P = {coef_str(res, 'peer_eb'):>10s}  "
                  f"{se_str(res, 'peer_eb'):>10s}  N={len(g_sub):,d}")
        except Exception as e:
            print(f"  Grade {g}: FAILED ({e})")

    # ── A2. β_P by upper/lower group ────────────────────────────────────
    print(f"\n{'─'*50}")
    print("A2. β_P by upper/lower group")
    print(f"{'─'*50}")

    for grp, label in [(0, "Lower"), (1, "Upper")]:
        g_sub = sub[sub["upper_group"] == grp]
        if len(g_sub) < 50:
            continue
        s_dum = strata_fe(g_sub["strata"])
        dt_dum = decile_treat_fe(g_sub["bl_decile"], g_sub["treat"])
        X = pd.concat([g_sub[["peer_eb"]], dt_dum, s_dum], axis=1)
        try:
            res = ols_cluster(g_sub["std_score_el"], X, g_sub["ggroup"])
            print(f"  {label:6s}: β_P = {coef_str(res, 'peer_eb'):>10s}  "
                  f"{se_str(res, 'peer_eb'):>10s}  N={len(g_sub):,d}")
        except Exception as e:
            print(f"  {label:6s}: FAILED ({e})")

    # ── A3. β_P in treatment vs control separately ──────────────────────
    print(f"\n{'─'*50}")
    print("A3. β_P in treatment vs control separately")
    print(f"   (Control: variation from different school compositions)")
    print(f"{'─'*50}")

    for t_val, t_lab in [(1, "Treatment"), (0, "Control")]:
        t_sub = sub[sub["treat"] == t_val]
        if len(t_sub) < 50:
            print(f"  {t_lab}: too few obs (N={len(t_sub)})")
            continue
        s_dum = strata_fe(t_sub["strata"])
        bl_dum = pd.get_dummies(t_sub["bl_decile"], prefix="d", drop_first=True, dtype=float)
        X = pd.concat([t_sub[["peer_eb"]], bl_dum, s_dum], axis=1)
        try:
            res = ols_cluster(t_sub["std_score_el"], X, t_sub["ggroup"])
            print(f"  {t_lab:10s}: β_P = {coef_str(res, 'peer_eb'):>10s}  "
                  f"{se_str(res, 'peer_eb'):>10s}  N={len(t_sub):,d}")
        except Exception as e:
            print(f"  {t_lab:10s}: FAILED ({e})")

    # ── A4. Peer quality vs class size correlation ───────────────────────
    print(f"\n{'─'*50}")
    print("A4. Is peer quality confounded with class size?")
    print(f"{'─'*50}")

    for t_val, t_lab in [(1, "Treatment"), (0, "Control")]:
        t_sub = sub[sub["treat"] == t_val].dropna(subset=["csize"])
        corr = t_sub["peer_eb"].corr(t_sub["csize"])
        print(f"  {t_lab}: cor(peer_eb, class_size) = {corr:.4f}  "
              f"N={len(t_sub):,d}")

    cell_ids = sub.groupby(["bl_decile", "treat"]).ngroup()
    residuals = []
    for cell_id in cell_ids.unique():
        cell = sub[cell_ids == cell_id].dropna(subset=["peer_eb", "csize"])
        if len(cell) > 5:
            residuals.append(cell[["peer_eb", "csize"]].corr().iloc[0, 1])
    if residuals:
        mean_within_corr = np.nanmean(residuals)
        print(f"  Within decile×T cells: mean cor(peer_eb, csize) = "
              f"{mean_within_corr:.4f}")

    # ── A5. School-level visualization ───────────────────────────────────
    print(f"\n{'─'*50}")
    print("A5. School-level peer quality vs outcomes")
    print(f"{'─'*50}")

    school_agg = sub.groupby(["academycode", "treat"]).agg(
        mean_peer=("peer_eb", "mean"),
        mean_el=("std_score_el", "mean"),
        mean_bl=("std_score_bl", "mean"),
        n=("studyid", "count"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, t_val, t_lab, color in zip(axes, [0, 1],
                                         ["Control", "Treatment"],
                                         ["steelblue", "firebrick"]):
        d = school_agg[school_agg["treat"] == t_val]
        ax.scatter(d["mean_peer"], d["mean_el"], s=d["n"] * 3,
                   alpha=0.6, color=color, edgecolors="white", lw=0.5)
        if len(d) > 2:
            z = np.polyfit(d["mean_peer"], d["mean_el"], 1)
            xline = np.linspace(d["mean_peer"].min(), d["mean_peer"].max(), 50)
            ax.plot(xline, np.polyval(z, xline), color="black", lw=2, ls="--")
            r = d["mean_peer"].corr(d["mean_el"])
            ax.set_title(f"{t_lab} (r={r:.3f}, N_schools={len(d)})")
        ax.set_xlabel("School mean peer EB")
        ax.set_ylabel("School mean std. endline")
    fig.suptitle("Kenya: School-level peer quality vs outcomes", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(OUT / "ke_fig_peer_school.pdf"); plt.close()
    print("  Saved ke_fig_peer_school.pdf")

    # ── A6. Residualized peer effect (partial out BL at school level) ────
    print(f"\n{'─'*50}")
    print("A6. School-level: partial out baseline ability")
    print(f"{'─'*50}")

    for t_val, t_lab in [(0, "Control"), (1, "Treatment")]:
        d = school_agg[school_agg["treat"] == t_val]
        if len(d) < 10:
            continue
        raw_corr = d["mean_peer"].corr(d["mean_el"])
        partial_corr_bl = d[["mean_peer", "mean_el", "mean_bl"]].dropna()
        if len(partial_corr_bl) > 5:
            from statsmodels.regression.linear_model import OLS
            X_bl = sm.add_constant(partial_corr_bl["mean_bl"])
            resid_peer = OLS(partial_corr_bl["mean_peer"], X_bl).fit().resid
            resid_el = OLS(partial_corr_bl["mean_el"], X_bl).fit().resid
            pcorr = np.corrcoef(resid_peer, resid_el)[0, 1]
            print(f"  {t_lab}: raw r(peer, EL) = {raw_corr:.4f}  "
                  f"partial r(peer, EL | BL) = {pcorr:.4f}")

    # ── A7. Same analysis for Liberia (comparison) ───────────────────────
    print(f"\n{'─'*50}")
    print("A7. Same β_P decomposition for Liberia (comparison)")
    print(f"{'─'*50}")

    cfg_lib = get_config("liberia")
    df_lib = pd.read_parquet(cfg_lib["ANALYSIS_FILE"])
    df_lib = df_lib[df_lib["finsamp"] == True].copy()
    sub_lib = df_lib[df_lib["std_score_el"].notna() & df_lib["bl_decile"].notna()
                      & df_lib["peer_eb"].notna()].copy()

    for t_val, t_lab in [(1, "Treatment"), (0, "Control")]:
        t_sub = sub_lib[sub_lib["treat"] == t_val]
        s_dum = strata_fe(t_sub["strata"])
        bl_dum = pd.get_dummies(t_sub["bl_decile"], prefix="d",
                                 drop_first=True, dtype=float)
        X = pd.concat([t_sub[["peer_eb"]], bl_dum, s_dum], axis=1)
        try:
            res = ols_cluster(t_sub["std_score_el"], X, t_sub["ggroup"])
            print(f"  Liberia {t_lab:10s}: β_P = {coef_str(res, 'peer_eb'):>10s}  "
                  f"{se_str(res, 'peer_eb'):>10s}  N={len(t_sub):,d}")
        except Exception as e:
            print(f"  Liberia {t_lab:10s}: FAILED ({e})")

    # ── A8. Leave-one-school-out sensitivity ─────────────────────────────
    print(f"\n{'─'*50}")
    print("A8. Leave-one-school-out sensitivity (Kenya)")
    print(f"{'─'*50}")

    academies = sub["academycode"].unique()
    loo_betas = []
    for acad in academies:
        loo_sub = sub[sub["academycode"] != acad]
        s_dum = strata_fe(loo_sub["strata"])
        dt_dum = decile_treat_fe(loo_sub["bl_decile"], loo_sub["treat"])
        X = pd.concat([loo_sub[["peer_eb"]], dt_dum, s_dum], axis=1)
        try:
            res = ols_cluster(loo_sub["std_score_el"], X, loo_sub["ggroup"])
            loo_betas.append(res.params["peer_eb"])
        except Exception:
            pass

    if loo_betas:
        loo_arr = np.array(loo_betas)
        print(f"  Full sample β_P: -0.208")
        print(f"  LOO range: [{loo_arr.min():.3f}, {loo_arr.max():.3f}]")
        print(f"  LOO mean:  {loo_arr.mean():.3f}  sd: {loo_arr.std():.3f}")
        print(f"  # times sign flips to positive: "
              f"{(loo_arr > 0).sum()}/{len(loo_arr)}")


# ═════════════════════════════════════════════════════════════════════════════
# B. CROSS-COUNTRY POOLED ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

def cross_country_pooled():
    print("\n" + "=" * 70)
    print("  B. THREE-COUNTRY POOLED ANALYSIS")
    print("=" * 70)

    datasets = {}
    r2_values = {}
    for cname in ["liberia", "kenya", "kenya2"]:
        cfg_c = get_config(cname)
        d = pd.read_parquet(cfg_c["ANALYSIS_FILE"])
        d = d[d["finsamp"] == True].copy()
        d["country"] = cname

        grade_r2 = []
        for g in d["grade"].dropna().unique():
            mask = ((d["treat"] == 0) & (d["grade"] == g)
                    & d["score_bl"].notna() & d["score_el"].notna())
            if mask.sum() > 10:
                grade_r2.append(
                    d.loc[mask, "score_bl"].corr(d.loc[mask, "score_el"]) ** 2)
        mean_r2 = np.mean(grade_r2) if grade_r2 else np.nan
        d["r2_country"] = mean_r2
        r2_values[cname] = mean_r2

        d["strata_pooled"] = f"{cname[:2].upper()}_" + d["strata"].astype(str)
        d["cluster_pooled"] = f"{cname[:2].upper()}_" + d["ggroup"].astype(str)
        datasets[cname] = d

    for cname, r2 in sorted(r2_values.items(), key=lambda x: x[1]):
        label = get_config(cname)["label"]
        print(f"  {label:15s} mean r² = {r2:.4f}  "
              f"N_finsamp = {len(datasets[cname]):,d}")

    pooled = pd.concat(datasets.values(), ignore_index=True)
    sub = pooled[pooled["std_score_el"].notna()].copy()

    country_counts = sub.groupby("country").size()
    print(f"\n  Pooled sample: {len(sub):,d} obs")
    for c, n in country_counts.items():
        print(f"    {get_config(c)['label']:15s}: {n:,d}")

    # ── B1. Country-specific ITT ─────────────────────────────────────────
    print(f"\n{'─'*50}")
    print("B1. Country-specific ITT (separate regressions)")
    print(f"{'─'*50}")

    country_itts = {}
    for cname in ["liberia", "kenya2", "kenya"]:
        c_sub = sub[sub["country"] == cname].copy()
        s_d = strata_fe(c_sub["strata_pooled"], prefix="sp")
        X = pd.concat([c_sub[["treat", "std_eb"]], s_d], axis=1)
        res = ols_cluster(c_sub["std_score_el"], X, c_sub["cluster_pooled"])
        country_itts[cname] = res
        label = get_config(cname)["label"]
        print(f"  {label:15s} (r²={r2_values[cname]:.3f}): "
              f"τ = {coef_str(res, 'treat'):>10s}  {se_str(res, 'treat')}")

    # ── B2. T × r² moderation (continuous, pooled) ───────────────────────
    print(f"\n{'─'*50}")
    print("B2. Treatment × r² (continuous moderation, 3 countries)")
    print(f"    Y = τ·T + δ·T×r² + θ_eb + strata FE + ε")
    print(f"{'─'*50}")

    s_dum = strata_fe(sub["strata_pooled"], prefix="sp")
    sub["treat_x_r2"] = sub["treat"] * sub["r2_country"]
    X2 = pd.concat([sub[["treat", "treat_x_r2", "std_eb"]], s_dum], axis=1)
    res2 = ols_cluster(sub["std_score_el"], X2, sub["cluster_pooled"])

    b_t = res2.params["treat"]
    b_txr2 = res2.params["treat_x_r2"]
    print(f"  T:              {coef_str(res2, 'treat'):>10s}  {se_str(res2, 'treat')}")
    print(f"  T×r²:           {coef_str(res2, 'treat_x_r2'):>10s}  "
          f"{se_str(res2, 'treat_x_r2')}")

    print(f"\n  Implied treatment effect at different r²:")
    for r2_val in [0.05, 0.10, 0.20, 0.35, 0.55]:
        implied = b_t + b_txr2 * r2_val
        print(f"    r²={r2_val:.2f}: τ = {implied:+.3f}")

    if b_txr2 != 0:
        breakeven = -b_t / b_txr2
        print(f"\n  Breakeven r²: {breakeven:.3f}")

    # ── B3. Quartile effects by country ──────────────────────────────────
    print(f"\n{'─'*50}")
    print("B3. Treatment effects by quartile × country")
    print(f"{'─'*50}")

    sub["bl_quartile"] = np.nan
    for cname in ["liberia", "kenya", "kenya2"]:
        for g in sub.loc[sub["country"] == cname, "grade"].dropna().unique():
            mask = ((sub["country"] == cname) & (sub["grade"] == g)
                    & sub["std_score_bl"].notna())
            if mask.sum() > 20:
                sub.loc[mask, "bl_quartile"] = pd.qcut(
                    sub.loc[mask, "std_score_bl"], q=4, labels=False,
                    duplicates="drop") + 1

    q_rows = []
    for cname in ["liberia", "kenya2", "kenya"]:
        label = get_config(cname)["label"]
        for q in sorted(sub["bl_quartile"].dropna().unique()):
            c_sub = sub[(sub["country"] == cname) & (sub["bl_quartile"] == q)
                        & sub["std_score_el"].notna()]
            if len(c_sub) < 20:
                continue
            try:
                s_d = strata_fe(c_sub["strata_pooled"], prefix="sp")
                X = pd.concat([c_sub[["treat", "std_eb"]], s_d], axis=1)
                res = ols_cluster(c_sub["std_score_el"], X,
                                  c_sub["cluster_pooled"])
                q_rows.append({
                    "Country": label, "Q": f"Q{int(q)}",
                    "r2": r2_values[cname],
                    "Coef": res.params["treat"], "SE": res.bse["treat"],
                    "N": len(c_sub),
                })
                print(f"  {label:15s} Q{int(q)}: "
                      f"β={coef_str(res, 'treat'):>10s}  "
                      f"{se_str(res, 'treat'):>10s}  N={len(c_sub):,d}")
            except Exception:
                pass

    q_df = pd.DataFrame(q_rows)
    if len(q_df) > 0:
        q_df.to_csv(OUT / "pooled3_quartile_effects.txt", sep="\t", index=False)

        countries_in_plot = q_df["Country"].unique()
        n_countries = len(countries_in_plot)
        colors = {"Liberia": "steelblue", "Kenya 2019": "darkorange",
                  "Kenya": "firebrick"}
        fig, ax = plt.subplots(figsize=(10, 5.5))
        width = 0.8 / n_countries
        q_labels = sorted(q_df["Q"].unique())
        for i, country in enumerate(countries_in_plot):
            cd = q_df[q_df["Country"] == country].sort_values("Q")
            x = np.arange(len(q_labels))
            offset = (i - (n_countries - 1) / 2) * width
            r2_c = cd["r2"].iloc[0] if len(cd) > 0 else 0
            ax.bar(x + offset, cd["Coef"], width, yerr=1.96 * cd["SE"],
                   label=f"{country} (r²≈{r2_c:.2f})",
                   color=colors.get(country, "gray"), alpha=0.7, capsize=3)
        ax.set_xticks(np.arange(len(q_labels)))
        ax.set_xticklabels(q_labels)
        ax.axhline(0, color="gray", ls="--", lw=1)
        ax.set_ylabel("Treatment effect (std. endline)")
        ax.set_xlabel("Baseline ability quartile")
        ax.set_title("Treatment effect by quartile: 3 countries")
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT / "pooled3_fig_quartiles.pdf"); plt.close()
        print("  Saved pooled3_fig_quartiles.pdf")

    # ── B4. Dispersion: T × r² (continuous) ──────────────────────────────
    print(f"\n{'─'*50}")
    print("B4. Dispersion effects: T × r² (continuous, 3 countries)")
    print(f"{'─'*50}")

    for out_var, out_label in [("dev_eb", "EB dispersion"),
                                ("dev_el", "EL dispersion")]:
        d = sub[sub[out_var].notna()].copy()
        s_d = strata_fe(d["strata_pooled"], prefix="sp")
        d["_txr2"] = d["treat"] * d["r2_country"]
        X = pd.concat([d[["treat", "std_eb"]], d["_txr2"].rename("treat_x_r2"),
                        s_d], axis=1)
        res = ols_cluster(d[out_var], X, d["cluster_pooled"])
        print(f"  {out_label:15s}: T = {coef_str(res, 'treat'):>10s}  "
              f"T×r² = {coef_str(res, 'treat_x_r2'):>10s}  "
              f"{se_str(res, 'treat_x_r2')}")

        for cname in ["liberia", "kenya2", "kenya"]:
            r2_c = r2_values[cname]
            implied = res.params["treat"] + res.params["treat_x_r2"] * r2_c
            label = get_config(cname)["label"]
            print(f"    {label:15s} (r²={r2_c:.3f}): implied = {implied:+.3f}")

    # ── B5. Summary ──────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    print("B5. Summary: Does diagnostic reliability moderate tracking effects?")
    print(f"{'─'*50}")

    print("  Country-level r²:")
    for cname in ["liberia", "kenya2", "kenya"]:
        label = get_config(cname)["label"]
        print(f"    {label:15s}: r² = {r2_values[cname]:.4f}")

    print(f"\n  T×r² (ITT):        {b_txr2:+.3f} "
          f"(p={res2.pvalues['treat_x_r2']:.3f})")
    if b_txr2 > 0 and b_t != 0:
        breakeven = -b_t / b_txr2
        print(f"  Breakeven r²:      {breakeven:.3f}")
    print(f"\n  Interpretation: {'Higher reliability → better tracking outcomes'}"
          if b_txr2 > 0 else
          f"\n  Interpretation: No clear moderation by reliability")

    print(f"\n✓ Three-country pooled analysis complete")


if __name__ == "__main__":
    investigate_peer_effect()
    cross_country_pooled()
