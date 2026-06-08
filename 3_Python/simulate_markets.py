"""
simulate_markets.py
===================
Moment simulation layer for first-pass SMM.

For this stage we simulate moments directly from parsimonious structural mappings,
anchored to the reduced-form moments file.
"""

from __future__ import annotations

from typing import Dict
import numpy as np
import pandas as pd

from model_primitives import (
    MARKETS,
    NaturalParams,
    market_dispersion,
    market_outcome_itt,
    market_peer_shift,
    nigeria_impl_moments,
)


def _select_target_moments(moments: pd.DataFrame) -> pd.DataFrame:
    """
    Keep a curated subset for stable first-pass optimization:
    - market signal quality (incremental R2)
    - ITT
    - peer/rank composite beta
    - dispersion first stage
    - peer mean reallocation
    - Nigeria implementation external targets
    """
    keep_rows = []
    for _, r in moments.iterrows():
        mkt = r["market"]
        cat = r["category"]
        mom = r["moment"]
        src = r["source"]

        if cat == "measurement" and mom == "incremental_r2_over_grade_fe":
            keep_rows.append(True)
        elif cat == "outcomes" and mom in {"itt_main", "peer_rank_composite_beta"}:
            keep_rows.append(True)
        elif cat == "assignment_reallocation" and mom in {"te_within_class_dispersion", "te_peer_mean"}:
            keep_rows.append(True)
        elif mkt == "nigeria" and cat == "implementation_nigeria_external":
            keep_rows.append(True)
        elif mkt == "nigeria" and cat == "implementation_nigeria":
            keep_rows.append(True)
        else:
            keep_rows.append(False)
    out = moments.loc[np.array(keep_rows)].copy()

    # Override Nigeria ITT with harmonized Stata target from pooled exercise
    # (prevents scaling mismatch from mixed cleaned sources).
    idx = (out["market"] == "nigeria") & (out["category"] == "outcomes") & (out["moment"] == "itt_main")
    if idx.any():
        out.loc[idx, "value"] = 0.105
        out.loc[idx, "variance"] = 0.132**2
        out.loc[idx, "variance_for_weight"] = 0.132**2
        out.loc[idx, "weight"] = 1.0 / (0.132**2)
        out.loc[idx, "notes"] = out.loc[idx, "notes"].astype(str) + " | overridden to harmonized Stata idx_t3_ete ITT target"
    return out


def simulate_moments(par: NaturalParams, target_moments: pd.DataFrame) -> pd.DataFrame:
    """
    Produce simulated counterparts for each selected empirical target moment.
    """
    sim = target_moments.copy()
    sim["sim_value"] = np.nan

    ng_impl = nigeria_impl_moments(par)

    for i, r in sim.iterrows():
        mkt = r["market"]
        cat = r["category"]
        mom = r["moment"]

        if cat == "measurement" and mom == "incremental_r2_over_grade_fe":
            sim.at[i, "sim_value"] = par.rho[mkt]
        elif cat == "outcomes" and mom == "itt_main":
            sim.at[i, "sim_value"] = market_outcome_itt(par, mkt)
        elif cat == "outcomes" and mom == "peer_rank_composite_beta":
            sim.at[i, "sim_value"] = par.zeta[mkt]
        elif cat == "assignment_reallocation" and mom == "te_within_class_dispersion":
            sim.at[i, "sim_value"] = market_dispersion(par, mkt)
        elif cat == "assignment_reallocation" and mom == "te_peer_mean":
            sim.at[i, "sim_value"] = market_peer_shift(par, mkt)
        elif mkt == "nigeria" and cat in {"implementation_nigeria_external", "implementation_nigeria"}:
            sim.at[i, "sim_value"] = ng_impl.get(mom, np.nan)
        else:
            sim.at[i, "sim_value"] = np.nan

    sim["error"] = sim["value"] - sim["sim_value"]
    sim["weighted_sq_error"] = sim["weight"] * (sim["error"] ** 2)
    return sim


def objective_value(par: NaturalParams, target_moments: pd.DataFrame) -> float:
    sim = simulate_moments(par, target_moments)
    if sim["weighted_sq_error"].isna().all():
        return 1e9
    return float(np.nansum(sim["weighted_sq_error"]))


def high_rho_high_tau_itt(par: NaturalParams) -> float:
    """
    Counterfactual point summary used in console diagnostics:
    keep structural slopes, set rho=tau=0.9 and execution=0.95, with Kenya social loading.
    """
    rho = 0.90
    tau = 0.90
    ex = 0.95
    zeta_ref = par.zeta["kenya"]
    return float(par.alpha0 + par.alpha_rho * rho + par.alpha_tau * tau + par.alpha_soc * zeta_ref + par.alpha_exec * ex)


def build_target_set(moments: pd.DataFrame) -> pd.DataFrame:
    return _select_target_moments(moments)
