#!/usr/bin/env python3
"""
Nigeria full-stack replication bundle aligned to the Kenya/Liberia paper pipeline.

Outputs are written to:
  3_Python/output/ng_full_stack/
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm

from config import get_config
from utils import ols_cluster


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "ng_full_stack"
OUT.mkdir(parents=True, exist_ok=True)


def _safe_to_float(v):
    try:
        return float(v)
    except Exception:
        return np.nan


def _stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _md_table(df: pd.DataFrame, digits: int = 4) -> str:
    if df is None or len(df) == 0:
        return "_No rows._"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in df.iterrows():
        row = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                row.append(f"{v:.{digits}f}")
            else:
                row.append(str(v))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _load_data():
    cfg_ng = get_config("nigeria")
    cfg_ke = get_config("kenya")
    cfg_lb = get_config("liberia")
    ng = pd.read_parquet(cfg_ng["ANALYSIS_FILE"])
    ke = pd.read_parquet(cfg_ke["ANALYSIS_FILE"])
    lb = pd.read_parquet(cfg_lb["ANALYSIS_FILE"])
    return (ng, cfg_ng), (ke, cfg_ke), (lb, cfg_lb)


def create_estimand_crosswalk():
    rows = [
        {
            "estimand": "Treatment assignment unit",
            "liberia": "school-grade group (cluster ggroup)",
            "kenya": "academy (cluster academycode)",
            "nigeria": "academy (cluster academycode; from placement file)",
            "nigeria_var": "treat",
            "comparability": "high",
        },
        {
            "estimand": "Primary endline outcome",
            "liberia": "std_score_el",
            "kenya": "std_score_el",
            "nigeria": "std_score_el (T3 ETE numeracy), plus std_score_el_math",
            "nigeria_var": "std_score_el / std_score_el_math",
            "comparability": "medium",
        },
        {
            "estimand": "Baseline signal",
            "liberia": "score_bl",
            "kenya": "score_bl (composite)",
            "nigeria": "score_bl (T1 ETE maths, cross-subject to numeracy endline)",
            "nigeria_var": "score_bl, std_eb",
            "comparability": "medium-low",
        },
        {
            "estimand": "Assignment rule",
            "liberia": "grade-specific cutoff",
            "kenya": "grade-specific cutoff",
            "nigeria": "placement group labels mapped to std_grp; fallback terciles",
            "nigeria_var": "std_grp, upper_group, group",
            "comparability": "medium",
        },
        {
            "estimand": "Peer composition",
            "liberia": "peer_eb",
            "kenya": "peer_eb",
            "nigeria": "peer_eb with treated track vs control grade counterfactuals",
            "nigeria_var": "peer_eb, peer_eb_treat, peer_eb_ctrl, exp_peer_eb",
            "comparability": "high",
        },
        {
            "estimand": "Dispersion / mismatch channels",
            "liberia": "dev_eb, misfit, csize",
            "kenya": "dev_eb, misfit, csize",
            "nigeria": "dev_eb, misfit, csize, dist_from_cutoff",
            "nigeria_var": "dev_eb, misfit, csize, dist_from_cutoff",
            "comparability": "high",
        },
        {
            "estimand": "Propensity for BH recentering",
            "liberia": "P_t by strata",
            "kenya": "P_t by constituency design strata",
            "nigeria": "P_t by constituency strata",
            "nigeria_var": "P_t, P_c, strata",
            "comparability": "medium-high",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "ng_estimand_crosswalk.csv", index=False)
    with open(OUT / "ng_estimand_crosswalk.md", "w", encoding="utf-8") as f:
        f.write("# Nigeria-Liberia-Kenya estimand crosswalk\n\n")
        f.write(_md_table(df, digits=3))
        f.write(
            "\n\nNotes:\n"
            "- Nigeria treatment assignment is anchored to placement-file truth.\n"
            "- Nigeria baseline-endline link is cross-subject (maths baseline, numeracy endline), so reliability differs.\n"
        )
    return df


def _run_itt(df: pd.DataFrame, yvar: str, cluster_var: str = "academycode") -> Tuple[float, float, float, int]:
    d = df[df["finsamp"] == 1].copy()
    d = d[d[yvar].notna() & d["treat"].notna() & d["std_eb"].notna() & d["strata"].notna()]
    if len(d) < 50:
        return np.nan, np.nan, np.nan, len(d)
    fe = pd.get_dummies(d["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
    X = pd.concat([d[["treat", "std_eb"]].astype(float), fe], axis=1)
    res = ols_cluster(d[yvar].astype(float), X, d[cluster_var])
    return float(res.params["treat"]), float(res.bse["treat"]), float(res.pvalues["treat"]), len(d)


def run_main_diagnostics(ng: pd.DataFrame):
    rows = []
    for y in ["std_score_el", "std_score_el_math", "dev_eb", "csize", "peer_eb"]:
        b, se, p, n = _run_itt(ng, y)
        rows.append(
            {
                "outcome": y,
                "coef_treat": b,
                "se_treat": se,
                "p_treat": p,
                "n": n,
                "control_mean": _safe_to_float(ng.loc[(ng["finsamp"] == 1) & (ng["treat"] == 0), y].mean()),
            }
        )
    itt = pd.DataFrame(rows)
    itt.to_csv(OUT / "ng_main_itt_mechanisms.csv", index=False)

    # Sample flow + balance basics.
    sf = pd.DataFrame(
        [
            {"step": "all_rows", "n": len(ng)},
            {"step": "non_missing_treat", "n": int(ng["treat"].notna().sum())},
            {"step": "has_bl", "n": int(ng["has_bl"].sum())},
            {"step": "finsamp", "n": int(ng["finsamp"].sum())},
            {"step": "finsamp_has_el", "n": int((ng["finsamp"] & ng["has_el"]).sum())},
        ]
    )
    sf.to_csv(OUT / "ng_sample_flow.csv", index=False)

    bal = []
    for v in ["score_bl", "std_eb", "upper_group", "has_el", "csize"]:
        d = ng[(ng["finsamp"] == 1) & ng[v].notna()].copy()
        if len(d) < 50:
            continue
        fe = pd.get_dummies(d["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
        X = pd.concat([d[["treat"]].astype(float), fe], axis=1)
        r = ols_cluster(d[v].astype(float), X, d["academycode"])
        bal.append(
            {
                "var": v,
                "mean_treat": float(d.loc[d["treat"] == 1, v].mean()),
                "mean_control": float(d.loc[d["treat"] == 0, v].mean()),
                "diff": float(r.params["treat"]),
                "se": float(r.bse["treat"]),
                "p": float(r.pvalues["treat"]),
            }
        )
    bal_df = pd.DataFrame(bal)
    bal_df.to_csv(OUT / "ng_balance_checks.csv", index=False)

    with open(OUT / "ng_main_diagnostics_note.md", "w", encoding="utf-8") as f:
        f.write("# Nigeria main diagnostics and ITT bundle\n\n")
        f.write("## ITT and mechanism outcomes\n\n")
        f.write(_md_table(itt, digits=4))
        f.write("\n\n## Sample flow\n\n")
        f.write(_md_table(sf, digits=2))
        f.write("\n\n## Balance checks\n\n")
        f.write(_md_table(bal_df, digits=4))
    return itt, sf, bal_df


def run_structural_peer(ng: pd.DataFrame):
    d = ng[(ng["finsamp"] == 1) & ng["std_score_el"].notna() & ng["bl_decile"].notna()].copy()
    d = d[d["peer_eb"].notna() & d["exp_peer_eb"].notna() & d["strata"].notna()]
    d["cell"] = d["bl_decile"].astype(int) * 10 + d["treat"].astype(int)
    dtfe = pd.get_dummies(d["cell"].astype(str), prefix="dt", drop_first=True, dtype=float)
    sfe = pd.get_dummies(d["strata"].astype(str), prefix="s", drop_first=True, dtype=float)

    # Baseline BH.
    X0 = pd.concat([d[["peer_eb"]].astype(float), dtfe, sfe], axis=1)
    r0 = ols_cluster(d["std_score_el"].astype(float), X0, d["academycode"])

    # Control-function exact BH.
    d["peer_tilde"] = d["peer_eb"] - d["exp_peer_eb"]
    X1 = pd.concat([d[["peer_tilde", "exp_peer_eb"]].astype(float), dtfe, sfe], axis=1)
    r1 = ols_cluster(d["std_score_el"].astype(float), X1, d["academycode"])

    # Recentered-only.
    X2 = pd.concat([d[["peer_tilde"]].astype(float), dtfe, sfe], axis=1)
    r2 = ols_cluster(d["std_score_el"].astype(float), X2, d["academycode"])

    # First-stage residualized variation.
    cell_mean = d.groupby("cell")["peer_eb"].transform("mean")
    resid = d["peer_eb"] - cell_mean
    fs = pd.DataFrame(
        [
            {
                "metric": "sd_peer_total",
                "value": float(d["peer_eb"].std()),
            },
            {
                "metric": "sd_peer_within_cell",
                "value": float(resid.std()),
            },
            {
                "metric": "share_within_cell_variance",
                "value": float((resid.std() / d["peer_eb"].std()) ** 2) if d["peer_eb"].std() > 0 else np.nan,
            },
            {"metric": "corr_peer_exppeer", "value": float(d["peer_eb"].corr(d["exp_peer_eb"]))},
        ]
    )
    fs.to_csv(OUT / "ng_bh_firststage_diagnostics.csv", index=False)

    tab = pd.DataFrame(
        [
            {
                "spec": "bh_baseline_peer_eb",
                "coef": float(r0.params["peer_eb"]),
                "se": float(r0.bse["peer_eb"]),
                "p": float(r0.pvalues["peer_eb"]),
                "n": len(d),
            },
            {
                "spec": "bh_control_function_peer_tilde",
                "coef": float(r1.params["peer_tilde"]),
                "se": float(r1.bse["peer_tilde"]),
                "p": float(r1.pvalues["peer_tilde"]),
                "n": len(d),
            },
            {
                "spec": "bh_control_function_exp_peer",
                "coef": float(r1.params["exp_peer_eb"]),
                "se": float(r1.bse["exp_peer_eb"]),
                "p": float(r1.pvalues["exp_peer_eb"]),
                "n": len(d),
            },
            {
                "spec": "bh_recentered_only",
                "coef": float(r2.params["peer_tilde"]),
                "se": float(r2.bse["peer_tilde"]),
                "p": float(r2.pvalues["peer_tilde"]),
                "n": len(d),
            },
        ]
    )
    tab.to_csv(OUT / "ng_structural_peer_bh.csv", index=False)
    with open(OUT / "ng_structural_peer_bh_note.md", "w", encoding="utf-8") as f:
        f.write("# Nigeria structural/peer/BH diagnostics\n\n")
        f.write("## BH regressions\n\n")
        f.write(_md_table(tab, digits=4))
        f.write("\n\n## First-stage diagnostics\n\n")
        f.write(_md_table(fs, digits=4))
    return tab, fs


def run_assignment_heterogeneity(ng: pd.DataFrame):
    d = ng[(ng["finsamp"] == 1) & ng["std_score_el"].notna()].copy()
    d = d[d["score_bl"].notna() & d["std_eb"].notna() & d["strata"].notna()]
    d["mover"] = (d["std_grp"].astype(float) != d["grade"].astype(float)).astype(int)

    # H1: mover heterogeneity
    fe = pd.get_dummies(d["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
    d["treat_x_mover"] = d["treat"] * d["mover"]
    X = pd.concat([d[["treat", "mover", "treat_x_mover", "std_eb"]].astype(float), fe], axis=1)
    r_mover = ols_cluster(d["std_score_el"].astype(float), X, d["academycode"])

    # H2: distance interaction among movers.
    dm = d[d["mover"] == 1].copy()
    dm["treat_x_dist"] = dm["treat"] * dm["dist_from_cutoff"]
    fe_m = pd.get_dummies(dm["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
    Xm = pd.concat([dm[["treat", "dist_from_cutoff", "treat_x_dist", "std_eb"]].astype(float), fe_m], axis=1)
    r_dist = ols_cluster(dm["std_score_el"].astype(float), Xm, dm["academycode"])

    # H3/H4: control-only mismatch and dispersion.
    dc = d[d["treat"] == 0].copy()
    fe_c = pd.get_dummies(dc["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
    Xmis = pd.concat([dc[["misfit", "std_eb"]].astype(float), fe_c], axis=1)
    r_mis = ols_cluster(dc["std_score_el"].astype(float), Xmis, dc["academycode"])
    Xdisp = pd.concat([dc[["dev_eb_ctrl", "std_eb"]].astype(float), fe_c], axis=1)
    r_disp = ols_cluster(dc["std_score_el"].astype(float), Xdisp, dc["academycode"])

    # H5: grade-specific ITT.
    grade_rows = []
    for g in sorted(d["grade"].dropna().unique()):
        dg = d[d["grade"] == g].copy()
        if len(dg) < 80 or dg["treat"].nunique() < 2:
            continue
        feg = pd.get_dummies(dg["strata"].astype(str), prefix="s", drop_first=True, dtype=float)
        Xg = pd.concat([dg[["treat", "std_eb"]].astype(float), feg], axis=1)
        rg = ols_cluster(dg["std_score_el"].astype(float), Xg, dg["academycode"])
        grade_rows.append(
            {
                "grade": int(g),
                "coef_treat": float(rg.params["treat"]),
                "se_treat": float(rg.bse["treat"]),
                "p_treat": float(rg.pvalues["treat"]),
                "n": len(dg),
            }
        )
    grade_df = pd.DataFrame(grade_rows)

    summary = pd.DataFrame(
        [
            {"test": "mover_main_treat", "coef": float(r_mover.params["treat"]), "se": float(r_mover.bse["treat"]), "p": float(r_mover.pvalues["treat"])},
            {"test": "mover_interaction_treat_x_mover", "coef": float(r_mover.params["treat_x_mover"]), "se": float(r_mover.bse["treat_x_mover"]), "p": float(r_mover.pvalues["treat_x_mover"])},
            {"test": "distance_interaction_movers", "coef": float(r_dist.params["treat_x_dist"]), "se": float(r_dist.bse["treat_x_dist"]), "p": float(r_dist.pvalues["treat_x_dist"])},
            {"test": "control_mismatch_effect", "coef": float(r_mis.params["misfit"]), "se": float(r_mis.bse["misfit"]), "p": float(r_mis.pvalues["misfit"])},
            {"test": "control_dispersion_effect", "coef": float(r_disp.params["dev_eb_ctrl"]), "se": float(r_disp.bse["dev_eb_ctrl"]), "p": float(r_disp.pvalues["dev_eb_ctrl"])},
        ]
    )
    summary.to_csv(OUT / "ng_assignment_heterogeneity_summary.csv", index=False)
    grade_df.to_csv(OUT / "ng_grade_specific_itt.csv", index=False)

    with open(OUT / "ng_assignment_heterogeneity_note.md", "w", encoding="utf-8") as f:
        f.write("# Nigeria assignment-channel heterogeneity diagnostics\n\n")
        f.write("## Core heterogeneity tests\n\n")
        f.write(_md_table(summary, digits=4))
        f.write("\n\n## Grade-specific ITT\n\n")
        f.write(_md_table(grade_df, digits=4))
    return summary, grade_df


def run_integration_decision(ng: pd.DataFrame, ke: pd.DataFrame, lb: pd.DataFrame):
    def reliability(df):
        c = df[(df["finsamp"] == 1) & (df["treat"] == 0) & df["score_bl"].notna() & df["score_el"].notna()]
        if len(c) < 40:
            return np.nan
        return float(c["score_bl"].corr(c["score_el"]) ** 2)

    def itt(df, cluster):
        b, se, p, n = _run_itt(df, "std_score_el", cluster)
        return b, se, p, n

    rows = []
    for name, df, cl in [("Liberia", lb, "ggroup"), ("Kenya", ke, "academycode"), ("Nigeria", ng, "academycode")]:
        b, se, p, n = itt(df, cl)
        rows.append(
            {
                "experiment": name,
                "n_finsamp": int(df["finsamp"].sum()),
                "schools": int(df.loc[df["finsamp"] == 1, "academycode"].nunique()),
                "reliability_r2_control": reliability(df),
                "itt_std_score_el": b,
                "itt_se": se,
                "itt_p": p,
            }
        )
    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "third_experiment_comparability_table.csv", index=False)

    # Decision heuristic.
    ng_row = comp[comp["experiment"] == "Nigeria"].iloc[0]
    coherent = bool(
        pd.notna(ng_row["reliability_r2_control"])
        and ng_row["schools"] >= 20
        and pd.notna(ng_row["itt_std_score_el"])
    )
    recommendation = (
        "Add Nigeria as a third experiment in a robustness/extension section first."
        if coherent
        else "Do not add Nigeria yet; additional design harmonization is required."
    )
    with open(OUT / "third_experiment_decision_memo.md", "w", encoding="utf-8") as f:
        f.write("# Third-experiment integration memo (Nigeria)\n\n")
        f.write("## Cross-country comparability snapshot\n\n")
        f.write(_md_table(comp, digits=4))
        f.write("\n\n## Recommendation\n\n")
        f.write(f"- {recommendation}\n")
        f.write(
            "- Nigeria is most comparable on assignment/peer mechanics and clustering, "
            "but differs in baseline-endline subject alignment and sample architecture.\n"
        )
        f.write(
            "- Suggested paper placement: extension experiment with aligned ITT/mechanism "
            "tables and transparent caveats on comparability.\n"
        )
    return comp, recommendation


def main():
    (ng, cfg_ng), (ke, cfg_ke), (lb, cfg_lb) = _load_data()
    # Ensure no stale assumptions about sample flags.
    ng["finsamp"] = ng["finsamp"].fillna(False).astype(bool)
    ke["finsamp"] = ke["finsamp"].fillna(False).astype(bool)
    lb["finsamp"] = lb["finsamp"].fillna(False).astype(bool)

    crosswalk = create_estimand_crosswalk()
    itt, sf, bal = run_main_diagnostics(ng)
    bh_tab, bh_fs = run_structural_peer(ng)
    het_summary, grade_df = run_assignment_heterogeneity(ng)
    comp, rec = run_integration_decision(ng, ke, lb)

    # One index manifest for easy review.
    manifest = pd.DataFrame(
        [
            {"artifact": "estimand_crosswalk", "file": "ng_estimand_crosswalk.csv"},
            {"artifact": "main_itt_mechanisms", "file": "ng_main_itt_mechanisms.csv"},
            {"artifact": "sample_flow", "file": "ng_sample_flow.csv"},
            {"artifact": "balance_checks", "file": "ng_balance_checks.csv"},
            {"artifact": "structural_peer_bh", "file": "ng_structural_peer_bh.csv"},
            {"artifact": "bh_firststage_diag", "file": "ng_bh_firststage_diagnostics.csv"},
            {"artifact": "heterogeneity_summary", "file": "ng_assignment_heterogeneity_summary.csv"},
            {"artifact": "grade_specific_itt", "file": "ng_grade_specific_itt.csv"},
            {"artifact": "comparability_table", "file": "third_experiment_comparability_table.csv"},
            {"artifact": "decision_memo", "file": "third_experiment_decision_memo.md"},
        ]
    )
    manifest.to_csv(OUT / "ng_full_stack_manifest.csv", index=False)

    print("Nigeria full-stack replication complete.")
    print(f"Output directory: {OUT}")
    print(f"Recommendation: {rec}")


if __name__ == "__main__":
    main()
