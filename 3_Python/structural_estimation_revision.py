#!/usr/bin/env python3
"""
structural_estimation_revision.py
=================================
Revision of the first-pass structural pipeline.

Design change versus previous version:
- Keep measurement + assignment as settled/core structural blocks.
- Make Kenya Y1 the primary production-estimation setting.
- Treat Liberia as reduced-form + sensitivity/policy contrast.
- Keep pooled nonlinear production as deprecated/secondary reference only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from config import get_config, OUT
from utils import ols_cluster

np.random.seed(42)

OUT_DIR = OUT / "structural_revision"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STUDIES = [("kenya", "Kenya Y1"), ("liberia", "Liberia")]


@dataclass
class Study:
    country: str
    label: str
    cfg: dict
    df: pd.DataFrame


def _save_table(df: pd.DataFrame, stem: str) -> None:
    df.to_csv(OUT_DIR / f"{stem}.txt", sep="\t", index=False)
    try:
        df.to_latex(OUT_DIR / f"{stem}.tex", index=False, float_format="%.4f")
    except Exception:
        pass


def _md_table(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "_No rows._"
    cols = list(df.columns)
    head = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [head, sep]
    for _, r in df.iterrows():
        row = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                row.append(f"{v:.4f}")
            else:
                row.append(str(v))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _load() -> Dict[str, Study]:
    out = {}
    for country, label in STUDIES:
        cfg = get_config(country)
        df = pd.read_parquet(cfg["ANALYSIS_FILE"]).copy()
        df = df[df["finsamp"] == 1].copy()
        df["experiment"] = country
        df["experiment_label"] = label
        cl = cfg["cluster_var"] if cfg["cluster_var"] in df.columns else "academycode"
        df["cluster_id"] = df[cl].astype(str)
        out[country] = Study(country=country, label=label, cfg=cfg, df=df)
    return out


def _construct_classroom_objects(d: pd.DataFrame) -> pd.DataFrame:
    """Construct realized and counterfactual classroom objects."""
    df = d.copy()
    # Realized classroom id
    df["class_real"] = np.where(df["treat"] == 1, df["std_grp"], df["grade"])
    df["class_real_id"] = df["academycode"].astype(str) + "|" + df["class_real"].astype(str)

    grp_real = df.groupby("class_real_id")
    df["N_real"] = grp_real["studyid"].transform("count")
    df["Vgrade_real"] = grp_real["grade"].transform(lambda x: np.nanvar(x.astype(float), ddof=0))
    df["n_grades_real"] = grp_real["grade"].transform("nunique")
    df["rank_real"] = grp_real["std_eb"].transform(lambda x: x.rank(pct=True, method="average"))

    # Counterfactual classroom ids under treatment and control rules
    df["class_treat_id"] = df["academycode"].astype(str) + "|" + df["std_grp"].astype(str)
    df["class_ctrl_id"] = df["academycode"].astype(str) + "|" + df["grade"].astype(str)

    g_t = df.groupby("class_treat_id")
    g_c = df.groupby("class_ctrl_id")
    df["Vgrade_treat"] = g_t["grade"].transform(lambda x: np.nanvar(x.astype(float), ddof=0))
    df["Vgrade_ctrl"] = g_c["grade"].transform(lambda x: np.nanvar(x.astype(float), ddof=0))
    df["n_grades_treat"] = g_t["grade"].transform("nunique")
    df["n_grades_ctrl"] = g_c["grade"].transform("nunique")

    # Prefer precomputed csize_treat/csize_ctrl from cleaning; fallback if missing
    if "csize_treat" not in df.columns:
        df["csize_treat"] = g_t["studyid"].transform("count")
    if "csize_ctrl" not in df.columns:
        df["csize_ctrl"] = g_c["studyid"].transform("count")

    # Track-level instructional targets (preferred) vs class-mean target (legacy)
    track_targets_t = df[df["treat"] == 1].groupby("std_grp")["std_eb"].mean().to_dict()
    track_targets_c = df[df["treat"] == 0].groupby("grade")["std_eb"].mean().to_dict()
    df["I_track_treat"] = df["std_grp"].map(track_targets_t)
    df["I_track_ctrl"] = df["grade"].map(track_targets_c)
    df["I_track_real"] = np.where(df["treat"] == 1, df["I_track_treat"], df["I_track_ctrl"])

    # Legacy class-mean target
    if "class_mean_eb" in df.columns:
        df["I_classmean_real"] = df["class_mean_eb"]
    else:
        cm_t = df.groupby(["academycode", "std_grp"])["std_eb"].transform("mean")
        cm_c = df.groupby(["academycode", "grade"])["std_eb"].transform("mean")
        df["I_classmean_real"] = np.where(df["treat"] == 1, cm_t, cm_c)

    # Mismatch variants
    df["mismatch_track_real"] = (df["std_eb"] - df["I_track_real"]) ** 2
    df["mismatch_classmean_real"] = (df["std_eb"] - df["I_classmean_real"]) ** 2
    df["mismatch_track_treat"] = (df["std_eb"] - df["I_track_treat"]) ** 2
    df["mismatch_track_ctrl"] = (df["std_eb"] - df["I_track_ctrl"]) ** 2

    # Social composition
    if "peer_eb_treat" not in df.columns or "peer_eb_ctrl" not in df.columns:
        # Fallback if not present
        def loo_mean(group, val):
            s = group[val].sum()
            n = group[val].notna().sum()
            return (s - group[val]) / np.maximum(n - 1, 1)

        df["peer_eb_treat"] = df.groupby(["academycode", "std_grp"], group_keys=False).apply(
            lambda g: loo_mean(g, "std_eb")
        ).reset_index(level=[0, 1], drop=True)
        df["peer_eb_ctrl"] = df.groupby(["academycode", "grade"], group_keys=False).apply(
            lambda g: loo_mean(g, "std_eb")
        ).reset_index(level=[0, 1], drop=True)

    # Productivity/disruption alternatives
    def zscore(x):
        s = x.std()
        return (x - x.mean()) / s if s > 1e-12 else x * 0.0

    df["D_size_real"] = zscore(df["N_real"])
    df["D_vgrade_real"] = zscore(df["Vgrade_real"])
    df["D_ngrades_real"] = zscore(df["n_grades_real"])
    df["D_combined_real"] = 0.5 * df["D_size_real"] + 0.5 * df["D_vgrade_real"]

    df["D_size_treat"] = zscore(df["csize_treat"])
    df["D_size_ctrl"] = zscore(df["csize_ctrl"])
    df["D_vgrade_treat"] = zscore(df["Vgrade_treat"])
    df["D_vgrade_ctrl"] = zscore(df["Vgrade_ctrl"])
    df["D_combined_treat"] = 0.5 * df["D_size_treat"] + 0.5 * df["D_vgrade_treat"]
    df["D_combined_ctrl"] = 0.5 * df["D_size_ctrl"] + 0.5 * df["D_vgrade_ctrl"]
    return df


def _measurement_block(studies: Dict[str, Study]) -> pd.DataFrame:
    rows = []
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    ax_bl = axes[0, :]
    ax_scatter = axes[1, :]

    for i, (country, st) in enumerate(studies.items()):
        d = st.df.copy()
        c = d[d["treat"] == 0]
        for g in sorted(st.cfg["grades"]):
            cg = c[(c["grade"] == g) & c["score_bl"].notna() & c["score_el"].notna()]
            if len(cg) < 20:
                continue
            rho = cg["score_bl"].corr(cg["score_el"])
            rho2 = max(min(rho ** 2, 0.95), 0.01)
            var_s = cg["score_bl"].var()
            sigma2_theta = rho2 * var_s
            sigma2_u = (1 - rho2) * var_s
            post_var = sigma2_theta * (1 - rho2)
            rows.append(
                {
                    "experiment": st.label,
                    "grade": int(g),
                    "N_control": int(len(cg)),
                    "rho": rho,
                    "rho2": rho2,
                    "mu_bl": cg["score_bl"].mean(),
                    "var_s": var_s,
                    "sigma2_theta": sigma2_theta,
                    "sigma2_u": sigma2_u,
                    "posterior_var": post_var,
                }
            )

        # Save measurement dataset per study
        rho_map = {int(r["grade"]): r["rho2"] for r in rows if r["experiment"] == st.label}
        mu_map = {
            int(g): c[c["grade"] == g]["score_bl"].mean()
            for g in sorted(st.cfg["grades"])
            if (c["grade"] == g).sum() > 0
        }
        dd = d.copy()
        dd["rho2_grade"] = dd["grade"].map(rho_map)
        dd["mu_bl_grade"] = dd["grade"].map(mu_map)
        dd["a_hat_revision"] = dd["mu_bl_grade"] + dd["rho2_grade"] * (dd["score_bl"] - dd["mu_bl_grade"])
        dd["posterior_var_revision"] = dd["grade"].map(
            {int(r["grade"]): r["posterior_var"] for r in rows if r["experiment"] == st.label}
        )
        dd.to_parquet(OUT_DIR / f"{country}_measurement_dataset.parquet", index=False)

        # Baseline distribution
        for g in sorted(st.cfg["grades"]):
            dg = d[(d["grade"] == g) & d["score_bl"].notna()]
            if len(dg) > 0:
                ax_bl[i].hist(dg["score_bl"], bins=25, alpha=0.35, density=True, label=f"G{int(g)}")
        ax_bl[i].set_title(f"{st.label}: baseline score distribution")
        ax_bl[i].set_xlabel("Raw baseline score")
        ax_bl[i].legend(frameon=False, fontsize=8)

        # Posterior vs raw
        ds = dd[["score_bl", "a_hat_revision"]].dropna()
        if len(ds) > 3000:
            ds = ds.sample(3000, random_state=42)
        ax_scatter[i].scatter(ds["score_bl"], ds["a_hat_revision"], s=6, alpha=0.25)
        ax_scatter[i].set_title(f"{st.label}: posterior vs raw")
        ax_scatter[i].set_xlabel("Raw baseline score")
        ax_scatter[i].set_ylabel("Posterior mean")

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_F_posterior_shrinkage_comparison.pdf")
    plt.close(fig)

    tab = pd.DataFrame(rows).sort_values(["experiment", "grade"])
    _save_table(tab, "table_A_signal_quality_by_grade")
    return tab


def _signal_quality_alternatives(studies: Dict[str, Study]) -> pd.DataFrame:
    """
    Alternative signal-quality diagnostics by study:
      1) Incremental predictive power of baseline over grade FE.
      2) Within-grade baseline-endline rank persistence (weighted average).
    """
    rows = []
    for _, st in studies.items():
        d = st.df.copy()
        c = d[
            (d["treat"] == 0)
            & d["score_bl"].notna()
            & d["score_el"].notna()
            & d["grade"].notna()
        ].copy()
        if len(c) < 40:
            continue

        y = c["score_el"].astype(float)
        grade_fe = pd.get_dummies(
            c["grade"].astype(int).astype(str),
            prefix="g",
            drop_first=True,
            dtype=float,
        )
        X_grade = sm.add_constant(grade_fe, has_constant="add")
        X_grade_bl = sm.add_constant(
            pd.concat([grade_fe, c[["score_bl"]].astype(float)], axis=1),
            has_constant="add",
        )
        r2_grade_only = float(sm.OLS(y, X_grade).fit().rsquared)
        r2_grade_plus_bl = float(sm.OLS(y, X_grade_bl).fit().rsquared)
        inc_r2 = r2_grade_plus_bl - r2_grade_only

        rank_corr_vals = []
        rank_corr_w = []
        for g in sorted(st.cfg["grades"]):
            cg = c[c["grade"] == g].copy()
            if len(cg) < 20:
                continue
            rb = cg["score_bl"].rank(pct=True, method="average")
            re = cg["score_el"].rank(pct=True, method="average")
            corr = rb.corr(re)
            if pd.notna(corr):
                rank_corr_vals.append(float(corr))
                rank_corr_w.append(float(len(cg)))
        rank_persist = (
            float(np.average(rank_corr_vals, weights=rank_corr_w))
            if len(rank_corr_vals) > 0
            else np.nan
        )

        rows.append(
            {
                "experiment": st.label,
                "N_control": int(len(c)),
                "r2_grade_only": r2_grade_only,
                "r2_grade_plus_baseline": r2_grade_plus_bl,
                "incremental_r2_over_grade_fe": inc_r2,
                "within_grade_rank_persistence": rank_persist,
            }
        )

    tab = pd.DataFrame(rows).sort_values("experiment")
    _save_table(tab, "table_A2_signal_quality_alternatives")
    return tab


def _front_summary_figure(
    tableSignal: pd.DataFrame,
    tableAssign: pd.DataFrame,
    tableClassroom: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a front-stage summary across four empirical margins:
    1) predictive content, 2) assignment sharpness, 3) mismatch reduction,
    4) class-size reallocation.
    """
    # (1) predictive content: weighted mean rho^2 by study
    sig = (
        tableSignal.groupby("experiment")
        .apply(
            lambda g: np.average(
                g["rho2"].astype(float),
                weights=np.maximum(g["N_control"].astype(float), 1.0),
            )
        )
        .rename("predictive_content_rho2")
    )

    # (2) assignment sharpness: 1 - misclassification rate
    sharp = (
        tableAssign.groupby("experiment")["misclassification_rate"]
        .mean()
        .astype(float)
        .rsub(1.0)
        .rename("assignment_sharpness")
    )

    # (3) mismatch reduction and (4) class-size reallocation
    wide = (
        tableClassroom[
            ["experiment", "arm", "class_size_mean", "mismatch_track_mean"]
        ]
        .pivot(index="experiment", columns="arm")
    )
    mismatch_reduction = (
        wide["mismatch_track_mean"]["control"] - wide["mismatch_track_mean"]["treat"]
    ).rename("mismatch_reduction")
    class_size_change = (
        wide["class_size_mean"]["treat"] - wide["class_size_mean"]["control"]
    ).rename("class_size_change_treat_minus_control")

    summary = pd.concat([sig, sharp, mismatch_reduction, class_size_change], axis=1)
    summary = summary.reset_index()
    _save_table(summary, "table_A3_four_margin_summary")

    # Figure: 2x2 side-by-side bars
    exp_order = [e for e in ["Kenya Y1", "Liberia"] if e in summary["experiment"].tolist()]
    plot_df = summary.set_index("experiment").loc[exp_order].copy()
    colors = ["#4e79a7", "#e15759"]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    panels = [
        ("predictive_content_rho2", "Predictive content (weighted $R^2$)"),
        ("assignment_sharpness", "Assignment sharpness (1 - misclass.)"),
        ("mismatch_reduction", "Mismatch reduction (control - treat)"),
        ("class_size_change_treat_minus_control", "Class-size change (treat - control)"),
    ]
    for ax, (col, title) in zip(axes.flatten(), panels):
        vals = plot_df[col].to_numpy(float)
        ax.bar(exp_order, vals, color=colors)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_title(title)
        for xi, v in enumerate(vals):
            ax.text(xi, v + (0.02 if v >= 0 else -0.04), f"{v:.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_E_kenya_liberia_four_margins.pdf")
    plt.close(fig)
    return summary


