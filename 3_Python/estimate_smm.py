#!/usr/bin/env python3
"""
estimate_smm.py
===============
First-pass SMM optimizer launch on empirical moments.

This script:
- reads empirical moments built by empirical_moments.py
- selects a stable target subset for first-pass fitting
- runs multi-start optimization (and optional two-step weighting)
- writes fitted moments and parameter tables
- prints key diagnostics requested by paper workflow
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution

from model_primitives import unpack_params, MARKETS
from simulate_markets import build_target_set, simulate_moments, objective_value, high_rho_high_tau_itt


SEED = 20260403
RNG = np.random.default_rng(SEED)

OUT_DIR = Path(__file__).resolve().parent / "output" / "structural_smm"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _objective_raw(raw: np.ndarray, targets: pd.DataFrame) -> float:
    try:
        par = unpack_params(raw)
        fit = objective_value(par, targets)
        ridge = 0.02 * float(np.mean(np.square(raw)))
        return fit + ridge
    except Exception:
        return 1e12


def _run_multistart(
    targets: pd.DataFrame,
    n_starts: int = 24,
    use_de_fallback: bool = True,
) -> tuple[np.ndarray, pd.DataFrame]:
    logs = []
    best_x = None
    best_f = np.inf

    # Structured start near interpretable priors
    base = np.zeros(23)
    # rho priors: Kenya high, Liberia low, Nigeria medium
    base[0:3] = np.array([1.2, -2.0, -0.2])
    # tau priors
    base[3:6] = np.array([0.4, -0.8, -0.3])
    # exec priors
    base[6:9] = np.array([2.2, 1.8, -0.8])
    # zeta priors
    base[9:12] = np.array([-0.12, -0.05, -0.10])
    # global slopes
    base[12:23] = np.array([0.0, 0.1, 0.1, 0.8, 0.3, 0.0, -0.2, -0.2, 0.0, 0.0, -0.2])

    for s in range(n_starts):
        x0 = base + RNG.normal(0.0, 0.7, size=base.shape[0])
        bounds = [(-3.0, 3.0)] * 23
        res = minimize(
            lambda x: _objective_raw(x, targets),
            x0=x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 800, "ftol": 1e-10},
        )
        val = float(res.fun)
        logs.append(
            {
                "method": "L-BFGS-B",
                "start_id": s,
                "success": bool(res.success),
                "nit": int(getattr(res, "nit", -1)),
                "nfev": int(getattr(res, "nfev", -1)),
                "objective": val,
                "message": str(res.message),
            }
        )
        if np.isfinite(val) and val < best_f:
            best_f = val
            best_x = res.x.copy()

    if use_de_fallback:
        bounds = [(-3.0, 3.0)] * 23
        de = differential_evolution(
            lambda x: _objective_raw(x, targets),
            bounds=bounds,
            seed=SEED,
            maxiter=120,
            polish=True,
            popsize=12,
            tol=1e-4,
            updating="deferred",
            workers=1,
        )
        de_val = float(de.fun)
        logs.append(
            {
                "method": "differential_evolution",
                "start_id": -1,
                "success": bool(de.success),
                "nit": int(getattr(de, "nit", -1)),
                "nfev": int(getattr(de, "nfev", -1)),
                "objective": de_val,
                "message": str(de.message),
            }
        )
        if np.isfinite(de_val) and de_val < best_f:
            best_f = de_val
            best_x = de.x.copy()

    if best_x is None:
        raise RuntimeError("Optimizer failed to produce a finite solution.")

    return best_x, pd.DataFrame(logs).sort_values("objective")


def _two_step_weights(targets: pd.DataFrame, fitted: pd.DataFrame) -> pd.DataFrame:
    """
    Simple two-step option: update diagonal weights using first-step residual scale.
    """
    t = targets.copy()
    f = fitted[["moment_id", "error"]].copy()
    t = t.merge(f, on="moment_id", how="left")
    eps = 1e-8
    # combined scale: original variance + squared residual
    t["variance_for_weight"] = np.maximum(t["variance_for_weight"].astype(float) + t["error"].astype(float) ** 2, eps)
    t["weight"] = 1.0 / t["variance_for_weight"]
    return t.drop(columns=["error"])


def _save_params(raw: np.ndarray) -> pd.DataFrame:
    par = unpack_params(raw)
    rows = []

    # market-level parameters
    for m in MARKETS:
        rows.append({"param": f"rho_{m}", "natural_value": par.rho[m]})
        rows.append({"param": f"tau_{m}", "natural_value": par.tau[m]})
        rows.append({"param": f"exec_{m}", "natural_value": par.exec_q[m]})
        rows.append({"param": f"zeta_{m}", "natural_value": par.zeta[m]})

    # global parameters
    for name in [
        "alpha0",
        "alpha_rho",
        "alpha_tau",
        "alpha_soc",
        "alpha_exec",
        "disp0",
        "disp_rho",
        "disp_exec",
        "peer0",
        "peer_rho",
        "peer_exec",
    ]:
        rows.append({"param": name, "natural_value": getattr(par, name)})

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "smm_parameter_table.csv", index=False)
    pd.DataFrame({"raw_index": np.arange(len(raw)), "raw_value": raw}).to_csv(
        OUT_DIR / "smm_parameter_raw_vector.csv", index=False
    )
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--moments", default=str(OUT_DIR / "empirical_moments.csv"))
    parser.add_argument("--starts", type=int, default=24)
    parser.add_argument("--two-step", action="store_true")
    parser.add_argument("--no-de", action="store_true")
    args = parser.parse_args()

    moments_path = Path(args.moments)
    if not moments_path.exists():
        raise FileNotFoundError(f"Missing moments file: {moments_path}")

    all_moments = pd.read_csv(moments_path)
    targets = build_target_set(all_moments)
    targets.to_csv(OUT_DIR / "smm_target_moments.csv", index=False)

    # Step 1
    best_raw, log1 = _run_multistart(targets, n_starts=args.starts, use_de_fallback=(not args.no_de))
    par1 = unpack_params(best_raw)
    fit1 = simulate_moments(par1, targets)

    # Optional step 2
    if args.two_step:
        targets2 = _two_step_weights(targets, fit1)
        best_raw2, log2 = _run_multistart(targets2, n_starts=max(8, args.starts // 2), use_de_fallback=False)
        best_raw = best_raw2
        par = unpack_params(best_raw)
        fit = simulate_moments(par, targets2)
        opt_log = pd.concat([log1.assign(step=1), log2.assign(step=2)], ignore_index=True)
        targets_used = targets2
    else:
        par = par1
        fit = fit1
        opt_log = log1.assign(step=1)
        targets_used = targets

    fit = fit.sort_values("weighted_sq_error", ascending=False).copy()
    fit["abs_pct_error"] = np.where(np.abs(fit["value"]) > 1e-8, np.abs((fit["value"] - fit["sim_value"]) / fit["value"]), np.nan)
    fit.to_csv(OUT_DIR / "fitted_moments.csv", index=False)

    params_df = _save_params(best_raw)
    opt_log.to_csv(OUT_DIR / "optimization_log.csv", index=False)

    final_obj = float(fit["weighted_sq_error"].sum())
    worst20 = fit.head(20)[["moment_id", "market", "category", "moment", "value", "sim_value", "error", "weighted_sq_error"]]
    worst20.to_csv(OUT_DIR / "worst_fit_moments_top20.csv", index=False)

    cf_high = high_rho_high_tau_itt(par)

    # Console diagnostics requested
    print("=" * 72)
    print("SMM optimization complete")
    print("=" * 72)
    print(f"Target moments used: {len(targets_used)}")
    print(f"Final objective value: {final_obj:.6f}")
    print("\nEstimated tau by market:")
    for m in MARKETS:
        print(f"  {m}: {par.tau[m]:.4f}")
    print("\nEstimated effective signal quality (rho) by market:")
    for m in MARKETS:
        print(f"  {m}: {par.rho[m]:.4f}")
    print(f"\nEstimated counterfactual high-rho, high-tau ITT: {cf_high:.4f}")

    print("\nTop 20 worst-fit moments:")
    print(worst20.to_string(index=False))

    # Save compact json report
    report = {
        "seed": SEED,
        "n_targets": int(len(targets_used)),
        "final_objective": final_obj,
        "tau": {m: par.tau[m] for m in MARKETS},
        "rho": {m: par.rho[m] for m in MARKETS},
        "high_rho_high_tau_itt": cf_high,
    }
    (OUT_DIR / "smm_run_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
