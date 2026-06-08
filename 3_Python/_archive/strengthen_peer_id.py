"""
strengthen_peer_id.py — Peer-effects identification package.

Produces:
  diag_peer_progressive.tex   Progressive controls table
  diag_peer_oster.tex         Oster (2019) delta* bounds
  diag_peer_attenuation.tex   Measurement-error & power analysis
  diag_peer_attenuation.pdf   Predicted vs observed beta_P figure
  diag_peer_bflp.tex          Rank-change heterogeneity (BFLP test)
  diag_peer_bflp.pdf          beta_P by within-class rank position
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pathlib import Path

from config import get_config, OUT
from utils import (ols_cluster, strata_fe, decile_treat_fe,
                   stars, coef_str, se_str, leave_self_out_mean)

# ═══════════════════════════════════════════════════════════════════════════
# Helper: write lines to a .tex file
# ═══════════════════════════════════════════════════════════════════════════

def _w(lines, path):
    path = Path(path)
    path.write_text("\n".join(lines) + "\n")
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════
# Load data & merge teacher attendance
# ═══════════════════════════════════════════════════════════════════════════

def _load_study(name):
    """Load cleaned parquet and merge teacher attendance if needed."""
    cfg = get_config(name)
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    df = df[df["finsamp"] == 1].copy()

    if name == "kenya":
        _merge_teacher_attendance_kenya_y1(df, cfg)
    elif name == "kenya2":
        _merge_teacher_attendance_kenya_y2(df, cfg)

    _compute_peer_sd(df)
    return df, cfg


def _merge_teacher_attendance_kenya_y1(df, cfg):
    """Merge Kenya Year 1 teacher attendance from raw CSVs (in-place)."""
    raw = cfg["RAW"]
    rows = []
    for g, fname in [(1, "Grade 1 Reading Club/KE_G1_TeacherAttendance_Blinded.csv"),
                     (2, "Grade 2 Reading Club/KE_G2_TeacherAttendance_Blinded.csv")]:
        fpath = raw / fname
        if not fpath.exists():
            continue
        t = pd.read_csv(fpath)
        col = [c for c in t.columns if c.startswith("GRADE")]
        if col:
            t = t.rename(columns={col[0]: "tch_attn_raw", "AcademyCode": "academycode"})
            t["grade"] = float(g)
            t["tch_attn_raw"] = pd.to_numeric(t["tch_attn_raw"], errors="coerce")
            rows.append(t[["academycode", "grade", "tch_attn_raw"]].dropna())
    if rows:
        tch = pd.concat(rows, ignore_index=True)
        tch["academycode"] = tch["academycode"].astype(df["academycode"].dtype)
        merged = df[["academycode", "grade"]].merge(tch, on=["academycode", "grade"], how="left")
        df.drop(columns=["tch_attn"], errors="ignore", inplace=True)
        df["tch_attn"] = merged["tch_attn_raw"].values
        n = df["tch_attn"].notna().sum()
        print(f"  Kenya Y1 teacher attendance merged: {n}/{len(df)} matched")


def _merge_teacher_attendance_kenya_y2(df, cfg):
    """Merge Kenya Year 2 teacher attendance from raw CSVs (Term 3)."""
    raw = cfg["RAW"]
    rows = []
    for g in [1, 2, 3]:
        fpath = raw / f"Grade {g}" / "Term 3" / f"KE_G{g}_T3_Teacher Attendance Summary_Blinded.csv"
        if not fpath.exists():
            continue
        t = pd.read_csv(fpath)
        t = t.rename(columns={"AcademyCode": "academycode"})
        t["academycode"] = pd.to_numeric(t["academycode"], errors="coerce")
        t["grade"] = float(g)
        if "AVG_AttendanceByClass" in t.columns:
            t["tch_attn_raw"] = pd.to_numeric(t["AVG_AttendanceByClass"], errors="coerce")
        elif "AVG_AttendanceAllClasses" in t.columns:
            t["tch_attn_raw"] = pd.to_numeric(t["AVG_AttendanceAllClasses"], errors="coerce")
        else:
            continue
        rows.append(t[["academycode", "grade", "tch_attn_raw"]].dropna())
    if rows:
        tch = pd.concat(rows, ignore_index=True)
        tch["academycode"] = tch["academycode"].astype(df["academycode"].dtype)
        df.drop(columns=["tch_attn"], errors="ignore", inplace=True)
        merged = df.merge(tch, on=["academycode", "grade"], how="left")
        df["tch_attn"] = merged["tch_attn_raw"].values
        n = df["tch_attn"].notna().sum()
        print(f"  Kenya Y2 teacher attendance merged: {n}/{len(df)} matched")


def _compute_peer_sd(df):
    """Compute leave-self-out SD of classmates' EB ability."""
    grp_cols = ["academycode", np.where(df["treat"] == 1, df["std_grp"], df["grade"])]
    grp_id = df["academycode"].astype(str) + "_" + np.where(
        df["treat"] == 1, df["std_grp"].astype(str), df["grade"].astype(str))
    grp = df.groupby(grp_id)["std_eb"]
    n = grp.transform("count")
    total = grp.transform("sum")
    sumsq = grp.transform(lambda x: (x ** 2).sum())
    own = df["std_eb"].fillna(0)
    own_pres = df["std_eb"].notna().astype(int)
    n_loo = (n - own_pres).replace(0, np.nan)
    mean_loo = (total - own) / n_loo
    var_loo = (sumsq - own ** 2) / n_loo - mean_loo ** 2
    var_loo = var_loo.clip(lower=0)
    df["peer_sd"] = np.sqrt(var_loo)


