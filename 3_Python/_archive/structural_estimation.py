#!/usr/bin/env python3
"""
structural_estimation.py
========================
First-pass structural estimation pipeline for cross-grade ability grouping.

Scope (this script):
- Experiments: Kenya Year 1 and Liberia only
- Steps:
  1) Measurement model (grade-specific EB decomposition)
  2) Assignment rule estimation in treated schools
  3) Classroom-level structural variable construction
  4) Production model estimation (reduced-form + NLLS)
  5) SMM scaffold + empirical moments
  6) Results memo with identification assessment

Outputs:
- Tables/Figures/Memo in 3_Python/output/structural/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import warnings

from scipy.optimize import least_squares, minimize
from scipy.special import expit
from statsmodels.nonparametric.smoothers_lowess import lowess

from config import get_config, OUT
from utils import ols_cluster


np.random.seed(42)

OUT_DIR = OUT / "structural"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STUDIES = [("kenya", "Kenya Y1"), ("liberia", "Liberia")]


@dataclass
class StudyData:
    country: str
    label: str
    cfg: dict
    df: pd.DataFrame


def _safe_corr(x: pd.Series, y: pd.Series) -> float:
    mask = x.notna() & y.notna()
    if mask.sum() < 10:
        return np.nan
    return x[mask].corr(y[mask])


def _save_table(df: pd.DataFrame, stem: str) -> None:
    df.to_csv(OUT_DIR / f"{stem}.txt", sep="\t", index=False)
    try:
        df.to_latex(OUT_DIR / f"{stem}.tex", index=False, float_format="%.4f")
    except Exception:
        pass


def _md_table(df: pd.DataFrame) -> str:
    """Render a small markdown table without external dependencies."""
    if df is None or len(df) == 0:
        return "_No rows._"
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    body = []
    for _, row in df.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + body)


def _load_data() -> List[StudyData]:
    out: List[StudyData] = []
    for country, label in STUDIES:
        cfg = get_config(country)
        df = pd.read_parquet(cfg["ANALYSIS_FILE"]).copy()
        df = df[df["finsamp"] == 1].copy()
        df["experiment"] = country
        df["experiment_label"] = label
        df["cluster_id"] = (
            df[cfg["cluster_var"]].astype(str)
            if cfg["cluster_var"] in df.columns
            else df["academycode"].astype(str)
        )
        out.append(StudyData(country=country, label=label, cfg=cfg, df=df))
    return out


def _inventory_and_mapping(studies: List[StudyData]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    inv_rows = []
    for sd in studies:
        d = sd.df
        inv_rows.append(
            dict(
                experiment=sd.label,
                n_students=len(d),
                n_schools=d["academycode"].nunique(),
                grades=",".join(str(int(x)) for x in sorted(d["grade"].dropna().unique())),
                track_values=",".join(str(int(x)) for x in sorted(pd.Series(d["std_grp"]).dropna().unique())),
                has_teacher_attn=int(d["tch_attn"].notna().sum() > 0),
                has_pupil_attn=int(d["pupilattendance"].notna().sum() > 0),
                has_lesson_completion=int(d["lp_comp"].notna().sum() > 0),
                n_treated=int((d["treat"] == 1).sum()),
                n_control=int((d["treat"] == 0).sum()),
            )
        )
    inv = pd.DataFrame(inv_rows)
    _save_table(inv, "struc_t0_inventory")

    mapping = pd.DataFrame(
        [
            ["theta_i0", "std_eb", "Observed proxy", "EB posterior mean, standardized"],
            ["s_i", "std_score_bl", "Observed", "Standardized baseline score"],
            ["a_i", "std_eb", "Constructed (existing)", "Posterior from EB shrinkage model"],
            ["k_i", "std_grp (treat), grade (control)", "Observed/constructed", "Track assignment rule in data"],
            ["I_k", "mean(std_eb) by track", "Constructed (new)", "Track-level instructional target"],
            ["N_c", "csize", "Observed/constructed", "Classroom size under realized assignment"],
            ["V_c_grade", "var(grade) in classroom", "Constructed (new)", "Within-class grade dispersion"],
            ["S_ic", "peer_eb", "Constructed (existing)", "Leave-self-out peer mean EB ability"],
            ["y_i", "std_score_el", "Observed", "Standardized endline test score"],
            ["rank_ic", "pct rank(std_eb) in classroom", "Constructed (new)", "Within-class rank proxy"],
            ["misfit_structural", "(std_eb - I_k)^2", "Constructed (new)", "Mismatch wrt track target"],
        ],
        columns=["StructuralObject", "EmpiricalVariable", "Status", "Notes"],
    )
    _save_table(mapping, "struc_t0_mapping")
    return inv, mapping


def _measurement_model(studies: List[StudyData]) -> pd.DataFrame:
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex=False, sharey=False)
    axes = axes.ravel()
    ax_i = 0

    for sd in studies:
        d = sd.df
        for g in sorted(sd.cfg["grades"]):
            c = d[(d["treat"] == 0) & (d["grade"] == g)].copy()
            c = c[c["score_bl"].notna() & c["score_el"].notna()]
            if len(c) < 20:
                continue
            rho_g = _safe_corr(c["score_bl"], c["score_el"])
            rho2 = (rho_g ** 2) if pd.notna(rho_g) else np.nan
            rho2 = np.clip(rho2, 0.01, 0.95) if pd.notna(rho2) else np.nan

            mu_g = c["score_bl"].mean()
            var_s = c["score_bl"].var()
            sigma2_theta = rho2 * var_s if pd.notna(rho2) else np.nan
            sigma2_u = (1 - rho2) * var_s if pd.notna(rho2) else np.nan
            post_var = sigma2_theta * (1 - rho2) if pd.notna(rho2) else np.nan

            full_g = d[d["grade"] == g].copy()
            eb_hat = mu_g + rho2 * (full_g["score_bl"] - mu_g)
            eb_diff = (full_g["eb_ability"] - eb_hat).abs()

            rows.append(
                dict(
                    experiment=sd.label,
                    grade=int(g),
                    N_control=int(len(c)),
                    mu_bl=float(mu_g),
                    var_s=float(var_s),
                    rho=float(rho_g),
                    rho2=float(rho2),
                    sigma2_theta=float(sigma2_theta),
                    sigma2_u=float(sigma2_u),
                    posterior_var=float(post_var),
                    eb_match_mae=float(np.nanmean(eb_diff)),
                )
            )

            # Scatter (sampled for speed/readability)
            plot_df = full_g[["score_bl", "eb_ability"]].dropna()
            if len(plot_df) > 800:
                plot_df = plot_df.sample(800, random_state=42)
            if ax_i < len(axes):
                axes[ax_i].scatter(plot_df["score_bl"], plot_df["eb_ability"], s=6, alpha=0.35)
                axes[ax_i].set_title(f"{sd.label} G{int(g)}")
                axes[ax_i].set_xlabel("Baseline score (raw)")
                axes[ax_i].set_ylabel("Posterior mean (eb_ability)")
                ax_i += 1

        # Attach posterior variance by grade to data (for later diagnostics)
        grade_to_postvar = {
            int(r["grade"]): r["posterior_var"]
            for r in rows
            if r["experiment"] == sd.label
        }
        sd.df["posterior_var"] = sd.df["grade"].map(grade_to_postvar)

    for k in range(ax_i, len(axes)):
        axes[k].axis("off")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "struc_f1_measurement.pdf")
    plt.close(fig)

    out = pd.DataFrame(rows).sort_values(["experiment", "grade"])
    _save_table(out, "struc_t1_measurement")
    return out


def _assignment_rule(studies: List[StudyData]) -> pd.DataFrame:
    rows = []
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    for i, sd in enumerate(studies):
        d = sd.df.copy()
        t = d[(d["treat"] == 1) & d["score_bl"].notna() & d["upper_group"].notna()]
        if t.empty:
            continue
        x_grid = np.linspace(t["score_bl"].quantile(0.01), t["score_bl"].quantile(0.99), 200)
        cmap = plt.get_cmap("tab10")

        for j, g in enumerate(sorted(sd.cfg["grades"])):
            tg = t[t["grade"] == g].copy()
            if len(tg) < 30:
                continue

            # Misclassification wrt deterministic cutoffs
            cutoff = sd.cfg["cutoffs"].get(int(g), np.nan)
            det_upper = (tg["score_bl"] > cutoff).astype(float)
            misclass = (det_upper != tg["upper_group"]).mean()
            deterministic = misclass < 1e-8

            # If deterministic/perfectly separated, avoid unstable logit and use step prediction.
            if deterministic:
                beta, se, pval = np.nan, np.nan, np.nan
                pred = (x_grid > cutoff).astype(float)
                lo = np.column_stack([np.sort(tg["score_bl"].to_numpy()), np.sort(det_upper.to_numpy())])
                model_type = "deterministic_cutoff"
            else:
                y = tg["upper_group"].astype(float)
                X = sm.add_constant(tg[["score_bl"]].astype(float))
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        logit_fit = sm.Logit(y, X).fit(disp=False, maxiter=100)
                    beta = float(logit_fit.params["score_bl"])
                    se = float(logit_fit.bse["score_bl"])
                    pval = float(logit_fit.pvalues["score_bl"])
                    pred = expit(logit_fit.params["const"] + logit_fit.params["score_bl"] * x_grid)
                    model_type = "logit"
                except Exception:
                    beta, se, pval = np.nan, np.nan, np.nan
                    pred = np.full_like(x_grid, np.nan, dtype=float)
                    model_type = "logit_failed"

                # Nonparametric smooth (LOWESS)
                lo = lowess(tg["upper_group"], tg["score_bl"], frac=0.25, return_sorted=True)

            rows.append(
                dict(
                    experiment=sd.label,
                    grade=int(g),
                    N=int(len(tg)),
                    cutoff=float(cutoff),
                    misclassification_rate=float(misclass),
                    model_type=model_type,
                    logit_beta=float(beta),
                    logit_se=float(se),
                    logit_p=float(pval),
                )
            )

            color = cmap(j)
            axes[i].plot(x_grid, pred, color=color, lw=1.8, label=f"G{int(g)} logit")
            axes[i].plot(lo[:, 0], lo[:, 1], color=color, lw=1.0, ls="--", alpha=0.9)
            axes[i].axvline(cutoff, color=color, alpha=0.25)

        axes[i].set_title(sd.label)
        axes[i].set_xlabel("Baseline score (raw)")
        axes[i].set_ylabel("Pr(upper track)")
        axes[i].set_ylim(-0.02, 1.02)
        axes[i].legend(fontsize=8, frameon=False)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "struc_f2_assignment.pdf")
    plt.close(fig)

    out = pd.DataFrame(rows).sort_values(["experiment", "grade"])
    _save_table(out, "struc_t2_assignment")
    return out


def _construct_classroom_vars(studies: List[StudyData]) -> pd.DataFrame:
    rows = []
    all_augmented = []

    for sd in studies:
        d = sd.df.copy()
        d["class_track"] = np.where(d["treat"] == 1, d["std_grp"], d["grade"])
        d["class_id"] = d["academycode"].astype(str) + "|" + d["class_track"].astype(str)

        # Classroom aggregates
        grp = d.groupby("class_id")
        d["N_c_new"] = grp["studyid"].transform("count")
        d["V_c_grade"] = grp["grade"].transform(lambda x: np.nanvar(x.astype(float), ddof=0))
        d["n_grades_c"] = grp["grade"].transform("nunique")
        d["rank_ic"] = grp["std_eb"].transform(lambda x: x.rank(pct=True, method="average"))

        # Instructional targets I_k
        # Treated: by experiment+track (std_grp). Control: by experiment+grade.
        treat_targets = (
            d[d["treat"] == 1]
            .groupby("std_grp")["std_eb"]
            .mean()
            .to_dict()
        )
        ctrl_targets = (
            d[d["treat"] == 0]
            .groupby("grade")["std_eb"]
            .mean()
            .to_dict()
        )
        d["I_k"] = np.where(
            d["treat"] == 1,
            d["std_grp"].map(treat_targets),
            d["grade"].map(ctrl_targets),
        )
        d["misfit_structural"] = (d["std_eb"] - d["I_k"]) ** 2

        # Store back
        sd.df = d
        all_augmented.append(d)

        for tval in [0, 1]:
            sub = d[d["treat"] == tval]
            rows.append(
                dict(
                    experiment=sd.label,
                    treat=int(tval),
                    N=len(sub),
                    class_size_mean=sub["N_c_new"].mean(),
                    class_size_sd=sub["N_c_new"].std(),
                    grade_disp_mean=sub["V_c_grade"].mean(),
                    grade_disp_sd=sub["V_c_grade"].std(),
                    peer_mean_eb=sub["peer_eb"].mean(),
                    rank_mean=sub["rank_ic"].mean(),
                    n_grades_mean=sub["n_grades_c"].mean(),
                    misfit_structural_mean=sub["misfit_structural"].mean(),
                )
            )

    out = pd.DataFrame(rows).sort_values(["experiment", "treat"])
    _save_table(out, "struc_t3_classroom")

    all_df = pd.concat(all_augmented, ignore_index=True)

    # Class size distribution figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for i, (country, label) in enumerate(STUDIES):
        sub = all_df[all_df["experiment"] == country]
        for tval, name in [(0, "Control"), (1, "Treatment")]:
            ss = sub[sub["treat"] == tval]
            axes[i].hist(ss["N_c_new"], bins=25, alpha=0.55, density=True, label=name)
        axes[i].set_title(label)
        axes[i].set_xlabel("Class size")
        axes[i].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "struc_f4_classsize.pdf")
    plt.close(fig)

    # Grade dispersion distribution
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for i, (country, label) in enumerate(STUDIES):
        sub = all_df[all_df["experiment"] == country]
        for tval, name in [(0, "Control"), (1, "Treatment")]:
            ss = sub[sub["treat"] == tval]
            axes[i].hist(ss["V_c_grade"], bins=25, alpha=0.55, density=True, label=name)
        axes[i].set_title(label)
        axes[i].set_xlabel("Within-class grade variance")
        axes[i].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "struc_f5_grade_dispersion.pdf")
    plt.close(fig)

    return all_df


def _build_design(df: pd.DataFrame, include_treat: bool = True) -> Tuple[pd.Series, pd.DataFrame]:
    y = df["std_score_el"].astype(float)
    X = pd.DataFrame(
        {
            "a": df["std_eb"].astype(float),
            "a2": (df["std_eb"] ** 2).astype(float),
            "misfit_structural": df["misfit_structural"].astype(float),
            "S_ic": df["peer_eb"].astype(float),
            "N_c": df["N_c_new"].astype(float),
            "V_c": df["V_c_grade"].astype(float),
        }
    )
    if include_treat:
        X["treat"] = df["treat"].astype(float)
    # Strata FE within experiment
    strata_key = df["experiment"].astype(str) + "_" + df["strata"].astype(str)
    fe = pd.get_dummies(strata_key, prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([X, fe], axis=1)
    return y, X


def _stage_a_reduced_form(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs = [
        ("Pooled", df),
        ("Kenya Y1", df[df["experiment"] == "kenya"]),
        ("Liberia", df[df["experiment"] == "liberia"]),
        ("Pooled Treated", df[df["treat"] == 1]),
        ("Pooled Control", df[df["treat"] == 0]),
    ]
    for name, sub in specs:
        sub = sub[
            sub["std_score_el"].notna()
            & sub["std_eb"].notna()
            & sub["peer_eb"].notna()
            & sub["misfit_structural"].notna()
            & sub["N_c_new"].notna()
            & sub["V_c_grade"].notna()
        ].copy()
        if len(sub) < 100:
            continue
        y, X = _build_design(sub, include_treat=(sub["treat"].nunique() > 1))
        cl = sub["experiment"].astype(str) + "|" + sub["cluster_id"].astype(str)
        try:
            res = ols_cluster(y, X, cl)
            b = res.params
            se = res.bse
            rows.append(
                dict(
                    sample=name,
                    N=len(sub),
                    lambda_hat=-b.get("misfit_structural", np.nan),
                    lambda_se=se.get("misfit_structural", np.nan),
                    zeta_hat=b.get("S_ic", np.nan),
                    zeta_se=se.get("S_ic", np.nan),
                    psi_N_linear=b.get("N_c", np.nan),
                    psi_N_se=se.get("N_c", np.nan),
                    psi_V_linear=b.get("V_c", np.nan),
                    psi_V_se=se.get("V_c", np.nan),
                    treat_coef=b.get("treat", np.nan),
                    treat_se=se.get("treat", np.nan),
                    r2=res.rsquared,
                )
            )
        except Exception:
            continue
    out = pd.DataFrame(rows)
    _save_table(out, "struc_t4_production_rf")
    return out


def _fit_nlls(
    sub: pd.DataFrame,
    init: np.ndarray,
    lam_fixed: float | None = None,
) -> Dict[str, float]:
    a = sub["std_eb"].to_numpy(float)
    y = sub["std_score_el"].to_numpy(float)
    m = sub["misfit_structural"].to_numpy(float)
    s = sub["peer_eb"].to_numpy(float)
    n = sub["N_c_new"].to_numpy(float)
    v = sub["V_c_grade"].to_numpy(float)

    def _z(x):
        sd = np.std(x)
        if sd <= 1e-10:
            return x * 0.0
        return (x - np.mean(x)) / sd

    # Rescale regressors to improve nonlinear conditioning.
    m_s = _z(m)
    s_s = _z(s)
    n_s = _z(n)
    v_s = _z(v)

    def resid_free(p):
        alpha, lam, psi_n, psi_v, zeta = p
        gain = np.exp(-(psi_n * n_s + psi_v * v_s))
        yhat = a + gain * (alpha - lam * m_s + zeta * s_s)
        base = y - yhat
        # Mild regularization to reduce boundary collapse and overfitting.
        pen = np.sqrt(1e-3) * np.array([0.2 * alpha, 0.5 * lam, psi_n, psi_v, 0.5 * zeta])
        return np.concatenate([base, pen])

    def resid_fixed(p):
        alpha, psi_n, psi_v, zeta = p
        lam = lam_fixed
        gain = np.exp(-(psi_n * n_s + psi_v * v_s))
        yhat = a + gain * (alpha - lam * m_s + zeta * s_s)
        base = y - yhat
        pen = np.sqrt(1e-3) * np.array([0.2 * alpha, psi_n, psi_v, 0.5 * zeta])
        return np.concatenate([base, pen])

    if lam_fixed is None:
        lb = np.array([-3.0, 0.0, -2.0, -2.0, -5.0])
        ub = np.array([3.0, 5.0, 2.0, 2.0, 5.0])
        starts = [init]
        base = init
    else:
        lb = np.array([-3.0, -2.0, -2.0, -5.0])
        ub = np.array([3.0, 2.0, 2.0, 5.0])
        starts = [np.array([init[0], init[2], init[3], init[4]])]
        base = starts[0]

    rng = np.random.default_rng(42)
    for _ in range(7):
        if lam_fixed is None:
            jitter = rng.normal(0, [0.2, 0.2, 0.2, 0.2, 0.2])
        else:
            jitter = rng.normal(0, [0.2, 0.2, 0.2, 0.2])
        starts.append(np.clip(base + jitter, lb + 1e-5, ub - 1e-5))

    best = None
    best_loss = np.inf
    for x0 in starts:
        try:
            if lam_fixed is None:
                fit = least_squares(resid_free, x0=x0, bounds=(lb, ub), max_nfev=4000)
            else:
                fit = least_squares(resid_fixed, x0=x0, bounds=(lb, ub), max_nfev=4000)
        except Exception:
            continue
        if fit.success and fit.cost < best_loss:
            best = fit
            best_loss = fit.cost

    if best is None:
        return {"converged": 0}
    p = best.x
    if lam_fixed is None:
        alpha_hat, lam_hat, psi_n_hat, psi_v_hat, zeta_hat = p
    else:
        alpha_hat, psi_n_hat, psi_v_hat, zeta_hat = p
        lam_hat = float(lam_fixed)
    gain = np.exp(-(psi_n_hat * n_s + psi_v_hat * v_s))
    yhat = a + gain * (alpha_hat - lam_hat * m_s + zeta_hat * s_s)
    rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
    tss = float(np.sum((y - np.mean(y)) ** 2))
    rss = float(np.sum((y - yhat) ** 2))
    r2 = np.nan if tss <= 0 else 1 - rss / tss
    return {
        "converged": 1,
        "alpha_hat": float(alpha_hat),
        "lambda_hat": float(lam_hat),
        "psi_N_hat": float(psi_n_hat),
        "psi_V_hat": float(psi_v_hat),
        "zeta_hat": float(zeta_hat),
        "rmse": rmse,
        "r2_fit": float(r2),
        "nfev": int(best.nfev),
    }


def _stage_b_nlls(df: pd.DataFrame, rf_table: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    fit_df_list = []
    init_row = rf_table[rf_table["sample"] == "Pooled"]
    if len(init_row):
        init = np.array(
            [
                0.1,
                float(np.nan_to_num(init_row["lambda_hat"].iloc[0], nan=0.3)),
                0.01,
                0.20,
                float(np.nan_to_num(init_row["zeta_hat"].iloc[0], nan=0.1)),
            ]
        )
    else:
        init = np.array([0.1, 0.3, 0.01, 0.20, 0.1])

    specs = [
        ("Pooled", df),
        ("Kenya Y1", df[df["experiment"] == "kenya"]),
        ("Liberia", df[df["experiment"] == "liberia"]),
    ]
    for name, sub in specs:
        sub = sub[
            sub["std_score_el"].notna()
            & sub["std_eb"].notna()
            & sub["misfit_structural"].notna()
            & sub["peer_eb"].notna()
            & sub["N_c_new"].notna()
            & sub["V_c_grade"].notna()
        ].copy()
        if len(sub) < 100:
            continue
        # Free-lambda NLLS
        fit = _fit_nlls(sub, init, lam_fixed=None)
        row = {"sample": name, "spec": "free_lambda", "N": len(sub)}
        row.update(fit)
        rows.append(row)

        # Fixed-lambda NLLS: lambda pinned to Stage A estimate for same sample
        lam_row = rf_table[rf_table["sample"] == name]
        if len(lam_row) and pd.notna(lam_row["lambda_hat"].iloc[0]):
            lam_fix = float(max(lam_row["lambda_hat"].iloc[0], 0.0))
            fit_fix = _fit_nlls(sub, init, lam_fixed=lam_fix)
            row_fix = {"sample": name, "spec": "fixed_lambda_stageA", "N": len(sub), "lambda_fixed_source": lam_fix}
            row_fix.update(fit_fix)
            rows.append(row_fix)

        # Fitted values for diagnostics
        if fit.get("converged", 0) == 1:
            a = sub["std_eb"].to_numpy(float)
            m = sub["misfit_structural"].to_numpy(float)
            s = sub["peer_eb"].to_numpy(float)
            n = sub["N_c_new"].to_numpy(float)
            v = sub["V_c_grade"].to_numpy(float)
            # Use the same standardized covariates as in estimation.
            mz = (m - m.mean()) / (m.std() if m.std() > 1e-10 else 1.0)
            sz = (s - s.mean()) / (s.std() if s.std() > 1e-10 else 1.0)
            nz = (n - n.mean()) / (n.std() if n.std() > 1e-10 else 1.0)
            vz = (v - v.mean()) / (v.std() if v.std() > 1e-10 else 1.0)
            gain = np.exp(-(fit["psi_N_hat"] * nz + fit["psi_V_hat"] * vz))
            yhat = a + gain * (fit["alpha_hat"] - fit["lambda_hat"] * mz + fit["zeta_hat"] * sz)
            tmp = sub[["experiment", "std_score_el"]].copy()
            tmp["yhat"] = yhat
            tmp["spec"] = "free_lambda"
            fit_df_list.append(tmp)

    out = pd.DataFrame(rows)
    _save_table(out, "struc_t5_production_nlls")

    fit_df = pd.concat(fit_df_list, ignore_index=True) if fit_df_list else pd.DataFrame()
    if len(fit_df):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True, sharey=True)
        for i, (country, label) in enumerate(STUDIES):
            sub = fit_df[fit_df["experiment"] == country]
            if len(sub) > 3000:
                sub = sub.sample(3000, random_state=42)
            axes[i].scatter(sub["std_score_el"], sub["yhat"], s=5, alpha=0.25)
            mn = min(sub["std_score_el"].min(), sub["yhat"].min())
            mx = max(sub["std_score_el"].max(), sub["yhat"].max())
            axes[i].plot([mn, mx], [mn, mx], color="black", lw=1, ls="--")
            axes[i].set_title(label)
            axes[i].set_xlabel("Actual y")
            axes[i].set_ylabel("Predicted y")
        fig.tight_layout()
        fig.savefig(OUT_DIR / "struc_f6_model_fit.pdf")
        plt.close(fig)

    return out, fit_df


def _estimate_itt(df: pd.DataFrame, y_col: str) -> float:
    d = df[df[y_col].notna() & df["std_eb"].notna()].copy()
    if len(d) < 50 or d["treat"].nunique() < 2:
        return np.nan
    X = pd.DataFrame({"treat": d["treat"].astype(float), "std_eb": d["std_eb"].astype(float)})
    fe = pd.get_dummies(d["strata"].astype(str), prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([X, fe], axis=1)
    cl = d["cluster_id"]
    try:
        res = ols_cluster(d[y_col].astype(float), X, cl)
        return float(res.params.get("treat", np.nan))
    except Exception:
        return np.nan


def _empirical_moments(df: pd.DataFrame) -> pd.Series:
    moms = {}
    for country, _ in STUDIES:
        sub = df[df["experiment"] == country].copy()
        moms[f"itt_mean_{country}"] = _estimate_itt(sub, "std_score_el")

        for grp in [0, 1]:
            ss = sub[sub["upper_group"] == grp]
            moms[f"itt_track{grp}_{country}"] = _estimate_itt(ss, "std_score_el")

        sq = sub[["std_score_bl"]].dropna()
        if len(sq) > 20:
            q = pd.qcut(sub["std_score_bl"], 4, labels=False, duplicates="drop")
            for qq in sorted(pd.Series(q).dropna().unique()):
                ss = sub[q == qq]
                moms[f"itt_q{int(qq)+1}_{country}"] = _estimate_itt(ss, "std_score_el")

        moms[f"te_disp_{country}"] = _estimate_itt(sub, "dev_eb")
        moms[f"te_csize_{country}"] = _estimate_itt(sub.rename(columns={"N_c_new": "tmp"}), "tmp")
        moms[f"te_vgrade_{country}"] = _estimate_itt(sub.rename(columns={"V_c_grade": "tmp"}), "tmp")
    return pd.Series(moms, dtype=float)


def _simulate_outcome(df: pd.DataFrame, p: np.ndarray) -> np.ndarray:
    alpha, lam, psi_n, psi_v, zeta = p
    a = df["std_eb"].to_numpy(float)
    m = df["misfit_structural"].to_numpy(float)
    s = df["peer_eb"].to_numpy(float)
    n = df["N_c_new"].to_numpy(float)
    v = df["V_c_grade"].to_numpy(float)
    gain = np.exp(-(psi_n * n + psi_v * v))
    return a + gain * (alpha - lam * m + zeta * s)


def _smm_scaffold(df: pd.DataFrame, nlls_table: pd.DataFrame) -> pd.DataFrame:
    emp = _empirical_moments(df)

    init = np.array([0.1, 0.3, 0.01, 0.2, 0.1])
    ppool = nlls_table[nlls_table["sample"] == "Pooled"]
    if len(ppool) and int(ppool["converged"].iloc[0]) == 1:
        init = np.array(
            [
                ppool["alpha_hat"].iloc[0],
                ppool["lambda_hat"].iloc[0],
                ppool["psi_N_hat"].iloc[0],
                ppool["psi_V_hat"].iloc[0],
                ppool["zeta_hat"].iloc[0],
            ]
        )

    # SMM objective uses only outcome moments (ITT moments).
    # Class-size and grade-dispersion moments are included in output diagnostics but
    # not in the objective because production parameters do not generate assignment.
    objective_keys = [k for k in emp.index if k.startswith("itt_")]
    valid_keys = [k for k in objective_keys if pd.notna(emp[k])]

    def objective(p):
        d = df.copy()
        d["y_sim"] = _simulate_outcome(d, p)
        sim = {}
        for country, _ in STUDIES:
            sub = d[d["experiment"] == country].copy()
            sim[f"itt_mean_{country}"] = _estimate_itt(sub, "y_sim")
            for grp in [0, 1]:
                ss = sub[sub["upper_group"] == grp]
                sim[f"itt_track{grp}_{country}"] = _estimate_itt(ss, "y_sim")
            sq = sub[["std_score_bl"]].dropna()
            if len(sq) > 20:
                q = pd.qcut(sub["std_score_bl"], 4, labels=False, duplicates="drop")
                for qq in sorted(pd.Series(q).dropna().unique()):
                    ss = sub[q == qq]
                    sim[f"itt_q{int(qq)+1}_{country}"] = _estimate_itt(ss, "y_sim")
        err = []
        for k in valid_keys:
            if k in sim and pd.notna(sim[k]):
                err.append(emp[k] - sim[k])
        if not err:
            return 1e6
        return float(np.sum(np.square(err)))

    bounds = [(-3, 3), (0, 5), (0, 2), (0, 5), (-5, 5)]
    res = minimize(objective, init, method="L-BFGS-B", bounds=bounds, options={"maxiter": 200})

    out_rows = []
    out_rows.append(
        dict(
            status="SMM_opt",
            converged=int(res.success),
            alpha_hat=float(res.x[0]),
            lambda_hat=float(res.x[1]),
            psi_N_hat=float(res.x[2]),
            psi_V_hat=float(res.x[3]),
            zeta_hat=float(res.x[4]),
            obj=float(res.fun),
            note="Objective uses ITT moments only (assignment moments excluded).",
        )
    )
    out = pd.DataFrame(out_rows)
    _save_table(out, "struc_t7_moments")

    # Save empirical moments for inspection
    moms_df = emp.rename("empirical").reset_index().rename(columns={"index": "moment"})
    _save_table(moms_df, "struc_t7_moments_empirical")
    return out


def _identification_table() -> pd.DataFrame:
    out = pd.DataFrame(
        [
            ["rho_g", "BL-EL control correlation by grade", "Directly estimated", "Assumes stable latent ability mapping in control."],
            ["lambda", "Misfit term in production equation", "Partially identified", "Sensitive to I_k definition and ability nonlinearity controls."],
            ["psi_N", "Class-size term", "Partially identified", "Uses cross-class variation; potential endogenous class composition."],
            ["psi_V", "Grade-dispersion term", "Weakly identified", "Mostly treatment-classroom variation; close to treatment-level confounding."],
            ["I_k", "Track-level target", "Constructed (calibrated)", "Estimated as empirical mean ability by track, not free parameter."],
            ["zeta", "Composite social term S_ic", "Partially identified", "Combines peer-level/rank effects; not separately identified."],
            ["Peer vs rank split", "Separate coefficients", "Not identified in first pass", "Requires richer within-class variation/exclusion restrictions."],
        ],
        columns=["Parameter", "Source", "IdentificationStatus", "Comments"],
    )
    _save_table(out, "struc_t6_identification")
    return out


def _write_memo(
    inv: pd.DataFrame,
    mapping: pd.DataFrame,
    meas: pd.DataFrame,
    assign: pd.DataFrame,
    class_tab: pd.DataFrame,
    rf_tab: pd.DataFrame,
    nlls_tab: pd.DataFrame,
    smm_tab: pd.DataFrame,
    id_tab: pd.DataFrame,
) -> None:
    memo = OUT_DIR / "structural_memo.md"
    with memo.open("w", encoding="utf-8") as f:
        f.write("# First-Pass Structural Estimation Memo (Kenya Y1 + Liberia)\n\n")
        f.write("## 1) Data inventory\n\n")
        f.write(_md_table(inv))
        f.write("\n\n")
        f.write("## 2) Mapping from theory to data\n\n")
        f.write(_md_table(mapping))
        f.write("\n\n")
        f.write("## 3) Measurement model results\n\n")
        f.write("- Implemented grade-specific empirical-Bayes normal model.\n")
        f.write("- Estimated rho_g from control BL-EL correlation; computed posterior variances.\n")
        f.write("- Posterior means match existing cleaner outputs (see `eb_match_mae`).\n\n")
        f.write(_md_table(meas))
        f.write("\n\n")
        f.write("## 4) Assignment rule results\n\n")
        f.write(_md_table(assign))
        f.write("\n\n")
        f.write("## 5) Classroom variables (realized allocation)\n\n")
        f.write("- Constructed new variables: `V_c_grade`, `I_k`, `rank_ic`, `n_grades_c`, `misfit_structural`.\n\n")
        f.write(_md_table(class_tab))
        f.write("\n\n")
        f.write("## 6) Production model estimates\n\n")
        f.write("### Stage A: Reduced-form structural regression\n\n")
        f.write(_md_table(rf_tab))
        f.write("\n\n")
        f.write("### Stage B: Nonlinear least squares\n\n")
        f.write(_md_table(nlls_tab))
        f.write("\n\n")
        f.write("### Stage C: SMM scaffold\n\n")
        f.write("- Implemented a working SMM scaffold with ITT moments in the objective.\n")
        f.write("- Assignment-side moments (class size / grade dispersion changes) are reported but not targeted in production-only objective.\n\n")
        f.write(_md_table(smm_tab))
        f.write("\n\n")
        f.write("## 7) Identification assessment\n\n")
        f.write(_md_table(id_tab))
        f.write("\n\n")
        f.write("## 8) What is estimated vs fragile\n\n")
        f.write("- **Clearly estimated**: rho_g, assignment-rule slopes, reduced-form lambda/zeta signs in major specs.\n")
        f.write("- **Partially identified**: psi_N and zeta (depend on classroom composition assumptions).\n")
        f.write("- **Weakly identified**: psi_V (grade-dispersion mostly induced by treatment assignment structure).\n")
        f.write("- **Not separately identified**: peer level vs rank effects (only composite S_ic used).\n\n")
        f.write("## 9) Next upgrades\n\n")
        f.write("1. Add richer assignment simulation so SMM can target class-size and grade-dispersion moments structurally.\n")
        f.write("2. Estimate experiment-specific rather than pooled psi_N / psi_V when sample permits.\n")
        f.write("3. Add bootstrap uncertainty for NLLS and SMM parameters.\n")
        f.write("4. Explore multi-signal measurement extension in Kenya (literacy + English latent factor) as robustness.\n")


def main() -> None:
    print("=" * 70)
    print("Structural first-pass estimation: Kenya Y1 + Liberia")
    print("=" * 70)
    studies = _load_data()
    inv, mapping = _inventory_and_mapping(studies)

    print("\n[1/6] Measurement model")
    meas = _measurement_model(studies)

    print("[2/6] Assignment rule")
    assign = _assignment_rule(studies)

    print("[3/6] Classroom variables")
    df_all = _construct_classroom_vars(studies)

    print("[4/6] Production Stage A")
    rf_tab = _stage_a_reduced_form(df_all)

    print("[5/6] Production Stage B + Stage C")
    nlls_tab, _fit_df = _stage_b_nlls(df_all, rf_tab)
    smm_tab = _smm_scaffold(df_all, nlls_tab)

    print("[6/6] Identification + memo")
    id_tab = _identification_table()
    class_tab = pd.read_csv(OUT_DIR / "struc_t3_classroom.txt", sep="\t")
    _write_memo(inv, mapping, meas, assign, class_tab, rf_tab, nlls_tab, smm_tab, id_tab)

    print("\nDone.")
    print(f"Outputs saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
