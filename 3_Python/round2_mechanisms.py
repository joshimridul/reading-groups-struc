"""
round2_mechanisms.py
====================
Round 2 mechanism tests for the ability-grouping paper.

Produces:
  R2.1  Liberia ITT heterogeneity by distance-to-cutoff
  R2.2  Liberia upper/lower track effects by baseline ability bins
  R2.3  ITT controlling for class size (all studies)
  R2.4  Liberia predicted misclassification vs treatment harm (figure)
  R2.5  Kenya peer effects robustness (class-size, alt definitions, by grade)
  R2.6  Kenya reduced-form build-up before formal BH
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats as sp_stats

from config import get_config, OUT
from utils import ols_cluster, coef_str, se_str, stars, strata_fe, decile_treat_fe

np.random.seed(42)

STUDIES = [("liberia", "Liberia"), ("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]


def _load(country):
    cfg = get_config(country)
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    return df[df["finsamp"] == 1].copy(), cfg


# ═══════════════════════════════════════════════════════════════════════════════
# R2.1  Liberia: ITT heterogeneity by distance-to-cutoff
# ═══════════════════════════════════════════════════════════════════════════════
def r2_cutoff_heterogeneity():
    print("\n" + "=" * 70)
    print("R2.1: Liberia ITT heterogeneity by distance-to-cutoff")
    print("=" * 70)

    df, cfg = _load("liberia")
    an = df[df["std_score_el"].notna()].copy()

    an["abs_dist"] = an["dist_from_cutoff"].abs()
    an["dist_quintile"] = pd.qcut(an["abs_dist"], q=5, labels=False,
                                   duplicates="drop") + 1

    rows = []
    for q in sorted(an["dist_quintile"].dropna().unique()):
        sub = an[an["dist_quintile"] == q]
        mn_dist = sub["abs_dist"].mean()
        fe = strata_fe(sub["strata"])
        X = pd.concat([sub[["treat", "std_eb"]], fe], axis=1)
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        rows.append(dict(Q=int(q), mean_dist=mn_dist,
                         coef=res.params["treat"], se=res.bse["treat"],
                         p=res.pvalues["treat"], N=len(sub)))
        print(f"  Q{int(q)} (|d|={mn_dist:.1f}): β={res.params['treat']:.3f} "
              f"({res.bse['treat']:.3f}){stars(res.pvalues['treat'])}  N={len(sub)}")

    rdf = pd.DataFrame(rows)

    # Continuous interaction: T × abs_dist
    an["treat_x_absdist"] = an["treat"] * an["abs_dist"]
    fe = strata_fe(an["strata"])
    X = pd.concat([an[["treat", "treat_x_absdist", "abs_dist", "std_eb"]], fe], axis=1)
    res_int = ols_cluster(an["std_score_el"], X, an["ggroup"])
    print(f"\n  Continuous interaction T×|d|: β={res_int.params['treat_x_absdist']:.4f} "
          f"({res_int.bse['treat_x_absdist']:.4f}) p={res_int.pvalues['treat_x_absdist']:.3f}")
    print(f"  (Positive means harm concentrated near cutoff)")

    # Figure
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(rdf["mean_dist"], rdf["coef"], yerr=1.96 * rdf["se"],
                fmt="o-", color="steelblue", capsize=5, lw=2, ms=8)
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Mean |distance from cutoff| in quintile")
    ax.set_ylabel("ITT effect (std. endline)")
    ax.set_title("Treatment Effect by Proximity to Assignment Cutoff (Liberia)")
    fig.tight_layout()
    path = OUT / "diag_r2_cutoff_het.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{ITT Heterogeneity by Distance from Assignment Cutoff (Liberia)}",
        r"\label{tab:cutoff_het}",
        r"\begin{tabular}{lccccc}", r"\toprule",
        r"Quintile & Mean $|s-c|$ & ITT & SE & $p$ & $N$ \\", r"\midrule"]
    for _, r in rdf.iterrows():
        tex.append(f"Q{int(r['Q'])} & {r['mean_dist']:.1f} & "
                   f"{r['coef']:.3f}{stars(r['p'])} & ({r['se']:.3f}) & "
                   f"{r['p']:.3f} & {int(r['N']):,d} \\\\")
    tex.append(r"\midrule")
    b_int = res_int.params["treat_x_absdist"]
    se_int = res_int.bse["treat_x_absdist"]
    p_int = res_int.pvalues["treat_x_absdist"]
    tex.append(f"T $\\times$ $|s-c|$ (continuous) & & "
               f"{b_int:.4f}{stars(p_int)} & ({se_int:.4f}) & {p_int:.3f} & "
               f"{len(an):,d} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Quintiles of absolute distance from "
            r"grade-specific assignment cutoff. OLS with strata FE, EB ability control, "
            r"cluster-robust SEs. Positive interaction coefficient means harm is "
            r"concentrated near the cutoff.}", r"\end{table}"]
    path_tex = OUT / "diag_r2_cutoff_het.tex"
    path_tex.write_text("\n".join(tex))
    print(f"  -> {path_tex}")


# ═══════════════════════════════════════════════════════════════════════════════
# R2.2  Liberia: Upper/lower track by baseline ability bins
# ═══════════════════════════════════════════════════════════════════════════════
def r2_track_ability_bins():
    print("\n" + "=" * 70)
    print("R2.2: Liberia upper/lower track effects by baseline ability bins")
    print("=" * 70)

    df, cfg = _load("liberia")
    an = df[df["std_score_el"].notna()].copy()

    rows = []
    for track_label, track_val in [("Lower", 0), ("Upper", 1)]:
        sub = an[an["upper_group"] == track_val].copy()
        sub["ability_tercile"] = pd.qcut(sub["std_score_bl"], q=3,
                                          labels=["Bottom", "Middle", "Top"],
                                          duplicates="drop")
        for terc in ["Bottom", "Middle", "Top"]:
            ts = sub[sub["ability_tercile"] == terc]
            if len(ts) < 20 or ts["treat"].nunique() < 2:
                continue
            fe = strata_fe(ts["strata"])
            X = pd.concat([ts[["treat", "std_eb"]], fe], axis=1)
            res = ols_cluster(ts["std_score_el"], X, ts["ggroup"])
            rows.append(dict(Track=track_label, Tercile=terc,
                             coef=res.params["treat"], se=res.bse["treat"],
                             p=res.pvalues["treat"], N=len(ts)))
            print(f"  {track_label} track, {terc}: β={res.params['treat']:.3f} "
                  f"({res.bse['treat']:.3f}){stars(res.pvalues['treat'])}  N={len(ts)}")

    rdf = pd.DataFrame(rows)

    # Figure: grouped bar chart
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for idx, track in enumerate(["Lower", "Upper"]):
        ax = axes[idx]
        sub = rdf[rdf["Track"] == track]
        x = np.arange(len(sub))
        colors = ["#4C72B0" if p > 0.1 else "#DD8452" if p > 0.05
                   else "#C44E52" for p in sub["p"]]
        ax.bar(x, sub["coef"], yerr=1.96 * sub["se"], capsize=5,
               color=colors, alpha=0.8, edgecolor="white")
        ax.set_xticks(x)
        ax.set_xticklabels(sub["Tercile"])
        ax.axhline(0, color="gray", ls="--", lw=1)
        ax.set_title(f"{track} Track")
        ax.set_xlabel("Baseline ability tercile (within track)")
        if idx == 0:
            ax.set_ylabel("ITT (std. endline)")
    fig.suptitle("Treatment Effects by Track and Ability (Liberia)", fontsize=13)
    fig.tight_layout()
    path = OUT / "diag_r2_track_bins.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Treatment Effects by Track and Baseline Ability Tercile (Liberia)}",
        r"\label{tab:track_bins}",
        r"\begin{tabular}{llcccc}", r"\toprule",
        r"Track & Ability bin & ITT & SE & $p$ & $N$ \\", r"\midrule"]
    prev_track = ""
    for _, r in rdf.iterrows():
        tlab = r["Track"] if r["Track"] != prev_track else ""
        tex.append(f"{tlab} & {r['Tercile']} & "
                   f"{r['coef']:.3f}{stars(r['p'])} & ({r['se']:.3f}) & "
                   f"{r['p']:.3f} & {int(r['N']):,d} \\\\")
        prev_track = r["Track"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Within-track ability terciles. "
            r"OLS with strata FE, EB control, cluster-robust SEs. If misclassification "
            r"drives harm, the upper-track bottom tercile (students most likely "
            r"misclassified into a too-advanced group) should show the largest "
            r"negative effect.}", r"\end{table}"]
    path_tex = OUT / "diag_r2_track_bins.tex"
    path_tex.write_text("\n".join(tex))
    print(f"  -> {path_tex}")


# ═══════════════════════════════════════════════════════════════════════════════
# R2.3  ITT controlling for class size (all studies)
# ═══════════════════════════════════════════════════════════════════════════════
def r2_classsize_control():
    print("\n" + "=" * 70)
    print("R2.3: ITT with and without class-size control")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        an = df[df["std_score_el"].notna() & df["csize"].notna()].copy()

        fe = strata_fe(an["strata"])

        # Without class size
        X1 = pd.concat([an[["treat", "std_eb"]], fe], axis=1)
        res1 = ols_cluster(an["std_score_el"], X1, an[cfg["cluster_var"]])

        # With class size
        X2 = pd.concat([an[["treat", "std_eb", "csize"]], fe], axis=1)
        res2 = ols_cluster(an["std_score_el"], X2, an[cfg["cluster_var"]])

        # Upper/lower interaction without class size
        an["treat_x_upper"] = an["treat"] * an["upper_group"]
        X3 = pd.concat([an[["treat", "treat_x_upper", "upper_group", "std_eb"]], fe],
                        axis=1)
        res3 = ols_cluster(an["std_score_el"], X3, an[cfg["cluster_var"]])

        # Upper/lower interaction with class size
        X4 = pd.concat([an[["treat", "treat_x_upper", "upper_group", "std_eb", "csize"]],
                         fe], axis=1)
        res4 = ols_cluster(an["std_score_el"], X4, an[cfg["cluster_var"]])

        rows.append(dict(
            Study=label, N=len(an),
            b_no=f"{res1.params['treat']:.3f}{stars(res1.pvalues['treat'])}",
            se_no=f"({res1.bse['treat']:.3f})",
            b_cs=f"{res2.params['treat']:.3f}{stars(res2.pvalues['treat'])}",
            se_cs=f"({res2.bse['treat']:.3f})",
            b_csize=f"{res2.params['csize']:.4f}{stars(res2.pvalues['csize'])}",
            txu_no=f"{res3.params['treat_x_upper']:.3f}{stars(res3.pvalues['treat_x_upper'])}",
            txu_cs=f"{res4.params['treat_x_upper']:.3f}{stars(res4.pvalues['treat_x_upper'])}"))

        print(f"  {label}:")
        print(f"    ITT no csize: {coef_str(res1, 'treat')} {se_str(res1, 'treat')}")
        print(f"    ITT w/ csize: {coef_str(res2, 'treat')} {se_str(res2, 'treat')}  "
              f"csize: {coef_str(res2, 'csize')}")
        print(f"    T×Upper no csize: {coef_str(res3, 'treat_x_upper')} "
              f"{se_str(res3, 'treat_x_upper')}")
        print(f"    T×Upper w/ csize: {coef_str(res4, 'treat_x_upper')} "
              f"{se_str(res4, 'treat_x_upper')}")

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{ITT With and Without Class-Size Control}",
        r"\label{tab:itt_classsize}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r" & \multicolumn{2}{c}{Average ITT} & \multicolumn{2}{c}{$T \times$ Upper} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
        r" & No control & + Class size & No control & + Class size \\", r"\midrule"]
    for r in rows:
        tex.append(f"{r['Study']} & {r['b_no']} & {r['b_cs']} & "
                   f"{r['txu_no']} & {r['txu_cs']} \\\\")
        tex.append(f" & {r['se_no']} & {r['se_cs']} & & \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small All specifications include strata FE "
            r"and EB ability control. Class size is number of students in the "
            r"student's classroom (grade$\times$stream for treatment, "
            r"grade for control). Cluster-robust SEs at school-grade level.}",
            r"\end{table}"]
    path = OUT / "diag_r2_classsize_ctrl.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R2.4  Liberia: Predicted misclassification × treatment harm
# ═══════════════════════════════════════════════════════════════════════════════
def r2_misclass_harm():
    print("\n" + "=" * 70)
    print("R2.4: Predicted misclassification vs. treatment harm (Liberia)")
    print("=" * 70)

    df, cfg = _load("liberia")
    an = df[df["std_score_el"].notna()].copy()
    cutoffs = cfg["cutoffs"]

    s_mean = an["score_bl"].mean()
    s_std = an["score_bl"].std()

    r2_pool = an.loc[an["treat"] == 0].pipe(
        lambda d: np.corrcoef(d.loc[d["score_el"].notna(), "score_bl"],
                               d.loc[d["score_el"].notna(), "score_el"])[0, 1] ** 2)
    sigma_cond = np.sqrt(1 - r2_pool) * s_std

    an["theta_eb"] = s_mean + r2_pool * (an["score_bl"] - s_mean)
    an["pr_misclass"] = an.apply(
        lambda r: sp_stats.norm.cdf(cutoffs.get(int(r["grade"]), 999),
                                     loc=r["theta_eb"], scale=sigma_cond)
        if r["score_bl"] >= cutoffs.get(int(r["grade"]), 999)
        else 1 - sp_stats.norm.cdf(cutoffs.get(int(r["grade"]), 999),
                                     loc=r["theta_eb"], scale=sigma_cond),
        axis=1)

    an["misclass_quintile"] = pd.qcut(an["pr_misclass"], q=5, labels=False,
                                       duplicates="drop") + 1

    rows = []
    for q in sorted(an["misclass_quintile"].dropna().unique()):
        sub = an[an["misclass_quintile"] == q]
        mn_pr = sub["pr_misclass"].mean()
        fe = strata_fe(sub["strata"])
        X = pd.concat([sub[["treat", "std_eb"]], fe], axis=1)
        res = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        rows.append(dict(Q=int(q), mean_pr=mn_pr,
                         coef=res.params["treat"], se=res.bse["treat"],
                         p=res.pvalues["treat"], N=len(sub)))
        print(f"  Q{int(q)} (Pr(mis)={mn_pr:.2f}): β={res.params['treat']:.3f} "
              f"({res.bse['treat']:.3f}){stars(res.pvalues['treat'])}  N={len(sub)}")

    rdf = pd.DataFrame(rows)

    # Continuous interaction: T × Pr(mis)
    an["treat_x_misclass"] = an["treat"] * an["pr_misclass"]
    fe = strata_fe(an["strata"])
    X = pd.concat([an[["treat", "treat_x_misclass", "pr_misclass", "std_eb"]], fe], axis=1)
    res_int = ols_cluster(an["std_score_el"], X, an["ggroup"])
    print(f"\n  T×Pr(mis) interaction: {res_int.params['treat_x_misclass']:.3f} "
          f"({res_int.bse['treat_x_misclass']:.3f}) "
          f"p={res_int.pvalues['treat_x_misclass']:.3f}")
    print(f"  (Negative means higher misclassification probability → worse treatment effect)")

    # Figure: two panels
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    ax.errorbar(rdf["mean_pr"], rdf["coef"], yerr=1.96 * rdf["se"],
                fmt="o-", color="steelblue", capsize=5, lw=2, ms=8)
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Mean Pr(misclassified) in quintile")
    ax.set_ylabel("ITT (std. endline)")
    ax.set_title("(a) Treatment Effect by Misclassification Risk")

    ax = axes[1]
    for track, color, marker in [(0, "#4C72B0", "o"), (1, "#C44E52", "s")]:
        sub_t = an[an["upper_group"] == track].copy()
        sub_t["mq"] = pd.qcut(sub_t["pr_misclass"], q=5, labels=False,
                                duplicates="drop") + 1
        pts = []
        for q in sorted(sub_t["mq"].dropna().unique()):
            qs = sub_t[sub_t["mq"] == q]
            mn_pr = qs["pr_misclass"].mean()
            if qs["treat"].nunique() < 2 or len(qs) < 20:
                continue
            fe_t = strata_fe(qs["strata"])
            X_t = pd.concat([qs[["treat", "std_eb"]], fe_t], axis=1)
            try:
                res_t = ols_cluster(qs["std_score_el"], X_t, qs["ggroup"])
                pts.append((mn_pr, res_t.params["treat"], res_t.bse["treat"]))
            except Exception as e:
                print(f"      Peer bin {mn_pr:.2f}: SKIPPED ({e})")
        if pts:
            pts = pd.DataFrame(pts, columns=["pr", "b", "se"])
            tlabel = "Lower track" if track == 0 else "Upper track"
            ax.errorbar(pts["pr"], pts["b"], yerr=1.96 * pts["se"],
                        fmt=f"{marker}-", color=color, capsize=4, lw=1.5,
                        ms=7, label=tlabel)
    ax.axhline(0, color="gray", ls="--", lw=1)
    ax.set_xlabel("Mean Pr(misclassified)")
    ax.set_ylabel("ITT (std. endline)")
    ax.set_title("(b) By Track")
    ax.legend()

    fig.suptitle("Misclassification Risk and Treatment Harm (Liberia)", fontsize=13)
    fig.tight_layout()
    path = OUT / "diag_r2_misclass_harm.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R2.5  Kenya: Peer effects robustness
# ═══════════════════════════════════════════════════════════════════════════════
def r2_peer_robustness():
    print("\n" + "=" * 70)
    print("R2.5: Kenya peer effects robustness")
    print("=" * 70)

    for country, label in [("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]:
        df, cfg = _load(country)
        an = df[df["std_score_el"].notna() & df["bl_decile"].notna()].copy()

        print(f"\n  --- {label} ---")

        # Baseline BH spec
        sub_base = an[an["peer_eb"].notna()].copy()
        fe_s = strata_fe(sub_base["strata"])
        fe_dt = decile_treat_fe(sub_base["bl_decile"], sub_base["treat"])
        X0 = pd.concat([sub_base[["peer_eb"]], fe_dt, fe_s], axis=1)
        res0 = ols_cluster(sub_base["std_score_el"], X0, sub_base["ggroup"])
        print(f"    [Baseline] β_P(EB) = {coef_str(res0, 'peer_eb')} "
              f"{se_str(res0, 'peer_eb')}")

        # + class size
        sub_cs = an[an["peer_eb"].notna() & an["csize"].notna()].copy()
        fe_s2 = strata_fe(sub_cs["strata"])
        fe_dt2 = decile_treat_fe(sub_cs["bl_decile"], sub_cs["treat"])
        X1 = pd.concat([sub_cs[["peer_eb", "csize"]], fe_dt2, fe_s2], axis=1)
        res1 = ols_cluster(sub_cs["std_score_el"], X1, sub_cs["ggroup"])
        print(f"    [+CSize]   β_P(EB) = {coef_str(res1, 'peer_eb')} "
              f"{se_str(res1, 'peer_eb')}  β_C = {coef_str(res1, 'csize')}")

        # Alternative peer: raw BL
        sub_bl = an[an["peer_bl"].notna()].copy()
        fe_s3 = strata_fe(sub_bl["strata"])
        fe_dt3 = decile_treat_fe(sub_bl["bl_decile"], sub_bl["treat"])
        X2 = pd.concat([sub_bl[["peer_bl"]], fe_dt3, fe_s3], axis=1)
        res2 = ols_cluster(sub_bl["std_score_el"], X2, sub_bl["ggroup"])
        print(f"    [BL peer]  β_P(BL) = {coef_str(res2, 'peer_bl')} "
              f"{se_str(res2, 'peer_bl')}")

        # By grade
        print(f"    By grade:")
        grade_rows = []
        for g in sorted(an["grade"].unique()):
            sub_g = an[(an["grade"] == g) & an["peer_eb"].notna()].copy()
            if len(sub_g) < 50 or sub_g["bl_decile"].nunique() < 3:
                continue
            fe_sg = strata_fe(sub_g["strata"])
            fe_dtg = decile_treat_fe(sub_g["bl_decile"], sub_g["treat"])
            Xg = pd.concat([sub_g[["peer_eb"]], fe_dtg, fe_sg], axis=1)
            try:
                resg = ols_cluster(sub_g["std_score_el"], Xg, sub_g["ggroup"])
                grade_rows.append(dict(
                    Grade=int(g), b=resg.params["peer_eb"],
                    se=resg.bse["peer_eb"], p=resg.pvalues["peer_eb"],
                    N=len(sub_g)))
                print(f"      G{int(g)}: β_P = {coef_str(resg, 'peer_eb')} "
                      f"{se_str(resg, 'peer_eb')}  N={len(sub_g)}")
            except Exception as e:
                print(f"      G{int(g)}: FAILED ({e})")

        # By upper/lower track
        print(f"    By track:")
        for track_label, track_val in [("Lower", 0), ("Upper", 1)]:
            sub_tr = an[(an["upper_group"] == track_val) & an["peer_eb"].notna()].copy()
            if len(sub_tr) < 50 or sub_tr["bl_decile"].nunique() < 3:
                continue
            fe_str = strata_fe(sub_tr["strata"])
            fe_dtr = decile_treat_fe(sub_tr["bl_decile"], sub_tr["treat"])
            Xtr = pd.concat([sub_tr[["peer_eb"]], fe_dtr, fe_str], axis=1)
            try:
                restr = ols_cluster(sub_tr["std_score_el"], Xtr, sub_tr["ggroup"])
                print(f"      {track_label}: β_P = {coef_str(restr, 'peer_eb')} "
                      f"{se_str(restr, 'peer_eb')}  N={len(sub_tr)}")
            except Exception as e:
                print(f"      {track_label}: FAILED ({e})")

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Peer Effect Robustness (Kenya)}", r"\label{tab:peer_robust}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Specification & Kenya Y1 & & Kenya Y2 & \\",
        r" & $\hat{\beta}_P$ & SE & $\hat{\beta}_P$ & SE \\", r"\midrule"]

    spec_rows = {}
    for country, label in [("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]:
        df, cfg = _load(country)
        an = df[df["std_score_el"].notna() & df["bl_decile"].notna()].copy()

        results = {}

        sub = an[an["peer_eb"].notna()].copy()
        fe_s = strata_fe(sub["strata"])
        fe_dt = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_eb"]], fe_dt, fe_s], axis=1)
        r = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        results["Baseline (EB peer)"] = (r.params["peer_eb"], r.bse["peer_eb"],
                                          r.pvalues["peer_eb"])

        sub = an[an["peer_eb"].notna() & an["csize"].notna()].copy()
        fe_s = strata_fe(sub["strata"])
        fe_dt = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_eb", "csize"]], fe_dt, fe_s], axis=1)
        r = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        results["+ Class size control"] = (r.params["peer_eb"], r.bse["peer_eb"],
                                            r.pvalues["peer_eb"])

        sub = an[an["peer_bl"].notna()].copy()
        fe_s = strata_fe(sub["strata"])
        fe_dt = decile_treat_fe(sub["bl_decile"], sub["treat"])
        X = pd.concat([sub[["peer_bl"]], fe_dt, fe_s], axis=1)
        r = ols_cluster(sub["std_score_el"], X, sub["ggroup"])
        results["Raw BL peer mean"] = (r.params["peer_bl"], r.bse["peer_bl"],
                                        r.pvalues["peer_bl"])

        spec_rows[label] = results

    for spec_name in ["Baseline (EB peer)", "+ Class size control", "Raw BL peer mean"]:
        ky1 = spec_rows.get("Kenya Y1", {}).get(spec_name, (np.nan, np.nan, np.nan))
        ky2 = spec_rows.get("Kenya Y2", {}).get(spec_name, (np.nan, np.nan, np.nan))
        tex.append(f"{spec_name} & {ky1[0]:.3f}{stars(ky1[2])} & ({ky1[1]:.3f}) & "
                   f"{ky2[0]:.3f}{stars(ky2[2])} & ({ky2[1]:.3f}) \\\\")

    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small All specifications include "
            r"baseline-decile $\times$ treatment FE and strata FE. "
            r"Cluster-robust SEs at school-grade level.}", r"\end{table}"]
    path = OUT / "diag_r2_peer_robust.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R2.6  Kenya: Reduced-form build-up
# ═══════════════════════════════════════════════════════════════════════════════
def r2_reduced_form_buildup():
    print("\n" + "=" * 70)
    print("R2.6: Kenya reduced-form build-up (descriptive peer composition changes)")
    print("=" * 70)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    for study_idx, (country, label) in enumerate(
            [("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]):
        df, cfg = _load(country)
        an = df.copy()

        # Panel A: Mean peer EB by decile, T vs C
        ax = axes[0, study_idx]
        for treat_val, treat_label, color in [(0, "Control", "#4C72B0"),
                                               (1, "Treatment", "#C44E52")]:
            sub = an[(an["treat"] == treat_val) & an["bl_decile"].notna() &
                     an["peer_eb"].notna()]
            dec_means = sub.groupby("bl_decile")["peer_eb"].mean()
            ax.plot(dec_means.index, dec_means.values, "o-", color=color,
                    label=treat_label, ms=6, lw=1.5)
        ax.set_xlabel("Baseline decile")
        ax.set_ylabel("Mean peer EB ability")
        ax.set_title(f"{label}: Peer Composition")
        ax.legend()

        # Panel B: ΔP = P_treat - P_ctrl by decile
        ax = axes[1, study_idx]
        deltas = []
        for d in sorted(an["bl_decile"].dropna().unique()):
            sub = an[an["bl_decile"] == d]
            t_p = sub.loc[sub["treat"] == 1, "peer_eb"].mean()
            c_p = sub.loc[sub["treat"] == 0, "peer_eb"].mean()
            if pd.notna(t_p) and pd.notna(c_p):
                deltas.append((d, t_p - c_p))
        if deltas:
            ddf = pd.DataFrame(deltas, columns=["decile", "delta_P"])
            colors = ["#C44E52" if v < 0 else "#4C72B0" for v in ddf["delta_P"]]
            ax.bar(ddf["decile"], ddf["delta_P"], color=colors, alpha=0.7)
            ax.axhline(0, color="gray", ls="--", lw=1)
        ax.set_xlabel("Baseline decile")
        ax.set_ylabel("ΔP (Treatment − Control)")
        ax.set_title(f"{label}: Treatment-Induced Peer Change")

        # Print descriptive stats
        t_peer = an.loc[an["treat"] == 1, "peer_eb"].mean()
        c_peer = an.loc[an["treat"] == 0, "peer_eb"].mean()
        t_disp = an.loc[an["treat"] == 1, "dev_eb"].mean()
        c_disp = an.loc[an["treat"] == 0, "dev_eb"].mean()
        print(f"\n  {label}:")
        print(f"    Mean peer EB: T={t_peer:.3f}, C={c_peer:.3f}, "
              f"Δ={t_peer - c_peer:.3f}")
        print(f"    Mean within-class dev(EB): T={t_disp:.3f}, C={c_disp:.3f}, "
              f"Δ={t_disp - c_disp:.3f}")

        # T-C differences by decile
        fe = strata_fe(an["strata"])
        for var, var_label in [("peer_eb", "Peer EB"), ("csize", "Class size"),
                                ("dev_eb", "Within-class dev(EB)")]:
            sub_v = an[an[var].notna()].copy()
            X = pd.concat([sub_v[["treat", "std_eb"]], strata_fe(sub_v["strata"])],
                          axis=1)
            res = ols_cluster(sub_v[var], X, sub_v[cfg["cluster_var"]])
            print(f"    Treatment effect on {var_label}: "
                  f"{coef_str(res, 'treat')} {se_str(res, 'treat')}")

    fig.suptitle("Reduced-Form Evidence on Peer Composition Changes", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path = OUT / "diag_r2_rf_buildup.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"\n  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    r2_cutoff_heterogeneity()
    r2_track_ability_bins()
    r2_classsize_control()
    r2_misclass_harm()
    r2_peer_robustness()
    r2_reduced_form_buildup()
    print("\n" + "=" * 70)
    print("✓ Round 2 mechanism tests complete.")
    print("=" * 70)
