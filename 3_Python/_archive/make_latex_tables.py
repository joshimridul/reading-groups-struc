#!/usr/bin/env python3
"""
make_latex_tables.py — Publication-quality LaTeX tables (A1–A10) and figures
(A11–A15) for all three studies.

Tables are cross-study (columns = Liberia / Kenya Y1 / Kenya Y2 / Kenya Y2 matched).
Figures are multi-panel (one panel per study).
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from config import get_config, OUT, SEED
from utils import (ols_cluster, strata_fe, decile_treat_fe, stars)

np.random.seed(SEED)

sns.set_style("whitegrid")
plt.rcParams.update({
    "figure.dpi": 300, "savefig.bbox": "tight", "savefig.dpi": 300,
    "font.size": 10, "axes.titlesize": 12, "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
})

STUDY_COLORS = {"liberia": "#4878A8", "kenya": "#E87D3E",
                "kenya2": "#5BA85B", "kenya2m": "#2D882D"}

STUDIES = [
    ("liberia",  False, "Liberia"),
    ("kenya",    False, "Kenya Y1"),
    ("kenya2",   False, "Kenya Y2"),
    ("kenya2",   True,  "Kenya Y2 (matched)"),
]
COL_HDRS = ["Liberia", "Kenya Y1", "Kenya Y2", "Kenya Y2 (m)"]
NCOL = len(STUDIES)


def _w(lines, path):
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  -> {path.name}")


def _s(val, fmt=".3f"):
    if pd.isna(val):
        return "---"
    return f"{val:{fmt}}"


def _cs(coef, pval, fmt=".3f"):
    return f"{coef:{fmt}}{stars(pval)}"


def _se(val, fmt=".3f"):
    if pd.isna(val):
        return ""
    return f"({val:{fmt}})"


# ─── Data loading ────────────────────────────────────────────────────────────

def load_studies():
    """Load analysis data for each study configuration."""
    datasets = []
    for country, matched, label in STUDIES:
        cfg = get_config(country)
        try:
            df_full = pd.read_parquet(cfg["ANALYSIS_FILE"])
        except FileNotFoundError:
            print(f"  SKIP: {cfg['ANALYSIS_FILE']} not found")
            datasets.append((None, cfg, label))
            continue
        df = df_full[df_full["finsamp"]].copy()
        if matched and "matched_grp" in df.columns:
            df = df[df["matched_grp"]].copy()
        datasets.append((df, cfg, label))
    return datasets


def get_experiments(country):
    if country == "kenya":
        return [("Stacked (G1-2)", "exp0")]
    elif country == "kenya2":
        return [("Stacked (G1-3)", "exp0"), ("Grades 1-2", "exp2")]
    else:
        return [("Stacked", "exp0"), ("Grades 3-4", "exp1"), ("Grades 1-2", "exp2")]


# ═══════════════════════════════════════════════════════════════════════════════
# A1: Main ITT Effects
# ═══════════════════════════════════════════════════════════════════════════════

def a1_itt_table(datasets):
    results = {}
    for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
        if df is None:
            results[col_hdr] = {}
            continue
        exps = get_experiments(cfg["country"])
        r = {}
        for exp_label, exp_col in exps:
            sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
            if len(sub) < 20:
                continue
            sfe = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat", "std_eb"]], sfe], axis=1)
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            cm = sub.loc[sub["treat"] == 0, "std_score_el"].mean()
            r[exp_label] = dict(
                b=res.params["treat"], se=res.bse["treat"],
                p=res.pvalues["treat"], N=len(sub), cm=cm)
        results[col_hdr] = r

    stacked_key = {
        "Liberia": "Stacked", "Kenya Y1": "Stacked (G1-2)",
        "Kenya Y2": "Stacked (G1-3)", "Kenya Y2 (m)": "Stacked (G1-3)",
    }
    upper_key = {"Liberia": "Grades 3-4"}
    lower_key = {
        "Liberia": "Grades 1-2",
        "Kenya Y2": "Grades 1-2", "Kenya Y2 (m)": "Grades 1-2",
    }

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Intent-to-Treat Effects on Standardized Endline Scores}",
        r"\label{tab:itt}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(f"({i+1})" for i in range(NCOL)) + r" \\",
        " & " + " & ".join(COL_HDRS) + r" \\",
        r"\midrule",
        r"\addlinespace",
        r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{Panel A: All grades}} \\",
    ]

    def _add_row(key_map, row_label):
        bvals, sevals = [], []
        for hdr in COL_HDRS:
            k = key_map.get(hdr)
            r = results[hdr].get(k) if k else None
            if r:
                bvals.append(_cs(r["b"], r["p"]))
                sevals.append(_se(r["se"]))
            else:
                bvals.append("")
                sevals.append("")
        L.append(row_label + " & " + " & ".join(bvals) + r" \\")
        L.append(" & " + " & ".join(sevals) + r" \\")

    _add_row(stacked_key, "Treatment")

    L.append(r"\addlinespace")
    L.append(r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{Panel B: Upper grades}} \\")
    _add_row(upper_key, "Treatment")

    L.append(r"\addlinespace")
    L.append(r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{Panel C: Lower grades}} \\")
    _add_row(lower_key, "Treatment")

    L.append(r"\addlinespace")
    L.append(r"\midrule")
    nvals, cmvals = [], []
    for hdr in COL_HDRS:
        k = stacked_key.get(hdr)
        r = results[hdr].get(k)
        nvals.append(f"{r['N']:,d}" if r else "")
        cmvals.append(f"{r['cm']:.3f}" if r else "")
    L.append("Observations & " + " & ".join(nvals) + r" \\")
    L.append("Control mean & " + " & ".join(cmvals) + r" \\")
    L.append(r"Strata FE & " + " & ".join(["Yes"] * NCOL) + r" \\")
    L.append(r"Ability control & " + " & ".join(["Yes"] * NCOL) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a1_itt.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A2: ITT by Upper/Lower Group
# ═══════════════════════════════════════════════════════════════════════════════

def a2_upper_lower(datasets):
    results = {}
    for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
        if df is None:
            results[col_hdr] = None
            continue
        exps = get_experiments(cfg["country"])
        exp_label, exp_col = exps[0]
        sub = df[(df[exp_col] == 1) & df["std_score_el"].notna()].copy()
        sub["treat_x_upper"] = sub["treat"] * sub["upper_group"]
        sfe = strata_fe(sub["strata"])
        X = pd.concat([sub[["treat", "treat_x_upper", "upper_group", "std_eb"]], sfe], axis=1)
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])

        b_upper = res.params["treat"] + res.params["treat_x_upper"]
        se_upper = np.sqrt(
            res.cov_params().loc["treat", "treat"] +
            res.cov_params().loc["treat_x_upper", "treat_x_upper"] +
            2 * res.cov_params().loc["treat", "treat_x_upper"])
        t_upper = b_upper / se_upper
        p_upper = 2 * (1 - sp_stats.t.cdf(abs(t_upper), res.df_resid))

        results[col_hdr] = dict(
            b_low=res.params["treat"], se_low=res.bse["treat"], p_low=res.pvalues["treat"],
            b_txu=res.params["treat_x_upper"], se_txu=res.bse["treat_x_upper"],
            p_txu=res.pvalues["treat_x_upper"],
            b_up=b_upper, se_up=se_upper, p_up=p_upper, N=len(sub))

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Treatment Effects by Ability Group}",
        r"\label{tab:upper_lower}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    def _row(key_b, key_se, key_p, row_label):
        vals, ses = [], []
        for hdr in COL_HDRS:
            r = results[hdr]
            if r:
                vals.append(_cs(r[key_b], r[key_p]))
                ses.append(_se(r[key_se]))
            else:
                vals.append("")
                ses.append("")
        L.append(row_label + " & " + " & ".join(vals) + r" \\")
        L.append(" & " + " & ".join(ses) + r" \\")

    _row("b_low", "se_low", "p_low", "Treatment (lower)")
    L.append(r"\addlinespace")
    _row("b_txu", "se_txu", "p_txu", r"Treatment $\times$ Upper")
    L.append(r"\addlinespace")
    _row("b_up", "se_up", "p_up", "Treatment (upper)")

    L.append(r"\addlinespace\midrule")
    nvals = [f"{results[h]['N']:,d}" if results[h] else "" for h in COL_HDRS]
    L.append("Observations & " + " & ".join(nvals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a2_upper_lower.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A3: Within-Class Dispersion Effects
# ═══════════════════════════════════════════════════════════════════════════════

def a3_dispersion(datasets):
    outcomes = [("EB ability", "dev_eb"), ("Endline scores", "dev_el")]

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Treatment Effect on Within-Class Dispersion}",
        r"\label{tab:dispersion}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    for out_label, out_var in outcomes:
        L.append(r"\addlinespace")
        L.append(r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{" + out_label + r"}} \\")

        bvals, sevals, cmvals = [], [], []
        for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
            if df is None:
                bvals.append(""); sevals.append(""); cmvals.append("")
                continue
            sub = df[df["std_score_el"].notna() & df[out_var].notna()].copy()
            sfe = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat", "std_eb"]], sfe], axis=1)
            res = ols_cluster(sub[out_var], X, sub["ggroup"])
            cm = sub.loc[sub["treat"] == 0, out_var].mean()
            bvals.append(_cs(res.params["treat"], res.pvalues["treat"]))
            sevals.append(_se(res.bse["treat"]))
            cmvals.append(f"{cm:.3f}")

        L.append("Treatment & " + " & ".join(bvals) + r" \\")
        L.append(" & " + " & ".join(sevals) + r" \\")
        L.append("Control mean & " + " & ".join(cmvals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a3_dispersion.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A4: Diagnostic Reliability
# ═══════════════════════════════════════════════════════════════════════════════

def a4_reliability(datasets):
    all_grades = [1, 2, 3, 4]
    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Diagnostic Reliability: $R^2$(Baseline $\to$ Endline)}",
        r"\label{tab:reliability}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    for g in all_grades:
        vals = []
        for (df, cfg, label) in datasets:
            if df is None or g not in cfg["grades"]:
                vals.append("")
                continue
            ctrl_g = (df["treat"] == 0) & (df["grade"] == g)
            m = ctrl_g & df["score_bl"].notna() & df["score_el"].notna()
            if m.sum() > 10:
                r2 = df.loc[m, "score_bl"].corr(df.loc[m, "score_el"]) ** 2
                n = m.sum()
                vals.append(f"{r2:.3f} ({n:,d})")
            else:
                vals.append("---")
        if all(v == "" for v in vals):
            continue
        L.append(f"Grade {g} & " + " & ".join(vals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small $R^2$ from correlation of raw BL and EL scores in control group. $N$ in parentheses.}",
          r"\end{table}"]
    _w(L, OUT / "tab_a4_reliability.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A5: Treatment Heterogeneity by Quartile
# ═══════════════════════════════════════════════════════════════════════════════

def a5_quartile_effects(datasets):
    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Treatment Effects by Baseline Ability Quartile}",
        r"\label{tab:quartiles}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    quartile_data = {}
    for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
        if df is None:
            quartile_data[col_hdr] = {}
            continue
        grades = sorted(df["grade"].dropna().unique())
        df["bl_q"] = np.nan
        for g in grades:
            m = (df["grade"] == g) & df["std_score_bl"].notna()
            df.loc[m, "bl_q"] = pd.qcut(
                df.loc[m, "std_score_bl"], q=4, labels=False, duplicates="drop") + 1

        qr = {}
        for q in [1, 2, 3, 4]:
            sub = df[(df["bl_q"] == q) & df["std_score_el"].notna()]
            if len(sub) < 20:
                continue
            sfe = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat", "std_eb"]], sfe], axis=1)
            res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            qr[q] = dict(b=res.params["treat"], se=res.bse["treat"],
                         p=res.pvalues["treat"], N=len(sub))
        quartile_data[col_hdr] = qr

    for q in [1, 2, 3, 4]:
        bvals, sevals = [], []
        for hdr in COL_HDRS:
            r = quartile_data[hdr].get(q)
            if r:
                bvals.append(_cs(r["b"], r["p"]))
                sevals.append(_se(r["se"]))
            else:
                bvals.append(""); sevals.append("")
        L.append(f"Q{q} & " + " & ".join(bvals) + r" \\")
        L.append(" & " + " & ".join(sevals) + r" \\")
        if q < 4:
            L.append(r"\addlinespace")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small Q1 = lowest ability, Q4 = highest. Quartiles defined within grade.}",
          r"\end{table}"]
    _w(L, OUT / "tab_a5_quartiles.tex")
    return quartile_data


# ═══════════════════════════════════════════════════════════════════════════════
# A6: Borusyak-Hull Peer Effects
# ═══════════════════════════════════════════════════════════════════════════════

def a6_mechanism(datasets):
    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Peer Effects: Borusyak-Hull Estimates}",
        r"\label{tab:mechanism}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    specs = [
        ("Main: EB peer mean", "peer_eb", False),
        ("Raw BL peer mean", "peer_bl", False),
        ("EB + class size", "peer_eb", True),
    ]

    for spec_label, peer_var, add_csize in specs:
        bvals, sevals = [], []
        for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
            if df is None:
                bvals.append(""); sevals.append("")
                continue
            sub = df[df["std_score_el"].notna() & df["bl_decile"].notna()
                     & df[peer_var].notna()].copy()
            if add_csize:
                sub = sub[sub["csize"].notna()].copy()
            if len(sub) < 20:
                bvals.append(""); sevals.append("")
                continue
            sfe = strata_fe(sub["strata"])
            dtfe = decile_treat_fe(sub["bl_decile"], sub["treat"])
            cols = [peer_var] + (["csize"] if add_csize else [])
            X = pd.concat([sub[cols], dtfe, sfe], axis=1)
            try:
                res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
                bvals.append(_cs(res.params[peer_var], res.pvalues[peer_var]))
                sevals.append(_se(res.bse[peer_var]))
            except Exception as e:
                print(f"    WARNING: {spec_label}/{cname} failed ({e})")
                bvals.append(""); sevals.append("")

        L.append(spec_label + " & " + " & ".join(bvals) + r" \\")
        L.append(" & " + " & ".join(sevals) + r" \\")
        L.append(r"\addlinespace")

    L.append(r"\midrule")
    L.append(r"Decile $\times$ Treatment FE & " + " & ".join(["Yes"] * NCOL) + r" \\")
    L.append(r"Strata FE & " + " & ".join(["Yes"] * NCOL) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a6_mechanism.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A7: Variance Decomposition
# ═══════════════════════════════════════════════════════════════════════════════

def a7_variance_decomp(datasets):
    all_grades = [1, 2, 3, 4]

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Within-Class Variance: Treatment vs.\ Control}",
        r"\label{tab:variance_decomp}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    for panel_label, var in [("EB ability", "std_eb"), ("Endline scores", "std_score_el")]:
        L.append(r"\addlinespace")
        L.append(r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{" +
                 panel_label + r": $\Delta V = V_C - V_T$}} \\")
        for g in all_grades:
            vals = []
            for (df, cfg, label) in datasets:
                if df is None or g not in cfg["grades"]:
                    vals.append("")
                    continue
                g_df = df[(df["grade"] == g) & df[var].notna()]
                g_c = g_df[g_df["treat"] == 0]
                g_t = g_df[g_df["treat"] == 1]
                if len(g_c) < 10 or len(g_t) < 10:
                    vals.append("")
                    continue
                vc = g_c.groupby(["academycode", "grade"])[var].transform("var").mean()
                vt = g_t.groupby(["academycode", "std_grp"])[var].transform("var").mean()
                dv = vc - vt
                vals.append(f"{dv:+.3f}")
            if all(v == "" for v in vals):
                continue
            L.append(f"Grade {g} & " + " & ".join(vals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small Positive $\Delta V$ = sorting reduced within-class variance.}",
          r"\end{table}"]
    _w(L, OUT / "tab_a7_variance.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A8: Structural Calibration
# ═══════════════════════════════════════════════════════════════════════════════

def a8_calibration(datasets):
    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Structural Calibration}",
        r"\label{tab:calibration}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    params_by_study = {}
    for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
        if df is None:
            params_by_study[col_hdr] = None
            continue
        sub = df[df["std_score_el"].notna() & df["std_score_bl"].notna()].copy()
        for gt, suf in [("std_grp", "treat"), ("grade", "ctrl")]:
            cm = sub.groupby(["academycode", gt])["std_score_bl"].transform("mean")
            sub[f"_cm_{suf}"] = cm
        sub["_cm"] = np.where(sub["treat"] == 1, sub["_cm_treat"], sub["_cm_ctrl"])
        sub["misfit_bl"] = (sub["std_score_bl"] - sub["_cm"]) ** 2
        sub["std_bl_sq"] = sub["std_score_bl"] ** 2

        res = ols_cluster(sub["std_score_el"],
                          sub[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                          sub["ggroup"])
        lam = -res.params["misfit_bl"]
        tau = res.params["treat"]
        t_lam = -res.tvalues["misfit_bl"]

        if tau < 0 and lam > 0:
            rho = 2 * np.sqrt(lam * (-tau))
        else:
            rho = np.nan

        params_by_study[col_hdr] = dict(lam=lam, tau=tau, rho=rho,
                                         t_lam=t_lam, N=len(sub), cfg=cfg)

    lam_vals, tau_vals, rho_vals = [], [], []
    for hdr in COL_HDRS:
        p = params_by_study[hdr]
        if p is None:
            lam_vals.append(""); tau_vals.append(""); rho_vals.append("")
        else:
            lam_vals.append(f"{p['lam']:.4f}")
            tau_vals.append(f"{p['tau']:.4f}")
            rho_vals.append(f"{p['rho']:.4f}" if pd.notna(p['rho']) else r"$\tau \geq 0$")

    L.append(r"$\hat{\lambda}$ (mismatch cost) & " + " & ".join(lam_vals) + r" \\")
    L.append(r"$\hat{\tau}$ (net tracking effect) & " + " & ".join(tau_vals) + r" \\")
    L.append(r"$\hat{\rho}$ (distortion cost) & " + " & ".join(rho_vals) + r" \\")

    L.append(r"\addlinespace\midrule")
    L.append(r"\multicolumn{" + str(NCOL + 1) + r"}{l}{\textit{Threshold $r^{2*}$ by grade}} \\")

    all_grades = [1, 2, 3, 4]
    for g in all_grades:
        vals = []
        for hdr in COL_HDRS:
            p = params_by_study[hdr]
            if p is None or g not in p["cfg"]["grades"]:
                vals.append("")
                continue
            df_ = datasets[COL_HDRS.index(hdr)][0]
            ctrl_g = (df_["treat"] == 0) & (df_["grade"] == g)
            m = ctrl_g & df_["score_bl"].notna() & df_["score_el"].notna()
            r2_obs = df_.loc[m, "score_bl"].corr(df_.loc[m, "score_el"]) ** 2 if m.sum() > 10 else np.nan
            sigma2 = df_.loc[ctrl_g & df_["score_bl"].notna(), "std_score_bl"].var()

            if pd.notna(p["rho"]) and p["lam"] > 0 and sigma2 > 0:
                r2_star = p["rho"] ** 2 / (4 * p["lam"] ** 2 * sigma2)
                v = "PASS" if r2_obs >= r2_star else "FAIL"
                vals.append(f"{r2_star:.3f} ({v})")
            elif p["tau"] >= 0:
                vals.append("PASS")
            else:
                vals.append("---")
        if all(v == "" for v in vals):
            continue
        L.append(f"Grade {g} & " + " & ".join(vals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a8_calibration.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A9: Robustness
# ═══════════════════════════════════════════════════════════════════════════════

def a9_robustness(datasets):
    spec_labels = [
        ("EB + Strata FE", ["treat", "std_eb"], True),
        ("Raw BL + Strata FE", ["treat", "std_score_bl"], True),
        ("No BL + Strata FE", ["treat"], True),
        (r"EB + Linear $P_t$", ["treat", "std_eb", "P_t"], False),
    ]

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Robustness: Alternative Specifications}",
        r"\label{tab:robustness}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    for spec_name, covars, use_strata in spec_labels:
        bvals, sevals = [], []
        for (df, cfg, label), col_hdr in zip(datasets, COL_HDRS):
            if df is None:
                bvals.append(""); sevals.append("")
                continue
            sub = df[df["std_score_el"].notna()].copy()
            try:
                if use_strata:
                    sfe = strata_fe(sub["strata"])
                    X = pd.concat([sub[covars], sfe], axis=1)
                else:
                    X = sub[covars].copy()
                res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
                bvals.append(_cs(res.params["treat"], res.pvalues["treat"]))
                sevals.append(_se(res.bse["treat"]))
            except Exception as e:
                print(f"    WARNING: {spec_name}/{cname} failed ({e})")
                bvals.append(""); sevals.append("")
        L.append(spec_name + " & " + " & ".join(bvals) + r" \\")
        L.append(" & " + " & ".join(sevals) + r" \\")
        L.append(r"\addlinespace")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a9_robustness.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A10: Attrition and Permutation
# ═══════════════════════════════════════════════════════════════════════════════

def a10_attrition_perm(datasets):
    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Attrition and Permutation Inference}",
        r"\label{tab:attrition_perm}",
        r"\begin{tabular}{l*{" + str(NCOL) + r"}{c}}", r"\toprule",
        " & " + " & ".join(COL_HDRS) + r" \\", r"\midrule",
    ]

    att_vals, att_se_vals, att_t, att_c = [], [], [], []
    for (df, cfg, label) in datasets:
        if df is None:
            att_vals.append(""); att_se_vals.append("")
            att_t.append(""); att_c.append("")
            continue
        full = pd.read_parquet(cfg["ANALYSIS_FILE"])
        full = full[full["treat"].notna()].copy()
        full["attrited"] = (~full["has_el"]).astype(float)
        t_rate = full.loc[full["treat"] == 1, "attrited"].mean()
        c_rate = full.loc[full["treat"] == 0, "attrited"].mean()
        try:
            sfe = strata_fe(full["strata"])
            X = pd.concat([full[["treat"]], sfe], axis=1)
            res = ols_cluster(full["attrited"], X, full[cfg["cluster_var"]])
            att_vals.append(_cs(res.params["treat"], res.pvalues["treat"]))
            att_se_vals.append(_se(res.bse["treat"]))
        except Exception as e:
            print(f"    WARNING: Attrition regression for {cname} failed ({e})")
            att_vals.append(""); att_se_vals.append("")
        att_t.append(f"{t_rate:.3f}")
        att_c.append(f"{c_rate:.3f}")

    L.append("Treatment attrition & " + " & ".join(att_t) + r" \\")
    L.append("Control attrition & " + " & ".join(att_c) + r" \\")
    L.append("Differential & " + " & ".join(att_vals) + r" \\")
    L.append(" & " + " & ".join(att_se_vals) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / "tab_a10_attrition.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# A11: tau(s) by Baseline Decile (figure)
# ═══════════════════════════════════════════════════════════════════════════════

def a11_tau_s_figure(datasets):
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.5 * len(datasets), 4),
                             squeeze=False, sharey=True)
    for idx, ((df, cfg, label), col_hdr) in enumerate(zip(datasets, COL_HDRS)):
        ax = axes[0, idx]
        if df is None:
            ax.set_visible(False)
            continue
        dec_results = []
        for d in sorted(df["bl_decile"].dropna().unique()):
            sub = df[(df["bl_decile"] == d) & df["std_score_el"].notna()]
            if len(sub) < 20 or sub["treat"].nunique() < 2:
                continue
            try:
                res = ols_cluster(sub["std_score_el"], sub[["treat"]], sub["ggroup"])
                dec_results.append(dict(d=d, b=res.params["treat"], se=res.bse["treat"]))
            except Exception as e:
                print(f"    WARNING: Decile {d} het. effect failed ({e})")
        if not dec_results:
            continue
        dd = pd.DataFrame(dec_results)
        color = list(STUDY_COLORS.values())[idx]
        ax.errorbar(dd["d"], dd["b"], yerr=1.96 * dd["se"],
                    fmt="o-", color=color, capsize=3, lw=1.8, markersize=5)
        ax.axhline(0, color="gray", ls="--", lw=0.8)
        ax.set_xlabel("Baseline Decile")
        if idx == 0:
            ax.set_ylabel("Treatment Effect (SD)")
        ax.set_title(col_hdr)
        ax.set_xticks(range(1, 11))

    fig.tight_layout()
    fig.savefig(OUT / "fig_a11_tau_s.pdf")
    plt.close()
    print("  -> fig_a11_tau_s.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# A12: BL-EL Scatter with Reliability (figure)
# ═══════════════════════════════════════════════════════════════════════════════

def a12_reliability_scatter(datasets):
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.5 * len(datasets), 4),
                             squeeze=False)
    for idx, ((df, cfg, label), col_hdr) in enumerate(zip(datasets, COL_HDRS)):
        ax = axes[0, idx]
        if df is None:
            ax.set_visible(False)
            continue
        ctrl = df[(df["treat"] == 0) & df["std_score_bl"].notna()
                  & df["std_score_el"].notna()]
        if len(ctrl) < 20:
            continue
        ax.scatter(ctrl["std_score_bl"], ctrl["std_score_el"],
                   alpha=0.08, s=5, color="gray", rasterized=True)
        z = np.polyfit(ctrl["std_score_bl"].values, ctrl["std_score_el"].values, 1)
        xr = np.linspace(ctrl["std_score_bl"].min(), ctrl["std_score_bl"].max(), 100)
        color = list(STUDY_COLORS.values())[idx]
        ax.plot(xr, np.polyval(z, xr), color=color, lw=2)
        r2 = ctrl["std_score_bl"].corr(ctrl["std_score_el"]) ** 2
        ax.text(0.05, 0.95, f"$R^2 = {r2:.3f}$\n$N = {len(ctrl):,d}$",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", fc="white", alpha=0.8))
        ax.set_xlabel("Std. Baseline")
        if idx == 0:
            ax.set_ylabel("Std. Endline")
        ax.set_title(col_hdr)

    fig.tight_layout()
    fig.savefig(OUT / "fig_a12_reliability.pdf")
    plt.close()
    print("  -> fig_a12_reliability.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# A13: Delta-P, Delta-M, Delta-Y Decomposition (figure)
# ═══════════════════════════════════════════════════════════════════════════════

def a13_delta_decomposition(datasets):
    fig, axes = plt.subplots(len(datasets), 3,
                             figsize=(12, 3.5 * len(datasets)), squeeze=False)
    series = [("peer_eb", r"$\Delta P$"), ("misfit", r"$\Delta M$"),
              ("std_score_el", r"$\Delta Y$")]

    for row, ((df, cfg, label), col_hdr) in enumerate(zip(datasets, COL_HDRS)):
        color = list(STUDY_COLORS.values())[row]
        for col, (var, var_label) in enumerate(series):
            ax = axes[row, col]
            if df is None:
                ax.set_visible(False)
                continue
            delta_vals = []
            for d in sorted(df["bl_decile"].dropna().unique()):
                sub = df[df["bl_decile"] == d]
                tm = sub.loc[sub["treat"] == 1, var].mean()
                cm = sub.loc[sub["treat"] == 0, var].mean()
                if pd.notna(tm) and pd.notna(cm):
                    delta_vals.append(dict(d=d, delta=tm - cm))
            if not delta_vals:
                continue
            dd = pd.DataFrame(delta_vals)
            ax.bar(dd["d"], dd["delta"], color=color, alpha=0.7, width=0.7)
            ax.axhline(0, color="gray", ls="--", lw=0.8)
            ax.set_xlabel("BL Decile")
            if col == 0:
                ax.set_ylabel(col_hdr, fontsize=10, fontweight="bold")
            if row == 0:
                ax.set_title(var_label)
            ax.set_xticks(range(1, 11))

    fig.tight_layout()
    fig.savefig(OUT / "fig_a13_delta_decomp.pdf")
    plt.close()
    print("  -> fig_a13_delta_decomp.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# A14: Permutation Inference (figure, 200 iterations for speed)
# ═══════════════════════════════════════════════════════════════════════════════

def a14_permutation_figure(datasets):
    N_PERMS = 200
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.5 * len(datasets), 4),
                             squeeze=False)
    for idx, ((df, cfg, label), col_hdr) in enumerate(zip(datasets, COL_HDRS)):
        ax = axes[0, idx]
        if df is None:
            ax.set_visible(False)
            continue
        sub = df[df["std_score_el"].notna()].copy()
        sfe = strata_fe(sub["strata"])
        Xr = pd.concat([sub[["treat", "std_eb"]], sfe], axis=1)
        res_r = ols_cluster(sub["std_score_el"], Xr, sub["ggroup"])
        t_real = res_r.tvalues["treat"]

        gi = sub.drop_duplicates("ggroup")[["ggroup", "treat", "strata"]].copy()
        t_perms = []
        for _ in range(N_PERMS):
            pi = gi.copy()
            pi["tp"] = pi.groupby("strata")["treat"].transform(
                lambda x: x.sample(frac=1, replace=False).values)
            pm = dict(zip(pi["ggroup"], pi["tp"]))
            sub["_tp"] = sub["ggroup"].map(pm)
            Xp = pd.concat([sub[["_tp", "std_eb"]].rename(columns={"_tp": "treat"}),
                             sfe], axis=1)
            try:
                rp = ols_cluster(sub["std_score_el"], Xp, sub["ggroup"])
                t_perms.append(rp.tvalues["treat"])
            except Exception as e:
                if i < 3:
                    print(f"    WARNING: Perm {i} failed ({e})")

        t_perms = np.array(t_perms)
        p_perm = (np.abs(t_perms) >= np.abs(t_real)).mean()
        color = list(STUDY_COLORS.values())[idx]
        ax.hist(t_perms, bins=25, color=color, alpha=0.6, density=True, edgecolor="white")
        ax.axvline(t_real, color="darkred", lw=2, ls="--",
                   label=f"Obs. $t$ = {t_real:.2f}")
        ax.set_xlabel("$t$-statistic")
        if idx == 0:
            ax.set_ylabel("Density")
        ax.set_title(f"{col_hdr} ($p$ = {p_perm:.3f})")
        ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT / "fig_a14_permutation.pdf")
    plt.close()
    print("  -> fig_a14_permutation.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# A15: Quartile Effects Bar Chart (figure)
# ═══════════════════════════════════════════════════════════════════════════════

def a15_quartile_bar_chart(quartile_data):
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(4)
    width = 0.2
    offsets = np.linspace(-1.5 * width, 1.5 * width, NCOL)

    for i, hdr in enumerate(COL_HDRS):
        qd = quartile_data.get(hdr, {})
        bs = [qd.get(q, {}).get("b", np.nan) for q in [1, 2, 3, 4]]
        ses = [qd.get(q, {}).get("se", 0) for q in [1, 2, 3, 4]]
        color = list(STUDY_COLORS.values())[i]
        ax.bar(x + offsets[i], bs, width, yerr=[1.96 * s for s in ses],
               color=color, alpha=0.7, label=hdr, capsize=3, edgecolor="white")

    ax.axhline(0, color="gray", ls="--", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["Q1\n(lowest)", "Q2", "Q3", "Q4\n(highest)"])
    ax.set_ylabel("Treatment Effect (SD)")
    ax.set_xlabel("Baseline Ability Quartile")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "fig_a15_quartile_effects.pdf")
    plt.close()
    print("  -> fig_a15_quartile_effects.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Loading study data...")
    datasets = load_studies()
    for (df, cfg, label) in datasets:
        if df is not None:
            print(f"  {label}: N={len(df):,d}")

    print("\n--- LaTeX Tables ---")
    a1_itt_table(datasets)
    a2_upper_lower(datasets)
    a3_dispersion(datasets)
    a4_reliability(datasets)
    qd = a5_quartile_effects(datasets)
    a6_mechanism(datasets)
    a7_variance_decomp(datasets)
    a8_calibration(datasets)
    a9_robustness(datasets)
    a10_attrition_perm(datasets)

    print("\n--- Figures ---")
    a11_tau_s_figure(datasets)
    a12_reliability_scatter(datasets)
    a13_delta_decomposition(datasets)
    a14_permutation_figure(datasets)
    a15_quartile_bar_chart(qd)

    print("\nAll tables and figures complete.")