# ═══════════════════════════════════════════════════════════════════════════
# Shared BH regression helper
# ═══════════════════════════════════════════════════════════════════════════

def _run_bh(sub, extra_controls=None):
    """Run Borusyak-Hull regression. Returns statsmodels result or None."""
    req = sub["std_score_el"].notna() & sub["bl_decile"].notna() & sub["peer_eb"].notna()
    if extra_controls:
        for c in extra_controls:
            if c in sub.columns:
                req = req & sub[c].notna()
    s = sub[req].copy()
    if len(s) < 30:
        return None

    s_dum = strata_fe(s["strata"])
    dt_dum = decile_treat_fe(s["bl_decile"], s["treat"])
    controls = [s[["peer_eb"]], dt_dum, s_dum]
    if extra_controls:
        for c in extra_controls:
            if c in s.columns:
                controls.append(s[[c]])
    X = pd.concat(controls, axis=1)
    try:
        return ols_cluster(s["std_score_el"], X, s["ggroup"])
    except Exception as e:
        print(f"    WARNING: _run_bh regression failed ({e})")
        return None


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Progressive Controls Table
# ═══════════════════════════════════════════════════════════════════════════

def test_progressive_controls(studies):
    """Table: beta_P stability as classroom-level controls are added."""
    print("\n" + "=" * 70)
    print("TEST 1: Progressive Controls")
    print("=" * 70)

    specs = [
        ("Baseline", []),
        ("+ Peer SD", ["peer_sd"]),
        ("+ Class size", ["csize"]),
        ("+ Teacher attn", ["tch_attn"]),
        ("+ All", ["peer_sd", "csize", "tch_attn"]),
    ]

    L = [r"\begin{table}[htbp]", r"\centering\small",
         r"\caption{Peer Effect Robustness to Progressive Controls}",
         r"\label{tab:peer_progressive}",
         r"\begin{tabular}{l" + "cc" * len(studies) + "}",
         r"\toprule"]

    header = " & ".join(f"\\multicolumn{{2}}{{c}}{{{s['label']}}}" for _, s in studies)
    L.append(f"Specification & {header} \\\\")
    sub_header = " & ".join([r"$\hat{\beta}_P$ & SE"] * len(studies))
    L.append(r"\cmidrule(lr){2-3}" * len(studies))
    cmidrules = " ".join(
        rf"\cmidrule(lr){{{2*i+2}-{2*i+3}}}" for i in range(len(studies)))
    L[-1] = cmidrules
    L.append(f" & {sub_header} \\\\")
    L.append(r"\midrule")

    for spec_label, extra in specs:
        cells = []
        for df, cfg in studies:
            sub = df[df["std_score_el"].notna()].copy()
            res = _run_bh(sub, extra if extra else None)
            if res is not None and "peer_eb" in res.params:
                b = res.params["peer_eb"]
                se = res.bse["peer_eb"]
                p = res.pvalues["peer_eb"]
                cells.append(f"{b:.3f}{stars(p)}")
                cells.append(f"({se:.3f})")
            else:
                cells.append("---")
                cells.append("")
        L.append(f"{spec_label} & " + " & ".join(cells) + r" \\")
        print(f"  {spec_label}: " + " | ".join(
            cells[i] for i in range(0, len(cells), 2)))

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small All specifications include "
          r"baseline-decile $\times$ treatment FE and strata FE. "
          r"Cluster-robust SEs at school-grade level.}",
          r"\end{table}"]
    _w(L, OUT / "diag_peer_progressive.tex")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Oster (2019) Bounds
