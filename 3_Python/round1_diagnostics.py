"""
round1_diagnostics.py
=====================
Round 1 diagnostic analyses for the ability-grouping paper.

Produces:
  R1.1  Treatment effect on class size (table)
  R1.2  Misclassification rates by distance from cutoff (figure, Liberia)
  R1.3  BH first-stage diagnostics for Kenya (table + figure)
  R1.4  Classification accuracy and sorting metrics (table)
  R1.5  Reliability bootstrap CIs (table)
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy import stats as sp_stats

from config import get_config, OUT
from utils import ols_cluster, strata_fe, stars

np.random.seed(42)

STUDIES = [
    ("liberia",  "Liberia"),
    ("kenya",    "Kenya Y1"),
    ("kenya2",   "Kenya Y2"),
]


def _load(country):
    cfg = get_config(country)
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    return df, cfg


def _fs(df):
    """Final analytic sample."""
    return df[df["finsamp"] == 1].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# R1.1  Treatment effect on class size
# ═══════════════════════════════════════════════════════════════════════════════
def r1_classsize():
    print("\n" + "=" * 70)
    print("R1.1: Treatment effect on class size")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        an = _fs(df)

        t_mean = an.loc[an["treat"] == 1, "csize"].mean()
        c_mean = an.loc[an["treat"] == 0, "csize"].mean()

        fe = strata_fe(an["strata"])
        X = pd.concat([an[["treat", "std_eb"]].reset_index(drop=True),
                        fe.reset_index(drop=True)], axis=1)
        res = ols_cluster(
            an["csize"].reset_index(drop=True),
            X.astype(float),
            an[cfg["cluster_var"]].reset_index(drop=True))
        b = res.params["treat"]
        se = res.bse["treat"]
        p = res.pvalues["treat"]

        rows.append(dict(Study=label, T_mean=f"{t_mean:.1f}",
                         C_mean=f"{c_mean:.1f}",
                         Diff=f"{b:.1f}{stars(p)}",
                         SE=f"({se:.1f})", N=f"{len(an):,d}"))
        print(f"  {label:15s}  T={t_mean:.1f}  C={c_mean:.1f}  "
              f"Diff={b:.1f} ({se:.1f})  p={p:.3f}")

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Treatment Effect on Class Size}", r"\label{tab:classsize_effect}",
        r"\begin{tabular}{lrrrrr}", r"\toprule",
        r" & T Mean & C Mean & Difference & SE & $N$ \\", r"\midrule"]
    for r in rows:
        tex.append(f"{r['Study']} & {r['T_mean']} & {r['C_mean']} & "
                   f"{r['Diff']} & {r['SE']} & {r['N']} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small OLS with strata FE, "
            r"cluster-robust SEs at school-grade-group level.}",
            r"\end{table}"]
    path = OUT / "diag_r1_classsize.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R1.2  Misclassification rates (Liberia)
# ═══════════════════════════════════════════════════════════════════════════════
def r1_misclassification():
    print("\n" + "=" * 70)
    print("R1.2: Misclassification rates by distance from cutoff (Liberia)")
    print("=" * 70)

    df, cfg = _load("liberia")
    an = _fs(df)

    cutoffs = cfg["cutoffs"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)

    for idx, (gg_label, gg_grades) in enumerate(
            [("Grades 1-2", [1, 2]), ("Grades 3-4", [3, 4])]):
        ax = axes[idx]
        sub = an[an["grade"].isin(gg_grades)].copy()
        c = cutoffs[gg_grades[0]]

        r2 = sub.loc[sub["treat"] == 0].pipe(
            lambda d: d["score_bl"].corr(d["score_el"]) ** 2
            if d["score_el"].notna().sum() > 10 else 0.05)
        r2 = max(r2, 0.01)

        s_mean = sub["score_bl"].mean()
        s_std = sub["score_bl"].std()
        sigma_theta_given_s = np.sqrt((1 - r2)) * s_std

        sub["theta_eb"] = s_mean + r2 * (sub["score_bl"] - s_mean)
        sub["pr_misclass"] = np.where(
            sub["score_bl"] >= c,
            sp_stats.norm.cdf(c, loc=sub["theta_eb"], scale=sigma_theta_given_s),
            1 - sp_stats.norm.cdf(c, loc=sub["theta_eb"], scale=sigma_theta_given_s))

        dist = sub["score_bl"] - c
        bins = np.arange(dist.min() - 0.5, dist.max() + 1.5, 2)
        sub["dist_bin"] = pd.cut(dist, bins=bins)
        binned = sub.groupby("dist_bin", observed=True).agg(
            pr_mis=("pr_misclass", "mean"),
            n=("pr_misclass", "count")).reset_index()
        binned["mid"] = binned["dist_bin"].apply(lambda x: x.mid)
        binned = binned[binned["n"] >= 10]

        ax.bar(binned["mid"], binned["pr_mis"], width=1.8,
               color="steelblue", alpha=0.7, edgecolor="white")
        ax.axvline(0, color="red", ls="--", lw=1.2)
        ax.axhline(0.5, color="gray", ls=":", lw=0.8)
        ax.set_xlabel("Distance from cutoff (score − c)")
        if idx == 0:
            ax.set_ylabel("Pr(misclassified)")
        ax.set_title(f"{gg_label} (r² ≈ {r2:.2f})")
        ax.set_ylim(0, 0.65)

        upper_mis = sub.loc[sub["score_bl"] >= c, "pr_misclass"].mean()
        lower_mis = sub.loc[sub["score_bl"] < c, "pr_misclass"].mean()
        print(f"  {gg_label}: r²={r2:.3f}  upper-track Pr(mis)={upper_mis:.2f}  "
              f"lower-track Pr(mis)={lower_mis:.2f}")

    fig.suptitle("Predicted Misclassification Rate by Distance from Cutoff (Liberia)",
                 fontsize=13, y=1.02)
    fig.tight_layout()
    path = OUT / "diag_r1_misclass.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R1.3  BH first-stage diagnostics (Kenya Y1 and Y2)
# ═══════════════════════════════════════════════════════════════════════════════
def r1_bh_firststage():
    print("\n" + "=" * 70)
    print("R1.3: Borusyak-Hull first-stage diagnostics")
    print("=" * 70)

    all_rows = []
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    for study_idx, (country, label) in enumerate(
            [("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]):
        df, cfg = _load(country)
        an = _fs(df)
        an = an.dropna(subset=["bl_decile", "treat", "peer_eb"])

        an["cell"] = an["bl_decile"].astype(int) * 10 + an["treat"].astype(int)

        cell_stats = an.groupby("cell").agg(
            n_students=("peer_eb", "count"),
            n_schools=("academycode", "nunique"),
            mean_P=("peer_eb", "mean"),
            sd_P=("peer_eb", "std")).reset_index()

        cell_mean = an.groupby("cell")["peer_eb"].transform("mean")
        an["P_resid"] = an["peer_eb"] - cell_mean

        resid_sd = an["P_resid"].std()
        total_sd = an["peer_eb"].std()
        frac_resid = (resid_sd / total_sd) ** 2

        school_cell = an.groupby(["cell", "academycode"]).agg(
            mean_Y=("std_score_el", "mean"),
            mean_P=("peer_eb", "mean"),
            n=("std_score_el", "count")).reset_index()
        school_cell = school_cell[school_cell["n"] >= 3]

        cell_grand_P = school_cell.groupby("cell")["mean_P"].transform("mean")
        school_cell["P_dev"] = school_cell["mean_P"] - cell_grand_P
        cell_grand_Y = school_cell.groupby("cell")["mean_Y"].transform("mean")
        school_cell["Y_dev"] = school_cell["mean_Y"] - cell_grand_Y

        if len(school_cell) > 5:
            X_f = sm.add_constant(school_cell["P_dev"])
            res_f = sm.OLS(school_cell["Y_dev"], X_f).fit()
            f_stat = res_f.fvalue
            r2_f = res_f.rsquared
            b_f = res_f.params["P_dev"]
            se_f = res_f.bse["P_dev"]
        else:
            f_stat = r2_f = b_f = se_f = np.nan

        all_rows.append(dict(
            Study=label,
            total_sd=f"{total_sd:.3f}",
            resid_sd=f"{resid_sd:.3f}",
            frac_resid=f"{frac_resid:.1%}".replace("%", r"\%"),
            n_cells=f"{cell_stats.shape[0]}",
            med_schools=f"{cell_stats['n_schools'].median():.0f}",
            eff_F=f"{f_stat:.1f}",
            slope=f"{b_f:.3f} ({se_f:.3f})"))

        print(f"  {label}:")
        print(f"    Total SD(P) = {total_sd:.3f}")
        print(f"    Resid SD(P) after cell FE = {resid_sd:.3f}")
        print(f"    Fraction residual = {frac_resid:.1%}")
        print(f"    N cells = {cell_stats.shape[0]}")
        print(f"    Median schools/cell = {cell_stats['n_schools'].median():.0f}")
        print(f"    School-level F(P_dev -> Y_dev) = {f_stat:.1f}")
        print(f"    Slope = {b_f:.3f} ({se_f:.3f})")

        ax = axes[study_idx]
        sc = ax.scatter(school_cell["P_dev"], school_cell["Y_dev"],
                        s=school_cell["n"] * 2, alpha=0.4, c="steelblue",
                        edgecolors="none")
        if not np.isnan(b_f):
            xr = np.array([school_cell["P_dev"].min(), school_cell["P_dev"].max()])
            ax.plot(xr, res_f.params["const"] + b_f * xr, "r-", lw=2)
        ax.axhline(0, color="gray", ls=":", lw=0.7)
        ax.axvline(0, color="gray", ls=":", lw=0.7)
        ax.set_xlabel("School peer-ability deviation (within cell)")
        if study_idx == 0:
            ax.set_ylabel("School mean endline deviation (within cell)")
        ax.set_title(f"{label}  (F={f_stat:.1f}, β={b_f:.3f})")

    fig.suptitle("BH First Stage: School-Level Peer Ability vs. Outcomes\n"
                 "(Within Decile × Treatment Cells)", fontsize=12, y=1.04)
    fig.tight_layout()
    path_fig = OUT / "diag_r1_bh_firststage.pdf"
    fig.savefig(path_fig, dpi=200)
    plt.close()
    print(f"  -> {path_fig}")

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Borusyak-Hull First-Stage Diagnostics}",
        r"\label{tab:bh_firststage}",
        r"\begin{tabular}{lcc}", r"\toprule",
        r" & Kenya Y1 & Kenya Y2 \\", r"\midrule"]
    for key, lbl in [("total_sd", r"SD(Peer EB), total"),
                     ("resid_sd", r"SD(Peer EB), within cell"),
                     ("frac_resid", r"Share residual variance"),
                     ("n_cells", r"Number of decile $\times$ T cells"),
                     ("med_schools", r"Median schools per cell"),
                     ("eff_F", r"School-level $F$-statistic"),
                     ("slope", r"School-level slope ($\hat{\beta}$, SE)")]:
        vals = " & ".join(r[key] for r in all_rows)
        tex.append(f"{lbl} & {vals} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small School-level regressions of "
            r"mean endline score on mean peer EB ability, demeaned within "
            r"baseline-decile $\times$ treatment cells. Schools with $<3$ "
            r"students in a cell excluded.}", r"\end{table}"]
    path_tex = OUT / "diag_r1_bh_firststage.tex"
    path_tex.write_text("\n".join(tex))
    print(f"  -> {path_tex}")


# ═══════════════════════════════════════════════════════════════════════════════
# R1.4  Classification accuracy and sorting metrics
# ═══════════════════════════════════════════════════════════════════════════════
def r1_sorting():
    print("\n" + "=" * 70)
    print("R1.4: Classification accuracy & sorting metrics")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        an = _fs(df)

        treat_an = an[an["treat"] == 1].copy()

        r2_all = an.loc[an["treat"] == 0].pipe(
            lambda d: np.corrcoef(
                d.loc[d["score_el"].notna(), "score_bl"],
                d.loc[d["score_el"].notna(), "score_el"])[0, 1] ** 2
            if d["score_el"].notna().sum() > 10 else np.nan)

        s_mean = an["score_bl"].mean()
        s_std = an["score_bl"].std()
        treat_an["theta_eb_full"] = s_mean + r2_all * (
            treat_an["score_bl"] - s_mean)

        cutoffs = cfg.get("cutoffs", cfg.get("Y1_CUTOFFS", {}))

        if len(treat_an) > 0 and len(cutoffs) > 0:
            has_cut = treat_an["grade"].apply(lambda g: int(g) in cutoffs)
            sub_cut = treat_an[has_cut].copy()
            if len(sub_cut) > 0:
                sub_cut["score_track"] = sub_cut.apply(
                    lambda r: 1 if r["score_bl"] >= cutoffs.get(
                        int(r["grade"]), 999) else 0, axis=1)
                sub_cut["eb_track"] = sub_cut.apply(
                    lambda r: 1 if r["theta_eb_full"] >= cutoffs.get(
                        int(r["grade"]), 999) else 0, axis=1)
                agree = (sub_cut["score_track"] == sub_cut["eb_track"]).mean()
            else:
                agree = np.nan
        else:
            agree = np.nan

        ctrl = an[(an["treat"] == 0) & an["score_bl"].notna()]
        ctrl_wc_sd = ctrl.groupby("ggroup")["score_bl"].transform("std").mean()

        if len(treat_an) > 0 and "upper_group" in treat_an.columns:
            upper_mean = treat_an.loc[treat_an["upper_group"] == 1,
                                       "score_bl"].mean()
            lower_mean = treat_an.loc[treat_an["upper_group"] == 0,
                                       "score_bl"].mean()
            gap = upper_mean - lower_mean
            total_sd = treat_an["score_bl"].std()
            gap_frac = gap / total_sd if total_sd > 0 else np.nan

            treat_wc_sd = treat_an.groupby("ggroup")[
                "score_bl"].transform("std").mean()
            ratio = treat_wc_sd / ctrl_wc_sd if ctrl_wc_sd > 0 else np.nan
        else:
            gap_frac = ratio = np.nan

        rows.append(dict(
            Study=label, r2=f"{r2_all:.3f}",
            class_acc=f"{agree:.1%}".replace("%", r"\%") if not np.isnan(agree) else "--",
            gap=f"{gap_frac:.2f}" if not np.isnan(gap_frac) else "--",
            wc_ratio=f"{ratio:.2f}" if not np.isnan(ratio) else "--"))

        print(f"  {label}: r²={r2_all:.3f}  class_acc={agree:.1%}  "
              f"gap/SD={gap_frac:.2f}  WC_SD_ratio={ratio:.2f}")

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Sorting Diagnostics}", r"\label{tab:sorting}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r" & $R^2$(BL$\to$EL) & Classification & Between-track & Within-class SD \\",
        r" & & accuracy & gap$/\sigma$ & ratio (T/C) \\",
        r"\midrule"]
    for r in rows:
        tex.append(f"{r['Study']} & {r['r2']} & {r['class_acc']} & "
                   f"{r['gap']} & {r['wc_ratio']} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Classification accuracy: share of "
            r"treatment-school students whose track assignment (score vs.\ cutoff) "
            r"matches EB-predicted track. Between-track gap: difference in mean "
            r"baseline scores between upper and lower tracks, divided by total SD. "
            r"Within-class SD ratio: mean within-classroom SD of baseline scores "
            r"in treatment schools divided by control schools.}",
            r"\end{table}"]
    path = OUT / "diag_r1_sorting.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R1.5  Reliability bootstrap CIs
# ═══════════════════════════════════════════════════════════════════════════════
def r1_reliability_bootstrap():
    print("\n" + "=" * 70)
    print("R1.5: Reliability bootstrap CIs")
    print("=" * 70)
    N_BOOT = 1000

    all_rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        an = _fs(df)
        ctrl = an[(an["treat"] == 0) & an["score_el"].notna() &
                  an["score_bl"].notna()].copy()

        for g in sorted(ctrl["grade"].unique()):
            gc = ctrl[ctrl["grade"] == g]
            if len(gc) < 20:
                continue

            r2_obs = np.corrcoef(gc["score_bl"], gc["score_el"])[0, 1] ** 2

            schools = gc["academycode"].unique()
            boot_r2 = []
            for _ in range(N_BOOT):
                s_boot = np.random.choice(schools, size=len(schools), replace=True)
                frames = [gc[gc["academycode"] == s] for s in s_boot]
                bdf = pd.concat(frames, ignore_index=True)
                if len(bdf) < 10:
                    continue
                r = np.corrcoef(bdf["score_bl"], bdf["score_el"])[0, 1]
                boot_r2.append(r ** 2)

            boot_r2 = np.array(boot_r2)
            ci_lo = np.percentile(boot_r2, 2.5)
            ci_hi = np.percentile(boot_r2, 97.5)
            se_boot = boot_r2.std()

            all_rows.append(dict(
                Study=label, Grade=int(g), N=len(gc),
                r2=f"{r2_obs:.3f}",
                ci=f"[{ci_lo:.3f}, {ci_hi:.3f}]",
                se=f"({se_boot:.3f})"))
            print(f"  {label} G{int(g)}: r²={r2_obs:.3f}  "
                  f"95% CI=[{ci_lo:.3f}, {ci_hi:.3f}]  "
                  f"SE={se_boot:.3f}  N={len(gc)}")

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Diagnostic Reliability with Bootstrap Confidence Intervals}",
        r"\label{tab:reliability_boot}",
        r"\begin{tabular}{llrccc}", r"\toprule",
        r"Study & Grade & $N$ & $R^2$ & 95\% CI & Boot SE \\",
        r"\midrule"]
    for r in all_rows:
        tex.append(f"{r['Study']} & {r['Grade']} & {r['N']} & "
                   f"{r['r2']} & {r['ci']} & {r['se']} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small $R^2$ from regressing endline on "
            r"baseline scores in control group. Bootstrap: 1{,}000 school-level "
            r"resamples within strata. CIs are percentile-based.}",
            r"\end{table}"]
    path = OUT / "diag_r1_reliability_boot.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    r1_classsize()
    r1_misclassification()
    r1_bh_firststage()
    r1_sorting()
    r1_reliability_bootstrap()
    print("\n✓ Round 1 diagnostics complete.")
