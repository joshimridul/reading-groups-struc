#!/usr/bin/env python3
"""
make_descriptives.py — Descriptive exhibits (D1–D10) for each study.

Produces LaTeX tables (.tex) and figures (.pdf) in 3_Python/output/.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats as sp_stats

from config import get_config, OUT
from utils import ols_cluster, strata_fe

sns.set_style("whitegrid")
plt.rcParams.update({
    "figure.dpi": 300, "savefig.bbox": "tight", "savefig.dpi": 300,
    "font.size": 10, "axes.titlesize": 12, "font.family": "serif",
    "axes.spines.top": False, "axes.spines.right": False,
})

T_COL = "#C0392B"
C_COL = "#2980B9"

COUNTRIES = ["liberia", "kenya", "kenya2"]


def _w(lines, path):
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  -> {path.name}")


def _esc(s):
    return str(s).replace("%", r"\%").replace("_", r"\_")


def _fmt(x, d=1):
    if pd.isna(x):
        return "---"
    return f"{x:.{d}f}"


# ═══════════════════════════════════════════════════════════════════════════════
# D1: Summary Statistics
# ═══════════════════════════════════════════════════════════════════════════════

def d1_summary_stats(df, cfg, pfx):
    fin = df[df["finsamp"]].copy()
    grades = sorted(fin["grade"].dropna().unique())

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Summary Statistics --- " + cfg["label"] + r"}",
        r"\label{tab:" + pfx + r"sumstats}",
        r"\begin{tabular}{l*{3}{r}}", r"\toprule",
        r" & Treatment & Control & Full \\", r"\midrule",
    ]

    for g in grades:
        gdf = fin[fin["grade"] == g]
        t, c = gdf[gdf["treat"] == 1], gdf[gdf["treat"] == 0]
        L.append(r"\addlinespace")
        L.append(r"\multicolumn{4}{l}{\textit{Grade " + str(int(g)) + r"}} \\")

        L.append(f"Students & {len(t):,d} & {len(c):,d} & {len(gdf):,d} \\\\")
        L.append(f"Academies & {t['academycode'].nunique()} & "
                 f"{c['academycode'].nunique()} & {gdf['academycode'].nunique()} \\\\")

        for lbl, col in [("Baseline score", "score_bl"), ("Endline score", "score_el")]:
            vt, vc, va = t[col].dropna(), c[col].dropna(), gdf[col].dropna()
            if len(vt) == 0 or len(vc) == 0:
                continue
            L.append(f"{lbl} & {vt.mean():.1f} & {vc.mean():.1f} & {va.mean():.1f} \\\\")
            L.append(f"\\quad (SD) & ({vt.std():.1f}) & ({vc.std():.1f}) & ({va.std():.1f}) \\\\")

        L.append(f"Has endline (\\%) & {t['has_el'].mean()*100:.1f} & "
                 f"{c['has_el'].mean()*100:.1f} & {gdf['has_el'].mean()*100:.1f} \\\\")
        L.append(f"Upper group (\\%) & {t['upper_group'].mean()*100:.1f} & "
                 f"{c['upper_group'].mean()*100:.1f} & {gdf['upper_group'].mean()*100:.1f} \\\\")
        cs = gdf["csize"].dropna()
        if len(cs) > 0:
            L.append(f"Class size & {t['csize'].mean():.1f} & "
                     f"{c['csize'].mean():.1f} & {cs.mean():.1f} \\\\")

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / f"desc_{pfx}d1_sumstats.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# D2: Balance Table
# ═══════════════════════════════════════════════════════════════════════════════

def d2_balance(df, cfg, pfx):
    fin = df[df["finsamp"]].copy()
    cluster = fin[cfg["cluster_var"]]

    bal_vars = [
        ("Baseline score", "score_bl"),
        ("Upper group", "upper_group"),
        ("Has endline", "has_el"),
        ("Class size", "csize"),
    ]

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Balance of Baseline Covariates --- " + cfg["label"] + r"}",
        r"\label{tab:" + pfx + r"balance}",
        r"\begin{tabular}{l*{5}{r}}", r"\toprule",
        r" & T Mean & C Mean & Diff & SE & $p$ \\", r"\midrule",
    ]

    for lbl, col in bal_vars:
        sub = fin[fin[col].notna()].copy()
        if len(sub) < 20:
            continue
        tm = sub.loc[sub["treat"] == 1, col].mean()
        cm = sub.loc[sub["treat"] == 0, col].mean()
        try:
            sfe = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat"]], sfe], axis=1)
            res = ols_cluster(sub[col], X, sub[cfg["cluster_var"]])
            diff = res.params["treat"]
            se = res.bse["treat"]
            pv = res.pvalues["treat"]
        except Exception as e:
            print(f"    WARNING: Balance regression for '{lbl}' failed ({e}), using raw diff")
            diff = tm - cm
            se, pv = np.nan, np.nan
        L.append(f"{lbl} & {tm:.3f} & {cm:.3f} & {diff:.3f} & "
                 f"({se:.3f}) & {pv:.3f} \\\\")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small Difference estimated via OLS with strata FE and cluster-robust SEs.}",
          r"\end{table}"]
    _w(L, OUT / f"desc_{pfx}d2_balance.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# D3: Attrition Table
# ═══════════════════════════════════════════════════════════════════════════════

def d3_attrition(df, cfg, pfx):
    full = df[df["treat"].notna()].copy()
    full["attrited"] = (~full["has_el"]).astype(float)
    grades = sorted(full["grade"].dropna().unique())

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Attrition --- " + cfg["label"] + r"}",
        r"\label{tab:" + pfx + r"attrition}",
        r"\begin{tabular}{l*{5}{r}}", r"\toprule",
        r"Sample & T Rate & C Rate & Diff & SE & $N$ \\", r"\midrule",
    ]

    def _att_row(label, sub):
        at = sub.loc[sub["treat"] == 1, "attrited"].mean()
        ac = sub.loc[sub["treat"] == 0, "attrited"].mean()
        try:
            sfe = strata_fe(sub["strata"])
            X = pd.concat([sub[["treat"]], sfe], axis=1)
            res = ols_cluster(sub["attrited"], X, sub[cfg["cluster_var"]])
            d, se = res.params["treat"], res.bse["treat"]
        except Exception as e:
            print(f"    WARNING: Attrition regression for '{label}' failed ({e}), using raw diff")
            d, se = at - ac, np.nan
        L.append(f"{label} & {at:.3f} & {ac:.3f} & {d:.3f} & ({se:.3f}) & {len(sub):,d} \\\\")

    _att_row("Overall", full)
    L.append(r"\addlinespace")
    for g in grades:
        _att_row(f"Grade {int(g)}", full[full["grade"] == g])

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / f"desc_{pfx}d3_attrition.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# D4: Sample Flow Table
# ═══════════════════════════════════════════════════════════════════════════════

def d4_sample_flow(df, cfg, pfx):
    grades = sorted(df["grade"].dropna().unique())

    L = [
        r"\begin{table}[htbp]", r"\centering", r"\small",
        r"\caption{Sample Construction --- " + cfg["label"] + r"}",
        r"\label{tab:" + pfx + r"sampleflow}",
        r"\begin{tabular}{l*{" + str(len(grades) + 1) + r"}{r}}", r"\toprule",
        r" & " + " & ".join(f"Grade {int(g)}" for g in grades) + r" & Total \\",
        r"\midrule",
    ]

    def _row(label, mask):
        vals = [str((mask & (df["grade"] == g)).sum()) for g in grades]
        vals.append(str(mask.sum()))
        L.append(f"{label} & " + " & ".join(vals) + r" \\")

    _row("All observations", pd.Series(True, index=df.index))
    _row("Non-missing treatment", df["treat"].notna())
    _row("Has baseline", df["has_bl"])
    _row("Final analytic sample", df["finsamp"])
    _row("\\quad with endline", df["finsamp"] & df["has_el"])

    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    _w(L, OUT / f"desc_{pfx}d4_sampleflow.tex")


# ═══════════════════════════════════════════════════════════════════════════════
# D5: Baseline Score Distributions
# ═══════════════════════════════════════════════════════════════════════════════

def d5_bl_distributions(df, cfg, pfx):
    fin = df[df["finsamp"] & df["score_bl"].notna()].copy()
    grades = sorted(fin["grade"].dropna().unique())
    cutoffs = cfg.get("cutoffs", {})

    ncols = len(grades)
    fig, axes = plt.subplots(1, ncols, figsize=(4.5 * ncols, 3.5), squeeze=False)
    for i, g in enumerate(grades):
        ax = axes[0, i]
        gdf = fin[fin["grade"] == g]
        t_scores = gdf.loc[gdf["treat"] == 1, "score_bl"]
        c_scores = gdf.loc[gdf["treat"] == 0, "score_bl"]
        ax.hist(c_scores, bins=30, density=True, alpha=0.5, color=C_COL, label="Control")
        ax.hist(t_scores, bins=30, density=True, alpha=0.5, color=T_COL, label="Treatment")
        if g in cutoffs:
            ax.axvline(cutoffs[g], color="black", ls="--", lw=1.2, label=f"Cutoff={cutoffs[g]}")
        ax.set_xlabel("Baseline Score")
        ax.set_ylabel("Density" if i == 0 else "")
        ax.set_title(f"Grade {int(g)}")
        ax.legend(fontsize=8)

    fig.suptitle(f"Baseline Score Distribution --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d5_bl_dist.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d5_bl_dist.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# D6: Endline Score Distributions
# ═══════════════════════════════════════════════════════════════════════════════

def d6_el_distributions(df, cfg, pfx):
    fin = df[df["finsamp"] & df["has_el"] & df["score_el"].notna()].copy()
    grades = sorted(fin["grade"].dropna().unique())

    ncols = len(grades)
    fig, axes = plt.subplots(1, ncols, figsize=(4.5 * ncols, 3.5), squeeze=False)
    for i, g in enumerate(grades):
        ax = axes[0, i]
        gdf = fin[fin["grade"] == g]
        t_scores = gdf.loc[gdf["treat"] == 1, "score_el"]
        c_scores = gdf.loc[gdf["treat"] == 0, "score_el"]
        ax.hist(c_scores, bins=30, density=True, alpha=0.5, color=C_COL, label="Control")
        ax.hist(t_scores, bins=30, density=True, alpha=0.5, color=T_COL, label="Treatment")
        ax.set_xlabel("Endline Score")
        ax.set_ylabel("Density" if i == 0 else "")
        ax.set_title(f"Grade {int(g)}")
        ax.legend(fontsize=8)

    fig.suptitle(f"Endline Score Distribution --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d6_el_dist.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d6_el_dist.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# D7: BL vs EL Binscatter
# ═══════════════════════════════════════════════════════════════════════════════

def d7_binscatter(df, cfg, pfx):
    fin = df[df["finsamp"] & df["score_bl"].notna() & df["score_el"].notna()].copy()
    grades = sorted(fin["grade"].dropna().unique())
    nbins = 20

    ncols = len(grades)
    fig, axes = plt.subplots(1, ncols, figsize=(4.5 * ncols, 4), squeeze=False)
    for i, g in enumerate(grades):
        ax = axes[0, i]
        gdf = fin[fin["grade"] == g]

        for treat_val, color, label in [(0, C_COL, "Control"), (1, T_COL, "Treatment")]:
            sub = gdf[gdf["treat"] == treat_val]
            if len(sub) < nbins:
                continue
            sub = sub.copy()
            sub["bl_bin"] = pd.qcut(sub["score_bl"], q=nbins, duplicates="drop")
            binned = sub.groupby("bl_bin", observed=True).agg(
                bl_mean=("score_bl", "mean"), el_mean=("score_el", "mean")).reset_index()
            ax.scatter(binned["bl_mean"], binned["el_mean"], color=color, s=40,
                       alpha=0.8, label=label, zorder=3)
            z = np.polyfit(sub["score_bl"].values, sub["score_el"].values, 1)
            xr = np.linspace(sub["score_bl"].min(), sub["score_bl"].max(), 100)
            ax.plot(xr, np.polyval(z, xr), color=color, lw=1.5, alpha=0.7)

        ax.set_xlabel("Baseline Score")
        ax.set_ylabel("Endline Score" if i == 0 else "")
        ax.set_title(f"Grade {int(g)}")
        ax.legend(fontsize=8)

    fig.suptitle(f"Baseline vs. Endline (Binscatter) --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d7_binscatter.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d7_binscatter.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# D8: Within-Class Dispersion Boxplots
# ═══════════════════════════════════════════════════════════════════════════════

def d8_dispersion_boxplots(df, cfg, pfx):
    fin = df[df["finsamp"] & df["score_bl"].notna()].copy()

    treat_class = fin[fin["treat"] == 1].groupby(
        ["academycode", "std_grp"])["score_bl"].std().dropna().reset_index()
    treat_class["group"] = "Treatment"

    ctrl_class = fin[fin["treat"] == 0].groupby(
        ["academycode", "grade"])["score_bl"].std().dropna().reset_index()
    ctrl_class["group"] = "Control"

    treat_class.rename(columns={"score_bl": "within_sd"}, inplace=True)
    ctrl_class.rename(columns={"score_bl": "within_sd"}, inplace=True)
    combined = pd.concat([
        treat_class[["within_sd", "group"]],
        ctrl_class[["within_sd", "group"]],
    ])

    fig, ax = plt.subplots(figsize=(5, 4))
    bp = combined.boxplot(column="within_sd", by="group", ax=ax,
                          patch_artist=True, return_type="dict")
    colors = [T_COL, C_COL]
    for patch, color in zip(bp["within_sd"]["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)
    ax.set_title("")
    fig.suptitle("")
    ax.set_ylabel("Within-Class SD of Baseline Scores")
    ax.set_xlabel("")

    t_med = treat_class["within_sd"].median()
    c_med = ctrl_class["within_sd"].median()
    ax.text(0.02, 0.97, f"Median SD: T={t_med:.1f}, C={c_med:.1f}",
            transform=ax.transAxes, fontsize=9, va="top")

    fig.suptitle(f"Within-Class Score Dispersion --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d8_dispersion.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d8_dispersion.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# D9: Class Size Distributions
# ═══════════════════════════════════════════════════════════════════════════════

def d9_class_sizes(df, cfg, pfx):
    fin = df[df["finsamp"]].copy()

    t_sizes = fin[fin["treat"] == 1].groupby(
        ["academycode", "std_grp"]).size().reset_index(name="class_size")
    c_sizes = fin[fin["treat"] == 0].groupby(
        ["academycode", "grade"]).size().reset_index(name="class_size")

    fig, ax = plt.subplots(figsize=(6, 4))
    bins = np.arange(0, max(t_sizes["class_size"].max(), c_sizes["class_size"].max()) + 5, 5)
    ax.hist(c_sizes["class_size"], bins=bins, density=True, alpha=0.5,
            color=C_COL, label=f"Control (N={len(c_sizes)}, med={c_sizes['class_size'].median():.0f})")
    ax.hist(t_sizes["class_size"], bins=bins, density=True, alpha=0.5,
            color=T_COL, label=f"Treatment (N={len(t_sizes)}, med={t_sizes['class_size'].median():.0f})")
    ax.set_xlabel("Students per Class")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)
    fig.suptitle(f"Class Size Distribution --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d9_classsize.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d9_classsize.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# D10: Propensity Score Distribution
# ═══════════════════════════════════════════════════════════════════════════════

def d10_propensity(df, cfg, pfx):
    fin = df[df["finsamp"] & df["P_t"].notna()].copy()

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(fin["P_t"], bins=40, color="#555555", alpha=0.7, edgecolor="white")
    ax.axvline(fin["P_t"].mean(), color=T_COL, ls="--", lw=1.5,
               label=f"Mean = {fin['P_t'].mean():.3f}")
    ax.set_xlabel("Treatment Propensity ($P_t$)")
    ax.set_ylabel("Count")
    ax.legend(fontsize=9)
    fig.suptitle(f"Treatment Propensity Distribution --- {cfg['label']}", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / f"desc_{pfx}d10_propensity.pdf")
    plt.close()
    print(f"  -> desc_{pfx}d10_propensity.pdf")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    for country in COUNTRIES:
        cfg = get_config(country)
        pfx = cfg["OUT_PREFIX"]
        print(f"\n{'='*60}")
        print(f"  Descriptives: {cfg['label']}")
        print(f"{'='*60}")

        try:
            df = pd.read_parquet(cfg["ANALYSIS_FILE"])
        except FileNotFoundError:
            print(f"  SKIP: {cfg['ANALYSIS_FILE']} not found")
            continue

        d1_summary_stats(df, cfg, pfx)
        d2_balance(df, cfg, pfx)
        d3_attrition(df, cfg, pfx)
        d4_sample_flow(df, cfg, pfx)
        d5_bl_distributions(df, cfg, pfx)
        d6_el_distributions(df, cfg, pfx)
        d7_binscatter(df, cfg, pfx)
        d8_dispersion_boxplots(df, cfg, pfx)
        d9_class_sizes(df, cfg, pfx)
        d10_propensity(df, cfg, pfx)

        print(f"  Done: {cfg['label']}")

    print("\nAll descriptives complete.")