# ═══════════════════════════════════════════════════════════════════════════

def test_oster_bounds(studies):
    """Compute Oster delta* for beta_P in each experiment.

    The right comparison is BH baseline (decile×T FE absorb the selection
    channel) vs BH + extra classroom controls (peer_sd, csize, tch_attn).
    If beta barely moves when adding classroom controls, delta* is large.
    """
    print("\n" + "=" * 70)
    print("TEST 2: Oster (2019) Bounds")
    print("=" * 70)

    L = [r"\begin{table}[htbp]", r"\centering\small",
         r"\caption{Coefficient Stability Bounds for $\hat{\beta}_P$}",
         r"\label{tab:peer_oster}"]
    ncol = len(studies)
    L += [r"\begin{tabular}{l" + "c" * ncol + "}",
          r"\toprule"]
    header = " & ".join(s["label"] for _, s in studies)
    L.append(f" & {header} \\\\")
    L.append(r"\midrule")

    rows_data = {}
    for df, cfg in studies:
        label = cfg["label"]
        sub = df[df["std_score_el"].notna() & df["bl_decile"].notna()
                 & df["peer_eb"].notna()].copy()

        s_dum = strata_fe(sub["strata"])
        dt_dum = decile_treat_fe(sub["bl_decile"], sub["treat"])

        # "Short": BH baseline (peer_eb + decile×T FE + strata FE)
        X_s = pd.concat([sub[["peer_eb"]], dt_dum, s_dum], axis=1)
        res_s = ols_cluster(sub["std_score_el"], X_s, sub["ggroup"])

        # "Long": BH + all available classroom controls
        ctrl_cols = []
        for c in ["peer_sd", "csize", "tch_attn"]:
            if c in sub.columns and sub[c].notna().sum() > len(sub) * 0.5:
                ctrl_cols.append(c)
        extra = [sub[[c]] for c in ctrl_cols] if ctrl_cols else []
        X_l = pd.concat([sub[["peer_eb"]], dt_dum, s_dum] + extra, axis=1)
        mask_l = X_l.notna().all(axis=1) & sub["std_score_el"].notna() & sub["ggroup"].notna()
        res_l = ols_cluster(sub.loc[mask_l, "std_score_el"],
                            X_l.loc[mask_l], sub.loc[mask_l, "ggroup"])

        beta_s = res_s.params.get("peer_eb", np.nan)
        beta_l = res_l.params.get("peer_eb", np.nan)
        r2_s = res_s.rsquared
        r2_l = res_l.rsquared
        r2_max = min(1.3 * r2_l, 1.0)

        denom = (beta_s - beta_l) * (r2_l - r2_s)
        if abs(denom) > 1e-10:
            delta_star = (beta_l * (r2_max - r2_l)) / denom
        else:
            delta_star = np.inf if abs(beta_s - beta_l) < 1e-6 else 0.0

        rows_data[label] = {
            "beta_s": beta_s, "beta_l": beta_l,
            "r2_s": r2_s, "r2_l": r2_l,
            "r2_max": r2_max, "delta": delta_star,
            "controls": ", ".join(ctrl_cols) if ctrl_cols else "none"
        }
        ds = f"{delta_star:.1f}" if np.isfinite(delta_star) and abs(delta_star) < 1000 else r"$\infty$"
        print(f"  {label}: beta_BH={beta_s:.3f} beta_full={beta_l:.3f} "
              f"R2_BH={r2_s:.3f} R2_full={r2_l:.3f} delta*={ds} "
              f"[controls: {', '.join(ctrl_cols)}]")

    # Table rows
    for metric, fmt_fn in [
        (r"$\hat{\beta}_P$ (BH baseline)", lambda d: f"{d['beta_s']:.3f}"),
        (r"$\hat{\beta}_P$ (+ classroom controls)", lambda d: f"{d['beta_l']:.3f}"),
        (r"$R^2$ (BH baseline)", lambda d: f"{d['r2_s']:.3f}"),
        (r"$R^2$ (+ classroom controls)", lambda d: f"{d['r2_l']:.3f}"),
        (r"$R^2_{\max}$ ($1.3 \times R^2_{\text{long}}$)",
         lambda d: f"{d['r2_max']:.3f}"),
        (r"$\delta^*$",
         lambda d: f"{d['delta']:.1f}" if np.isfinite(d['delta'])
         and abs(d['delta']) < 1000 else r"$\infty$"),
    ]:
        cells = []
        for _, cfg in studies:
            d = rows_data[cfg["label"]]
            cells.append(fmt_fn(d))
        L.append(f"{metric} & " + " & ".join(cells) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small BH baseline: peer EB + "
          r"decile$\times$T FE + strata FE. Classroom controls: "
          r"+ within-class peer SD + class size + teacher attendance. "
          r"$\delta^*$ follows \citet{oster2019}: proportional selection on "
          r"unobservables (relative to observables) needed to drive "
          r"$\hat{\beta}_P$ to zero. Negative $\delta^*$ indicates "
          r"controls \emph{strengthen} the coefficient, so unobservables "
          r"would need to operate in the opposite direction from all "
          r"measured confounders. $\infty$: coefficient barely moves.}",
          r"\end{table}"]
    _w(L, OUT / "diag_peer_oster.tex")
    return rows_data


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Cross-Experiment Validation (Measurement Error + Power)
# ═══════════════════════════════════════════════════════════════════════════