def _assignment_block(studies: Dict[str, Study]) -> pd.DataFrame:
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    for i, (country, st) in enumerate(studies.items()):
        d = st.df.copy()
        t = d[(d["treat"] == 1) & d["score_bl"].notna() & d["upper_group"].notna()]
        x_min, x_max = t["score_bl"].quantile(0.01), t["score_bl"].quantile(0.99)
        x_grid = np.linspace(x_min, x_max, 300)
        cmap = plt.get_cmap("tab10")
        for j, g in enumerate(sorted(st.cfg["grades"])):
            tg = t[t["grade"] == g]
            if len(tg) == 0:
                continue
            cutoff = st.cfg["cutoffs"][int(g)]
            det = (tg["score_bl"] > cutoff).astype(float)
            misclass = (det != tg["upper_group"]).mean()
            rows.append(
                {
                    "experiment": st.label,
                    "grade": int(g),
                    "N_treated": int(len(tg)),
                    "cutoff": float(cutoff),
                    "misclassification_rate": float(misclass),
                    "assignment_rule": "deterministic_cutoff",
                }
            )

            # Plot empirical binned means + deterministic step
            bins = np.quantile(tg["score_bl"], np.linspace(0, 1, 12))
            bins = np.unique(bins)
            if len(bins) > 2:
                cats = pd.cut(tg["score_bl"], bins=bins, include_lowest=True, duplicates="drop")
                bmean = tg.groupby(cats, observed=False)["upper_group"].mean()
                bx = np.array([iv.mid for iv in bmean.index])
                axes[i].plot(bx, bmean.values, "o", color=cmap(j), ms=4, alpha=0.8)
            step = (x_grid > cutoff).astype(float)
            axes[i].plot(x_grid, step, color=cmap(j), lw=1.7, label=f"G{int(g)} cutoff={cutoff:g}")

        axes[i].set_title(st.label)
        axes[i].set_xlabel("Baseline score")
        axes[i].set_ylabel("Pr(upper track)")
        axes[i].set_ylim(-0.02, 1.02)
        axes[i].legend(frameon=False, fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_G_deterministic_assignment_cutoffs.pdf")
    plt.close(fig)

    tab = pd.DataFrame(rows).sort_values(["experiment", "grade"])
    _save_table(tab, "table_B_assignment_cutoff_summary")
    return tab


def _classroom_reallocation_table(studies: Dict[str, Study]) -> pd.DataFrame:
    rows = []
    for country, st in studies.items():
        d = _construct_classroom_objects(st.df)
        st.df = d
        for tval, name in [(0, "control"), (1, "treat")]:
            sub = d[d["treat"] == tval]
            rows.append(
                {
                    "experiment": st.label,
                    "arm": name,
                    "N": len(sub),
                    "class_size_mean": sub["N_real"].mean(),
                    "class_size_sd": sub["N_real"].std(),
                    "V_c_grade_mean": sub["Vgrade_real"].mean(),
                    "V_c_grade_sd": sub["Vgrade_real"].std(),
                    "n_grades_mean": sub["n_grades_real"].mean(),
                    "peer_mean_eb": sub["peer_eb"].mean(),
                    "mismatch_track_mean": sub["mismatch_track_real"].mean(),
                    "mismatch_classmean_mean": sub["mismatch_classmean_real"].mean(),
                }
            )
    tab = pd.DataFrame(rows)
    _save_table(tab, "table_C_classroom_reallocation_summary")

    # Figure H: shifts by study
    shifts = []
    for st in studies.values():
        d = st.df
        c = d[d["treat"] == 0]
        t = d[d["treat"] == 1]
        shifts.append(
            {
                "experiment": st.label,
                "delta_class_size": t["N_real"].mean() - c["N_real"].mean(),
                "delta_vgrade": t["Vgrade_real"].mean() - c["Vgrade_real"].mean(),
                "delta_n_grades": t["n_grades_real"].mean() - c["n_grades_real"].mean(),
            }
        )
    sh = pd.DataFrame(shifts)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for j, col in enumerate(["delta_class_size", "delta_vgrade", "delta_n_grades"]):
        axes[j].bar(sh["experiment"], sh[col], color=["#4e79a7", "#e15759"])
        axes[j].axhline(0, color="black", lw=0.8)
        axes[j].set_title(col.replace("_", " "))
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_H_classsize_grade_dispersion_shifts.pdf")
    plt.close(fig)

    return tab


def _estimate_itt(sub: pd.DataFrame, y_col: str) -> float:
    d = sub[sub[y_col].notna() & sub["std_eb"].notna()].copy()
    if len(d) < 40 or d["treat"].nunique() < 2:
        return np.nan
    X = pd.DataFrame({"treat": d["treat"].astype(float), "std_eb": d["std_eb"].astype(float)})
    fe = pd.get_dummies(d["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([X, fe], axis=1)
    try:
        res = ols_cluster(d[y_col].astype(float), X, d["cluster_id"])
        return float(res.params.get("treat", np.nan))
    except Exception:
        return np.nan


def _kenya_production_module(kenya: Study) -> Tuple[pd.DataFrame, pd.DataFrame]:
    d = kenya.df.copy()
    d = d[
        d["std_score_el"].notna()
        & d["std_eb"].notna()
        & d["mismatch_track_real"].notna()
        & d["peer_eb"].notna()
    ].copy()

    # Compare disruption alternatives
    disruptions = [
        ("size_only", "D_size_real"),
        ("vgrade_only", "D_vgrade_real"),
        ("combined", "D_combined_real"),
        ("n_grades_only", "D_ngrades_real"),
    ]
    rows_alt = []
    for name, dcol in disruptions:
        X = pd.DataFrame(
            {
                "treat": d["treat"].astype(float),
                "a": d["std_eb"].astype(float),
                "a2": (d["std_eb"] ** 2).astype(float),
                "mismatch_track": d["mismatch_track_real"].astype(float),
                "social": d["peer_eb"].astype(float),
                "disruption": d[dcol].astype(float),
            }
        )
        fe = pd.get_dummies(d["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
        X = pd.concat([X, fe], axis=1)
        res = ols_cluster(d["std_score_el"].astype(float), X, d["cluster_id"])
        rows_alt.append(
            {
                "spec": name,
                "N": len(d),
                "lambda_hat": -float(res.params["mismatch_track"]),
                "lambda_se": float(res.bse["mismatch_track"]),
                "zeta_hat": float(res.params["social"]),
                "zeta_se": float(res.bse["social"]),
                "psiD_hat": -float(res.params["disruption"]),
                "psiD_se": float(res.bse["disruption"]),
                "t_psiD": abs(float(res.params["disruption"] / res.bse["disruption"])),
                "r2": float(res.rsquared),
            }
        )
    alt_tab = pd.DataFrame(rows_alt).sort_values("t_psiD", ascending=False)
    _save_table(alt_tab, "table_D1_kenya_disruption_alternatives")

    # Choose preferred disruption by stability and interpretability: combined index
    preferred = "D_combined_real"
    X = pd.DataFrame(
        {
            "treat": d["treat"].astype(float),
            "a": d["std_eb"].astype(float),
            "a2": (d["std_eb"] ** 2).astype(float),
            "mismatch_track": d["mismatch_track_real"].astype(float),
            "social": d["peer_eb"].astype(float),
            "disruption": d[preferred].astype(float),
        }
    )
    fe = pd.get_dummies(d["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([X, fe], axis=1)
    res = ols_cluster(d["std_score_el"].astype(float), X, d["cluster_id"])

    main_tab = pd.DataFrame(
        [
            {
                "preferred_disruption": "combined(size,vgrade)",
                "N": len(d),
                "lambda_hat": -float(res.params["mismatch_track"]),
                "lambda_se": float(res.bse["mismatch_track"]),
                "zeta_hat": float(res.params["social"]),
                "zeta_se": float(res.bse["social"]),
                "psiD_hat": -float(res.params["disruption"]),
                "psiD_se": float(res.bse["disruption"]),
                "treat_coef": float(res.params["treat"]),
                "treat_se": float(res.bse["treat"]),
                "r2": float(res.rsquared),
            }
        ]
    )
    _save_table(main_tab, "table_D_kenya_structural_production")

    # Moment-focused minimum distance (Kenya)
    # Moments targeted: mean ITT + ITT by quartile
    kd = kenya.df.copy()
    kd = kd[kd["std_score_el"].notna() & kd["std_eb"].notna()].copy()
    q = pd.qcut(kd["std_score_bl"], 4, labels=False, duplicates="drop")
    kd["q"] = q
    moms_emp = {"mean": _estimate_itt(kd, "std_score_el")}
    for qq in sorted(kd["q"].dropna().unique()):
        moms_emp[f"q{int(qq)+1}"] = _estimate_itt(kd[kd["q"] == qq], "std_score_el")

    # Build potential outcomes from classroom objects (track-target mismatch preferred)
    dd = kenya.df.copy()
    dd = dd[
        dd["std_eb"].notna()
        & dd["mismatch_track_treat"].notna()
        & dd["mismatch_track_ctrl"].notna()
        & dd["peer_eb_treat"].notna()
        & dd["peer_eb_ctrl"].notna()
    ].copy()
    # disruption under potential assignments
    D_t = dd["D_combined_treat"].astype(float).to_numpy()
    D_c = dd["D_combined_ctrl"].astype(float).to_numpy()
    a = dd["std_eb"].astype(float).to_numpy()
    m_t = dd["mismatch_track_treat"].astype(float).to_numpy()
    m_c = dd["mismatch_track_ctrl"].astype(float).to_numpy()
    s_t = dd["peer_eb_treat"].astype(float).to_numpy()
    s_c = dd["peer_eb_ctrl"].astype(float).to_numpy()

    # Initial values from regression
    lam0 = max(main_tab["lambda_hat"].iloc[0], 0.0)
    z0 = main_tab["zeta_hat"].iloc[0]
    p0 = max(main_tab["psiD_hat"].iloc[0], 0.0)
    alpha0 = 0.0

    def model_delta(par):
        alpha, lam, zeta, psiD = par
        y1 = a + (alpha - lam * m_t + zeta * s_t - psiD * D_t)
        y0 = a + (alpha - lam * m_c + zeta * s_c - psiD * D_c)
        return y1 - y0

    q_all = pd.qcut(dd["std_score_bl"], 4, labels=False, duplicates="drop")

    def objective(par):
        delta = model_delta(par)
        vals = {"mean": float(np.nanmean(delta))}
        for qq in sorted(pd.Series(q_all).dropna().unique()):
            vals[f"q{int(qq)+1}"] = float(np.nanmean(delta[pd.Series(q_all) == qq]))
        err = []
        for k, v in moms_emp.items():
            if pd.notna(v) and k in vals and pd.notna(vals[k]):
                err.append(v - vals[k])
        if not err:
            return 1e6
        # mild regularization
        reg = 1e-3 * np.sum(np.square(par))
        return float(np.sum(np.square(err)) + reg)

    bounds = [(-1.5, 1.5), (0.0, 2.0), (-2.0, 2.0), (0.0, 2.0)]
    from scipy.optimize import minimize

    opt = minimize(
        objective,
        x0=np.array([alpha0, lam0, z0, p0]),
        bounds=bounds,
        method="L-BFGS-B",
        options={"maxiter": 300},
    )
    par = opt.x
    delta = model_delta(par)
    moms_mod = {"mean": float(np.nanmean(delta))}
    for qq in sorted(pd.Series(q_all).dropna().unique()):
        moms_mod[f"q{int(qq)+1}"] = float(np.nanmean(delta[pd.Series(q_all) == qq]))

    md_tab = pd.DataFrame(
        [
            {
                "converged": int(opt.success),
                "alpha_hat": par[0],
                "lambda_hat": par[1],
                "zeta_hat": par[2],
                "psiD_hat": par[3],
                "objective": float(opt.fun),
                "note": "Kenya-only minimum-distance to mean+quartile ITT moments",
            }
        ]
    )
    _save_table(md_tab, "table_D2_kenya_moment_estimator")

    # Figure I: empirical vs model moments
    keys = [k for k in ["mean", "q1", "q2", "q3", "q4"] if k in moms_emp and k in moms_mod]
    emp = np.array([moms_emp[k] for k in keys], dtype=float)
    mod = np.array([moms_mod[k] for k in keys], dtype=float)
    x = np.arange(len(keys))
    w = 0.38
    fig, ax = plt.subplots(1, 1, figsize=(8, 4))
    ax.bar(x - w / 2, emp, width=w, label="Empirical")
    ax.bar(x + w / 2, mod, width=w, label="Model")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(keys)
    ax.set_title("Kenya model fit to targeted moments")
    ax.set_ylabel("Treatment effect")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_I_kenya_moment_fit.pdf")
    plt.close(fig)

    return main_tab, md_tab


def _derive_latent_track_targets_kenya(d: pd.DataFrame) -> Dict[int, float]:
    """
    Latent track targets for Kenya:
    Choose (I1, I2) by minimizing treated-sample RSS in a reduced-form
    outcome regression with mismatch defined using candidate targets.
    """
    t = d[
        (d["treat"] == 1)
        & d["std_score_el"].notna()
        & d["std_eb"].notna()
        & d["peer_eb"].notna()
        & d["D_combined_real"].notna()
    ].copy()
    if len(t) < 200:
        # fallback
        means = t.groupby("std_grp")["std_eb"].mean().to_dict()
        return {1: float(means.get(1, -0.25)), 2: float(means.get(2, 0.25))}

    q10, q90 = t["std_eb"].quantile([0.10, 0.90])
    q50 = t["std_eb"].quantile(0.50)
    grid1 = np.linspace(q10, q50, 25)
    grid2 = np.linspace(q50, q90, 25)

    best = {"rss": np.inf, "I1": None, "I2": None}
    y = t["std_score_el"].astype(float)
    fe = pd.get_dummies(t["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
    for I1 in grid1:
        for I2 in grid2:
            if I2 <= I1:
                continue
            m = np.where(t["std_grp"] == 1, (t["std_eb"] - I1) ** 2, (t["std_eb"] - I2) ** 2)
            X = pd.DataFrame(
                {
                    "a": t["std_eb"].astype(float),
                    "a2": (t["std_eb"] ** 2).astype(float),
                    "mismatch": m.astype(float),
                    "social": t["peer_eb"].astype(float),
                    "disruption": t["D_combined_real"].astype(float),
                }
            )
            X = pd.concat([X, fe], axis=1)
            try:
                res = ols_cluster(y, X, t["cluster_id"])
                rss = float(np.sum(res.resid ** 2))
                if rss < best["rss"]:
                    best = {"rss": rss, "I1": float(I1), "I2": float(I2)}
            except Exception:
                continue
    if best["I1"] is None:
        means = t.groupby("std_grp")["std_eb"].mean().to_dict()
        return {1: float(means.get(1, -0.25)), 2: float(means.get(2, 0.25))}
    return {1: best["I1"], 2: best["I2"]}


def _kenya_moment_setup(
    d: pd.DataFrame,
    mismatch_treat_col: str,
    mismatch_ctrl_col: str,
    disruption_treat_col: str,
    disruption_ctrl_col: str,
) -> Tuple[Dict[str, float], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    kd = d[d["std_score_el"].notna() & d["std_eb"].notna()].copy()
    q = pd.qcut(kd["std_score_bl"], 4, labels=False, duplicates="drop")
    kd["q"] = q

    moms_emp = {"mean": _estimate_itt(kd, "std_score_el")}
    for qq in sorted(kd["q"].dropna().unique()):
        moms_emp[f"q{int(qq)+1}"] = _estimate_itt(kd[kd["q"] == qq], "std_score_el")

    # Track-specific ITT moments
    for tr in [0, 1]:
        moms_emp[f"track{tr}"] = _estimate_itt(kd[kd["upper_group"] == tr], "std_score_el")

    # Institutional moments (non-outcome; used as diagnostics / weakly weighted targets)
    moms_emp["te_mismatch"] = float(kd[mismatch_treat_col].mean() - kd[mismatch_ctrl_col].mean())
    moms_emp["te_classsize"] = float(kd["csize_treat"].mean() - kd["csize_ctrl"].mean())
    moms_emp["te_vgrade"] = float(kd["Vgrade_treat"].mean() - kd["Vgrade_ctrl"].mean())

    dd = d[
        d["std_eb"].notna()
        & d[mismatch_treat_col].notna()
        & d[mismatch_ctrl_col].notna()
        & d["peer_eb_treat"].notna()
        & d["peer_eb_ctrl"].notna()
        & d[disruption_treat_col].notna()
        & d[disruption_ctrl_col].notna()
    ].copy()

    dm = (dd[mismatch_treat_col] - dd[mismatch_ctrl_col]).to_numpy(float)
    dD = (dd[disruption_treat_col] - dd[disruption_ctrl_col]).to_numpy(float)
    ds = (dd["peer_eb_treat"] - dd["peer_eb_ctrl"]).to_numpy(float)
    q_all = pd.qcut(dd["std_score_bl"], 4, labels=False, duplicates="drop")
    tr_all = dd["upper_group"].to_numpy()
    return moms_emp, dm, dD, ds, q_all.to_numpy(), tr_all


def _kenya_moment_objective(
    par: np.ndarray,
    moms_emp: Dict[str, float],
    dm: np.ndarray,
    dD: np.ndarray,
    ds: np.ndarray,
    q_all: np.ndarray,
    tr_all: np.ndarray,
    weights: Dict[str, float] | None = None,
) -> float:
    lam, phi, zeta = par
    delta = -lam * dm + phi * dD + zeta * ds
    vals = {"mean": float(np.nanmean(delta))}
    for qq in sorted(pd.Series(q_all).dropna().unique()):
        vals[f"q{int(qq)+1}"] = float(np.nanmean(delta[pd.Series(q_all) == qq]))
    for tr in [0, 1]:
        vals[f"track{tr}"] = float(np.nanmean(delta[tr_all == tr]))
    vals["te_mismatch"] = float(np.nanmean(dm))
    # class-size / grade-dispersion are institutional reallocation moments,
    # not governed by production parameters in this lean estimator.
    vals["te_classsize"] = moms_emp.get("te_classsize", np.nan)
    vals["te_vgrade"] = moms_emp.get("te_vgrade", np.nan)

    # Weighted objective: primary on outcome moments, weak weights on institutional moments
    w_default = {
        "mean": 3.0,
        "q1": 1.0,
        "q2": 1.0,
        "q3": 1.0,
        "q4": 1.0,
        "track0": 1.0,
        "track1": 1.0,
        "te_mismatch": 0.15,
        "te_classsize": 0.0,
        "te_vgrade": 0.0,
    }
    w = w_default if weights is None else weights
    err = []
    for k, e in moms_emp.items():
        if pd.notna(e) and k in vals and pd.notna(vals[k]):
            err.append(w.get(k, 1.0) * (e - vals[k]))
    if not err:
        return 1e6
    reg = 1e-3 * (lam ** 2 + phi ** 2 + zeta ** 2)
    return float(np.sum(np.square(err)) + reg)


def _kenya_mismatch_comparison(kenya: Study) -> Tuple[pd.DataFrame, str]:
    """
    Compare mismatch definitions:
    A) classroom-mean proxy
    B) empirical track-target proxy
    C) latent estimated track target
    """
    d = kenya.df.copy()

    # Build latent track targets
    latent_targets = _derive_latent_track_targets_kenya(d)
    d["I_latent_treat"] = d["std_grp"].map(latent_targets)
    # control fallback: grade means in control
    c_grade_targets = d[d["treat"] == 0].groupby("grade")["std_eb"].mean().to_dict()
    d["I_latent_ctrl"] = d["grade"].map(c_grade_targets)
    d["mismatch_latent_real"] = np.where(
        d["treat"] == 1,
        (d["std_eb"] - d["I_latent_treat"]) ** 2,
        (d["std_eb"] - d["I_latent_ctrl"]) ** 2,
    )
    d["mismatch_latent_treat"] = (d["std_eb"] - d["I_latent_treat"]) ** 2
    d["mismatch_latent_ctrl"] = (d["std_eb"] - d["I_latent_ctrl"]) ** 2

    defs = [
        ("A_classmean", "mismatch_classmean_real", "misfit", "misfit"),
        ("B_track_empirical", "mismatch_track_real", "mismatch_track_treat", "mismatch_track_ctrl"),
        ("C_track_latent", "mismatch_latent_real", "mismatch_latent_treat", "mismatch_latent_ctrl"),
    ]

    rows = []
    from scipy.optimize import minimize
    for name, m_real, m_t, m_c in defs:
        sub = d[
            d["std_score_el"].notna()
            & d["std_eb"].notna()
            & d[m_real].notna()
            & d["peer_eb"].notna()
            & d["D_combined_real"].notna()
        ].copy()
        # Stability via reduced-form coefficients
        X = pd.DataFrame(
            {
                "treat": sub["treat"].astype(float),
                "a": sub["std_eb"].astype(float),
                "a2": (sub["std_eb"] ** 2).astype(float),
                "mismatch": sub[m_real].astype(float),
                "social": sub["peer_eb"].astype(float),
                "disruption": sub["D_combined_real"].astype(float),
            }
        )
        fe = pd.get_dummies(sub["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
        X = pd.concat([X, fe], axis=1)
        rf = ols_cluster(sub["std_score_el"].astype(float), X, sub["cluster_id"])

        moms_emp, dm, dD, ds, q_all, tr_all = _kenya_moment_setup(
            d, m_t, m_c, "D_combined_treat", "D_combined_ctrl"
        )
        obj = lambda p: _kenya_moment_objective(p, moms_emp, dm, dD, ds, q_all, tr_all)
        opt = minimize(
            obj,
            x0=np.array([0.05, 0.0, -0.1]),
            bounds=[(0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)],
            method="L-BFGS-B",
            options={"maxiter": 300},
        )
        lam, phi, zeta = opt.x
        rows.append(
            {
                "mismatch_def": name,
                "rf_lambda_hat": -float(rf.params["mismatch"]),
                "rf_lambda_se": float(rf.bse["mismatch"]),
                "rf_zeta_hat": float(rf.params["social"]),
                "rf_r2": float(rf.rsquared),
                "md_converged": int(opt.success),
                "md_lambda_hat": float(lam),
                "md_phi_hat": float(phi),
                "md_zeta_hat": float(zeta),
                "md_objective": float(opt.fun),
                "te_mismatch_observed": float(sub[m_t].mean() - sub[m_c].mean()) if (m_t in sub.columns and m_c in sub.columns) else np.nan,
            }
        )
    tab = pd.DataFrame(rows).sort_values("md_objective")
    _save_table(tab, "table_A_mismatch_definition_comparison")
    preferred = tab.iloc[0]["mismatch_def"]
    return tab, preferred


def _kenya_disruption_comparison(kenya: Study, mismatch_choice: str) -> Tuple[pd.DataFrame, str]:
    d = kenya.df.copy()
    # map mismatch choice
    if mismatch_choice == "A_classmean":
        m_real, m_t, m_c = "mismatch_classmean_real", "misfit", "misfit"
    elif mismatch_choice == "B_track_empirical":
        m_real, m_t, m_c = "mismatch_track_real", "mismatch_track_treat", "mismatch_track_ctrl"
    else:
        # recompute latent quickly
        latent_targets = _derive_latent_track_targets_kenya(d)
        d["I_latent_treat"] = d["std_grp"].map(latent_targets)
        c_grade_targets = d[d["treat"] == 0].groupby("grade")["std_eb"].mean().to_dict()
        d["I_latent_ctrl"] = d["grade"].map(c_grade_targets)
        d["mismatch_latent_real"] = np.where(
            d["treat"] == 1,
            (d["std_eb"] - d["I_latent_treat"]) ** 2,
            (d["std_eb"] - d["I_latent_ctrl"]) ** 2,
        )
        d["mismatch_latent_treat"] = (d["std_eb"] - d["I_latent_treat"]) ** 2
        d["mismatch_latent_ctrl"] = (d["std_eb"] - d["I_latent_ctrl"]) ** 2
        m_real, m_t, m_c = "mismatch_latent_real", "mismatch_latent_treat", "mismatch_latent_ctrl"

    dis_defs = [
        ("A_size_only", "D_size_real", "D_size_treat", "D_size_ctrl"),
        ("B_grade_disp_only", "D_vgrade_real", "D_vgrade_treat", "D_vgrade_ctrl"),
        ("C_n_grades_only", "D_ngrades_real", "n_grades_treat", "n_grades_ctrl"),
        ("D_combined", "D_combined_real", "D_combined_treat", "D_combined_ctrl"),
    ]

    from scipy.optimize import minimize
    rows = []
    for name, d_real, d_t, d_c in dis_defs:
        sub = d[
            d["std_score_el"].notna()
            & d["std_eb"].notna()
            & d[m_real].notna()
            & d["peer_eb"].notna()
            & d[d_real].notna()
        ].copy()
        X = pd.DataFrame(
            {
                "treat": sub["treat"].astype(float),
                "a": sub["std_eb"].astype(float),
                "a2": (sub["std_eb"] ** 2).astype(float),
                "mismatch": sub[m_real].astype(float),
                "social": sub["peer_eb"].astype(float),
                "disruption": sub[d_real].astype(float),
            }
        )
        fe = pd.get_dummies(sub["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
        X = pd.concat([X, fe], axis=1)
        rf = ols_cluster(sub["std_score_el"].astype(float), X, sub["cluster_id"])

        moms_emp, dm, dD, ds, q_all, tr_all = _kenya_moment_setup(d, m_t, m_c, d_t, d_c)
        obj = lambda p: _kenya_moment_objective(p, moms_emp, dm, dD, ds, q_all, tr_all)
        opt = minimize(
            obj,
            x0=np.array([0.05, 0.0, -0.1]),
            bounds=[(0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)],
            method="L-BFGS-B",
            options={"maxiter": 300},
        )
        lam, phi, zeta = opt.x
        rows.append(
            {
                "disruption_def": name,
                "rf_lambda_hat": -float(rf.params["mismatch"]),
                "rf_psi_hat": -float(rf.params["disruption"]),
                "rf_psi_se": float(rf.bse["disruption"]),
                "rf_zeta_hat": float(rf.params["social"]),
                "rf_r2": float(rf.rsquared),
                "md_converged": int(opt.success),
                "md_lambda_hat": float(lam),
                "md_phi_hat": float(phi),
                "md_zeta_hat": float(zeta),
                "md_objective": float(opt.fun),
            }
        )
    tab = pd.DataFrame(rows).sort_values("md_objective")
    _save_table(tab, "table_B_disruption_definition_comparison")
    preferred = tab.iloc[0]["disruption_def"]
    return tab, preferred


def _kenya_preferred_estimator_and_profiles(
    kenya: Study,
    mismatch_choice: str,
    disruption_choice: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    d = kenya.df.copy()
    if mismatch_choice == "A_classmean":
        m_real, m_t, m_c = "mismatch_classmean_real", "misfit", "misfit"
    elif mismatch_choice == "B_track_empirical":
        m_real, m_t, m_c = "mismatch_track_real", "mismatch_track_treat", "mismatch_track_ctrl"
    else:
        latent_targets = _derive_latent_track_targets_kenya(d)
        d["I_latent_treat"] = d["std_grp"].map(latent_targets)
        c_grade_targets = d[d["treat"] == 0].groupby("grade")["std_eb"].mean().to_dict()
        d["I_latent_ctrl"] = d["grade"].map(c_grade_targets)
        d["mismatch_latent_real"] = np.where(
            d["treat"] == 1,
            (d["std_eb"] - d["I_latent_treat"]) ** 2,
            (d["std_eb"] - d["I_latent_ctrl"]) ** 2,
        )
        d["mismatch_latent_treat"] = (d["std_eb"] - d["I_latent_treat"]) ** 2
        d["mismatch_latent_ctrl"] = (d["std_eb"] - d["I_latent_ctrl"]) ** 2
        m_real, m_t, m_c = "mismatch_latent_real", "mismatch_latent_treat", "mismatch_latent_ctrl"

    dmap = {
        "A_size_only": ("D_size_real", "D_size_treat", "D_size_ctrl"),
        "B_grade_disp_only": ("D_vgrade_real", "D_vgrade_treat", "D_vgrade_ctrl"),
        "C_n_grades_only": ("D_ngrades_real", "n_grades_treat", "n_grades_ctrl"),
        "D_combined": ("D_combined_real", "D_combined_treat", "D_combined_ctrl"),
    }
    d_real, d_t, d_c = dmap[disruption_choice]

    # Main reduced-form table
    sub = d[
        d["std_score_el"].notna()
        & d["std_eb"].notna()
        & d[m_real].notna()
        & d["peer_eb"].notna()
        & d[d_real].notna()
    ].copy()
    X = pd.DataFrame(
        {
            "treat": sub["treat"].astype(float),
            "a": sub["std_eb"].astype(float),
            "a2": (sub["std_eb"] ** 2).astype(float),
            "mismatch": sub[m_real].astype(float),
            "social": sub["peer_eb"].astype(float),
            "disruption": sub[d_real].astype(float),
        }
    )
    fe = pd.get_dummies(sub["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([X, fe], axis=1)
    rf = ols_cluster(sub["std_score_el"].astype(float), X, sub["cluster_id"])

    # Moment estimator as main
    moms_emp, dm, dD, ds, q_all, tr_all = _kenya_moment_setup(d, m_t, m_c, d_t, d_c)
    from scipy.optimize import minimize

    base_weights = {
        "mean": 3.0,
        "q1": 1.0,
        "q2": 1.0,
        "q3": 1.0,
        "q4": 1.0,
        "track0": 1.0,
        "track1": 1.0,
        "te_mismatch": 0.15,
        "te_classsize": 0.0,
        "te_vgrade": 0.0,
    }
    obj = lambda p: _kenya_moment_objective(p, moms_emp, dm, dD, ds, q_all, tr_all, weights=base_weights)
    opt = minimize(
        obj,
        x0=np.array([0.05, 0.0, -0.1]),
        bounds=[(0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)],
        method="L-BFGS-B",
        options={"maxiter": 400},
    )
    lam, phi, zeta = opt.x

    main = pd.DataFrame(
        [
            {
                "preferred_mismatch": mismatch_choice,
                "preferred_disruption": disruption_choice,
                "N": len(sub),
                "rf_lambda_hat": -float(rf.params["mismatch"]),
                "rf_lambda_se": float(rf.bse["mismatch"]),
                "rf_phi_hat": -float(rf.params["disruption"]),
                "rf_phi_se": float(rf.bse["disruption"]),
                "rf_zeta_hat": float(rf.params["social"]),
                "rf_zeta_se": float(rf.bse["social"]),
                "rf_r2": float(rf.rsquared),
                "md_converged": int(opt.success),
                "md_lambda_hat": float(lam),
                "md_phi_hat": float(phi),
                "md_zeta_hat": float(zeta),
                "md_objective": float(opt.fun),
            }
        ]
    )
    _save_table(main, "table_C_preferred_kenya_estimator")

    # Profile diagnostics
    # Profile lambda and phi by re-optimizing over the remaining parameters.
    grids = {
        "lambda": np.linspace(0.0, 0.40, 60),
        "phi": np.linspace(-0.60, 0.60, 60),
        "zeta": np.linspace(-0.80, 0.80, 60),
    }
    prof_rows = []
    # lambda profile: optimize phi,zeta
    for lv in grids["lambda"]:
        fun = lambda x: _kenya_moment_objective(
            np.array([lv, x[0], x[1]]), moms_emp, dm, dD, ds, q_all, tr_all, weights=base_weights
        )
        op = minimize(fun, x0=np.array([phi, zeta]), bounds=[(-2, 2), (-2, 2)], method="L-BFGS-B")
        prof_rows.append({"param": "lambda", "grid": float(lv), "obj": float(op.fun)})
    # phi profile: optimize lambda,zeta
    for pv in grids["phi"]:
        fun = lambda x: _kenya_moment_objective(
            np.array([x[0], pv, x[1]]), moms_emp, dm, dD, ds, q_all, tr_all, weights=base_weights
        )
        op = minimize(fun, x0=np.array([lam, zeta]), bounds=[(0, 2), (-2, 2)], method="L-BFGS-B")
        prof_rows.append({"param": "phi", "grid": float(pv), "obj": float(op.fun)})
    # zeta profile: optimize lambda,phi
    for zv in grids["zeta"]:
        fun = lambda x: _kenya_moment_objective(
            np.array([x[0], x[1], zv]), moms_emp, dm, dD, ds, q_all, tr_all, weights=base_weights
        )
        op = minimize(fun, x0=np.array([lam, phi]), bounds=[(0, 2), (-2, 2)], method="L-BFGS-B")
        prof_rows.append({"param": "zeta", "grid": float(zv), "obj": float(op.fun)})

    prof = pd.DataFrame(prof_rows)
    _save_table(prof, "table_D_parameter_profiles")

    # classify sharpness
    diag = []
    for p in ["lambda", "phi", "zeta"]:
        sp = prof[prof["param"] == p].copy()
        m = sp["obj"].min()
        tol = m + 0.10 * max(abs(m), 1e-6)
        width = sp.loc[sp["obj"] <= tol, "grid"].max() - sp.loc[sp["obj"] <= tol, "grid"].min()
        rng = sp["grid"].max() - sp["grid"].min()
        frac = width / rng if rng > 0 else np.nan
        if frac < 0.15:
            idn = "sharp"
        elif frac < 0.40:
            idn = "moderate"
        else:
            idn = "weak/flat"
        diag.append({"parameter": p, "argmin_grid": sp.loc[sp["obj"].idxmin(), "grid"], "obj_min": m, "relative_flat_width": frac, "identification": idn})
    diag_tab = pd.DataFrame(diag)
    _save_table(diag_tab, "table_D_profile_identification_note")

    # Figure D: profile plots
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for i, p in enumerate(["lambda", "phi", "zeta"]):
        sp = prof[prof["param"] == p]
        axes[i].plot(sp["grid"], sp["obj"], lw=2)
        axes[i].set_title(f"Profile: {p}")
        axes[i].set_xlabel(p)
        axes[i].set_ylabel("Objective")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig_D_kenya_parameter_profiles.pdf")
    plt.close(fig)
    # Weight robustness for profile diagnostics
    from scipy.optimize import minimize
    weight_specs = {
        "baseline": base_weights,
        "equal_weights": {
            "mean": 1.0, "q1": 1.0, "q2": 1.0, "q3": 1.0, "q4": 1.0, "track0": 1.0, "track1": 1.0,
            "te_mismatch": 0.0, "te_classsize": 0.0, "te_vgrade": 0.0,
        },
        "quartile_heavy": {
            "mean": 1.0, "q1": 2.0, "q2": 2.0, "q3": 2.0, "q4": 2.0, "track0": 1.0, "track1": 1.0,
            "te_mismatch": 0.0, "te_classsize": 0.0, "te_vgrade": 0.0,
        },
    }
    wr_rows = []
    for wname, ww in weight_specs.items():
        obj_w = lambda p: _kenya_moment_objective(p, moms_emp, dm, dD, ds, q_all, tr_all, weights=ww)
        op = minimize(
            obj_w,
            x0=np.array([lam, phi, zeta]),
            bounds=[(0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)],
            method="L-BFGS-B",
            options={"maxiter": 300},
        )
        lam_w, phi_w, zeta_w = op.x
        # profile width diagnostic under this weight set
        for pname, grid, base_vec in [
            ("lambda", np.linspace(0.0, 0.40, 40), np.array([phi_w, zeta_w])),
            ("phi", np.linspace(-0.60, 0.60, 40), np.array([lam_w, zeta_w])),
            ("zeta", np.linspace(-0.80, 0.80, 40), np.array([lam_w, phi_w])),
        ]:
            vals = []
            for gv in grid:
                if pname == "lambda":
                    fun = lambda x: _kenya_moment_objective(np.array([gv, x[0], x[1]]), moms_emp, dm, dD, ds, q_all, tr_all, weights=ww)
                    oo = minimize(fun, x0=base_vec, bounds=[(-2, 2), (-2, 2)], method="L-BFGS-B")
                elif pname == "phi":
                    fun = lambda x: _kenya_moment_objective(np.array([x[0], gv, x[1]]), moms_emp, dm, dD, ds, q_all, tr_all, weights=ww)
                    oo = minimize(fun, x0=base_vec, bounds=[(0, 2), (-2, 2)], method="L-BFGS-B")
                else:
                    fun = lambda x: _kenya_moment_objective(np.array([x[0], x[1], gv]), moms_emp, dm, dD, ds, q_all, tr_all, weights=ww)
                    oo = minimize(fun, x0=base_vec, bounds=[(0, 2), (-2, 2)], method="L-BFGS-B")
                vals.append(float(oo.fun))
            vals = np.array(vals)
            mobj = vals.min()
            tol = mobj + 0.10 * max(abs(mobj), 1e-6)
            width = grid[vals <= tol].max() - grid[vals <= tol].min()
            frac = float(width / (grid.max() - grid.min()))
            wr_rows.append(
                {
                    "weight_spec": wname,
                    "parameter": pname,
                    "estimate_lambda": float(lam_w),
                    "estimate_phi": float(phi_w),
                    "estimate_zeta": float(zeta_w),
                    "obj_min": float(mobj),
                    "relative_flat_width": frac,
                }
            )
    wr_tab = pd.DataFrame(wr_rows)
    _save_table(wr_tab, "table_D2_profile_weight_robustness")

    # Bootstrap CIs for Kenya preferred params (cluster bootstrap)
    # Uses preferred objective and sample moments, with fixed mismatch/disruption objects.
    from scipy.optimize import minimize
    kd = d[
        d["std_eb"].notna()
        & d[m_t].notna()
        & d[m_c].notna()
        & d[d_t].notna()
        & d[d_c].notna()
        & d["peer_eb_treat"].notna()
        & d["peer_eb_ctrl"].notna()
        & d["cluster_id"].notna()
    ].copy()
    clusters = kd["cluster_id"].unique()
    rng = np.random.default_rng(123)
    n_boot = 120
    b_rows = []
    for b in range(n_boot):
        sel = rng.choice(clusters, size=len(clusters), replace=True)
        bs = pd.concat([kd[kd["cluster_id"] == c] for c in sel], ignore_index=True)
        # recompute moments and deltas on bootstrap sample
        moms_b, dm_b, dD_b, ds_b, q_b, tr_b = _kenya_moment_setup(bs, m_t, m_c, d_t, d_c)
        obj_b = lambda p: _kenya_moment_objective(p, moms_b, dm_b, dD_b, ds_b, q_b, tr_b, weights=base_weights)
        try:
            op_b = minimize(
                obj_b,
                x0=np.array([lam, phi, zeta]),
                bounds=[(0.0, 2.0), (-2.0, 2.0), (-2.0, 2.0)],
                method="L-BFGS-B",
                options={"maxiter": 200},
            )
            if op_b.success:
                b_rows.append({"lambda": float(op_b.x[0]), "phi": float(op_b.x[1]), "zeta": float(op_b.x[2])})
        except Exception:
            continue
    if len(b_rows) > 10:
        bb = pd.DataFrame(b_rows)
        ci_tab = pd.DataFrame(
            [
                {
                    "parameter": p,
                    "boot_mean": float(bb[p].mean()),
                    "boot_p05": float(bb[p].quantile(0.05)),
                    "boot_p50": float(bb[p].quantile(0.50)),
                    "boot_p95": float(bb[p].quantile(0.95)),
                    "n_boot_success": int(len(bb)),
                }
                for p in ["lambda", "phi", "zeta"]
            ]
        )
    else:
        ci_tab = pd.DataFrame(
            [{"parameter": p, "boot_mean": np.nan, "boot_p05": np.nan, "boot_p50": np.nan, "boot_p95": np.nan, "n_boot_success": int(len(b_rows))} for p in ["lambda", "phi", "zeta"]]
        )
    _save_table(ci_tab, "table_D3_kenya_bootstrap_cis")

    return main, diag_tab


def _assignment_logic_raw_vs_eb(studies: Dict[str, Study]) -> pd.DataFrame:
    rows = []
    for country, st in studies.items():
        d = st.df.copy()
        for g in sorted(st.cfg["grades"]):
            dg = d[(d["grade"] == g) & d["score_bl"].notna() & d["std_eb"].notna() & d["std_score_el"].notna()].copy()
            if len(dg) < 30:
                continue
            cutoff = st.cfg["cutoffs"][int(g)]
            upper_raw = (dg["score_bl"] > cutoff).astype(int)
            # EB cutoff set to match raw upper share
            share = upper_raw.mean()
            eb_cut = dg["std_eb"].quantile(1 - share)
            upper_eb = (dg["std_eb"] > eb_cut).astype(int)

            def quality_metrics(up):
                gap_a = dg.loc[up == 1, "std_eb"].mean() - dg.loc[up == 0, "std_eb"].mean()
                gap_y = dg.loc[up == 1, "std_score_el"].mean() - dg.loc[up == 0, "std_score_el"].mean()
                # mismatch to two-group targets
                t1 = dg.loc[up == 0, "std_eb"].mean()
                t2 = dg.loc[up == 1, "std_eb"].mean()
                mis = np.where(up == 0, (dg["std_eb"] - t1) ** 2, (dg["std_eb"] - t2) ** 2).mean()
                return float(gap_a), float(gap_y), float(mis)

            ga_r, gy_r, mis_r = quality_metrics(upper_raw)
            ga_e, gy_e, mis_e = quality_metrics(upper_eb)
            rows.extend(
                [
                    {
                        "experiment": st.label,
                        "grade": int(g),
                        "logic": "raw_score_cutoff",
                        "upper_share": float(upper_raw.mean()),
                        "ability_gap": ga_r,
                        "endline_gap": gy_r,
                        "avg_mismatch": mis_r,
                    },
                    {
                        "experiment": st.label,
                        "grade": int(g),
                        "logic": "eb_posterior_cutoff",
                        "upper_share": float(upper_eb.mean()),
                        "ability_gap": ga_e,
                        "endline_gap": gy_e,
                        "avg_mismatch": mis_e,
                    },
                ]
            )

    tab = pd.DataFrame(rows)
    _save_table(tab, "table_F_raw_vs_eb_assignment_logic")
    return tab


def _liberia_module(liberia: Study, kenya_prod: pd.DataFrame, kenya_md: pd.DataFrame) -> pd.DataFrame:
    d = liberia.df.copy()
    # Reduced-form moments
    moms = {
        "itt_mean": _estimate_itt(d, "std_score_el"),
        "itt_q1": np.nan,
        "itt_q2": np.nan,
        "itt_q3": np.nan,
        "itt_q4": np.nan,
        "te_dispersion": _estimate_itt(d, "dev_eb"),
        "te_class_size": _estimate_itt(d.rename(columns={"N_real": "tmp"}), "tmp") if "N_real" in d.columns else np.nan,
        "te_grade_dispersion": _estimate_itt(d.rename(columns={"Vgrade_real": "tmp"}), "tmp") if "Vgrade_real" in d.columns else np.nan,
    }
    q = pd.qcut(d["std_score_bl"], 4, labels=False, duplicates="drop")
    for qq in sorted(pd.Series(q).dropna().unique()):
        moms[f"itt_q{int(qq)+1}"] = _estimate_itt(d[q == qq], "std_score_el")

    # Sensitivity grid: use observed Liberia reallocation margins + Kenya-informed parameters.
    # Attenuate mismatch/social channels by Liberia signal quality (low rho^2).
    base_df = d[
        d["std_eb"].notna()
        & d["mismatch_track_treat"].notna()
        & d["mismatch_track_ctrl"].notna()
        & d["peer_eb_treat"].notna()
        & d["peer_eb_ctrl"].notna()
        & d["D_combined_treat"].notna()
        & d["D_combined_ctrl"].notna()
    ].copy()

    # Kenya anchor from preferred production table (more stable than MD zeta)
    zeta_anchor = float(kenya_prod["zeta_hat"].iloc[0]) if len(kenya_prod) else -0.1

    # Liberia signal attenuation
    rho_rows = []
    c = d[d["treat"] == 0]
    for g in sorted(liberia.cfg["grades"]):
        cg = c[(c["grade"] == g) & c["score_bl"].notna() & c["score_el"].notna()]
        if len(cg) >= 20:
            rho_rows.append(cg["score_bl"].corr(cg["score_el"]) ** 2)
    rho_scale = float(np.nanmean(rho_rows)) if len(rho_rows) else 0.05

    lam_grid = np.linspace(0.0, 0.50, 101)
    # Wider disruption-penalty range to reflect Liberia's large reorganization shifts.
    psi_grid = np.linspace(0.0, 8.00, 121)

    zeta_grid = np.linspace(0.5 * zeta_anchor, 1.5 * zeta_anchor, 9)
    fixed_cost_grid = np.linspace(0.0, 0.05, 6)  # in SD units of outcome

    def _compute_maps(
        df_in: pd.DataFrame,
        lam_eval: np.ndarray,
        psi_eval: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
        dm = df_in["mismatch_track_treat"].to_numpy(float) - df_in["mismatch_track_ctrl"].to_numpy(float)
        ds = df_in["peer_eb_treat"].to_numpy(float) - df_in["peer_eb_ctrl"].to_numpy(float)
        dD = df_in["D_combined_treat"].to_numpy(float) - df_in["D_combined_ctrl"].to_numpy(float)
        z_base = np.zeros((len(psi_eval), len(lam_eval)))
        z_cons = np.zeros_like(z_base)
        s_pos = np.zeros_like(z_base)
        for i, psi in enumerate(psi_eval):
            for j, lam in enumerate(lam_eval):
                z_base[i, j] = float(np.nanmean(rho_scale * (-lam * dm + zeta_anchor * ds) - psi * dD))
                vals = []
                for z in zeta_grid:
                    for c0 in fixed_cost_grid:
                        vals.append(np.nanmean(rho_scale * (-lam * dm + z * ds) - psi * dD - c0))
                vals = np.array(vals)
                z_cons[i, j] = float(np.nanmean(vals))
                s_pos[i, j] = float(np.mean(vals > 0))
        share_base = float((z_base > 0).mean())
        share_cons = float(np.mean(s_pos > 0.5))
        return z_base, z_cons, s_pos, share_base, share_cons

    block_defs = {
        "pooled": base_df,
        "g1_g2_exp1": base_df[base_df.get("exp1", 0) == 1] if "exp1" in base_df.columns else base_df.iloc[0:0],
        "g3_g4_exp2": base_df[base_df.get("exp2", 0) == 1] if "exp2" in base_df.columns else base_df.iloc[0:0],
    }

    sens_rows = []
    maps = {}
    for bname, bdf in block_defs.items():
        if len(bdf) < 50:
            continue
        z_base, z_cons, s_pos, beneficial_base, beneficial_conservative = _compute_maps(bdf, lam_grid, psi_grid)
        maps[bname] = {"base": z_base, "cons": z_cons}
        sens_rows.append(
            {
                "block": bname,
                "N": int(len(bdf)),
                "liberia_itt_mean_observed": moms["itt_mean"],
                "zeta_anchor_from_kenya": zeta_anchor,
                "rho2_scale_liberia": rho_scale,
                "lambda_grid_min": lam_grid.min(),
                "lambda_grid_max": lam_grid.max(),
                "psiD_grid_min": psi_grid.min(),
                "psiD_grid_max": psi_grid.max(),
                "share_grid_regrouping_beneficial_base": beneficial_base,
                "share_grid_regrouping_beneficial_conservative": beneficial_conservative,
                "median_grid_effect_base": float(np.median(z_base)),
                "p10_grid_effect_base": float(np.quantile(z_base, 0.10)),
                "p90_grid_effect_base": float(np.quantile(z_base, 0.90)),
                "median_grid_effect_conservative": float(np.median(z_cons)),
                "p10_grid_effect_conservative": float(np.quantile(z_cons, 0.10)),
                "p90_grid_effect_conservative": float(np.quantile(z_cons, 0.90)),
            }
        )
    summary = pd.DataFrame(sens_rows)

    moms_tab = pd.DataFrame([moms])
    _save_table(moms_tab, "table_E1_liberia_reducedform_moments")
    _save_table(summary, "table_E2_liberia_sensitivity_summary")
    if len(summary):
        _save_table(summary, "table_E2b_liberia_sensitivity_by_block")

    # Compact main-text table
    compact = pd.DataFrame(
        [
            {
                "LiberiaObservedITT": float(moms["itt_mean"]),
                "SignalScaleRho2": float(rho_scale),
                "BeneficialShareBase": float(summary.loc[summary["block"] == "pooled", "share_grid_regrouping_beneficial_base"].iloc[0]) if (len(summary) and (summary["block"] == "pooled").any()) else np.nan,
                "BeneficialShareConservative": float(summary.loc[summary["block"] == "pooled", "share_grid_regrouping_beneficial_conservative"].iloc[0]) if (len(summary) and (summary["block"] == "pooled").any()) else np.nan,
                "PolicyInterpretation": (
                    "Under conservative uncertainty, regrouping is unattractive "
                    "across the plausible parameter region."
                    if (
                        len(summary)
                        and (summary["block"] == "pooled").any()
                        and float(summary.loc[summary["block"] == "pooled", "share_grid_regrouping_beneficial_conservative"].iloc[0]) < 0.25
                    )
                    else "Conservative region still leaves substantial favorable area."
                ),
            }
        ]
    )
    _save_table(compact, "table_E3_liberia_maintext_sensitivity")

    # Figure J (pooled base vs conservative)
    if "pooled" in maps:
        fig, axes = plt.subplots(
            1, 2, figsize=(12, 5), sharex=True, sharey=True, constrained_layout=True
        )
        im0 = axes[0].contourf(lam_grid, psi_grid, maps["pooled"]["base"], levels=24, cmap="coolwarm")
        axes[0].contour(lam_grid, psi_grid, maps["pooled"]["base"], levels=[0], colors="black", linewidths=1.1)
        axes[0].set_title("Pooled base map")
        axes[0].set_xlabel("lambda (mismatch penalty)")
        axes[0].set_ylabel("psiD (disruption penalty)")

        im1 = axes[1].contourf(lam_grid, psi_grid, maps["pooled"]["cons"], levels=24, cmap="coolwarm")
        axes[1].contour(lam_grid, psi_grid, maps["pooled"]["cons"], levels=[0], colors="black", linewidths=1.1)
        axes[1].set_title("Pooled conservative map")
        axes[1].set_xlabel("lambda (mismatch penalty)")
        cbar = fig.colorbar(
            im1,
            ax=axes,
            location="right",
            fraction=0.05,
            pad=0.03,
        )
        cbar.set_label("Predicted mean regrouping effect")
        fig.savefig(OUT_DIR / "fig_J_liberia_sensitivity_map.pdf")
        plt.close(fig)

    # Split-map figure: pooled + Liberia blocks (conservative maps)
    split_order = [b for b in ["pooled", "g1_g2_exp1", "g3_g4_exp2"] if b in maps]
    if split_order:
        fig, axes = plt.subplots(
            1,
            len(split_order),
            figsize=(5 * len(split_order), 4),
            sharex=True,
            sharey=True,
            constrained_layout=True,
        )
        if len(split_order) == 1:
            axes = [axes]
        im = None
        titles = {"pooled": "Pooled", "g1_g2_exp1": "Liberia G1-G2", "g3_g4_exp2": "Liberia G3-G4"}
        for ax, bn in zip(axes, split_order):
            im = ax.contourf(lam_grid, psi_grid, maps[bn]["cons"], levels=24, cmap="coolwarm")
            ax.contour(lam_grid, psi_grid, maps[bn]["cons"], levels=[0], colors="black", linewidths=1.0)
            ax.set_title(f"{titles.get(bn, bn)} conservative")
            ax.set_xlabel("lambda")
        axes[0].set_ylabel("psiD")
        if im is not None:
            cbar = fig.colorbar(
                im,
                ax=axes,
                location="right",
                fraction=0.04,
                pad=0.03,
                shrink=0.95,
            )
            cbar.set_label("Predicted mean regrouping effect")
        fig.savefig(OUT_DIR / "fig_J2_liberia_split_sensitivity_maps.pdf")
        plt.close(fig)

    # Bootstrap uncertainty for beneficial-share statistics (cluster bootstrap by block)
    b_rows = []
    rng = np.random.default_rng(2026)
    n_boot = 60
    lam_boot = np.linspace(0.0, 0.50, 31)
    psi_boot = np.linspace(0.0, 8.00, 31)
    for bname, bdf in block_defs.items():
        if len(bdf) < 50 or "cluster_id" not in bdf.columns:
            continue
        clusters = bdf["cluster_id"].dropna().unique()
        if len(clusters) < 10:
            continue
        base_list = []
        cons_list = []
        for _ in range(n_boot):
            sel = rng.choice(clusters, size=len(clusters), replace=True)
            bs = pd.concat([bdf[bdf["cluster_id"] == c] for c in sel], ignore_index=True)
            if len(bs) < 30:
                continue
            _, _, _, sb, sc = _compute_maps(bs, lam_boot, psi_boot)
            base_list.append(sb)
            cons_list.append(sc)
        if len(base_list) >= 20:
            b_rows.append(
                {
                    "block": bname,
                    "n_boot_success": int(len(base_list)),
                    "base_share_p05": float(np.quantile(base_list, 0.05)),
                    "base_share_p50": float(np.quantile(base_list, 0.50)),
                    "base_share_p95": float(np.quantile(base_list, 0.95)),
                    "cons_share_p05": float(np.quantile(cons_list, 0.05)),
                    "cons_share_p50": float(np.quantile(cons_list, 0.50)),
                    "cons_share_p95": float(np.quantile(cons_list, 0.95)),
                }
            )
    boot_tab = pd.DataFrame(b_rows)
    if len(boot_tab):
        _save_table(boot_tab, "table_E4_liberia_beneficial_share_bootstrap")

    return summary if len(summary) else moms_tab


def _write_revision_memo(
    tableSignal: pd.DataFrame,
    tableSignalAlt: pd.DataFrame,
    tableFourMargins: pd.DataFrame,
    tableAssign: pd.DataFrame,
    tableClassroom: pd.DataFrame,
    tableMismatch: pd.DataFrame,
    tableDisruption: pd.DataFrame,
    tableKenyaMain: pd.DataFrame,
    tableKenyaProfile: pd.DataFrame,
    tableLiberia: pd.DataFrame,
    tableRawEb: pd.DataFrame,
) -> None:
    path = OUT_DIR / "revision_results_memo.md"
    with path.open("w", encoding="utf-8") as f:
        f.write("# Structural Revision Memo (Kenya-focused production, Liberia sensitivity)\n\n")
        f.write("## What changed from previous version\n\n")
        f.write("- Measurement and assignment blocks are now treated as **settled** and primary.\n")
        f.write("- Pooled nonlinear production is **deprecated as a main estimator**.\n")
        f.write("- Kenya Y1 is now the **preferred production-estimation setting**.\n")
        f.write("- Liberia is now treated as **reduced-form + sensitivity policy contrast**.\n")
        f.write("- Main mismatch uses **track-level targets**; classroom-mean mismatch is secondary.\n\n")

        f.write("## A) Signal quality by study/grade\n\n")
        f.write(_md_table(tableSignal))
        f.write("\n\n")

        f.write("## A2) Alternative signal-quality diagnostics\n\n")
        f.write(_md_table(tableSignalAlt))
        f.write("\n\n")

        f.write("## A3) Four-margin Kenya-Liberia summary\n\n")
        f.write(_md_table(tableFourMargins))
        f.write("\n\n")

        f.write("## B) Assignment/cutoff summary\n\n")
        f.write("Assignment is deterministic cutoff in both studies; assignment noise is not the binding margin here.\n\n")
        f.write(_md_table(tableAssign))
        f.write("\n\n")

        f.write("## C) Classroom reallocation summary\n\n")
        f.write(_md_table(tableClassroom))
        f.write("\n\n")

        f.write("## D) Mismatch definition comparison (Kenya)\n\n")
        f.write(_md_table(tableMismatch))
        f.write("\n\n")

        f.write("## E) Disruption definition comparison (Kenya)\n\n")
        f.write(_md_table(tableDisruption))
        f.write("\n\n")

        f.write("## F) Preferred Kenya estimator\n\n")
        f.write(_md_table(tableKenyaMain))
        f.write("\n\n")

        f.write("## G) Kenya profile identification diagnostics\n\n")
        f.write(_md_table(tableKenyaProfile))
        f.write("\n\n")

        f.write("## H) Liberia reduced-form + sensitivity (preferred for Liberia)\n\n")
        f.write(_md_table(tableLiberia))
        f.write("\n\n")

        f.write("## I) Raw-score vs EB assignment logic comparison\n\n")
        f.write(_md_table(tableRawEb))
        f.write("\n\n")

        # Optional robustness tables generated in this revision
        w_path = OUT_DIR / "table_D2_profile_weight_robustness.txt"
        kboot_path = OUT_DIR / "table_D3_kenya_bootstrap_cis.txt"
        lboot_path = OUT_DIR / "table_E4_liberia_beneficial_share_bootstrap.txt"
        lsplit_path = OUT_DIR / "table_E2b_liberia_sensitivity_by_block.txt"
        if w_path.exists():
            f.write("## J) Kenya profile robustness to moment weights\n\n")
            f.write(w_path.read_text(encoding="utf-8"))
            f.write("\n\n")
        if kboot_path.exists():
            f.write("## K) Kenya bootstrap parameter intervals\n\n")
            f.write(kboot_path.read_text(encoding="utf-8"))
            f.write("\n\n")
        if lsplit_path.exists():
            f.write("## L) Liberia split sensitivity (pooled vs G1-2 vs G3-4)\n\n")
            f.write(lsplit_path.read_text(encoding="utf-8"))
            f.write("\n\n")
        if lboot_path.exists():
            f.write("## M) Liberia beneficial-share bootstrap uncertainty\n\n")
            f.write(lboot_path.read_text(encoding="utf-8"))
            f.write("\n\n")

        f.write("## Preferred estimator/specification\n\n")
        f.write("1. Measurement: grade-specific EB with posterior variance.\n")
        f.write("2. Assignment: deterministic cutoffs by grade.\n")
        f.write("3. Production main: Kenya-only moment-focused estimator with preferred mismatch/disruption objects.\n")
        f.write("4. Liberia main: reduced-form moments and sensitivity map over plausible mismatch/disruption penalties.\n")
        f.write("5. Pooled nonlinear model: secondary/deprecated diagnostic, not main evidence.\n\n")

        f.write("## Solid vs fragile\n\n")
        f.write("- **Solid**: measurement heterogeneity (Kenya high signal, Liberia low signal), deterministic assignment, classroom reallocation facts.\n")
        f.write("- **Fragile**: pooled nonlinear production point estimates and cross-study parameter pooling.\n")
        f.write("- **Interpretation**: core heterogeneity across settings appears less about assignment implementation and more about signal quality plus classroom production responses.\n")

        f.write("\n## What improved in this revision\n\n")
        f.write("- Added explicit mismatch-definition comparison and selected preferred mismatch by objective fit/stability.\n")
        f.write("- Added explicit disruption-definition comparison and selected preferred classroom-cost object.\n")
        f.write("- Switched Kenya production emphasis to moment matching (mean, quartile, and track ITT moments).\n")
        f.write("- Added profile-objective diagnostics for lambda/phi/zeta to classify identification strength.\n")
        f.write("- Rebuilt Liberia sensitivity as base/conservative/very-conservative style maps under low-signal scaling.\n")
        f.write("- Added raw-vs-EB assignment logic comparison to quantify informational value for targeting quality.\n")
        f.write("- Added weight-robustness profiles and bootstrap uncertainty tables for Kenya and Liberia.\n")


def _write_preferred_spec_lock(
    preferred_mismatch: str,
    preferred_disruption: str,
    kenya_main: pd.DataFrame,
) -> None:
    """
    Write a reproducibility lock file for the preferred estimator choices.
    """
    lock = {
        "created_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "pipeline": "structural_estimation_revision.py",
        "preferred_estimator": {
            "country": "kenya",
            "estimation_style": "minimum_distance_moment_matching",
            "model": "theta1 = theta0 + [alpha - lambda*mismatch + phi*disruption + zeta*social] + eps",
            "preferred_mismatch_definition": preferred_mismatch,
            "preferred_disruption_definition": preferred_disruption,
            "objective_moments": [
                "mean_itt",
                "itt_q1",
                "itt_q2",
                "itt_q3",
                "itt_q4",
                "itt_track0",
                "itt_track1",
            ],
            "diagnostic_moments_nonstructural": [
                "te_mismatch",
                "te_classsize",
                "te_grade_dispersion",
            ],
            "moment_weights": {
                "mean": 3.0,
                "quartiles": 1.0,
                "track": 1.0,
                "te_mismatch": 0.15,
                "te_classsize": 0.0,
                "te_vgrade": 0.0,
            },
            "parameter_bounds": {
                "lambda": [0.0, 2.0],
                "phi": [-2.0, 2.0],
                "zeta": [-2.0, 2.0],
            },
        },
        "liberia_sensitivity": {
            "signal_scale": "mean_control_rho2",
            "lambda_grid": [0.0, 0.5, 101],
            "psiD_grid": [0.0, 8.0, 121],
            "base_assumption": "point_anchor_zeta_no_fixed_cost",
            "conservative_assumption": "zeta_band_0.5x_to_1.5x_and_fixed_cost_0_to_0.05",
        },
        "selected_estimates_snapshot": (
            kenya_main.iloc[0].to_dict() if len(kenya_main) else {}
        ),
    }
    with (OUT_DIR / "preferred_spec_lock.json").open("w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2)


def main() -> None:
    print("=" * 72)
    print("Structural estimation revision: Kenya-focused production + Liberia sensitivity")
    print("=" * 72)
    studies = _load()

    print("[1/7] Measurement block")
    tableA = _measurement_block(studies)
    tableA2 = _signal_quality_alternatives(studies)

    print("[2/7] Assignment block")
    tableB = _assignment_block(studies)

    print("[3/7] Classroom objects and reallocation")
    tableC = _classroom_reallocation_table(studies)
    tableA3 = _front_summary_figure(tableA, tableB, tableC)

    print("[4/7] Kenya mismatch/disruption comparisons + preferred estimator")
    tableMismatch, preferredMismatch = _kenya_mismatch_comparison(studies["kenya"])
    tableDisruption, preferredDisruption = _kenya_disruption_comparison(
        studies["kenya"], preferredMismatch
    )
    tableKenyaMain, tableKenyaProfile = _kenya_preferred_estimator_and_profiles(
        studies["kenya"], preferredMismatch, preferredDisruption
    )

    print("[5/7] Liberia reduced-form + sensitivity module")
    # anchor from preferred Kenya RF table
    kenya_prod_anchor = pd.DataFrame(
        [
            {
                "zeta_hat": tableKenyaMain["rf_zeta_hat"].iloc[0],
            }
        ]
    )
    kenya_md_anchor = pd.DataFrame(
        [
            {
                "zeta_hat": tableKenyaMain["md_zeta_hat"].iloc[0],
            }
        ]
    )
    tableLiberia = _liberia_module(studies["liberia"], kenya_prod_anchor, kenya_md_anchor)
    _save_table(tableLiberia, "table_E_liberia_combined")

    print("[6/7] Raw-score vs EB assignment logic comparison")
    tableRawEb = _assignment_logic_raw_vs_eb(studies)

    print("[7/7] Revision memo")
    _write_revision_memo(
        tableSignal=tableA,
        tableSignalAlt=tableA2,
        tableFourMargins=tableA3,
        tableAssign=tableB,
        tableClassroom=tableC,
        tableMismatch=tableMismatch,
        tableDisruption=tableDisruption,
        tableKenyaMain=tableKenyaMain,
        tableKenyaProfile=tableKenyaProfile,
        tableLiberia=tableLiberia,
        tableRawEb=tableRawEb,
    )
    _write_preferred_spec_lock(preferredMismatch, preferredDisruption, tableKenyaMain)

    # Save revised intermediate datasets
    studies["kenya"].df.to_parquet(OUT_DIR / "kenya_structural_revision_dataset.parquet", index=False)
    studies["liberia"].df.to_parquet(OUT_DIR / "liberia_structural_revision_dataset.parquet", index=False)

    print("\nDone.")
    print(f"Revised outputs: {OUT_DIR}")


if __name__ == "__main__":
    main()
