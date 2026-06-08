#!/usr/bin/env python3
"""
bootstrap_counterfactuals.py
============================
Bootstrap uncertainty and counterfactuals for the structural extension.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from model_primitives import unpack_params, market_outcome_itt, MARKETS
from simulate_markets import build_target_set
import estimate_smm as est


SEED = 20260403
RNG = np.random.default_rng(SEED)
OUT_DIR = Path(__file__).resolve().parent / "output" / "structural_smm"


def _load_latest_raw_params() -> np.ndarray:
    p = OUT_DIR / "smm_parameter_raw_vector.csv"
    if not p.exists():
        raise FileNotFoundError(f"Missing parameter file: {p}. Run estimate_smm.py first.")
    df = pd.read_csv(p)
    return df.sort_values("raw_index")["raw_value"].to_numpy(float)


def _scenario_values(raw: np.ndarray) -> dict[str, float]:
    par = unpack_params(raw)
    out = {}

    # Observed
    out["kenya_observed"] = market_outcome_itt(par, "kenya")
    out["liberia_observed"] = market_outcome_itt(par, "liberia")
    out["nigeria_realized"] = market_outcome_itt(par, "nigeria")

    # 1) Missing high-rho, high-tau cell:
    # Kenya high-rho assignment environment, elevate tau, hold high execution.
    rho_k = par.rho["kenya"]
    ex_k = max(par.exec_q["kenya"], 0.90)
    tau_hi = 0.90
    zeta_ref = par.zeta["kenya"]
    out["kenya_high_tau_counterfactual"] = float(
        par.alpha0
        + par.alpha_rho * rho_k
        + par.alpha_tau * tau_hi
        + par.alpha_soc * zeta_ref
        + par.alpha_exec * ex_k
    )

    # 2) Designed vs realized Nigeria: intended deterministic 3-track execution.
    rho_n = par.rho["nigeria"]
    tau_n = par.tau["nigeria"]
    zeta_n = par.zeta["nigeria"]
    ex_designed = 0.95
    out["nigeria_designed_counterfactual"] = float(
        par.alpha0
        + par.alpha_rho * rho_n
        + par.alpha_tau * tau_n
        + par.alpha_soc * zeta_n
        + par.alpha_exec * ex_designed
    )
    out["nigeria_gap_due_to_execution"] = out["nigeria_designed_counterfactual"] - out["nigeria_realized"]

    # 3) One-at-a-time decompositions for Nigeria
    out["nigeria_rho_only_counterfactual"] = float(
        par.alpha0
        + par.alpha_rho * par.rho["kenya"]  # transplant high-rho environment
        + par.alpha_tau * tau_n
        + par.alpha_soc * zeta_n
        + par.alpha_exec * par.exec_q["nigeria"]
    )
    out["nigeria_tau_only_counterfactual"] = float(
        par.alpha0
        + par.alpha_rho * rho_n
        + par.alpha_tau * par.tau["kenya"]  # transplant higher-fidelity benchmark
        + par.alpha_soc * zeta_n
        + par.alpha_exec * par.exec_q["nigeria"]
    )
    out["nigeria_exec_only_counterfactual"] = float(
        par.alpha0
        + par.alpha_rho * rho_n
        + par.alpha_tau * tau_n
        + par.alpha_soc * zeta_n
        + par.alpha_exec * ex_designed
    )
    return out


def _perturb_targets(targets: pd.DataFrame) -> pd.DataFrame:
    b = targets.copy()
    vals = b["value"].to_numpy(float)
    vars_ = b["variance_for_weight"].to_numpy(float)
    shocks = RNG.normal(0.0, np.sqrt(np.maximum(vars_, 1e-8)))
    b["value"] = vals + shocks
    return b


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=30)
    parser.add_argument("--starts", type=int, default=3)
    args = parser.parse_args()

    moments_path = OUT_DIR / "empirical_moments.csv"
    if not moments_path.exists():
        raise FileNotFoundError(f"Missing moments file: {moments_path}. Run empirical_moments.py first.")
    all_moments = pd.read_csv(moments_path)
    targets = build_target_set(all_moments)

    raw_hat = _load_latest_raw_params()
    base_sc = _scenario_values(raw_hat)
    base_df = pd.DataFrame([{"scenario": k, "value": v} for k, v in base_sc.items()])
    base_df.to_csv(OUT_DIR / "counterfactuals_point_estimates.csv", index=False)

    # Bootstrap by perturbing moment targets and re-estimating
    boot_rows = []
    fail = 0
    for b in range(args.n_boot):
        tb = _perturb_targets(targets)
        try:
            raw_b, _ = est._run_multistart(tb, n_starts=args.starts, use_de_fallback=False)  # noqa: SLF001
            sc_b = _scenario_values(raw_b)
            for k, v in sc_b.items():
                boot_rows.append({"boot_id": b, "scenario": k, "value": v})
        except Exception:
            fail += 1
            continue

    boot_df = pd.DataFrame(boot_rows)
    boot_df.to_csv(OUT_DIR / "counterfactuals_bootstrap_draws.csv", index=False)

    if len(boot_df) > 0:
        ci = (
            boot_df.groupby("scenario")["value"]
            .agg(
                boot_mean="mean",
                p05=lambda x: np.quantile(x, 0.05),
                p50=lambda x: np.quantile(x, 0.50),
                p95=lambda x: np.quantile(x, 0.95),
                n_boot="count",
            )
            .reset_index()
        )
    else:
        ci = pd.DataFrame(columns=["scenario", "boot_mean", "p05", "p50", "p95", "n_boot"])

    final = base_df.merge(ci, on="scenario", how="left")
    final["bootstrap_failures"] = fail
    final.to_csv(OUT_DIR / "counterfactuals_with_ci.csv", index=False)

    print("=" * 72)
    print("Counterfactual bootstrap complete")
    print("=" * 72)
    print(f"Bootstrap draws requested: {args.n_boot}")
    print(f"Bootstrap failures: {fail}")
    print(f"Saved: {OUT_DIR / 'counterfactuals_with_ci.csv'}")
    print(final.to_string(index=False))


if __name__ == "__main__":
    main()
