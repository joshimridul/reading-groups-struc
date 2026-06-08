#!/usr/bin/env python3
"""
Control-trained predictions of assignment gains.

This script implements a theory-guided validation exercise:
1) Estimate control-only predictive objects and baseline signal metrics.
2) Construct ex ante assignment-gain measures from pre-treatment variables.
3) Test whether control-trained gains organize treatment heterogeneity.

Outputs are written to: 3_Python/output/control_trained_gains/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "output"
OUT_DIR = DATA_DIR / "control_trained_gains"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES = ["kenya", "liberia", "nigeria"]
CLUSTER_VAR = {"kenya": "academycode", "liberia": "ggroup", "nigeria": "academycode"}
CUTOFFS = {
    "kenya": {1: 40, 2: 35},
    "liberia": {1: 23, 2: 23, 3: 14, 4: 14},
}


@dataclass
class CountryObjects:
    country: str
    data: pd.DataFrame
    predictive_metrics: dict[str, float]
    heterogeneity_rows: list[dict[str, Any]]
    school_summary: pd.DataFrame
    assumptions: list[str]


def _safe_z(s: pd.Series) -> pd.Series:
    sd = float(s.std(ddof=0))
    if not np.isfinite(sd) or sd <= 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - float(s.mean())) / sd


def _load_country(country: str) -> pd.DataFrame:
    p = DATA_DIR / f"analysis_{country}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"Missing cleaned file: {p}")
    d = pd.read_parquet(p).copy()
    d["country"] = country
    return d


def _add_control_standardized_outcome(d: pd.DataFrame, assumptions: list[str]) -> pd.DataFrame:
    out = d.copy()
    if "score_el" not in out.columns:
        assumptions.append("score_el missing; falling back to std_score_el.")
        out["y_std"] = out["std_score_el"].astype(float)
        return out
    c = out.loc[out["treat"] == 0, "score_el"].dropna()
    mu = float(c.mean()) if len(c) else np.nan
    sd = float(c.std(ddof=0)) if len(c) else np.nan
    if not np.isfinite(sd) or sd <= 1e-12:
        assumptions.append("Control SD(score_el) invalid; falling back to std_score_el.")
        out["y_std"] = out["std_score_el"].astype(float)
    else:
        out["y_std"] = (out["score_el"].astype(float) - mu) / sd
    return out


def _designed_track(country: str, d: pd.DataFrame, assumptions: list[str]) -> pd.Series:
    if country in {"kenya", "liberia"}:
        out = pd.Series(np.nan, index=d.index, dtype=float)
        for g, c in CUTOFFS[country].items():
            m = d["grade"] == g
            upper = (d.loc[m, "score_bl"] > c).astype(float)
            if country == "kenya":
                out.loc[m] = np.where(upper == 1.0, 2.0, 1.0)
            else:
                # Liberia uses four realized groups mapped by grade pair.
                if g in {1, 2}:
                    out.loc[m] = np.where(upper == 1.0, 2.0, 1.0)
                else:
                    out.loc[m] = np.where(upper == 1.0, 4.0, 3.0)
        return out

    # Nigeria: intended assignment is 3-track by placement test.
    # If placement is missing, fallback to baseline score terciles by grade.
    out = pd.Series(np.nan, index=d.index, dtype=float)
    for g in sorted(d["grade"].dropna().unique()):
        m = d["grade"] == g
        src = d.loc[m, "placement_score"].copy()
        if src.notna().sum() < 30:
            assumptions.append(
                f"Nigeria grade {int(g)}: placement_score sparse; fallback to score_bl terciles."
            )
            src = d.loc[m, "score_bl"].copy()
        try:
            q = pd.qcut(src.rank(method="first"), q=3, labels=[1, 2, 3])
            out.loc[m] = q.astype(float)
        except ValueError:
            # Degenerate distribution fallback.
            assumptions.append(
                f"Nigeria grade {int(g)}: tercile split degenerate; fallback to std_grp."
            )
            out.loc[m] = d.loc[m, "std_grp"].astype(float)
    return out


def _control_predictive_metrics(d: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    c = d[
        (d["treat"] == 0)
        & d["score_bl"].notna()
        & d["y_std"].notna()
        & d["grade"].notna()
        & d["strata"].notna()
    ].copy()

    rows = []
    r2s: list[float] = []
    ws: list[int] = []
    for g in sorted(c["grade"].unique()):
        cg = c[c["grade"] == g].copy()
        if len(cg) < 30:
            continue
        m = smf.ols("y_std ~ score_bl", data=cg).fit()
        r2 = float(m.rsquared)
        rows.append({"grade": int(g), "n": int(len(cg)), "within_grade_r2": r2})
        r2s.append(r2)
        ws.append(len(cg))

    # Incremental R2 over grade FE using flexible baseline curve.
    m0 = smf.ols("y_std ~ C(grade)", data=c).fit()
    m1 = smf.ols(
        "y_std ~ C(grade) + score_bl + I(score_bl**2) + I(score_bl**3) "
        "+ C(grade):score_bl + C(grade):I(score_bl**2) + C(grade):I(score_bl**3)",
        data=c,
    ).fit()
    metrics = {
        "within_grade_r2": float(np.average(r2s, weights=ws)) if ws else np.nan,
        "incremental_r2": float(m1.rsquared - m0.rsquared),
        "n_controls_used": int(len(c)),
    }
    by_grade = pd.DataFrame(rows)
    return metrics, by_grade


def _control_frontier_predictions(d: pd.DataFrame) -> pd.DataFrame:
    # Fit in controls only, predict for all students.
    c = d[
        d["treat"].eq(0)
        & d["score_bl"].notna()
        & d["y_std"].notna()
        & d["grade"].notna()
    ].copy()
    # Omit strata FE in prediction frontier to avoid unseen strata-level issues
    # when projecting onto treated units.
    formula = (
        "y_std ~ C(grade) + score_bl + I(score_bl**2) + I(score_bl**3) "
        "+ C(grade):score_bl + C(grade):I(score_bl**2) + C(grade):I(score_bl**3)"
    )
    m = smf.ols(formula, data=c).fit()
    out = d.copy()
    out["yhat_grade_rule"] = m.predict(out)
    return out


def _ability_proxy(d: pd.DataFrame, assumptions: list[str]) -> pd.Series:
    if "std_eb" in d.columns and d["std_eb"].notna().mean() > 0.9:
        return d["std_eb"].astype(float)
    assumptions.append("Using z-scored score_bl as ability proxy because std_eb unavailable.")
    return _safe_z(d["score_bl"].astype(float))


def _compute_gain_objects(country: str, d: pd.DataFrame, assumptions: list[str]) -> pd.DataFrame:
    out = d.copy()
    out["ability_proxy"] = _ability_proxy(out, assumptions)
    out["designed_track"] = _designed_track(country, out, assumptions)
    out["realized_track"] = out["std_grp"].astype(float)

    # Targets from pre-treatment ability distributions (no outcomes used).
    out["grade_target"] = out.groupby("grade")["ability_proxy"].transform("mean")
    out["track_target_designed"] = out.groupby("designed_track")["ability_proxy"].transform("mean")
    out["track_target_realized"] = out.groupby("realized_track")["ability_proxy"].transform("mean")

    out["mismatch_grade"] = (out["ability_proxy"] - out["grade_target"]) ** 2
    out["mismatch_designed"] = (out["ability_proxy"] - out["track_target_designed"]) ** 2
    out["gain_mismatch_designed"] = out["mismatch_grade"] - out["mismatch_designed"]

    out["mismatch_realized"] = (out["ability_proxy"] - out["track_target_realized"]) ** 2
    out["gain_mismatch_realized"] = out["mismatch_grade"] - out["mismatch_realized"]

    # Version B (auxiliary): map mismatch reduction into outcome units via controls-only slope.
    c = out[
        out["treat"].eq(0)
        & out["y_std"].notna()
        & out["ability_proxy"].notna()
        & out["mismatch_grade"].notna()
        & out["grade"].notna()
        & out["strata"].notna()
    ].copy()
    if len(c) >= 80:
        mm = smf.ols(
            "y_std ~ C(grade) + C(strata) + ability_proxy + I(ability_proxy**2) + I(ability_proxy**3) + mismatch_grade",
            data=c,
        ).fit()
        gamma = float(mm.params.get("mismatch_grade", np.nan))
        out["gain_pred_designed"] = gamma * out["gain_mismatch_designed"]
        out["gain_pred_realized"] = gamma * out["gain_mismatch_realized"]
        out["mismatch_to_outcome_slope_control"] = gamma
    else:
        assumptions.append("Controls too small for Version B; using NaN gain_pred.")
        out["gain_pred_designed"] = np.nan
        out["gain_pred_realized"] = np.nan
        out["mismatch_to_outcome_slope_control"] = np.nan

    out["pred_gain_main"] = out["gain_mismatch_designed"]
    out["pred_gain_main_z"] = _safe_z(out["pred_gain_main"])
    return out


def _fit_clustered(formula: str, data: pd.DataFrame, cluster_var: str):
    dd = data.dropna(subset=["y_std", "treat", "pred_gain_main_z", "std_eb", "strata", cluster_var]).copy()
    if len(dd) < 80:
        return None, dd
    model = smf.ols(formula, data=dd).fit(cov_type="cluster", cov_kwds={"groups": dd[cluster_var]})
    return model, dd


def _heterogeneity_main(country: str, d: pd.DataFrame) -> dict[str, Any]:
    formula = "y_std ~ treat + pred_gain_main_z + treat:pred_gain_main_z + std_eb + C(strata)"
    m, dd = _fit_clustered(formula, d, CLUSTER_VAR[country])
    if m is None:
        return {
            "country": country,
            "coef_treat": np.nan,
            "se_treat": np.nan,
            "coef_predgain": np.nan,
            "se_predgain": np.nan,
            "coef_treat_x_predgain": np.nan,
            "se_treat_x_predgain": np.nan,
            "n": int(len(dd)),
            "cluster_unit": CLUSTER_VAR[country],
            "baseline_controls": "std_eb + strata FE",
        }
    return {
        "country": country,
        "coef_treat": float(m.params.get("treat", np.nan)),
        "se_treat": float(m.bse.get("treat", np.nan)),
        "coef_predgain": float(m.params.get("pred_gain_main_z", np.nan)),
        "se_predgain": float(m.bse.get("pred_gain_main_z", np.nan)),
        "coef_treat_x_predgain": float(m.params.get("treat:pred_gain_main_z", np.nan)),
        "se_treat_x_predgain": float(m.bse.get("treat:pred_gain_main_z", np.nan)),
        "n": int(len(dd)),
        "cluster_unit": CLUSTER_VAR[country],
        "baseline_controls": "std_eb + strata FE",
    }


def _itt_quartile(country: str, d: pd.DataFrame) -> pd.DataFrame:
    dd = d.dropna(subset=["pred_gain_main", "y_std", "treat", "std_eb", "strata", CLUSTER_VAR[country]]).copy()
    cvals = dd.loc[dd["treat"] == 0, "pred_gain_main"]
    q = np.quantile(cvals, [0.25, 0.50, 0.75])
    dd["gain_q"] = pd.cut(
        dd["pred_gain_main"],
        bins=[-np.inf, q[0], q[1], q[2], np.inf],
        labels=["Q1", "Q2", "Q3", "Q4"],
    )
    rows = []
    for qname in ["Q1", "Q2", "Q3", "Q4"]:
        dq = dd[dd["gain_q"] == qname].copy()
        if len(dq) < 50:
            rows.append({"country": country, "quartile": qname, "itt": np.nan, "se": np.nan, "n": len(dq)})
            continue
        m = smf.ols("y_std ~ treat + std_eb + C(strata)", data=dq).fit(
            cov_type="cluster", cov_kwds={"groups": dq[CLUSTER_VAR[country]]}
        )
        rows.append(
            {
                "country": country,
                "quartile": qname,
                "itt": float(m.params.get("treat", np.nan)),
                "se": float(m.bse.get("treat", np.nan)),
                "n": int(len(dq)),
            }
        )
    return pd.DataFrame(rows)


def _nigeria_impl_quality(d: pd.DataFrame) -> pd.DataFrame:
    n = d[d["country"] == "nigeria"].copy()
    t = n[n["treat"] == 1].copy()
    rows = []
    for sch, ds in t.groupby("academycode"):
        # Score-to-group monotonicity
        g = ds[ds["placement_score"].notna() & ds["std_grp"].notna()].copy()
        sp = np.nan
        if len(g) >= 15:
            sp = float(g["placement_score"].rank(pct=True).corr(g["std_grp"].rank(pct=True)))
        formed_all = float(ds["std_grp"].nunique() >= 3)
        recorded = float(ds["group"].notna().mean()) if "group" in ds.columns else np.nan
        rows.append(
            {
                "academycode": sch,
                "formed_all_groups": formed_all,
                "assignment_record_share": recorded,
                "score_group_spearman": sp,
            }
        )
    q = pd.DataFrame(rows)
    for c in ["formed_all_groups", "assignment_record_share", "score_group_spearman"]:
        if c in q.columns:
            q[f"z_{c}"] = _safe_z(q[c].fillna(q[c].mean()))
    q["impl_quality"] = q[[x for x in q.columns if x.startswith("z_")]].mean(axis=1)
    return q


def _nigeria_validation_specs(d: pd.DataFrame, impl: pd.DataFrame) -> pd.DataFrame:
    n = d[d["country"] == "nigeria"].copy().merge(impl[["academycode", "impl_quality"]], on="academycode", how="left")
    n["impl_quality"] = n["impl_quality"].fillna(0.0)
    n["pred_gain_main_z"] = _safe_z(n["pred_gain_main"])
    dd = n.dropna(subset=["y_std", "treat", "pred_gain_main_z", "std_eb", "strata", "academycode"]).copy()
    m = smf.ols(
        "y_std ~ treat + pred_gain_main_z + impl_quality + treat:pred_gain_main_z "
        "+ treat:pred_gain_main_z:impl_quality + std_eb + C(strata)",
        data=dd,
    ).fit(cov_type="cluster", cov_kwds={"groups": dd["academycode"]})
    rows = []
    for term in ["treat", "pred_gain_main_z", "treat:pred_gain_main_z", "treat:pred_gain_main_z:impl_quality"]:
        rows.append(
            {
                "term": term,
                "coef": float(m.params.get(term, np.nan)),
                "se": float(m.bse.get(term, np.nan)),
                "n": int(len(dd)),
            }
        )
    return pd.DataFrame(rows)


def _figure_distributions(all_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        d = all_df[all_df["country"] == c]["pred_gain_main"].dropna()
        ax.hist(d, bins=30, alpha=0.8, color="#4E79A7", edgecolor="white")
        ax.axvline(d.mean(), color="black", linestyle="--", linewidth=1)
        ax.set_title(c.capitalize())
        ax.set_xlabel("Predicted mismatch gain")
    axes[0].set_ylabel("Count")
    fig.suptitle("Figure 1: Distribution of predicted assignment gains by experiment")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig1_predicted_gain_distribution.png", dpi=200)
    plt.close(fig)


def _figure_quartile_effects(quart: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=True)
    xmap = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
    for ax, c in zip(axes, COUNTRIES):
        d = quart[quart["country"] == c].copy()
        d["x"] = d["quartile"].map(xmap)
        ax.errorbar(d["x"], d["itt"], yerr=1.96 * d["se"], fmt="o-", color="#E15759", capsize=3)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks([1, 2, 3, 4], ["Q1", "Q2", "Q3", "Q4"])
        ax.set_title(c.capitalize())
        ax.set_xlabel("Predicted-gain quartile")
    axes[0].set_ylabel("ITT (std outcome)")
    fig.suptitle("Figure 2: Treatment effects by predicted-gain quartile")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig2_itt_by_predgain_quartile.png", dpi=200)
    plt.close(fig)


def _figure_nigeria_impl(d: pd.DataFrame, impl: pd.DataFrame) -> None:
    n = d[d["country"] == "nigeria"].copy().merge(impl, on="academycode", how="left")

    # School-level treated residualized outcome as realized-impact proxy.
    c = n[n["treat"] == 0].dropna(subset=["y_std", "std_eb", "grade"]).copy()
    m = smf.ols("y_std ~ std_eb + C(grade)", data=c).fit()
    n["resid_y"] = n["y_std"] - m.predict(n)
    sch = (
        n[n["treat"] == 1]
        .groupby("academycode")
        .agg(
            mean_designed_gain=("gain_mismatch_designed", "mean"),
            mean_realized_gain=("gain_mismatch_realized", "mean"),
            school_te_proxy=("resid_y", "mean"),
            n_students=("studyid", "count"),
        )
        .reset_index()
        .merge(impl, on="academycode", how="left")
    )
    sch.to_csv(OUT_DIR / "nigeria_school_gain_implementation.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(
        sch["mean_designed_gain"],
        sch["school_te_proxy"],
        c=sch["impl_quality"],
        s=30 + sch["n_students"],
        cmap="viridis",
        alpha=0.9,
        edgecolor="k",
        linewidth=0.3,
    )
    z = np.polyfit(sch["mean_designed_gain"], sch["school_te_proxy"], 1)
    xx = np.linspace(sch["mean_designed_gain"].min(), sch["mean_designed_gain"].max(), 100)
    ax.plot(xx, z[0] * xx + z[1], color="black", linestyle="--", linewidth=1)
    cb = plt.colorbar(sc, ax=ax)
    cb.set_label("Implementation quality (z-index)")
    ax.set_title("Figure 3: Nigeria designed gains vs implementation and realized impacts")
    ax.set_xlabel("School mean designed-rule predicted gain")
    ax.set_ylabel("School realized impact proxy (treated residual mean)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig3_nigeria_designed_gain_vs_implementation.png", dpi=220)
    plt.close(fig)


def _write_memo(
    table1: pd.DataFrame,
    table2: pd.DataFrame,
    nigeria_val: pd.DataFrame,
    assumptions: list[str],
) -> None:
    p = OUT_DIR / "control_trained_predictions_note.md"
    lines = [
        "# Control-Trained Predictions of Assignment Gains",
        "",
        "## Identification logic",
        "- Control outcomes are used only to estimate predictive objects (R2 and smooth achievement frontier).",
        "- Ex ante gain objects are built from pre-treatment variables and assignment rules.",
        "- Validation tests whether these control-trained sufficient statistics organize treatment-effect heterogeneity.",
        "- This is not presented as one-for-one prediction of treated outcomes.",
        "",
        "## Construction of predicted gains",
        "- Main object (Version A): mismatch-reduction gain using ability proxy (`std_eb`) and squared mismatch to grade target versus treatment track target.",
        "- Auxiliary object (Version B): controls-only mismatch-to-outcome slope applied to Version A mismatch reduction.",
        "- Nigeria includes designed-rule and realized-rule gains; implementation quality is measured at school level.",
        "",
        "## Controls-only objects",
        "- Within-grade R2 and incremental R2 are estimated in controls only.",
        "- Flexible frontier model uses controls only with grade FE, strata FE, and cubic baseline terms by grade.",
        "",
        "## Main findings (from generated tables)",
        f"- Table 1 metrics by experiment are saved in `table1_control_trained_predictive_power.csv`.",
        f"- Heterogeneity regressions are saved in `table2_heterogeneity_by_predicted_gain.csv`.",
        f"- Nigeria implementation interaction results are saved in `table_nigeria_implementation_validation.csv`.",
        "",
        "## Interpretation for paper",
        "- Positive `T x PredGain` supports the claim that control-trained assignment-gain sufficient statistics organize treatment heterogeneity.",
        "- Nigeria deviations should be interpreted through implementation quality: designed potential can fail to realize when execution weakens score-based assignment.",
        "",
        "## Ambiguities and fallbacks used",
    ]
    if assumptions:
        for a in assumptions:
            lines.append(f"- {a}")
    else:
        lines.append("- None triggered in this run.")
    p.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    assumptions: list[str] = [
        "Nigeria designed-rule assignment is proxied by within-grade placement-score terciles (fallback to score_bl terciles when placement is sparse).",
        "Figure 3 Nigeria school impacts use treated-school residualized means as descriptive proxies, not causal school-level ATE estimators.",
    ]
    all_country_rows: list[pd.DataFrame] = []
    table1_rows: list[dict[str, Any]] = []
    table2_rows: list[dict[str, Any]] = []
    quartile_rows: list[pd.DataFrame] = []
    school_summaries: list[pd.DataFrame] = []

    for country in COUNTRIES:
        d = _load_country(country)
        d = _add_control_standardized_outcome(d, assumptions)
        metrics, by_grade = _control_predictive_metrics(d)
        by_grade.to_csv(OUT_DIR / f"{country}_control_r2_by_grade.csv", index=False)

        d = _control_frontier_predictions(d)
        d = _compute_gain_objects(country, d, assumptions)
        d.to_parquet(OUT_DIR / f"{country}_predicted_gains.parquet", index=False)
        all_country_rows.append(d)

        # Table 1 entries
        notes = "Designed=realized deterministic rule"
        if country == "nigeria":
            notes = "Designed and realized gains both reported; implementation quality used in validation"
        table1_rows.append(
            {
                "experiment": country.capitalize(),
                "within_grade_r2_controls": metrics["within_grade_r2"],
                "incremental_r2_controls": metrics["incremental_r2"],
                "mean_predicted_mismatch_gain": float(d["gain_mismatch_designed"].mean()),
                "sd_predicted_mismatch_gain": float(d["gain_mismatch_designed"].std(ddof=0)),
                "designed_vs_realized_note": notes,
            }
        )

        # Table 2 entries
        table2_rows.append(_heterogeneity_main(country, d))
        quartile_rows.append(_itt_quartile(country, d))

        sch = (
            d.groupby("academycode", as_index=False)
            .agg(
                country=("country", "first"),
                school_mean_pred_gain=("gain_mismatch_designed", "mean"),
                school_sd_pred_gain=("gain_mismatch_designed", "std"),
                n_students=("studyid", "count"),
            )
        )
        school_summaries.append(sch)

    all_df = pd.concat(all_country_rows, ignore_index=True)
    quart = pd.concat(quartile_rows, ignore_index=True)
    school_df = pd.concat(school_summaries, ignore_index=True)

    # Cross-experiment summary (requested in Part 5.3).
    cross_rows = []
    for country in COUNTRIES:
        d = all_df[all_df["country"] == country].copy()
        tt = d.dropna(subset=["y_std", "treat", "std_eb", "strata", CLUSTER_VAR[country]])
        m = smf.ols("y_std ~ treat + std_eb + C(strata)", data=tt).fit(
            cov_type="cluster", cov_kwds={"groups": tt[CLUSTER_VAR[country]]}
        )
        row_t1 = [r for r in table1_rows if r["experiment"].lower() == country][0]
        cross_rows.append(
            {
                "experiment": country.capitalize(),
                "within_grade_r2_controls": row_t1["within_grade_r2_controls"],
                "incremental_r2_controls": row_t1["incremental_r2_controls"],
                "mean_predicted_assignment_gain": float(d["gain_mismatch_designed"].mean()),
                "realized_itt": float(m.params.get("treat", np.nan)),
                "realized_itt_se": float(m.bse.get("treat", np.nan)),
            }
        )
    cross = pd.DataFrame(cross_rows)

    table1 = pd.DataFrame(table1_rows)
    table2 = pd.DataFrame(table2_rows)

    # Nigeria implementation validation
    impl = _nigeria_impl_quality(all_df)
    impl.to_csv(OUT_DIR / "nigeria_implementation_quality.csv", index=False)
    nigeria_val = _nigeria_validation_specs(all_df, impl)

    # Save tables
    table1.to_csv(OUT_DIR / "table1_control_trained_predictive_power.csv", index=False)
    table2.to_csv(OUT_DIR / "table2_heterogeneity_by_predicted_gain.csv", index=False)
    quart.to_csv(OUT_DIR / "table_quartile_itt_by_predgain.csv", index=False)
    cross.to_csv(OUT_DIR / "table_cross_experiment_summary.csv", index=False)
    school_df.to_csv(OUT_DIR / "school_level_predicted_gain_summary.csv", index=False)
    nigeria_val.to_csv(OUT_DIR / "table_nigeria_implementation_validation.csv", index=False)

    table1.to_latex(OUT_DIR / "table1_control_trained_predictive_power.tex", index=False, float_format="%.3f")
    table2.to_latex(OUT_DIR / "table2_heterogeneity_by_predicted_gain.tex", index=False, float_format="%.3f")

    # Save core long file
    keep_cols = [
        "studyid",
        "academycode",
        "country",
        "treat",
        "grade",
        "strata",
        "std_score_el",
        "std_eb",
        "y_std",
        "yhat_grade_rule",
        "designed_track",
        "realized_track",
        "gain_mismatch_designed",
        "gain_mismatch_realized",
        "gain_pred_designed",
        "gain_pred_realized",
        "pred_gain_main",
        "pred_gain_main_z",
    ]
    all_df[[c for c in keep_cols if c in all_df.columns]].to_parquet(
        OUT_DIR / "predicted_assignment_gains_all_countries.parquet", index=False
    )

    # Figures
    _figure_distributions(all_df)
    _figure_quartile_effects(quart)
    _figure_nigeria_impl(all_df, impl)

    _write_memo(table1, table2, nigeria_val, assumptions)

    print("Control-trained assignment-gain workflow complete.")
    print(f"Output directory: {OUT_DIR}")


if __name__ == "__main__":
    main()
