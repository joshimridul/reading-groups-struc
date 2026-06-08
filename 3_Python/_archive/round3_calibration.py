"""
round3_calibration.py
=====================
Round 3 calibration robustness for the ability-grouping paper.

Produces:
  R3.1  Bootstrap CIs for lambda, tau, rho, and r²* (all studies)
  R3.2  Sensitivity of threshold to alternative specifications
  R3.3  Grade-specific calibration (not just pooled)
  R3.4  Alternative misfit definitions and functional forms
  R3.5  Calibration summary table across all studies
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from config import get_config, OUT
from utils import ols_cluster, stars, strata_fe

np.random.seed(42)

STUDIES = [("liberia", "Liberia"), ("kenya", "Kenya Y1"), ("kenya2", "Kenya Y2")]


def _load(country):
    cfg = get_config(country)
    df = pd.read_parquet(cfg["ANALYSIS_FILE"])
    return df[df["finsamp"] == 1].copy(), cfg


def _build_cal_data(df, cfg):
    """Prepare calibration dataset with misfit, quadratic ability control."""
    sub = df[df["std_score_el"].notna() & df["std_score_bl"].notna()].copy()
    for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
        cm = sub.groupby(["academycode", grp_type]
                          )["std_score_bl"].transform("mean")
        sub[f"_cm_{suffix}"] = cm
    sub["_cm"] = np.where(sub["treat"] == 1, sub["_cm_treat"], sub["_cm_ctrl"])
    sub["misfit_bl"] = (sub["std_score_bl"] - sub["_cm"]) ** 2
    sub["std_bl_sq"] = sub["std_score_bl"] ** 2
    return sub


def _calibrate(sub, cluster):
    """Run the 2-step calibration. Returns dict with lambda, tau, rho, etc.
    cluster: Series of cluster IDs (not a column name).
    """
    res = ols_cluster(sub["std_score_el"],
                       sub[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                       cluster)
    lam = -res.params["misfit_bl"]
    tau = res.params["treat"]
    se_lam = res.bse["misfit_bl"]
    se_tau = res.bse["treat"]

    if tau < 0 and lam > 0:
        rho = 2 * np.sqrt(lam * (-tau))
    else:
        rho = np.nan

    return dict(lam=lam, tau=tau, rho=rho, se_lam=se_lam, se_tau=se_tau,
                N=len(sub), res=res)


def _r2_star(lam, rho, sigma2):
    if pd.notna(rho) and lam > 0 and sigma2 > 0:
        return rho ** 2 / (4 * lam ** 2 * sigma2)
    return np.nan


# ═══════════════════════════════════════════════════════════════════════════════
# R3.1  Bootstrap CIs for structural parameters
# ═══════════════════════════════════════════════════════════════════════════════
def r3_bootstrap_calibration():
    print("\n" + "=" * 70)
    print("R3.1: Bootstrap CIs for structural parameters")
    print("=" * 70)
    N_BOOT = 500

    all_results = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        sub = _build_cal_data(df, cfg)
        cl = cfg["cluster_var"]
        grades = sorted(df["grade"].dropna().unique())
        ctrl = df["treat"] == 0

        point = _calibrate(sub, sub["ggroup"])
        print(f"\n  {label} point estimates:")
        print(f"    λ = {point['lam']:.4f}  τ = {point['tau']:.4f}  "
              f"ρ = {point['rho']:.4f}" if pd.notna(point["rho"])
              else f"    λ = {point['lam']:.4f}  τ = {point['tau']:.4f}  ρ = NA")

        schools = sub["academycode"].unique()
        boot_lam, boot_tau, boot_rho = [], [], []
        boot_r2star = {g: [] for g in grades}

        for b in range(N_BOOT):
            s_boot = np.random.choice(schools, size=len(schools), replace=True)
            frames = [sub[sub["academycode"] == s] for s in s_boot]
            bdf = pd.concat(frames, ignore_index=True)
            if len(bdf) < 50:
                continue
            try:
                X = bdf[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]]
                y = bdf["std_score_el"]
                mask = y.notna() & X.notna().all(axis=1)
                y_, X_ = y[mask], sm.add_constant(X[mask])
                res_b = sm.OLS(y_, X_).fit()
                lam_b = -res_b.params["misfit_bl"]
                tau_b = res_b.params["treat"]
                boot_lam.append(lam_b)
                boot_tau.append(tau_b)
                if tau_b < 0 and lam_b > 0:
                    rho_b = 2 * np.sqrt(lam_b * (-tau_b))
                    boot_rho.append(rho_b)

                    for g in grades:
                        g_ctrl = df[(df["treat"] == 0) & (df["grade"] == g) &
                                    df["score_bl"].notna()]
                        sigma2_g = g_ctrl["std_score_bl"].var()
                        if sigma2_g > 0:
                            boot_r2star[g].append(
                                rho_b ** 2 / (4 * lam_b ** 2 * sigma2_g))
                else:
                    boot_rho.append(np.nan)
            except Exception as e:
                if b < 3:
                    print(f"    Bootstrap rep {b}: FAILED ({e})")

        boot_lam = np.array(boot_lam)
        boot_tau = np.array(boot_tau)
        boot_rho = np.array([x for x in boot_rho if pd.notna(x)])

        result = dict(
            Study=label,
            lam=point["lam"],
            lam_ci=(np.percentile(boot_lam, 2.5), np.percentile(boot_lam, 97.5)),
            tau=point["tau"],
            tau_ci=(np.percentile(boot_tau, 2.5), np.percentile(boot_tau, 97.5)),
            rho=point["rho"],
            rho_ci=((np.percentile(boot_rho, 2.5), np.percentile(boot_rho, 97.5))
                    if len(boot_rho) > 10 else (np.nan, np.nan)),
            rho_valid_frac=len(boot_rho) / len(boot_lam) if len(boot_lam) > 0 else 0,
            N=point["N"])

        print(f"    λ = {point['lam']:.4f}  [{result['lam_ci'][0]:.4f}, "
              f"{result['lam_ci'][1]:.4f}]")
        print(f"    τ = {point['tau']:.4f}  [{result['tau_ci'][0]:.4f}, "
              f"{result['tau_ci'][1]:.4f}]")
        if pd.notna(result["rho"]):
            print(f"    ρ = {result['rho']:.4f}  [{result['rho_ci'][0]:.4f}, "
                  f"{result['rho_ci'][1]:.4f}]  "
                  f"(defined in {result['rho_valid_frac']:.0%} of boots)")
        else:
            print(f"    ρ = NA  (defined in {result['rho_valid_frac']:.0%} of boots)")

        for g in grades:
            arr = np.array(boot_r2star[g])
            if len(arr) > 10:
                r2obs = df.loc[(df["treat"] == 0) & (df["grade"] == g) &
                               df["score_bl"].notna() & df["score_el"].notna()].pipe(
                    lambda d: np.corrcoef(d["score_bl"], d["score_el"])[0, 1] ** 2
                    if len(d) > 10 else np.nan)
                r2s_pt = _r2_star(point["lam"], point["rho"],
                                   df.loc[(df["treat"] == 0) & (df["grade"] == g),
                                          "std_score_bl"].var())
                ci_lo, ci_hi = np.percentile(arr, [2.5, 97.5])
                print(f"    G{int(g)}: r²*={r2s_pt:.4f} [{ci_lo:.4f}, {ci_hi:.4f}]  "
                      f"r²_obs={r2obs:.4f}  "
                      f"{'FAIL' if r2obs < ci_lo else 'PASS/AMBIGUOUS'}")
                result[f"r2star_g{int(g)}"] = r2s_pt
                result[f"r2star_ci_g{int(g)}"] = (ci_lo, ci_hi)
                result[f"r2obs_g{int(g)}"] = r2obs

        all_results.append(result)

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Structural Calibration with Bootstrap Confidence Intervals}",
        r"\label{tab:calib_boot}",
        r"\begin{tabular}{lccc}", r"\toprule",
        r" & Liberia & Kenya Y1 & Kenya Y2 \\", r"\midrule"]
    for key, lbl, fmt in [
        ("lam", r"$\hat{\lambda}$", ".3f"),
        ("tau", r"$\hat{\tau}$", ".3f"),
        ("rho", r"$\hat{\rho}$", ".3f")]:
        vals = []
        for r in all_results:
            v = r[key]
            ci = r[f"{key}_ci"]
            if pd.notna(v):
                vals.append(f"{v:{fmt}} [{ci[0]:{fmt}}, {ci[1]:{fmt}}]")
            else:
                vals.append("---")
        tex.append(f"{lbl} & " + " & ".join(vals) + r" \\")

    row_frac = " & ".join(f"{r.get('rho_valid_frac', 0):.0%}".replace("%", r"\%") for r in all_results)
    tex.append(r"$\rho$ defined (\% of boots) & " + row_frac + r" \\")

    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small 500 school-level bootstrap resamples. "
            r"$\rho$ is defined only when $\hat{\lambda}>0$ and $\hat{\tau}<0$.}",
            r"\end{table}"]
    path = OUT / "diag_r3_calib_boot.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# R3.2  Sensitivity to alternative specifications
# ═══════════════════════════════════════════════════════════════════════════════
def r3_sensitivity():
    print("\n" + "=" * 70)
    print("R3.2: Sensitivity of calibration to alternative specifications")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        sub = _build_cal_data(df, cfg)
        cl = sub["ggroup"]

        # Spec A: Baseline (quadratic + treat)
        res_a = _calibrate(sub, cl)

        # Spec B: No quadratic
        res_b_r = ols_cluster(sub["std_score_el"],
                               sub[["misfit_bl", "treat", "std_score_bl"]], cl)
        lam_b = -res_b_r.params["misfit_bl"]
        tau_b = res_b_r.params["treat"]

        # Spec C: With strata FE
        fe = strata_fe(sub["strata"])
        X_c = pd.concat([sub[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                          fe], axis=1)
        res_c_r = ols_cluster(sub["std_score_el"], X_c, cl)
        lam_c = -res_c_r.params["misfit_bl"]
        tau_c = res_c_r.params["treat"]

        # Spec D: EB-based misfit (instead of raw BL)
        sub_d = sub.copy()
        for grp_type, suffix in [("std_grp", "treat"), ("grade", "ctrl")]:
            cm = sub_d.groupby(["academycode", grp_type]
                                )["std_eb"].transform("mean")
            sub_d[f"_cm_eb_{suffix}"] = cm
        sub_d["_cm_eb"] = np.where(sub_d["treat"] == 1,
                                    sub_d["_cm_eb_treat"], sub_d["_cm_eb_ctrl"])
        sub_d["misfit_eb"] = (sub_d["std_eb"] - sub_d["_cm_eb"]) ** 2
        sub_d["std_eb_sq"] = sub_d["std_eb"] ** 2
        res_d_r = ols_cluster(sub_d["std_score_el"],
                               sub_d[["misfit_eb", "treat", "std_eb", "std_eb_sq"]],
                               cl)
        lam_d = -res_d_r.params["misfit_eb"]
        tau_d = res_d_r.params["treat"]

        # Spec E: Treatment group only
        sub_t = sub[sub["treat"] == 1].copy()
        if len(sub_t) > 50:
            res_e_r = ols_cluster(sub_t["std_score_el"],
                                   sub_t[["misfit_bl", "std_score_bl", "std_bl_sq"]],
                                   sub_t["ggroup"])
            lam_e = -res_e_r.params["misfit_bl"]
        else:
            lam_e = np.nan

        specs = [
            ("(A) Baseline (quadratic)", res_a["lam"], res_a["tau"]),
            ("(B) No quadratic", lam_b, tau_b),
            ("(C) + Strata FE", lam_c, tau_c),
            ("(D) EB-based misfit", lam_d, tau_d),
            ("(E) Treatment only ($\\lambda$)", lam_e, np.nan),
        ]
        for spec_name, lam_v, tau_v in specs:
            rho_v = 2 * np.sqrt(lam_v * (-tau_v)) if (
                pd.notna(tau_v) and tau_v < 0 and lam_v > 0) else np.nan
            rows.append(dict(Study=label, Spec=spec_name,
                             lam=lam_v, tau=tau_v, rho=rho_v))
            rho_s = f"{rho_v:.4f}" if pd.notna(rho_v) else "---"
            tau_s = f"{tau_v:.4f}" if pd.notna(tau_v) else "---"
            print(f"  {label:12s} {spec_name:30s}  λ={lam_v:+.4f}  "
                  f"τ={tau_s}  ρ={rho_s}")

    rdf = pd.DataFrame(rows)

    # LaTeX table
    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Sensitivity of Structural Parameters to Specification}",
        r"\label{tab:calib_sensitivity}",
        r"\begin{tabular}{llrrr}", r"\toprule",
        r"Study & Specification & $\hat{\lambda}$ & $\hat{\tau}$ & $\hat{\rho}$ \\",
        r"\midrule"]
    prev_study = ""
    for _, r in rdf.iterrows():
        s = r["Study"] if r["Study"] != prev_study else ""
        tau_s = f"{r['tau']:.4f}" if pd.notna(r["tau"]) else "---"
        rho_s = f"{r['rho']:.4f}" if pd.notna(r["rho"]) else "---"
        tex.append(f"{s} & {r['Spec']} & {r['lam']:.4f} & {tau_s} & {rho_s} \\\\")
        if r["Study"] != prev_study and prev_study:
            tex.insert(-1, r"\addlinespace")
        prev_study = r["Study"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Baseline: $Y = -\lambda \cdot M + "
            r"\tau \cdot T + \gamma \cdot s + \delta \cdot s^2 + \varepsilon$ "
            r"with cluster-robust SEs.}", r"\end{table}"]
    path = OUT / "diag_r3_calib_sensitivity.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R3.3  Grade-specific calibration
# ═══════════════════════════════════════════════════════════════════════════════
def r3_grade_calibration():
    print("\n" + "=" * 70)
    print("R3.3: Grade-specific calibration")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        sub_all = _build_cal_data(df, cfg)
        grades = sorted(df["grade"].dropna().unique())

        # Pooled
        pt = _calibrate(sub_all, sub_all["ggroup"])
        rows.append(dict(Study=label, Grade="Pooled",
                         lam=pt["lam"], tau=pt["tau"], rho=pt["rho"],
                         N=pt["N"]))
        print(f"  {label} Pooled: λ={pt['lam']:.4f}  τ={pt['tau']:.4f}  "
              f"ρ={pt['rho']:.4f}" if pd.notna(pt["rho"])
              else f"  {label} Pooled: λ={pt['lam']:.4f}  τ={pt['tau']:.4f}  ρ=NA")

        for g in grades:
            sub_g = sub_all[sub_all["grade"] == g].copy()
            if len(sub_g) < 50:
                continue
            try:
                pt_g = _calibrate(sub_g, sub_g["ggroup"])

                ctrl_g = df[(df["treat"] == 0) & (df["grade"] == g) &
                            df["score_bl"].notna() & df["score_el"].notna()]
                r2_obs = (np.corrcoef(ctrl_g["score_bl"],
                                       ctrl_g["score_el"])[0, 1] ** 2
                          if len(ctrl_g) > 10 else np.nan)
                sigma2 = df.loc[(df["treat"] == 0) & (df["grade"] == g),
                                "std_score_bl"].var()
                r2s = _r2_star(pt_g["lam"], pt_g["rho"], sigma2)

                rows.append(dict(Study=label, Grade=f"G{int(g)}",
                                 lam=pt_g["lam"], tau=pt_g["tau"],
                                 rho=pt_g["rho"], r2_obs=r2_obs,
                                 r2_star=r2s, N=pt_g["N"]))
                rho_s = f"{pt_g['rho']:.4f}" if pd.notna(pt_g["rho"]) else "NA"
                r2s_s = f"{r2s:.4f}" if pd.notna(r2s) else "NA"
                print(f"  {label} G{int(g)}: λ={pt_g['lam']:.4f}  "
                      f"τ={pt_g['tau']:.4f}  ρ={rho_s}  "
                      f"r²_obs={r2_obs:.4f}  r²*={r2s_s}  N={pt_g['N']}")
            except Exception as e:
                print(f"  {label} G{int(g)}: FAILED ({e})")

    rdf = pd.DataFrame(rows)

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Grade-Specific Structural Calibration}",
        r"\label{tab:calib_grade}",
        r"\begin{tabular}{llrrrrrr}", r"\toprule",
        r"Study & Grade & $\hat{\lambda}$ & $\hat{\tau}$ & $\hat{\rho}$ & "
        r"$r^2_{\text{obs}}$ & $r^{2*}$ & $N$ \\", r"\midrule"]
    prev_study = ""
    for _, r in rdf.iterrows():
        s = r["Study"] if r["Study"] != prev_study else ""
        lam_s = f"{r['lam']:.3f}"
        tau_s = f"{r['tau']:.3f}"
        rho_s = f"{r['rho']:.3f}" if pd.notna(r.get("rho")) else "---"
        r2o_s = f"{r['r2_obs']:.3f}" if pd.notna(r.get("r2_obs")) else ""
        r2s_s = f"{r['r2_star']:.3f}" if pd.notna(r.get("r2_star")) else "---"
        if r["Study"] != prev_study and prev_study:
            tex.append(r"\addlinespace")
        tex.append(f"{s} & {r['Grade']} & {lam_s} & {tau_s} & {rho_s} & "
                   f"{r2o_s} & {r2s_s} & {int(r['N']):,d} \\\\")
        prev_study = r["Study"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small Grade-specific estimates of "
            r"$Y = -\lambda \cdot M + \tau \cdot T + \gamma \cdot s + "
            r"\delta \cdot s^2 + \varepsilon$. $r^{2*} = \rho^2 / "
            r"(4\lambda^2 \sigma^2)$.}", r"\end{table}"]
    path = OUT / "diag_r3_calib_grade.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")

    return rdf


# ═══════════════════════════════════════════════════════════════════════════════
# R3.4  Alternative misfit definitions
# ═══════════════════════════════════════════════════════════════════════════════
def r3_alt_misfit():
    print("\n" + "=" * 70)
    print("R3.4: Alternative misfit definitions and functional forms")
    print("=" * 70)

    rows = []
    for country, label in STUDIES:
        df, cfg = _load(country)
        sub = _build_cal_data(df, cfg)
        cl = sub["ggroup"]

        # A: Baseline (squared deviation from class mean BL)
        res_a = ols_cluster(sub["std_score_el"],
                             sub[["misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                             cl)
        lam_a = -res_a.params["misfit_bl"]

        # B: Absolute deviation (not squared)
        sub["abs_misfit_bl"] = np.abs(sub["std_score_bl"] - sub["_cm"])
        res_b = ols_cluster(sub["std_score_el"],
                             sub[["abs_misfit_bl", "treat", "std_score_bl", "std_bl_sq"]],
                             cl)
        lam_b = -res_b.params["abs_misfit_bl"]

        # C: Signed deviation (not absolute)
        sub["signed_misfit_bl"] = sub["std_score_bl"] - sub["_cm"]
        res_c = ols_cluster(sub["std_score_el"],
                             sub[["signed_misfit_bl", "treat", "std_score_bl",
                                  "std_bl_sq"]], cl)
        b_signed = res_c.params["signed_misfit_bl"]

        # D: Within-class rank
        sub["_class_id"] = np.where(sub["treat"] == 1, sub["std_grp"], sub["grade"])
        sub["rank_in_class"] = sub.groupby(
            ["academycode", "_class_id"]
        )["std_score_bl"].rank(pct=True)
        sub["rank_dev"] = (sub["rank_in_class"] - 0.5) ** 2
        res_d = ols_cluster(sub["std_score_el"],
                             sub[["rank_dev", "treat", "std_score_bl", "std_bl_sq"]],
                             cl)
        lam_d = -res_d.params["rank_dev"]

        # E: Misfit using the variable already in data (from cleaning script)
        if "misfit" in sub.columns and sub["misfit"].notna().sum() > 50:
            res_e = ols_cluster(sub["std_score_el"],
                                 sub[["misfit", "treat", "std_score_bl", "std_bl_sq"]],
                                 cl)
            lam_e = -res_e.params["misfit"]
        else:
            lam_e = np.nan

        for spec, lam_v, note in [
            ("Squared dev (baseline)", lam_a, ""),
            ("Absolute dev", lam_b, ""),
            ("Signed dev", b_signed, "(positive = above class mean helps)"),
            ("Rank-based dev", lam_d, ""),
            ("Pre-built misfit (EB)", lam_e, "")]:
            rows.append(dict(Study=label, Spec=spec, lam=lam_v))
            print(f"  {label:12s} {spec:30s}  coef={lam_v:+.4f}  {note}")

    rdf = pd.DataFrame(rows)

    tex = [
        r"\begin{table}[htbp]", r"\centering\small",
        r"\caption{Alternative Misfit Definitions}",
        r"\label{tab:alt_misfit}",
        r"\begin{tabular}{llr}", r"\toprule",
        r"Study & Misfit definition & Coefficient \\", r"\midrule"]
    prev = ""
    for _, r in rdf.iterrows():
        s = r["Study"] if r["Study"] != prev else ""
        v = f"{r['lam']:.4f}" if pd.notna(r["lam"]) else "---"
        if r["Study"] != prev and prev:
            tex.append(r"\addlinespace")
        tex.append(f"{s} & {r['Spec']} & {v} \\\\")
        prev = r["Study"]
    tex += [r"\bottomrule", r"\end{tabular}",
            r"\par\smallskip\noindent{\small All specifications: "
            r"$Y_i = \beta_0 + \text{coef} \cdot \text{misfit}_i + \tau T_i "
            r"+ \gamma s_i + \delta s_i^2 + \varepsilon_i$. For squared/absolute/rank "
            r"definitions, $-\text{coef} = \hat{\lambda}$. For signed deviation, "
            r"the coefficient directly measures the return to being above "
            r"class mean.}", r"\end{table}"]
    path = OUT / "diag_r3_alt_misfit.tex"
    path.write_text("\n".join(tex))
    print(f"\n  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# R3.5  Summary figure: calibration across studies
# ═══════════════════════════════════════════════════════════════════════════════
def r3_summary_figure():
    print("\n" + "=" * 70)
    print("R3.5: Calibration summary figure")
    print("=" * 70)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    colors = {"Liberia": "#C44E52", "Kenya Y1": "#4C72B0", "Kenya Y2": "#55A868"}

    param_data = {}
    for country, label in STUDIES:
        df, cfg = _load(country)
        sub = _build_cal_data(df, cfg)
        pt = _calibrate(sub, sub["ggroup"])
        grades = sorted(df["grade"].dropna().unique())

        grade_data = []
        for g in grades:
            ctrl_g = df[(df["treat"] == 0) & (df["grade"] == g) &
                        df["score_bl"].notna() & df["score_el"].notna()]
            r2_obs = (np.corrcoef(ctrl_g["score_bl"],
                                   ctrl_g["score_el"])[0, 1] ** 2
                      if len(ctrl_g) > 10 else np.nan)
            sigma2 = df.loc[(df["treat"] == 0) & (df["grade"] == g),
                            "std_score_bl"].var()
            r2s = _r2_star(pt["lam"], pt["rho"], sigma2)
            grade_data.append(dict(grade=g, r2_obs=r2_obs, r2_star=r2s,
                                    sigma2=sigma2))
        param_data[label] = dict(pt=pt, grades=grade_data)

    # Panel A: Lambda across studies
    ax = axes[0]
    labels = [l for _, l in STUDIES]
    lams = [param_data[l]["pt"]["lam"] for l in labels]
    se_lams = [param_data[l]["pt"]["se_lam"] for l in labels]
    x = np.arange(len(labels))
    ax.bar(x, lams, yerr=[1.96 * s for s in se_lams], capsize=5,
           color=[colors[l] for l in labels], alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel(r"$\hat{\lambda}$ (return to match)")
    ax.axhline(0, color="gray", ls="--", lw=0.8)
    ax.set_title(r"(a) $\hat{\lambda}$")

    # Panel B: Tau across studies
    ax = axes[1]
    taus = [param_data[l]["pt"]["tau"] for l in labels]
    se_taus = [param_data[l]["pt"]["se_tau"] for l in labels]
    ax.bar(x, taus, yerr=[1.96 * s for s in se_taus], capsize=5,
           color=[colors[l] for l in labels], alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel(r"$\hat{\tau}$ (net tracking effect)")
    ax.axhline(0, color="gray", ls="--", lw=0.8)
    ax.set_title(r"(b) $\hat{\tau}$")

    # Panel C: r² observed vs r²* threshold
    ax = axes[2]
    all_pts = []
    for label_s in labels:
        for gd in param_data[label_s]["grades"]:
            if pd.notna(gd["r2_obs"]):
                all_pts.append((label_s, gd["grade"], gd["r2_obs"], gd.get("r2_star")))

    for label_s, g, r2o, r2s in all_pts:
        ax.scatter(r2o, r2s if pd.notna(r2s) else 0, color=colors[label_s],
                   s=80, zorder=5, edgecolors="white", linewidth=0.5)
        ax.annotate(f"G{int(g)}", (r2o, r2s if pd.notna(r2s) else 0),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points")

    r2_range = np.linspace(0, 0.7, 100)
    ax.plot(r2_range, r2_range, "k--", lw=1, alpha=0.5, label=r"$r^2 = r^{2*}$")
    ax.set_xlabel(r"$r^2_{\mathrm{obs}}$ (diagnostic reliability)")
    ax.set_ylabel(r"$r^{2*}$ (threshold)")
    ax.set_title(r"(c) Observed vs.\ threshold $r^2$")
    ax.legend(fontsize=8)

    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker="o", color="w",
                               markerfacecolor=colors[l], markersize=8, label=l)
                       for l in labels]
    ax.legend(handles=legend_elements, fontsize=8, loc="upper left")

    fig.suptitle("Structural Calibration Summary", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path = OUT / "diag_r3_calib_summary.pdf"
    fig.savefig(path, dpi=200)
    plt.close()
    print(f"  -> {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    r3_bootstrap_calibration()
    r3_sensitivity()
    r3_grade_calibration()
    r3_alt_misfit()
    r3_summary_figure()
    print("\n" + "=" * 70)
    print("✓ Round 3 calibration robustness complete.")
    print("=" * 70)
