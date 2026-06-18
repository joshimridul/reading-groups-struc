#!/usr/bin/env python3
"""Verify the current structural package contract.

The verifier intentionally checks current paper-facing invariants rather than
old exact prose. It should pass after `./run_all.sh` completes successfully.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
STRUCT_DIR = REPO / "3_Python" / "output" / "structural_smm"
PAPER_STRUCT = REPO / "structural_output"
MANUSCRIPT = REPO / "main_3country_new.structural_edit.tex"
BUILD_LOG = REPO / "build" / "main_3country_new.structural_edit.log"
ACTIVE_MANIFEST = REPO / "paper_pipeline" / "active_inputs_manifest.csv"
VERIFY_OUT = STRUCT_DIR / "structural_package_verification.json"


REQUIRED_STRUCTURAL_FILES = [
    "acceptance_tests.json",
    "run_manifest.json",
    "counterfactual_summary.csv",
    "target_vs_fitted_moments.csv",
    "assignment_value_payoff_sensitivity.csv",
    "nigeria_endpoint_sensitivity.csv",
    "regularization_sensitivity.csv",
    "tau_calibration_sensitivity.csv",
    "nigeria_complementarity_decomposition.csv",
    "signal_delivery_marginal_products.csv",
    "combined_uncertainty_summary.csv",
    "latex/tab_counterfactuals.tex",
    "latex/tab_struct_regularization_sensitivity.tex",
    "latex/tab_struct_assignment_value_sensitivity.tex",
    "latex/tab_struct_nigeria_endpoint_sensitivity.tex",
    "latex/tab_struct_tau_raw_thresholds.tex",
    "latex/tab_struct_validation_checks.tex",
]

REQUIRED_PAPER_OUTPUTS = [
    "tab_counterfactuals.tex",
    "tab_struct_regularization_sensitivity.tex",
    "tab_struct_assignment_value_sensitivity.tex",
    "tab_struct_nigeria_endpoint_sensitivity.tex",
    "tab_struct_stage4_discipline.tex",
    "fig_counterfactual_ladder.pdf",
    "fig_assignment_mismatch_distributions.pdf",
    "fig_struct_complementarity_surface.pdf",
]

FORBIDDEN_MANUSCRIPT_TERMS = [
    "Structural Validation Checks",
    "high-input dominance",
    "Nigeria-environment $\\rho+\\tau$",
    "high-$\\rho$, high-$\\omega$, high-$\\tau$ cell",
    "falls to $+0.068$ SD with no auxiliary scale restriction",
]


def read_json(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"Could not read JSON {path}: {exc}")
        return {}


def read_csv(path: Path, failures: list[str]) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        failures.append(f"Could not read CSV {path}: {exc}")
        return pd.DataFrame()


def scalar(df: pd.DataFrame, key_col: str, key: str, value_col: str, failures: list[str]) -> float:
    if df.empty:
        failures.append(f"Cannot read {key}.{value_col}: empty table")
        return float("nan")
    rows = df[df[key_col] == key]
    if len(rows) != 1:
        failures.append(f"Expected one row where {key_col}={key}; found {len(rows)}")
        return float("nan")
    if value_col not in rows.columns:
        failures.append(f"Missing column {value_col} for {key}")
        return float("nan")
    return float(rows.iloc[0][value_col])


def in_range(name: str, value: float, low: float, high: float, failures: list[str]) -> None:
    if not (low <= value <= high):
        failures.append(f"{name}={value:.6f} outside [{low:.6f}, {high:.6f}]")


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_STRUCTURAL_FILES:
        if not (STRUCT_DIR / rel).exists():
            failures.append(f"Missing structural output: {rel}")

    for rel in REQUIRED_PAPER_OUTPUTS:
        if not (PAPER_STRUCT / rel).exists():
            failures.append(f"Missing paper-facing structural output: structural_output/{rel}")

    acceptance = read_json(STRUCT_DIR / "acceptance_tests.json", failures)
    if acceptance.get("all_pass") is not True:
        failures.append("acceptance_tests.json does not report all_pass=true")
    for key, value in acceptance.items():
        if key == "all_pass":
            continue
        if isinstance(value, dict) and value.get("pass") is not True:
            failures.append(f"Acceptance check failed: {key}")

    active = read_csv(ACTIVE_MANIFEST, failures)
    if not active.empty:
        missing_refs = active[(active["status"] != "materialized") | active["repo_target"].isna()]
        if len(missing_refs):
            failures.append(f"Active input manifest has {len(missing_refs)} non-materialized rows")
        for rel in REQUIRED_PAPER_OUTPUTS:
            if f"structural_output/{rel}" not in set(active["manuscript_path"]):
                warnings.append(f"Paper-facing output is not in active manifest: structural_output/{rel}")

    cf = read_csv(STRUCT_DIR / "counterfactual_summary.csv", failures)
    high = scalar(cf, "scenario", "idealized_high_rho_high_omega_high_tau", "ate", failures)
    kenya_obs = scalar(cf, "scenario", "kenya_observed", "ate", failures)
    kenya_high_tau = scalar(cf, "scenario", "kenya_high_tau", "ate", failures)
    nigeria_realized = scalar(cf, "scenario", "nigeria_realized", "ate", failures)
    nigeria_design = scalar(cf, "scenario", "nigeria_designed_execution", "ate", failures)
    in_range("Fully high-input ATE", high, 0.14, 0.40, failures)
    in_range("Kenya high-delivery ATE", kenya_high_tau, 0.10, 0.20, failures)
    if kenya_high_tau <= kenya_obs:
        failures.append("Kenya high-delivery ATE does not exceed observed Kenya ATE")
    if abs(nigeria_design - nigeria_realized) > 0.01:
        failures.append("Nigeria designed-execution counterfactual moved materially from realized Nigeria")

    comp = read_csv(STRUCT_DIR / "nigeria_complementarity_decomposition.csv", failures)
    g_tau = scalar(comp, "scenario", "g_tau", "complementarity_residual", failures)
    all_three = scalar(comp, "scenario", "g_omega_tau", "complementarity_residual", failures)
    in_range("Nigeria G+tau nonadditive gain", g_tau, 0.08, 0.13, failures)
    in_range("Nigeria all-three nonadditive gain", all_three, 0.10, 0.15, failures)

    margins = read_csv(STRUCT_DIR / "signal_delivery_marginal_products.csv", failures)
    low_gain = scalar(margins, "scenario", "nigeria_realized", "ate_gain_from_nigeria_to_kenya_g", failures)
    high_gain = scalar(margins, "scenario", "nigeria_high_delivery", "ate_gain_from_nigeria_to_kenya_g", failures)
    if high_gain <= low_gain + 0.05:
        failures.append("Assignment-value marginal product does not rise meaningfully at high delivery")

    reg = read_csv(STRUCT_DIR / "regularization_sensitivity.csv", failures)
    preferred = scalar(reg, "specification", "preferred", "idealized_high_rho_high_omega_high_tau", failures)
    no_aux = scalar(reg, "specification", "no_auxiliary_scale", "idealized_high_rho_high_omega_high_tau", failures)
    in_range("Preferred regularization high-input ATE", preferred, 0.14, 0.22, failures)
    if no_aux <= preferred:
        failures.append("No-auxiliary-scale sensitivity no longer shows scale extrapolation risk")

    if MANUSCRIPT.exists():
        manuscript = MANUSCRIPT.read_text(encoding="utf-8")
        for term in FORBIDDEN_MANUSCRIPT_TERMS:
            if term in manuscript:
                failures.append(f"Manuscript contains stale phrase: {term}")
        required_terms = [
            "signed assignment value",
            "calibrated assignment-delivery benchmark",
            "false-discovery-rate q-values",
            "unrestricted scale choices can make the extrapolation too large",
            "measurement, execution, and delivery are jointly strong",
        ]
        for term in required_terms:
            if term not in manuscript:
                failures.append(f"Manuscript missing current structural/prose term: {term}")
    else:
        failures.append(f"Missing manuscript: {MANUSCRIPT}")

    if BUILD_LOG.exists():
        log = BUILD_LOG.read_text(encoding="utf-8", errors="ignore")
        serious = re.findall(
            r"undefined|Citation.*undefined|Reference.*undefined|There were undefined|"
            r"Label\(s\) may have changed|Fatal|Emergency|Error|Overfull",
            log,
        )
        if serious:
            failures.append("LaTeX log has serious warnings/errors: " + ", ".join(sorted(set(serious))))
    else:
        failures.append(f"Missing build log: {BUILD_LOG}")

    report = {
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "warnings": warnings,
        "key_values": {
            "fully_high_input_ate": high,
            "kenya_high_delivery_ate": kenya_high_tau,
            "nigeria_g_tau_nonadditive_gain": g_tau,
            "nigeria_all_three_nonadditive_gain": all_three,
            "regularization_preferred": preferred,
            "regularization_no_auxiliary_scale": no_aux,
        },
    }
    VERIFY_OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    if failures:
        print("Structural package verification: FAIL")
        for failure in failures:
            print(f"- {failure}")
        print(f"Wrote diagnostics to {VERIFY_OUT}")
        return 1

    print("Structural package verification: PASS")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print(f"Wrote diagnostics to {VERIFY_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
