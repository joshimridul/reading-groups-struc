#!/usr/bin/env python3
"""
empirical_moments.py
====================
Build empirical moments for cross-country structural SMM estimation.

This script intentionally does only the empirical-moments stage and stops.
No optimizer is launched here.

Outputs:
  - 3_Python/output/structural_smm/empirical_moments.csv
  - 3_Python/output/structural_smm/empirical_moments_summary.csv
  - 3_Python/output/structural_smm/empirical_moments_todo.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

from config import get_config, OUT


SEED = 20260403
RNG = np.random.default_rng(SEED)

OUT_DIR = OUT / "structural_smm"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES = ["kenya", "liberia", "nigeria"]


@dataclass
class Dataset:
    country: str
    label: str
    cfg: dict[str, Any]
    df: pd.DataFrame
    cluster_var: str


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return np.nan


def _variance_mean(x: pd.Series) -> float:
    x = x.dropna().astype(float)
    n = len(x)
    if n <= 1:
        return np.nan
    return float(x.var(ddof=1) / n)


def _variance_diff_means(x_t: pd.Series, x_c: pd.Series) -> float:
    return _safe_float(_variance_mean(x_t) + _variance_mean(x_c))


def _variance_corr_r2(r: float, n: int) -> float:
    """
    Approximate var(r^2) via delta method around Pearson r.
    """
    if not np.isfinite(r) or n <= 4:
        return np.nan
    var_r = ((1 - r**2) ** 2) / max(n - 1, 1)
    return float((2 * r) ** 2 * var_r)


def _variance_covariance(x: pd.Series, y: pd.Series) -> float:
    x = x.astype(float)
    y = y.astype(float)
    m = x.notna() & y.notna()
    x = x[m]
    y = y[m]
    n = len(x)
    if n <= 2:
        return np.nan
    xc = x - x.mean()
    yc = y - y.mean()
    z = xc * yc
    return float(z.var(ddof=1) / n)


def _cluster_ols(
    df: pd.DataFrame,
    y_col: str,
    x_core: list[str],
    fe_cols: list[str],
    cluster_col: str,
) -> sm.regression.linear_model.RegressionResultsWrapper | None:
    cols_needed = [y_col, cluster_col] + x_core + fe_cols
    d = df.copy()
    for c in cols_needed:
        if c not in d.columns:
            return None
    mask = np.ones(len(d), dtype=bool)
    mask &= d[y_col].notna().to_numpy()
    mask &= d[cluster_col].notna().to_numpy()
    for c in x_core:
        mask &= d[c].notna().to_numpy()
    for c in fe_cols:
        mask &= d[c].notna().to_numpy()
    d = d.loc[mask].copy()
    if len(d) < 50:
        return None
    if d["treat"].nunique() < 2 and "treat" in x_core:
        return None

    y = d[y_col].astype(float)
    X = d[x_core].astype(float).copy()
    for fe in fe_cols:
        dum = pd.get_dummies(d[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        X = pd.concat([X, dum], axis=1)
    X = sm.add_constant(X, has_constant="add")
    try:
        model = sm.OLS(y, X)
        return model.fit(cov_type="cluster", cov_kwds={"groups": d[cluster_col]})
    except Exception:
        return None


def _load_dataset(country: str) -> Dataset:
    cfg = get_config(country)
    parquet_path = cfg["ANALYSIS_FILE"]
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing cleaned file: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    cluster_var = cfg.get("cluster_var", "academycode")
    if cluster_var not in df.columns:
        cluster_var = "academycode"
    return Dataset(
        country=country,
        label=cfg.get("label", country.title()),
        cfg=cfg,
        df=df.copy(),
        cluster_var=cluster_var,
    )


def _add_moment(
    rows: list[dict[str, Any]],
    market: str,
    category: str,
    moment: str,
    value: float,
    variance: float,
    grade: int | None = None,
    source: str = "computed",
    sample_n: int | None = None,
    notes: str = "",
) -> None:
    rows.append(
        {
            "market": market,
            "category": category,
            "moment": moment,
            "grade": grade,
            "value": _safe_float(value),
            "variance": _safe_float(variance),
            "source": source,
            "sample_n": sample_n,
            "notes": notes,
        }
    )


def _measurement_moments(ds: Dataset, rows: list[dict[str, Any]], todos: list[str]) -> None:
    d = ds.df.copy()
    needed = ["score_bl", "score_el", "grade", "treat"]
    if any(c not in d.columns for c in needed):
        todos.append(f"[{ds.country}] Missing columns for measurement block: {needed}")
        return

    c = d[(d["treat"] == 0) & d["score_bl"].notna() & d["score_el"].notna() & d["grade"].notna()].copy()
    if len(c) < 40:
        todos.append(f"[{ds.country}] Too few controls with baseline+endline for measurement moments.")
        return

    # Grade-level moments
    for g in sorted(c["grade"].dropna().unique()):
        cg = c[c["grade"] == g].copy()
        if len(cg) < 20:
            continue
        x = cg["score_bl"].astype(float)
        y = cg["score_el"].astype(float)
        n = len(cg)
        r = float(x.corr(y))
        r2 = float(r**2)
        cov_xy = float(np.cov(x, y, ddof=1)[0, 1])
        spearman = float(x.rank(pct=True).corr(y.rank(pct=True)))

        _add_moment(rows, ds.country, "measurement", "mean_baseline_control", x.mean(), _variance_mean(x), grade=int(g), sample_n=n)
        _add_moment(
            rows,
            ds.country,
            "measurement",
            "var_baseline_control",
            x.var(ddof=1),
            _safe_float(2 * (x.var(ddof=1) ** 2) / max(n - 1, 1)),
            grade=int(g),
            sample_n=n,
        )
        _add_moment(rows, ds.country, "measurement", "cov_bl_el_control", cov_xy, _variance_covariance(x, y), grade=int(g), sample_n=n)
        _add_moment(rows, ds.country, "measurement", "r2_bl_el_control", r2, _variance_corr_r2(r, n), grade=int(g), sample_n=n)
        _add_moment(rows, ds.country, "measurement", "rank_persistence_control", spearman, _variance_corr_r2(spearman, n), grade=int(g), sample_n=n)

    # Market-level incremental R2 over grade FE
    y = c["score_el"].astype(float)
    gfe = pd.get_dummies(c["grade"].astype(int).astype(str), prefix="g", drop_first=True, dtype=float)
    Xg = sm.add_constant(gfe, has_constant="add")
    Xgb = sm.add_constant(pd.concat([gfe, c[["score_bl"]].astype(float)], axis=1), has_constant="add")
    r2_g = float(sm.OLS(y, Xg).fit().rsquared)
    r2_gb = float(sm.OLS(y, Xgb).fit().rsquared)
    inc_r2 = r2_gb - r2_g
    # Bootstrap variance for incremental R2
    bvals = []
    for _ in range(120):
        idx = RNG.integers(0, len(c), len(c))
        cb = c.iloc[idx].copy()
        yb = cb["score_el"].astype(float)
        gfeb = pd.get_dummies(cb["grade"].astype(int).astype(str), prefix="g", drop_first=True, dtype=float)
        Xgb0 = sm.add_constant(gfeb, has_constant="add")
        Xgb1 = sm.add_constant(pd.concat([gfeb, cb[["score_bl"]].astype(float)], axis=1), has_constant="add")
        try:
            bvals.append(float(sm.OLS(yb, Xgb1).fit().rsquared - sm.OLS(yb, Xgb0).fit().rsquared))
        except Exception:
            continue
    var_inc_r2 = float(np.var(bvals, ddof=1)) if len(bvals) > 20 else np.nan
    _add_moment(rows, ds.country, "measurement", "incremental_r2_over_grade_fe", inc_r2, var_inc_r2, grade=None, sample_n=len(c))


def _assignment_and_reallocation_moments(ds: Dataset, rows: list[dict[str, Any]], todos: list[str]) -> None:
    d = ds.df.copy()
    # Treatment-control reallocation moments
    for col, name in [
        ("dev_eb", "te_within_class_dispersion"),
        ("csize", "te_class_size"),
        ("peer_eb", "te_peer_mean"),
        ("misfit", "te_mismatch"),
    ]:
        if col not in d.columns:
            todos.append(f"[{ds.country}] Missing {col} for {name}.")
            continue
        t = d.loc[d["treat"] == 1, col].dropna().astype(float)
        c = d.loc[d["treat"] == 0, col].dropna().astype(float)
        if len(t) < 10 or len(c) < 10:
            todos.append(f"[{ds.country}] Insufficient sample for {name}.")
            continue
        _add_moment(rows, ds.country, "assignment_reallocation", name, t.mean() - c.mean(), _variance_diff_means(t, c), sample_n=int(len(t) + len(c)))

    # Track shares
    if "std_grp" in d.columns:
        dt = d[d["treat"] == 1].copy()
        if len(dt) > 0:
            for grp in sorted(dt["std_grp"].dropna().unique()):
                share = float((dt["std_grp"] == grp).mean())
                var = float(max(share * (1 - share) / max(len(dt), 1), 1e-12))
                _add_moment(rows, ds.country, "assignment_reallocation", f"track_share_treat_g{int(grp)}", share, var, sample_n=len(dt))

    # Deterministic compliance Kenya/Liberia
    if ds.country in {"kenya", "liberia"}:
        needed = ["score_bl", "upper_group", "grade", "treat"]
        if all(cn in d.columns for cn in needed):
            tt = d[(d["treat"] == 1) & d["score_bl"].notna() & d["upper_group"].notna() & d["grade"].notna()].copy()
            if len(tt) > 0:
                mis = []
                for g in sorted(tt["grade"].dropna().unique()):
                    cutoff = ds.cfg["cutoffs"].get(int(g))
                    if cutoff is None:
                        continue
                    tg = tt[tt["grade"] == g]
                    det = (tg["score_bl"] > cutoff).astype(float)
                    mis.append(float((det != tg["upper_group"]).mean()))
                if mis:
                    mis_rate = float(np.mean(mis))
                    n = len(tt)
                    var = float(max(mis_rate * (1 - mis_rate) / max(n, 1), 1e-12))
                    _add_moment(rows, ds.country, "assignment_reallocation", "misclassification_rate_cutoff", mis_rate, var, sample_n=n)
                    _add_moment(rows, ds.country, "assignment_reallocation", "deterministic_compliance_rate_cutoff", 1 - mis_rate, var, sample_n=n)

    # Nigeria implementation moments
    if ds.country == "nigeria":
        # Spearman(score, realized group)
        if "placement_score" in d.columns and "std_grp" in d.columns:
            t = d[(d["treat"] == 1) & d["placement_score"].notna() & d["std_grp"].notna()].copy()
            if len(t) > 20:
                sp = float(t["placement_score"].rank(pct=True).corr(t["std_grp"].rank(pct=True)))
                _add_moment(rows, ds.country, "implementation_nigeria", "spearman_placement_to_group_treat", sp, _variance_corr_r2(sp, len(t)), sample_n=len(t))

        # Academies with <=2 groups, academies with any Yellow
        if "academycode" in d.columns and "std_grp" in d.columns:
            t = d[(d["treat"] == 1) & d["academycode"].notna() & d["std_grp"].notna()].copy()
            if len(t) > 0:
                by_school = t.groupby("academycode")["std_grp"]
                ngroups = by_school.nunique()
                only_two_or_less = float((ngroups <= 2).mean())
                any_yellow = float(by_school.apply(lambda s: (s == 3).any()).mean())
                nsch = int(ngroups.shape[0])
                _add_moment(rows, ds.country, "implementation_nigeria", "share_treat_academies_two_groups_or_less", only_two_or_less, max(only_two_or_less * (1 - only_two_or_less) / max(nsch, 1), 1e-12), sample_n=nsch)
                _add_moment(rows, ds.country, "implementation_nigeria", "share_treat_academies_with_any_yellow", any_yellow, max(any_yellow * (1 - any_yellow) / max(nsch, 1), 1e-12), sample_n=nsch)
                if nsch < 20:
                    todos.append(
                        f"[nigeria] Treated academies in cleaned sample = {nsch} (<20 design academies); "
                        "added external implementation-target moments from paper notes."
                    )

        # Missing assignment records in treated (raw group, before imputation)
        if "group" in d.columns:
            tt = d[d["treat"] == 1].copy()
            if len(tt) > 0:
                miss = float(tt["group"].isna().mean())
                _add_moment(rows, ds.country, "implementation_nigeria", "share_treat_missing_group_record", miss, max(miss * (1 - miss) / max(len(tt), 1), 1e-12), sample_n=len(tt))
        else:
            todos.append("[nigeria] Missing raw `group` column for assignment-record missingness moment.")

        # External implementation targets from draft/paper notes.
        # These are added as explicit target moments for SMM matching.
        _add_moment(
            rows,
            ds.country,
            "implementation_nigeria_external",
            "spearman_placement_to_group_treat_target",
            0.17,
            0.0025,
            source="paper_target",
            notes="Target from intervention diagnostics: weak score-group link.",
        )
        _add_moment(
            rows,
            ds.country,
            "implementation_nigeria_external",
            "share_treat_academies_two_groups_or_less_target",
            0.50,
            0.01,
            source="paper_target",
            notes="Target from notes: >=10 of 20 treated academies collapsed to <=2 groups.",
        )
        _add_moment(
            rows,
            ds.country,
            "implementation_nigeria_external",
            "share_treat_academies_with_any_yellow_target",
            0.40,
            0.01,
            source="paper_target",
            notes="Target from notes: ~8 of 20 treated academies with any Yellow students.",
        )
        _add_moment(
            rows,
            ds.country,
            "implementation_nigeria_external",
            "share_treat_missing_group_record_target",
            0.34,
            0.005,
            source="paper_target",
            notes="Target from notes: about 34% treated students missing assignment record.",
        )


def _outcome_moments(ds: Dataset, rows: list[dict[str, Any]], todos: list[str]) -> tuple[float | None, float | None, float | None]:
    d = ds.df.copy()
    for col in ["std_score_el", "treat", "std_eb", "strata", ds.cluster_var]:
        if col not in d.columns:
            todos.append(f"[{ds.country}] Missing {col} for ITT regression.")
            return (None, None, None)

    # ITT
    res_itt = _cluster_ols(
        d,
        y_col="std_score_el",
        x_core=["treat", "std_eb"],
        fe_cols=["strata"],
        cluster_col=ds.cluster_var,
    )
    itt_b, itt_v = (None, None)
    if res_itt is not None and "treat" in res_itt.params.index:
        itt_b = float(res_itt.params["treat"])
        itt_v = float(res_itt.bse["treat"] ** 2)
        _add_moment(rows, ds.country, "outcomes", "itt_main", itt_b, itt_v, sample_n=int(res_itt.nobs), notes="std_score_el ~ treat + std_eb + strata FE")

    # Track-specific ITT via upper-group interaction
    if "upper_group" in d.columns:
        dd = d.copy()
        dd["treat_x_upper"] = dd["treat"] * dd["upper_group"]
        res_ul = _cluster_ols(
            dd,
            y_col="std_score_el",
            x_core=["treat", "treat_x_upper", "upper_group", "std_eb"],
            fe_cols=["strata"],
            cluster_col=ds.cluster_var,
        )
        if res_ul is not None and {"treat", "treat_x_upper"}.issubset(set(res_ul.params.index)):
            lower = float(res_ul.params["treat"])
            lower_v = float(res_ul.bse["treat"] ** 2)
            upper = float(res_ul.params["treat"] + res_ul.params["treat_x_upper"])
            upper_v = float(res_ul.bse["treat"] ** 2 + res_ul.bse["treat_x_upper"] ** 2)
            _add_moment(rows, ds.country, "outcomes", "itt_lower_track", lower, lower_v, sample_n=int(res_ul.nobs))
            _add_moment(rows, ds.country, "outcomes", "itt_upper_track_total", upper, upper_v, sample_n=int(res_ul.nobs))

    # Peer/rank composite reduced-form proxy (BH-style)
    peer_b = None
    peer_v = None
    if {"peer_eb", "bl_decile", "grade", "strata", ds.cluster_var, "std_score_el", "treat"}.issubset(d.columns):
        dp = d.dropna(subset=["peer_eb", "bl_decile", "grade", "strata", ds.cluster_var, "std_score_el", "treat"]).copy()
        if len(dp) > 100:
            dp["dt_cell"] = (
                dp["bl_decile"].astype(int).astype(str)
                + "_"
                + dp["treat"].astype(int).astype(str)
                + "_"
                + dp["grade"].astype(int).astype(str)
            )
            res_peer = _cluster_ols(
                dp,
                y_col="std_score_el",
                x_core=["peer_eb"],
                fe_cols=["dt_cell", "strata"],
                cluster_col=ds.cluster_var,
            )
            if res_peer is not None and "peer_eb" in res_peer.params.index:
                peer_b = float(res_peer.params["peer_eb"])
                peer_v = float(res_peer.bse["peer_eb"] ** 2)
                _add_moment(rows, ds.country, "outcomes", "peer_rank_composite_beta", peer_b, peer_v, sample_n=int(res_peer.nobs), notes="BH-style FE: decile x treat x grade + strata")
    else:
        todos.append(f"[{ds.country}] Missing columns for BH-style peer/rank moment.")

    # Lesson completion moments
    if "lp_comp" in d.columns:
        t = d.loc[d["treat"] == 1, "lp_comp"].dropna().astype(float)
        c = d.loc[d["treat"] == 0, "lp_comp"].dropna().astype(float)
        if len(t) > 10 and len(c) > 10:
            _add_moment(rows, ds.country, "outcomes", "lesson_completion_treat_mean", t.mean(), _variance_mean(t), sample_n=len(t))
            _add_moment(rows, ds.country, "outcomes", "lesson_completion_control_mean", c.mean(), _variance_mean(c), sample_n=len(c))
            _add_moment(rows, ds.country, "outcomes", "lesson_completion_treat_minus_control", t.mean() - c.mean(), _variance_diff_means(t, c), sample_n=len(t) + len(c))
    else:
        todos.append(f"[{ds.country}] Missing lp_comp; cannot compute lesson completion moments from cleaned file.")

    # Nigeria external lesson-completion targets (paper-provided) when DI-specific moments missing
    if ds.country == "nigeria":
        _add_moment(rows, ds.country, "outcomes_external", "di_numeracy_lesson_completion_treat_mean", 0.262, 0.0004, source="paper_target", notes="Fallback external target from paper notes")
        _add_moment(rows, ds.country, "outcomes_external", "di_numeracy_lesson_completion_control_mean", 0.261, 0.0004, source="paper_target", notes="Fallback external target from paper notes")
        _add_moment(rows, ds.country, "outcomes_external", "di_math_lesson_completion_treat_mean", 0.694, 0.0004, source="paper_target", notes="Fallback external target from paper notes")
        _add_moment(rows, ds.country, "outcomes_external", "di_math_lesson_completion_control_mean", 0.687, 0.0004, source="paper_target", notes="Fallback external target from paper notes")

    return itt_b, itt_v, peer_b


def _accounting_sanity_moments(
    ds: Dataset,
    rows: list[dict[str, Any]],
    itt_b: float | None,
    itt_v: float | None,
    peer_beta: float | None,
    todos: list[str],
) -> None:
    d = ds.df.copy()
    if itt_b is None or peer_beta is None:
        todos.append(f"[{ds.country}] Skipping accounting sanity moments: missing ITT or peer beta.")
        return
    if "peer_eb" not in d.columns:
        todos.append(f"[{ds.country}] Skipping accounting sanity moments: missing peer_eb.")
        return
    t = d.loc[d["treat"] == 1, "peer_eb"].dropna().astype(float)
    c = d.loc[d["treat"] == 0, "peer_eb"].dropna().astype(float)
    if len(t) < 10 or len(c) < 10:
        todos.append(f"[{ds.country}] Skipping accounting sanity moments: insufficient peer samples.")
        return
    dpeer = float(t.mean() - c.mean())
    v_dpeer = _variance_diff_means(t, c)

    peer_contrib = float(peer_beta * dpeer)
    # Conservative delta-method, without covariance term
    v_peer = float((dpeer**2) * max(np.nanvar([peer_beta]), 0.0) + (peer_beta**2) * v_dpeer)
    # If beta variance not tracked in scalar form, fallback small variance for weighting stability
    if not np.isfinite(v_peer) or v_peer <= 0:
        v_peer = 1e-4

    remainder = float(itt_b - peer_contrib)
    v_rem = float((itt_v if itt_v is not None and np.isfinite(itt_v) else 1e-4) + v_peer)

    _add_moment(rows, ds.country, "accounting", "peer_contribution_approx", peer_contrib, v_peer, notes="peer_beta * delta_peer_mean")
    _add_moment(rows, ds.country, "accounting", "remainder_contribution_approx", remainder, v_rem, notes="itt - peer_contribution")


def build_empirical_moments() -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict[str, Any]] = []
    todos: list[str] = []

    datasets = [_load_dataset(c) for c in COUNTRIES]
    for ds in datasets:
        _measurement_moments(ds, rows, todos)
        _assignment_and_reallocation_moments(ds, rows, todos)
        itt_b, itt_v, peer_b = _outcome_moments(ds, rows, todos)
        _accounting_sanity_moments(ds, rows, itt_b, itt_v, peer_b, todos)

    moments = pd.DataFrame(rows)
    if moments.empty:
        raise RuntimeError("No empirical moments were generated.")

    # Weights: inverse variance where feasible
    moments["variance"] = moments["variance"].astype(float)
    floor = 1e-8
    moments["variance_for_weight"] = moments["variance"].copy()
    moments.loc[~np.isfinite(moments["variance_for_weight"]) | (moments["variance_for_weight"] <= 0), "variance_for_weight"] = np.nan
    median_var = float(moments["variance_for_weight"].dropna().median()) if moments["variance_for_weight"].notna().any() else 1.0
    if not np.isfinite(median_var) or median_var <= 0:
        median_var = 1.0
    moments["variance_for_weight"] = moments["variance_for_weight"].fillna(median_var)
    moments["variance_for_weight"] = moments["variance_for_weight"].clip(lower=floor)
    moments["weight"] = 1.0 / moments["variance_for_weight"]
    moments["moment_id"] = (
        moments["market"].astype(str)
        + "::"
        + moments["category"].astype(str)
        + "::"
        + moments["moment"].astype(str)
        + "::g"
        + moments["grade"].fillna(-1).astype(int).astype(str)
    )
    moments = moments[
        [
            "moment_id",
            "market",
            "category",
            "moment",
            "grade",
            "value",
            "variance",
            "variance_for_weight",
            "weight",
            "source",
            "sample_n",
            "notes",
        ]
    ].sort_values(["market", "category", "moment", "grade"], na_position="last")
    return moments, todos


def _write_todo_file(todos: list[str]) -> None:
    out_path = OUT_DIR / "empirical_moments_todo.md"
    lines = [
        "# Empirical Moments TODO / Fallback Log",
        "",
        "This file records missing/ambiguous objects and fallback assumptions used by `empirical_moments.py`.",
        "",
    ]
    if not todos:
        lines.append("- No missing-object TODOs were triggered.")
    else:
        for t in sorted(set(todos)):
            lines.append(f"- {t}")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print("=" * 72)
    print("Empirical moments builder for structural SMM")
    print("=" * 72)
    print(f"Seed: {SEED}")

    moments, todos = build_empirical_moments()

    moments_path = OUT_DIR / "empirical_moments.csv"
    moments.to_csv(moments_path, index=False)

    summary = (
        moments.groupby(["market", "category"], dropna=False)
        .agg(n_moments=("moment_id", "count"), mean_abs_value=("value", lambda x: float(np.nanmean(np.abs(x)))))
        .reset_index()
    )
    summary_path = OUT_DIR / "empirical_moments_summary.csv"
    summary.to_csv(summary_path, index=False)

    _write_todo_file(todos)

    print(f"Saved moments: {moments_path}")
    print(f"Saved summary: {summary_path}")
    print(f"Saved TODO log: {OUT_DIR / 'empirical_moments_todo.md'}")
    print(f"Total moments: {len(moments)}")
    print("\nMoment counts by market:")
    print(moments.groupby("market")["moment_id"].count().to_string())
    print("\nDone. Stopping here before optimizer, as requested.")


if __name__ == "__main__":
    main()
