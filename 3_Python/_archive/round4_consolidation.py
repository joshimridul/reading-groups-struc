"""
round4_consolidation.py
=======================
Round 4 final evidence consolidation.

Produces:
  R4.1  Differential attrition by treatment, track, and baseline ability
  R4.2  Ceiling/floor effects in test scores
  R4.3  Lee (2009) trimming bounds on ITT
  R4.4  Placebo checks (treatment on baseline scores)
  R4.5  Treatment effect on total score variance
  R4.6  Consolidated evidence summary table
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats as sp_stats

from config import get_config, OUT
from utils import ols_cluster, coef_str, se_str, stars, strata_fe

np.random.seed(42)

STUDIES = [("liberia", "Liberia"), ("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]


def _load_full(country):
    cfg = get_config(country)
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    return df, cfg


def _fs(df):
    return df[df["finsamp"] == 1].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# R4.1  Differential attrition
# ═══════════════════════════════════════════════════════════════════════════════
def r4_attrition():
    print("\n" + "=" * 70)
    print("R4.1: Differential attrition")
    print("=" * 70)

    rows = []
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    for idx, (country, label) in enumerate(STUDIES):
        df_full, cfg = _load_full(country)
        df = df_full[df_full["treat"].notna() & df_full["score_bl"].notna()].copy()
        df["attrited"] = (~df["has_el"]).astype(float)
        cl = cfg["cluster_var"]

        att_t = df.loc[df["treat"] == 1, "attrited"].mean()
        att_c = df.loc[df["treat"] == 0, "attrited"].mean()

        # Overall differential attrition
        fe = strata_fe(df["strata"])
        X = pd.concat([df[["treat"]], fe], axis=1)
        res_ov = ols_cluster(df["attrited"], X, df[cl])
        rows.append(dict(Study=label, Subgroup="Overall",
                         att_T=att_t, att_C=att_c,
                         diff=res_ov.params["treat"],
                         se=res_ov.bse["treat"],
                         p=res_ov.pvalues["treat"],
                         N=len(df)))
        print(f"\n  {label} Overall: T={att_t:.3f} C={att_c:.3f} "
              f"diff={coef_str(res_ov, 'treat')} {se_str(res_ov, 'treat')}")

        # By upper/lower group
        for track_lbl, track_val in [("Lower", 0), ("Upper", 1)]:
            sub = df[df["upper_group"] == track_val]
            if len(sub) < 20 or sub["treat"].nunique() < 2:
                continue
            fe_t = strata_fe(sub["strata"])
            X_t = pd.concat([sub[["treat"]], fe_t], axis=1)
            res_t = ols_cluster(sub["attrited"], X_t, sub[cl])
            rows.append(dict(Study=label, Subgroup=f"{track_lbl} track",
                             att_T=sub.loc[sub["treat"] == 1, "attrited"].mean(),
                             att_C=sub.loc[sub["treat"] == 0, "attrited"].mean(),
                             diff=res_t.params["treat"],
                             se=res_t.bse["treat"],
                             p=res_t.pvalues["treat"],
                             N=len(sub)))
            print(f"  {label} {track_lbl}: diff={coef_str(res_t, 'treat')} "
                  f"{se_str(res_t, 'treat')}")

        # Interaction: T × BL score predicting attrition
        df["treat_x_bl"] = df["treat"] * df["std_score_bl"]
        fe2 = strata_fe(df["strata"])
        X2 = pd.concat([df[["treat", "treat_x_bl", "std_score_bl"]], fe2], axis=1)
        res2 = ols_cluster(df["attrited"], X2, df[cl])
        print(f"  {label} T×BL: {coef_str(res2, 'treat_x_bl')} "
              f"{se_str(res2, 'treat_x_bl')} "
              f"({'diff attrition varies by ability' if res2.pvalues['treat_x_bl'] < 0.1 else 'no significant interaction'})")

        # Figure: attrition by baseline decile
        ax = axes[idx]
        df["bl_dec"] = pd.qcut(df["std_score_bl"], q=10, labels=False,
                                duplicates="drop") + 1
        for tv, tlbl, col in [(0, "Control", "#4C72B0"), (1, "Treatment", "#C44E52")]:
            grp = df[df["treat"] == tv].groupby("bl_dec")["attrited"].mean()
            ax.plot(grp.index, grp.values, "o-", color=col, label=tlbl, ms=5, lw=1.5)
        ax.set_xlabel("Baseline score decile")
        ax.set_ylabel("Attrition rate")
        ax.set_title(label)
        ax.legend(fontsize=8)
        ax.set_ylim(0, min(1, ax.get_ylim()[1] * 1.1))

    fig.suptitle("Attrition by Baseline Ability and Treatment Status", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path_fig = OUT / "diag_r4_attrition.pdf"
    fig.savefig(path_fig, dpi=200)
    plt.close()
    print(f"\n  -> {path_fig}")

    # LaTeX table
    rdf = pd.DataFrame(rows)
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Differential Attrition by Treatment and Track}",
        r"\label{tab:attrition}",
        r"\begin{tabular}{llccccr}", r"\toprule",
        r"Study & Subgroup & Att.\ T & Att.\ C & Diff & SE & $N$ \\", r"\midrule"]
    prev = ""
    for _, r in rdf.iterrows():
        s = r["Study"] if r["Study"] != prev else ""
        if r["Study"] != prev and prev:
            tex.append(r"\addlinespace")
        tex.append(f"{s} & {r['Subgroup']} & {r['att_T']:.3f} & {r['att_C']:.3f} & "
                   f"{r['diff']:.3f}{stars(r['p'])} & ({r['se']:.3f}) & "
                   f"{int(r['N']):,d} \\\\")
        prev = r["Study"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Attrition $= 1$ if student lacks "
            r"endline score. OLS with strata FE and cluster-robust SEs.}",
            r"\end{table}"]
    path_tex = OUT / "diag_r4_attrition.tex"
    path_tex.write_text("\n".join(tex))
    print(f"  -> {path_tex}")


# ═══════════════════════════════════════════════════════════════════════════════
# R4.2  Ceiling/floor effects
# ═══════════════════════════════════════════════════════════════════════════════
def r4_ceiling_floor():
    print("\n" + "=" * 70)
    print("R4.2: Ceiling/floor effects")
    print("=" * 70)

    fig, axes = plt.subplots(2, 3, figsize=(14, 9))

    for col_idx, (country, label) in enumerate(STUDIES):
        df, cfg = _load_full(country)
        an = _fs(df)

        for row_idx, (score_var, score_label) in enumerate(
                [("score_bl", "Baseline"), ("score_el", "Endline")]):
            ax = axes[row_idx, col_idx]
            vals = an[score_var].dropna()
            if len(vals) < 10:
                ax.set_title(f"{label} {score_label} (N/A)")
                continue

            ax.hist(vals, bins=40, color="steelblue", alpha=0.7,
                    edgecolor="white", density=True)

            p5 = vals.quantile(0.05)
            p95 = vals.quantile(0.95)
            floor_frac = (vals <= vals.min()).mean()
            ceil_frac = (vals >= vals.max()).mean() if "maxscore" not in an.columns else np.nan

            max_col = f"maxscore_{score_var.split('_')[1]}" if score_var != "score_bl" else None
            if max_col and max_col in an.columns:
                maxscore = an[max_col].dropna()
                if len(maxscore) > 0:
                    ms = maxscore.iloc[0]
                    ceil_frac = (vals >= ms * 0.95).mean()
                    ax.axvline(ms, color="red", ls="--", lw=1, label=f"Max={ms:.0f}")

            floor_frac_5 = (vals <= vals.quantile(0.02)).mean()

            ax.set_title(f"{label} {score_label} (N={len(vals):,d})")
            ax.set_xlabel("Score")
            if col_idx == 0:
                ax.set_ylabel("Density")

            info = f"Floor(≤P2)={floor_frac_5:.1%}"
            if pd.notna(ceil_frac):
                info += f", Ceil(≥95%max)={ceil_frac:.1%}"
            ax.text(0.98, 0.95, info, transform=ax.transAxes,
                    ha="right", va="top", fontsize=7,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.7))

            print(f"  {label} {score_label}: min={vals.min():.0f} max={vals.max():.0f} "
                  f"mean={vals.mean():.1f} sd={vals.std():.1f} "
                  f"P2={vals.quantile(0.02):.0f} P98={vals.quantile(0.98):.0f}")

    fig.suptitle("Score Distributions: Checking for Ceiling/Floor Effects", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path = OUT / "diag_r4_ceiling_floor.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R4.3  Lee (2009) trimming bounds
# ═══════════════════════════════════════════════════════════════════════════════
def r4_lee_bounds():
    print("\n" + "=" * 70)
    print("R4.3: Lee (2009) trimming bounds on ITT")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df_full, cfg = _load_full(country)
        df = df_full[df_full["treat"].notna() & df_full["score_bl"].notna()].copy()
        cl = cfg["cluster_var"]

        att_t = df.loc[df["treat"] == 1, "has_el"].mean()
        att_c = df.loc[df["treat"] == 0, "has_el"].mean()

        # Identify which group has higher response rate
        if att_t >= att_c:
            trim_group = 1
            excess = att_t - att_c
        else:
            trim_group = 0
            excess = att_c - att_t

        trim_frac = excess / max(att_t if trim_group == 1 else att_c, 0.01)

        # Get respondents
        resp = df[df["has_el"] == True].copy()
        resp_trim = resp[resp["treat"] == trim_group].copy()

        if trim_frac > 0 and trim_frac < 0.5 and len(resp_trim) > 20:
            n_trim = int(np.ceil(len(resp_trim) * trim_frac))

            # Upper bound: trim from bottom of the higher-response group
            resp_trim_sorted = resp_trim.sort_values("std_score_el")
            drop_ids_upper = resp_trim_sorted.index[:n_trim]
            resp_upper = resp[~resp.index.isin(drop_ids_upper)].copy()

            # Lower bound: trim from top
            drop_ids_lower = resp_trim_sorted.index[-n_trim:]
            resp_lower = resp[~resp.index.isin(drop_ids_lower)].copy()

            fe_u = strata_fe(resp_upper["strata"])
            X_u = pd.concat([resp_upper[["treat", "std_eb"]], fe_u], axis=1)
            res_u = ols_cluster(resp_upper["std_score_el"], X_u, resp_upper[cl])

            fe_l = strata_fe(resp_lower["strata"])
            X_l = pd.concat([resp_lower[["treat", "std_eb"]], fe_l], axis=1)
            res_l = ols_cluster(resp_lower["std_score_el"], X_l, resp_lower[cl])

            # Untrimmed
            fe_0 = strata_fe(resp["strata"])
            X_0 = pd.concat([resp[["treat", "std_eb"]], fe_0], axis=1)
            res_0 = ols_cluster(resp["std_score_el"], X_0, resp[cl])

            rows.append(dict(
                Study=label, trim_frac=trim_frac, trim_group=trim_group,
                b_untrimmed=res_0.params["treat"],
                se_untrimmed=res_0.bse["treat"],
                b_lower=min(res_l.params["treat"], res_u.params["treat"]),
                b_upper=max(res_l.params["treat"], res_u.params["treat"]),
                N_untrimmed=len(resp), n_trimmed=n_trim))

            print(f"  {label}: trim {trim_frac:.1%} from {'T' if trim_group == 1 else 'C'} "
                  f"({n_trim} obs)")
            print(f"    Untrimmed: {res_0.params['treat']:.3f} ({res_0.bse['treat']:.3f})")
            print(f"    Lee bounds: [{min(res_l.params['treat'], res_u.params['treat']):.3f}, "
                  f"{max(res_l.params['treat'], res_u.params['treat']):.3f}]")
        else:
            fe_0 = strata_fe(resp["strata"])
            X_0 = pd.concat([resp[["treat", "std_eb"]], fe_0], axis=1)
            res_0 = ols_cluster(resp["std_score_el"], X_0, resp[cl])
            rows.append(dict(
                Study=label, trim_frac=trim_frac, trim_group=trim_group,
                b_untrimmed=res_0.params["treat"],
                se_untrimmed=res_0.bse["treat"],
                b_lower=np.nan, b_upper=np.nan,
                N_untrimmed=len(resp), n_trimmed=0))
            print(f"  {label}: attrition diff too small for trimming ({trim_frac:.1%})")

    rdf = pd.DataFrame(rows)
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Lee (2009) Trimming Bounds on ITT}",
        r"\label{tab:lee_bounds}",
        r"\begin{tabular}{lcccc}", r"\toprule",
        r"Study & Untrimmed ITT & SE & Lee bounds & Trim \% \\", r"\midrule"]
    for _, r in rdf.iterrows():
        bounds = (f"[{r['b_lower']:.3f}, {r['b_upper']:.3f}]"
                  if pd.notna(r["b_lower"]) else "---")
        tex.append(f"{r['Study']} & {r['b_untrimmed']:.3f} & "
                   f"({r['se_untrimmed']:.3f}) & {bounds} & "
                   f"{r['trim_frac']:.1%}".replace("%", r"\%") + " \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Lee bounds trim the top/bottom of "
            r"the outcome distribution in the group with higher response rates "
            r"to equalize attrition. ITT with strata FE and EB control.}",
            r"\end{table}"]
    path = OUT / "diag_r4_lee_bounds.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R4.4  Placebo checks
# ═══════════════════════════════════════════════════════════════════════════════
def r4_placebo():
    print("\n" + "=" * 70)
    print("R4.4: Placebo checks (treatment on pre-treatment outcomes)")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df_full, cfg = _load_full(country)
        df = df_full[df_full["treat"].notna()].copy()
        cl = cfg["cluster_var"]

        # Treatment on baseline score
        sub_bl = df[df["score_bl"].notna()].copy()
        fe = strata_fe(sub_bl["strata"])
        X = pd.concat([sub_bl[["treat"]], fe], axis=1)
        res_bl = ols_cluster(sub_bl["std_score_bl"], X, sub_bl[cl])
        rows.append(dict(Study=label, Outcome="Std. baseline score",
                         coef=res_bl.params["treat"], se=res_bl.bse["treat"],
                         p=res_bl.pvalues["treat"], N=len(sub_bl)))
        print(f"  {label} BL: {coef_str(res_bl, 'treat')} {se_str(res_bl, 'treat')}")

        # Treatment on having baseline
        df["has_bl_f"] = df["score_bl"].notna().astype(float)
        fe2 = strata_fe(df["strata"])
        X2 = pd.concat([df[["treat"]], fe2], axis=1)
        res_hbl = ols_cluster(df["has_bl_f"], X2, df[cl])
        rows.append(dict(Study=label, Outcome="Has baseline (indicator)",
                         coef=res_hbl.params["treat"], se=res_hbl.bse["treat"],
                         p=res_hbl.pvalues["treat"], N=len(df)))
        print(f"  {label} Has BL: {coef_str(res_hbl, 'treat')} {se_str(res_hbl, 'treat')}")

        # Treatment on upper_group assignment (should be zero)
        sub_ug = df[df["upper_group"].notna()].copy()
        if len(sub_ug) > 50:
            fe3 = strata_fe(sub_ug["strata"])
            X3 = pd.concat([sub_ug[["treat"]], fe3], axis=1)
            res_ug = ols_cluster(sub_ug["upper_group"], X3, sub_ug[cl])
            rows.append(dict(Study=label, Outcome="Upper group (placebo)",
                             coef=res_ug.params["treat"], se=res_ug.bse["treat"],
                             p=res_ug.pvalues["treat"], N=len(sub_ug)))
            print(f"  {label} Upper grp: {coef_str(res_ug, 'treat')} "
                  f"{se_str(res_ug, 'treat')}")

    rdf = pd.DataFrame(rows)
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Placebo Checks: Treatment on Pre-Treatment Variables}",
        r"\label{tab:placebo}",
        r"\begin{tabular}{llccr}", r"\toprule",
        r"Study & Outcome & Coefficient & SE & $N$ \\", r"\midrule"]
    prev = ""
    for _, r in rdf.iterrows():
        s = r["Study"] if r["Study"] != prev else ""
        if r["Study"] != prev and prev:
            tex.append(r"\addlinespace")
        tex.append(f"{s} & {r['Outcome']} & "
                   f"{r['coef']:.3f}{stars(r['p'])} & ({r['se']:.3f}) & "
                   f"{int(r['N']):,d} \\\\")
        prev = r["Study"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small OLS with strata FE and "
            r"cluster-robust SEs. All outcomes are pre-treatment; "
            r"significant coefficients would indicate balance failures.}",
            r"\end{table}"]
    path = OUT / "diag_r4_placebo.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R4.5  Treatment effect on total score variance
# ═══════════════════════════════════════════════════════════════════════════════
def r4_variance():
    print("\n" + "=" * 70)
    print("R4.5: Treatment effect on total score variance")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load_full(country)
        an = _fs(df)
        an = an[an["std_score_el"].notna()].copy()

        var_t = an.loc[an["treat"] == 1, "std_score_el"].var()
        var_c = an.loc[an["treat"] == 0, "std_score_el"].var()

        fe = strata_fe(an["strata"])

        # Step 1: estimate mean model (Y = treat + ability + strata FE)
        X_mean = pd.concat([an[["treat", "std_eb"]], fe], axis=1)
        X_mean_c = sm.add_constant(X_mean)
        mean_ols = sm.OLS(an["std_score_el"], X_mean_c).fit()
        an["sq_resid_el"] = mean_ols.resid ** 2

        # Step 2: test whether treatment shifts residual variance
        X = pd.concat([an[["treat", "std_eb"]], fe], axis=1)
        res = ols_cluster(an["sq_resid_el"], X, an[cfg["cluster_var"]])

        # Levene's test (robust to non-normality)
        t_scores = an.loc[an["treat"] == 1, "std_score_el"].values
        c_scores = an.loc[an["treat"] == 0, "std_score_el"].values
        lev_stat, lev_p = sp_stats.levene(t_scores, c_scores)

        rows.append(dict(Study=label, var_T=var_t, var_C=var_c,
                         ratio=var_t / var_c,
                         sq_resid_coef=res.params["treat"],
                         sq_resid_se=res.bse["treat"],
                         sq_resid_p=res.pvalues["treat"],
                         levene_p=lev_p))

        print(f"  {label}: Var(T)={var_t:.3f}  Var(C)={var_c:.3f}  "
              f"ratio={var_t / var_c:.3f}")
        print(f"    Sq resid reg: {coef_str(res, 'treat')} {se_str(res, 'treat')}")
        print(f"    Levene test: p={lev_p:.3f}")

    rdf = pd.DataFrame(rows)
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Treatment Effect on Endline Score Variance}",
        r"\label{tab:variance}",
        r"\begin{tabular}{lcccccc}", r"\toprule",
        r"Study & Var(T) & Var(C) & Ratio & Sq.\ resid.\ coef & SE & Levene $p$ \\",
        r"\midrule"]
    for _, r in rdf.iterrows():
        tex.append(f"{r['Study']} & {r['var_T']:.3f} & {r['var_C']:.3f} & "
                   f"{r['ratio']:.3f} & {r['sq_resid_coef']:.3f}"
                   f"{stars(r['sq_resid_p'])} & ({r['sq_resid_se']:.3f}) & "
                   f"{r['levene_p']:.3f} \\\\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Variance of standardized endline scores. "
            r"Squared-residual regression: first estimate "
            r"$Y_i = \alpha + \beta_1 T_i + \gamma \hat{\theta}_i + "
            r"\text{strata FE} + u_i$, then regress $\hat{u}_i^2$ on "
            r"treatment, ability, and strata FE with cluster-robust SEs. "
            r"Levene test for equality of variances.}", r"\end{table}"]
    path = OUT / "diag_r4_variance.tex"
    path.write_text("\n".join(tex))
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R4.6  Consolidated evidence summary
# ═══════════════════════════════════════════════════════════════════════════════
def r4_consolidated_summary():
    print("\n" + "=" * 70)
    print("R4.6: Consolidated evidence summary")
    print("=" * 70)

    summary = []
    for country, label in STUDIES:
        df_full, cfg = _load_full(country)
        df = _fs(df_full)
        an = df[df["std_score_el"].notna()].copy()
        ctrl = an["treat"] == 0

        # R² (reliability)
        ctrl_be = an[ctrl & an["score_bl"].notna() & an["score_el"].notna()]
        r2 = np.corrcoef(ctrl_be["score_bl"], ctrl_be["score_el"])[0, 1] ** 2

        # ITT
        fe = strata_fe(an["strata"])
        X = pd.concat([an[["treat", "std_eb"]], fe], axis=1)
        res = ols_cluster(an["std_score_el"], X, an[cfg["cluster_var"]])
        itt = res.params["treat"]
        itt_p = res.pvalues["treat"]

        # Upper/lower interaction
        an["treat_x_upper"] = an["treat"] * an["upper_group"]
        X2 = pd.concat([an[["treat", "treat_x_upper", "upper_group", "std_eb"]], fe],
                        axis=1)
        res2 = ols_cluster(an["std_score_el"], X2, an[cfg["cluster_var"]])
        txu = res2.params["treat_x_upper"]
        txu_p = res2.pvalues["treat_x_upper"]

        # Class size diff
        cs_t = an.loc[an["treat"] == 1, "csize"].mean()
        cs_c = an.loc[an["treat"] == 0, "csize"].mean()

        # Within-class dispersion
        wcd_t = an.loc[an["treat"] == 1, "dev_eb"].mean()
        wcd_c = an.loc[an["treat"] == 0, "dev_eb"].mean()

        # Peer effect (BH)
        sub_bh = an[an["peer_eb"].notna() & an["bl_decile"].notna()].copy()
        if len(sub_bh) > 100:
            from utils import decile_treat_fe
            fe_s = strata_fe(sub_bh["strata"])
            fe_dt = decile_treat_fe(sub_bh["bl_decile"], sub_bh["treat"])
            X_bh = pd.concat([sub_bh[["peer_eb"]], fe_dt, fe_s], axis=1)
            res_bh = ols_cluster(sub_bh["std_score_el"], X_bh, sub_bh["ggroup"])
            beta_p = res_bh.params["peer_eb"]
            beta_p_p = res_bh.pvalues["peer_eb"]
        else:
            beta_p = beta_p_p = np.nan

        # N
        N = len(an)

        # Attrition
        df_att = df_full[df_full["treat"].notna()].copy()
        att_t = (~df_att.loc[df_att["treat"] == 1, "has_el"]).mean()
        att_c = (~df_att.loc[df_att["treat"] == 0, "has_el"]).mean()

        summary.append(dict(
            Study=label, N=N, r2=r2,
            ITT=f"{itt:.3f}{stars(itt_p)}",
            TxUpper=f"{txu:.3f}{stars(txu_p)}",
            CS_diff=f"{cs_t - cs_c:+.1f}",
            WCD_ratio=f"{wcd_t / wcd_c:.2f}" if wcd_c > 0 else "---",
            beta_P=f"{beta_p:.3f}{stars(beta_p_p)}" if pd.notna(beta_p) else "---",
            Attrition=f"T={att_t:.1%} C={att_c:.1%}".replace("%", r"\%")))

        bp_str = f"{beta_p:.3f}" if pd.notna(beta_p) else "NA"
        print(f"  {label}: r²={r2:.3f} ITT={itt:.3f} T×U={txu:.3f} "
              f"ΔCS={cs_t - cs_c:+.1f} WCD={wcd_t / wcd_c:.2f} β_P={bp_str}")

    sdf = pd.DataFrame(summary)

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Consolidated Evidence Summary Across Three Experiments}",
        r"\label{tab:consolidated}",
        r"\begin{tabular}{lccc}", r"\toprule",
        r" & Liberia & Kenya Y1 & Kenya Y2 \\", r"\midrule"]
    for key, lbl in [
        ("N", r"$N$ (analysis sample)"),
        ("r2", r"Diagnostic reliability $r^2$"),
        ("ITT", r"Average ITT"),
        ("TxUpper", r"$T \times$ Upper interaction"),
        ("CS_diff", r"$\Delta$ Class size (T$-$C)"),
        ("WCD_ratio", r"Within-class dispersion (T/C)"),
        ("beta_P", r"Peer effect $\hat{\beta}_P$ (BH)"),
        ("Attrition", r"Attrition rates")]:
        vals = []
        for _, r in sdf.iterrows():
            v = r[key]
            if key == "N":
                vals.append(f"{v:,d}")
            elif key == "r2":
                vals.append(f"{v:.3f}")
            else:
                vals.append(str(v))
        tex.append(f"{lbl} & " + " & ".join(vals) + r" \\")
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small All estimates include strata FE "
            r"and EB ability control. Peer effect from Borusyak-Hull design "
            r"with decile$\times$treatment FE. Cluster-robust SEs at "
            r"school-grade level.}", r"\end{table}"]
    path = OUT / "diag_r4_consolidated.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    r4_attrition()
    r4_ceiling_floor()
    r4_lee_bounds()
    r4_placebo()
    r4_variance()
    r4_consolidated_summary()
    print("\n" + "=" * 70)
    print("✓ Round 4 final evidence consolidation complete.")
    print("=" * 70)
