#!/usr/bin/env python3
"""
make_tables_figures.py
======================
Assemble structural-extension tables/figures from SMM outputs.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


OUT_DIR = Path(__file__).resolve().parent / "output" / "structural_smm"


def main() -> None:
    fitted_path = OUT_DIR / "fitted_moments.csv"
    param_path = OUT_DIR / "smm_parameter_table.csv"
    cf_path = OUT_DIR / "counterfactuals_with_ci.csv"

    if not fitted_path.exists():
        raise FileNotFoundError(f"Missing {fitted_path}. Run estimate_smm.py first.")
    if not param_path.exists():
        raise FileNotFoundError(f"Missing {param_path}. Run estimate_smm.py first.")

    fitted = pd.read_csv(fitted_path)
    params = pd.read_csv(param_path)

    fitted["pct_error"] = np.where(np.abs(fitted["value"]) > 1e-8, 100.0 * (fitted["sim_value"] - fitted["value"]) / fitted["value"], np.nan)
    fitted_table = fitted[
        [
            "moment_id",
            "market",
            "category",
            "moment",
            "value",
            "sim_value",
            "error",
            "pct_error",
            "weighted_sq_error",
        ]
    ].copy()
    fitted_table.to_csv(OUT_DIR / "table_target_vs_fitted_moments.csv", index=False)

    # Parameter table (already natural scale)
    params.to_csv(OUT_DIR / "table_structural_parameters.csv", index=False)

    # Counterfactual table
    if cf_path.exists():
        cf = pd.read_csv(cf_path)
        cf.to_csv(OUT_DIR / "table_counterfactuals_with_ci.csv", index=False)

        # Decomposition chart for Nigeria
        keep = [
            "nigeria_realized",
            "nigeria_rho_only_counterfactual",
            "nigeria_tau_only_counterfactual",
            "nigeria_exec_only_counterfactual",
            "nigeria_designed_counterfactual",
        ]
        d = cf[cf["scenario"].isin(keep)][["scenario", "value"]].copy()
        order = keep
        d["scenario"] = pd.Categorical(d["scenario"], categories=order, ordered=True)
        d = d.sort_values("scenario")

        plt.figure(figsize=(8, 4))
        plt.bar(d["scenario"].astype(str), d["value"], color="#4e79a7")
        plt.axhline(0, color="black", linewidth=0.8)
        plt.xticks(rotation=20, ha="right")
        plt.ylabel("Implied treatment effect")
        plt.title("Nigeria one-at-a-time counterfactual decomposition")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "fig_counterfactual_decomposition_nigeria.png", dpi=200)
        plt.close()

    print(f"Saved tables/figures to {OUT_DIR}")


if __name__ == "__main__":
    main()