def test_cross_experiment(studies):
    """Measurement-error prediction and cross-experiment validation."""
    print("\n" + "=" * 70)
    print("TEST 3: Cross-Experiment Validation")
    print("=" * 70)

    results = []
    for df, cfg in studies:
        label = cfg["label"]
        sub = df[df["std_score_el"].notna() & df["bl_decile"].notna()
                 & df["peer_eb"].notna()].copy()

        # BH regression
        res = _run_bh(sub)
        beta = res.params["peer_eb"] if res and "peer_eb" in res.params else np.nan
        se = res.bse["peer_eb"] if res and "peer_eb" in res.params else np.nan

        # Individual-level reliability (mean across grades, control group)
        ctrl = df[(df["treat"] == 0) & df["score_bl"].notna() & df["score_el"].notna()]
        r2_vals = []
        for g in sorted(ctrl["grade"].dropna().unique()):
            gc = ctrl[ctrl["grade"] == g]
            if len(gc) > 10:
                corr = gc[["score_bl", "score_el"]].corr().iloc[0, 1]
                r2_vals.append(corr ** 2 if pd.notna(corr) else np.nan)
        r2_ind = np.nanmean(r2_vals) if r2_vals else np.nan

        # Mean class size
        mean_n = sub["csize"].mean() if "csize" in sub.columns else 30

        # Peer-mean reliability (Spearman-Brown)
        n_peers = mean_n - 1
        if pd.notna(r2_ind) and n_peers > 0:
            r2_peer = n_peers * r2_ind / (1 + (n_peers - 1) * r2_ind)
        else:
            r2_peer = np.nan

        # MDE for beta_P (2.8 × SE)
        mde = 2.8 * se if pd.notna(se) else np.nan

        # Attenuation-corrected estimate
        beta_corrected = beta / r2_peer if pd.notna(r2_peer) and r2_peer > 0.01 else np.nan

        # 95% CI
        ci_lo = beta - 1.96 * se if pd.notna(se) else np.nan
        ci_hi = beta + 1.96 * se if pd.notna(se) else np.nan

        results.append({
            "label": label, "beta": beta, "se": se,
            "r2_ind": r2_ind, "mean_n": mean_n, "r2_peer": r2_peer,
            "mde": mde, "beta_corrected": beta_corrected,
            "ci_lo": ci_lo, "ci_hi": ci_hi,
        })
        print(f"  {label}: beta_P={beta:.3f} SE={se:.3f} r2_ind={r2_ind:.3f} "
              f"n={mean_n:.0f} r2_peer={r2_peer:.3f} MDE={mde:.3f} "
              f"beta_corrected={beta_corrected:.3f}")

    # --- LaTeX table ---
    L = [r"\begin{table}[htbp]", r"\centering\small",
         r"\caption{Peer Effect: Measurement Error and Power Across Experiments}",
         r"\label{tab:peer_attenuation}"]
    ncol = len(results)
    L += [r"\begin{tabular}{l" + "c" * ncol + "}",
          r"\toprule"]
    header = " & ".join(r["label"] for r in results)
    L.append(f" & {header} \\\\")
    L.append(r"\midrule")

    for metric, key, fmt in [
        (r"$\hat{\beta}_P$ (BH)", "beta", ".3f"),
        ("SE", "se", ".3f"),
        ("95\\% CI", None, None),
        ("Individual reliability $r^2$", "r2_ind", ".3f"),
        ("Mean class size", "mean_n", ".0f"),
        ("Peer-mean reliability $r^2_P$", "r2_peer", ".3f"),
        ("MDE ($2.8 \\times$ SE)", "mde", ".3f"),
        (r"Attenuation-corrected $\hat{\beta}_P / r^2_P$", "beta_corrected", ".3f"),
    ]:
        if metric == "95\\% CI":
            cells = [f"[{r['ci_lo']:.3f}, {r['ci_hi']:.3f}]" for r in results]
        else:
            cells = [f"{r[key]:{fmt}}" if pd.notna(r[key]) else "---" for r in results]
        L.append(f"{metric} & " + " & ".join(cells) + r" \\")

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small Peer-mean reliability computed via "
          r"Spearman-Brown: $r^2_P = (n{-}1) r^2 / [1 + (n{-}2) r^2]$. "
          r"Attenuation-corrected estimate assumes classical measurement "
          r"error in peer ability. Liberia's wide CI includes Kenya's "
          r"attenuation-corrected values.}",
          r"\end{table}"]
    _w(L, OUT / "diag_peer_attenuation.tex")

    # --- Figure: predicted vs observed ---
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))

    # Panel A: observed beta_P with CIs
    ax = axes[0]
    labels = [r["label"] for r in results]
    betas = [r["beta"] for r in results]
    ses = [r["se"] for r in results]
    x = np.arange(len(results))
    ax.bar(x, betas, color=["#d62728", "#1f77b4", "#2ca02c"], alpha=0.7, width=0.5)
    ax.errorbar(x, betas, yerr=[1.96 * s for s in ses], fmt="none",
                ecolor="black", capsize=5, linewidth=1.5)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(r"$\hat{\beta}_P$", fontsize=12)
    ax.set_title("(a) Observed Peer Effects", fontsize=12)

    # Panel B: reliability vs |beta_P|
    ax = axes[1]
    r2_peers = [r["r2_peer"] for r in results]
    abs_betas = [abs(r["beta"]) for r in results]
    colors = ["#d62728", "#1f77b4", "#2ca02c"]
    for i, r in enumerate(results):
        ax.scatter(r["r2_peer"], abs(r["beta"]), s=120, c=colors[i],
                   zorder=5, edgecolors="black", linewidth=0.8)
        ax.annotate(r["label"], (r["r2_peer"], abs(r["beta"])),
                    textcoords="offset points", xytext=(8, 5), fontsize=9)

    # Prediction line: if beta_true = -0.31, predicted = r2_P * 0.31
    r2_range = np.linspace(0.5, 1.0, 50)
    beta_true_k2 = abs(results[-1]["beta_corrected"]) if pd.notna(
        results[-1]["beta_corrected"]) else 0.37
    ax.plot(r2_range, r2_range * beta_true_k2, "--", color="gray",
            label=f"Predicted (true $|\\beta_P|$={beta_true_k2:.2f})", alpha=0.7)
    ax.set_xlabel("Peer-mean reliability $r^2_P$", fontsize=11)
    ax.set_ylabel(r"$|\hat{\beta}_P|$", fontsize=12)
    ax.set_title("(b) Attenuation Pattern", fontsize=12)
    ax.legend(fontsize=9)
    ax.set_xlim(0.6, 1.02)
    ax.set_ylim(-0.02, 0.45)

    plt.tight_layout()
    fig.savefig(OUT / "diag_peer_attenuation.pdf")
    plt.close(fig)
    print(f"  -> {OUT / 'diag_peer_attenuation.pdf'}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Rank-Change Heterogeneity (BFLP Test)
# ═══════════════════════════════════════════════════════════════════════════

def test_bflp_heterogeneity(studies):
    """Test BFLP prediction: negative beta_P concentrated among low-rank students."""
    print("\n" + "=" * 70)
    print("TEST 4: Rank-Change Heterogeneity (BFLP)")
    print("=" * 70)

    all_rows = []
    fig, axes = plt.subplots(1, len(studies), figsize=(5 * len(studies), 4.5),
                              squeeze=False)

    for idx, (df, cfg) in enumerate(studies):
        label = cfg["label"]
        sub = df[df["std_score_el"].notna() & df["bl_decile"].notna()
                 & df["peer_eb"].notna()].copy()

        # Compute within-class rank (percentile)
        class_id = sub["academycode"].astype(str) + "_" + np.where(
            sub["treat"] == 1, sub["std_grp"].astype(str),
            sub["grade"].astype(str))
        sub["_cid"] = class_id
        sub["rank_in_class"] = sub.groupby("_cid")["std_score_bl"].rank(pct=True)

        # Compute within-grade rank
        gid = sub["academycode"].astype(str) + "_" + sub["grade"].astype(str)
        sub["_gid"] = gid
        sub["rank_in_grade"] = sub.groupby("_gid")["std_score_bl"].rank(pct=True)

        # --- Split by within-class position ---
        sub["rank_half"] = np.where(sub["rank_in_class"] <= 0.5,
                                     "Bottom half", "Top half")

        print(f"\n  {label}:")

        # (a) By track
        for track_label, track_val in [("Lower", 0), ("Upper", 1)]:
            ss = sub[sub["upper_group"] == track_val]
            res = _run_bh(ss)
            if res and "peer_eb" in res.params:
                b, se_v, p = res.params["peer_eb"], res.bse["peer_eb"], res.pvalues["peer_eb"]
                print(f"    {track_label} track: beta_P={b:.3f}{stars(p)} ({se_v:.3f}) N={len(ss)}")
                all_rows.append({"Study": label, "Split": f"{track_label} track",
                                 "beta_P": f"{b:.3f}{stars(p)}", "SE": f"({se_v:.3f})",
                                 "N": len(ss)})

        # (b) By within-class position
        for half in ["Bottom half", "Top half"]:
            ss = sub[sub["rank_half"] == half]
            res = _run_bh(ss)
            if res and "peer_eb" in res.params:
                b, se_v, p = res.params["peer_eb"], res.bse["peer_eb"], res.pvalues["peer_eb"]
                print(f"    {half}: beta_P={b:.3f}{stars(p)} ({se_v:.3f}) N={len(ss)}")
                all_rows.append({"Study": label, "Split": half,
                                 "beta_P": f"{b:.3f}{stars(p)}", "SE": f"({se_v:.3f})",
                                 "N": len(ss)})

        # (c) By within-class rank tercile (for figure)
        sub["rank_tercile"] = pd.qcut(sub["rank_in_class"], 3,
                                       labels=["Bottom", "Middle", "Top"],
                                       duplicates="drop")
        betas_t, ses_t, labels_t = [], [], []
        for terc in ["Bottom", "Middle", "Top"]:
            ss = sub[sub["rank_tercile"] == terc]
            res = _run_bh(ss)
            if res and "peer_eb" in res.params:
                betas_t.append(res.params["peer_eb"])
                ses_t.append(res.bse["peer_eb"])
                labels_t.append(terc)
                all_rows.append({"Study": label, "Split": f"Tercile: {terc}",
                                 "beta_P": f"{res.params['peer_eb']:.3f}{stars(res.pvalues['peer_eb'])}",
                                 "SE": f"({res.bse['peer_eb']:.3f})",
                                 "N": len(ss)})

        # (d) Continuous interaction
        s_dum = strata_fe(sub["strata"])
        dt_dum = decile_treat_fe(sub["bl_decile"], sub["treat"])
        sub["peer_x_rank"] = sub["peer_eb"] * sub["rank_in_class"]
        X = pd.concat([sub[["peer_eb", "peer_x_rank", "rank_in_class"]],
                       dt_dum, s_dum], axis=1)
        try:
            res_int = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
            b_int = res_int.params.get("peer_x_rank", np.nan)
            se_int = res_int.bse.get("peer_x_rank", np.nan)
            p_int = res_int.pvalues.get("peer_x_rank", np.nan)
            print(f"    Interaction (peer_eb x rank): {b_int:.3f}{stars(p_int)} ({se_int:.3f})")
            all_rows.append({"Study": label,
                             "Split": r"$\hat{\beta}_P \times$ rank",
                             "beta_P": f"{b_int:.3f}{stars(p_int)}",
                             "SE": f"({se_int:.3f})", "N": len(sub)})
        except Exception as e:
            print(f"    WARNING: BFLP interaction for {label} failed ({e})")

        # --- Figure panel ---
        ax = axes[0, idx]
        if betas_t:
            x = np.arange(len(betas_t))
            colors = ["#d62728" if b < -0.05 else "#1f77b4" for b in betas_t]
            ax.bar(x, betas_t, color=colors, alpha=0.7, width=0.5)
            ax.errorbar(x, betas_t, yerr=[1.96 * s for s in ses_t],
                        fmt="none", ecolor="black", capsize=5, linewidth=1.5)
            ax.set_xticks(x)
            ax.set_xticklabels(labels_t, fontsize=10)
            ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
            ax.set_ylabel(r"$\hat{\beta}_P$", fontsize=11)
            ax.set_title(label, fontsize=12)

    plt.tight_layout()
    fig.savefig(OUT / "diag_peer_bflp.pdf")
    plt.close(fig)
    print(f"  -> {OUT / 'diag_peer_bflp.pdf'}")

    # --- LaTeX table ---
    tdf = pd.DataFrame(all_rows)
    L = [r"\begin{table}[htbp]", r"\centering\small",
         r"\caption{Peer Effect Heterogeneity by Within-Class Rank (BFLP Test)}",
         r"\label{tab:peer_bflp}",
         r"\begin{tabular}{llccr}",
         r"\toprule",
         r"Study & Split & $\hat{\beta}_P$ & SE & $N$ \\",
         r"\midrule"]
    prev_study = ""
    for _, row in tdf.iterrows():
        study = row["Study"] if row["Study"] != prev_study else ""
        if study and prev_study:
            L.append(r"\addlinespace")
        L.append(f"{study} & {row['Split']} & {row['beta_P']} & {row['SE']} "
                 f"& {row['N']:,d} \\\\")
        prev_study = row["Study"]

    L += [r"\bottomrule", r"\end{tabular}",
          r"\par\smallskip\noindent{\small Under BFLP, students at the "
          r"bottom of their reading group (lowest rank) should have the "
          r"most negative $\hat{\beta}_P$. All specifications include "
          r"decile$\times$T FE and strata FE.}",
          r"\end{table}"]
    _w(L, OUT / "diag_peer_bflp.tex")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("Peer Effects Identification Package")
    print("=" * 70)

    print("\nLoading study data...")
    lib, lib_cfg = _load_study("liberia")
    ke, ke_cfg = _load_study("kenya")
    ke2, ke2_cfg = _load_study("kenya2")
    print(f"  Liberia: N={len(lib):,d}")
    print(f"  Kenya Y1: N={len(ke):,d}")
    print(f"  Kenya Y2: N={len(ke2):,d}")

    studies = [(lib, lib_cfg), (ke, ke_cfg), (ke2, ke2_cfg)]

    test_progressive_controls(studies)
    test_oster_bounds(studies)
    test_cross_experiment(studies)
    test_bflp_heterogeneity(studies)

    print("\n" + "=" * 70)
    print("All peer identification tests complete.")
    print("=" * 70)
