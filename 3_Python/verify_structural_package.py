#!/usr/bin/env python3
"""
Verify the canonical structural-estimation package.

This script checks the chain from the blockwise estimator to the manuscript:
generated outputs exist, acceptance tests pass, structural manuscript inputs are
listed in the current manifest, stale legacy outputs are not cited, and the main
counterfactual claims are consistent with the generated CSV files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
STRUCT_DIR = Path(__file__).resolve().parent / "output" / "structural_smm"
TEX_DIR = STRUCT_DIR / "latex"
MANIFEST = STRUCT_DIR / "run_manifest.json"
ACCEPTANCE = STRUCT_DIR / "acceptance_tests.json"
LOCAL_MANUSCRIPT = REPO_ROOT / "main_3country_new.structural_edit.tex"
STRUCTURAL_README = Path(__file__).resolve().parent / "README_structural.md"
REDESIGN_NOTE = STRUCT_DIR / "structural_redesign_note.md"
VERIFY_OUT = STRUCT_DIR / "structural_package_verification.json"
LEGACY_ALL_AT_ONCE_OUTPUTS = {
    "counterfactuals_point_estimates.csv",
    "counterfactuals_bootstrap_draws.csv",
    "counterfactuals_with_ci.csv",
    "empirical_moments.csv",
    "empirical_moments_summary.csv",
    "empirical_moments_todo.md",
    "fig_counterfactual_decomposition_nigeria.png",
    "fitted_moments.csv",
    "optimization_log.csv",
    "smm_parameter_raw_vector.csv",
    "smm_parameter_table.csv",
    "smm_run_summary.json",
    "smm_target_moments.csv",
    "table_counterfactuals_with_ci.csv",
    "table_structural_parameters.csv",
    "table_target_vs_fitted_moments.csv",
    "worst_fit_moments_top20.csv",
}


def _failures() -> list[str]:
    return []


def _load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    if not path.exists():
        failures.append(f"Missing required file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"Could not parse JSON {path}: {exc}")
        return {}


def _read_csv(path: Path, failures: list[str]) -> pd.DataFrame:
    if not path.exists():
        failures.append(f"Missing required file: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - diagnostic path
        failures.append(f"Could not read CSV {path}: {exc}")
        return pd.DataFrame()


def _scenario_value(df: pd.DataFrame, scenario: str, column: str, failures: list[str]) -> float:
    if df.empty:
        failures.append(f"Cannot read {scenario}.{column}: source table is empty")
        return float("nan")
    rows = df[df["scenario"] == scenario]
    if len(rows) != 1:
        failures.append(f"Expected one row for scenario={scenario}, found {len(rows)}")
        return float("nan")
    if column not in rows.columns:
        failures.append(f"Missing column {column} for scenario={scenario}")
        return float("nan")
    return float(rows.iloc[0][column])


def _check_range(
    name: str,
    value: float,
    lo: float,
    hi: float,
    failures: list[str],
    inclusive: bool = True,
) -> None:
    if inclusive:
        ok = lo <= value <= hi
    else:
        ok = lo < value < hi
    if not ok:
        failures.append(f"{name}={value:.6f} outside expected range [{lo:.6f}, {hi:.6f}]")


def _fmt_signed(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}"


def _fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def _check_required_text(
    manuscript_text: str,
    requirements: dict[str, list[str]],
    failures: list[str],
) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for label, terms in requirements.items():
        missing = [term for term in terms if term not in manuscript_text]
        results[label] = not missing
        if missing:
            failures.append(f"Manuscript structural prose missing {label}: " + "; ".join(missing))
    return results


def _check_forbidden_text(
    manuscript_text: str,
    forbidden_terms: list[str],
    failures: list[str],
) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for term in forbidden_terms:
        absent = term not in manuscript_text
        results[term] = absent
        if not absent:
            failures.append(f"Manuscript structural prose contains stale/overstrong phrase: {term}")
    return results


def main() -> int:
    failures = _failures()
    warnings: list[str] = []

    manifest = _load_json(MANIFEST, failures)
    acceptance = _load_json(ACCEPTANCE, failures)
    generated = set(manifest.get("generated_outputs", []))
    legacy = set(manifest.get("legacy_outputs_not_regenerated", []))
    archived_legacy = set(manifest.get("archived_legacy_outputs", []))

    if manifest.get("script") != "structural_blockwise_redesign.py":
        failures.append("Manifest script is not structural_blockwise_redesign.py")
    if manifest.get("acceptance_all_pass") is not True:
        failures.append("Manifest acceptance_all_pass is not true")
    if acceptance.get("all_pass") is not True:
        failures.append("acceptance_tests.json all_pass is not true")

    for rel in sorted(generated):
        if not (STRUCT_DIR / rel).exists():
            failures.append(f"Manifest output is missing: {rel}")

    root_legacy = sorted(rel for rel in LEGACY_ALL_AT_ONCE_OUTPUTS if (STRUCT_DIR / rel).exists())
    if root_legacy:
        failures.append("Legacy all-at-once outputs remain in canonical output root: " + ", ".join(root_legacy))

    if not LOCAL_MANUSCRIPT.exists():
        failures.append(f"Missing local manuscript copy: {LOCAL_MANUSCRIPT}")
        manuscript_text = ""
    else:
        manuscript_text = LOCAL_MANUSCRIPT.read_text(encoding="utf-8")

    doc_requirements = {
        STRUCTURAL_README: [
            "stage4_local_identification.csv",
            "stage4_parameter_uncertainty.csv",
            "combined_uncertainty_summary.csv",
            "social_channel_sensitivity.csv",
            "stage4_market_influence.csv",
            "structural_validation_checks.csv",
            "stage4_normalizations.csv",
            "stage3_tau_calibration.csv",
            "tau_calibration_sensitivity.csv",
            "signal_delivery_marginal_products.csv",
            "disciplined counterfactual mapping",
            "market-level ATE map",
            "mechanical sorting first stage",
        ],
        REDESIGN_NOTE: [
            "stage4_local_identification.csv",
            "stage4_parameter_uncertainty.csv",
            "combined_uncertainty_summary.csv",
            "social_channel_sensitivity.csv",
            "stage4_market_influence.csv",
            "structural_validation_checks.csv",
            "stage4_normalizations.csv",
            "stage3_tau_calibration.csv",
            "tau_calibration_sensitivity.csv",
            "signal_delivery_marginal_products.csv",
            "disciplined counterfactual mapping",
            "stage-4 production mapping separates",
        ],
    }
    for doc_path, required_terms in doc_requirements.items():
        if not doc_path.exists():
            failures.append(f"Missing structural documentation file: {doc_path}")
            continue
        doc_text = doc_path.read_text(encoding="utf-8")
        missing_terms = [term for term in required_terms if term not in doc_text]
        if missing_terms:
            failures.append(f"Structural documentation {doc_path.name} missing terms: " + ", ".join(missing_terms))

    manuscript_inputs = sorted(set(re.findall(r"\\input\{structural_output/([^}]+)\}", manuscript_text)))
    for tex_name in manuscript_inputs:
        rel = f"latex/{tex_name}"
        if rel not in generated:
            failures.append(f"Manuscript structural input is not in manifest: structural_output/{tex_name}")
        if not (TEX_DIR / tex_name).exists():
            failures.append(f"Manuscript structural table missing in canonical latex dir: {tex_name}")

    legacy_or_archived = legacy | archived_legacy | {f"legacy_all_at_once/{name}" for name in LEGACY_ALL_AT_ONCE_OUTPUTS}
    for rel in sorted(legacy_or_archived):
        stem = Path(rel).name
        if stem in manuscript_text:
            failures.append(f"Manuscript appears to reference stale legacy structural output: {stem}")

    expected_tables = {
        "tab_struct_primitive_moments.tex",
        "tab_structural_params.tex",
        "tab_moment_fit.tex",
        "tab_struct_resid_sensitivity.tex",
        "tab_struct_influence.tex",
        "tab_struct_market_influence.tex",
        "tab_struct_primitive_sensitivity.tex",
        "tab_struct_primitive_uncertainty.tex",
        "tab_struct_delivery_activation.tex",
        "tab_struct_delivery_thresholds.tex",
        "tab_struct_target_blocks.tex",
        "tab_struct_tau_calibration.tex",
        "tab_struct_tau_sensitivity.tex",
        "tab_struct_regularization_sensitivity.tex",
        "tab_struct_signal_delivery_margins.tex",
        "tab_struct_social_channel_sensitivity.tex",
        "tab_struct_stage4_discipline.tex",
        "tab_struct_stage4_normalizations.tex",
        "tab_struct_stage4_param_uncertainty.tex",
        "tab_struct_combined_uncertainty.tex",
        "tab_struct_local_identification.tex",
        "tab_struct_validation_checks.tex",
        "tab_counterfactuals.tex",
        "tab_struct_component_decomp.tex",
        "tab_struct_complementarity.tex",
    }
    missing_from_paper = sorted(expected_tables - set(manuscript_inputs))
    if missing_from_paper:
        failures.append("Canonical structural tables not included in manuscript: " + ", ".join(missing_from_paper))
    expected_figures = {
        "fig_struct_complementarity_surface.pdf",
    }
    manuscript_figures = sorted(set(re.findall(r"\\includegraphics(?:\[[^\]]+\])?\{structural_output/([^}]+)\}", manuscript_text)))
    missing_figures = sorted(expected_figures - set(manuscript_figures))
    if missing_figures:
        failures.append("Canonical structural figures not included in manuscript: " + ", ".join(missing_figures))
    for fig_name in expected_figures:
        if fig_name not in generated:
            failures.append(f"Canonical structural figure is not in manifest: {fig_name}")
        if not (STRUCT_DIR / fig_name).exists():
            failures.append(f"Canonical structural figure is missing: {fig_name}")

    cf = _read_csv(STRUCT_DIR / "counterfactual_summary.csv", failures)
    comp = _read_csv(STRUCT_DIR / "nigeria_complementarity_decomposition.csv", failures)
    decomp = _read_csv(STRUCT_DIR / "counterfactual_component_decomposition.csv", failures)
    uncertainty = _read_csv(STRUCT_DIR / "stage4_counterfactual_uncertainty.csv", failures)
    combined_uncertainty = _read_csv(STRUCT_DIR / "combined_uncertainty_summary.csv", failures)
    delivery_thresholds = _read_csv(STRUCT_DIR / "delivery_threshold_diagnostics.csv", failures)
    signal_delivery_margins = _read_csv(STRUCT_DIR / "signal_delivery_marginal_products.csv", failures)
    combined_draws = _read_csv(STRUCT_DIR / "combined_uncertainty_draws.csv", failures)
    bootstrap_draws = _read_csv(STRUCT_DIR / "stage4_counterfactual_bootstrap_draws.csv", failures)
    parameter_draws = _read_csv(STRUCT_DIR / "stage4_parameter_bootstrap_draws.csv", failures)
    parameter_uncertainty = _read_csv(STRUCT_DIR / "stage4_parameter_uncertainty.csv", failures)
    local_identification = _read_csv(STRUCT_DIR / "stage4_local_identification.csv", failures)
    local_identification_summary = _read_csv(STRUCT_DIR / "stage4_local_identification_summary.csv", failures)
    influence = _read_csv(STRUCT_DIR / "stage4_influence_sensitivity.csv", failures)
    market_influence = _read_csv(STRUCT_DIR / "stage4_market_influence.csv", failures)
    stage4_targets = _read_csv(STRUCT_DIR / "stage4_target_moments.csv", failures)
    fitted_targets = _read_csv(STRUCT_DIR / "target_vs_fitted_moments.csv", failures)
    optimizer = _read_csv(STRUCT_DIR / "stage4_optimizer_diagnostics.csv", failures)
    params = _read_csv(STRUCT_DIR / "stage4_structural_parameters.csv", failures)
    objective_decomp = _read_csv(STRUCT_DIR / "stage4_objective_decomposition.csv", failures)
    stage4_normalizations = _read_csv(STRUCT_DIR / "stage4_normalizations.csv", failures)
    tau_calibration = _read_csv(STRUCT_DIR / "stage3_tau_calibration.csv", failures)
    tau_sensitivity = _read_csv(STRUCT_DIR / "tau_calibration_sensitivity.csv", failures)
    regularization = _read_csv(STRUCT_DIR / "regularization_sensitivity.csv", failures)
    social_channel = _read_csv(STRUCT_DIR / "social_channel_sensitivity.csv", failures)
    delivery_activation = _read_csv(STRUCT_DIR / "delivery_activation_sensitivity.csv", failures)
    validation_checks = _read_csv(STRUCT_DIR / "structural_validation_checks.csv", failures)

    if not stage4_normalizations.empty:
        required_norm_terms = {
            "Market residual shrinkage",
            "Raw-parameter norm",
            "Assignment-payoff scale",
            "Social-channel scale",
            "Comparative-static penalties",
        }
        observed_norm_terms = set(stage4_normalizations.get("term", pd.Series(dtype=str)).astype(str))
        missing_norm_terms = sorted(required_norm_terms - observed_norm_terms)
        if missing_norm_terms:
            failures.append("Stage-4 normalizations table missing terms: " + ", ".join(missing_norm_terms))
    if not tau_calibration.empty:
        required_tau_markets = {"Kenya", "Liberia", "Nigeria"}
        observed_tau_markets = set(tau_calibration.get("market", pd.Series(dtype=str)).astype(str))
        missing_tau_markets = sorted(required_tau_markets - observed_tau_markets)
        if missing_tau_markets:
            failures.append("Tau calibration table missing markets: " + ", ".join(missing_tau_markets))
        calibration_text = "\n".join(tau_calibration.get("calibration", pd.Series(dtype=str)).astype(str).tolist())
        for term in ["0.30+8", "0.10+0.80", "Not used in calibration"]:
            if term not in calibration_text:
                failures.append(f"Tau calibration table missing calibration term: {term}")
    if not tau_sensitivity.empty:
        required_tau_specs = {"lower_process_map", "preferred", "upper_process_map"}
        observed_tau_specs = set(tau_sensitivity.get("specification", pd.Series(dtype=str)).astype(str))
        missing_tau_specs = sorted(required_tau_specs - observed_tau_specs)
        if missing_tau_specs:
            failures.append("Tau sensitivity table missing specifications: " + ", ".join(missing_tau_specs))
        if "idealized_high_rho_high_omega_high_tau" in tau_sensitivity:
            min_tau_sens_high = float(tau_sensitivity["idealized_high_rho_high_omega_high_tau"].min())
            if min_tau_sens_high <= 0:
                failures.append(f"Tau calibration sensitivity has non-positive high-input ATE: {min_tau_sens_high:.4f}")

    if not stage4_targets.empty and not fitted_targets.empty:
        target_keys = {
            (str(r["market"]), str(r["moment"]))
            for _, r in stage4_targets.iterrows()
            if pd.notna(r.get("target"))
        }
        fitted_keys = {
            (str(r["market"]), str(r["moment"]))
            for _, r in fitted_targets.iterrows()
            if pd.notna(r.get("target"))
        }
        if target_keys != fitted_keys:
            missing_fit = sorted(target_keys - fitted_keys)
            extra_fit = sorted(fitted_keys - target_keys)
            failures.append(
                "Stage-4 target moments do not match fitted-moment diagnostics. "
                f"Missing fitted rows: {missing_fit}; extra fitted rows: {extra_fit}"
            )
    if (TEX_DIR / "tab_moment_fit.tex").exists():
        moment_fit_tex = (TEX_DIR / "tab_moment_fit.tex").read_text(encoding="utf-8")
        for term in ["Std. resid.", "Obj."]:
            if term not in moment_fit_tex:
                failures.append(f"Moment-fit table missing diagnostic column: {term}")

    if not optimizer.empty:
        if len(optimizer) < 25:
            failures.append(f"Stage-4 optimizer diagnostics have fewer than 25 starts: {len(optimizer)}")
        if "converged" not in optimizer.columns or int(optimizer["converged"].sum()) < 20:
            failures.append("Stage-4 optimizer diagnostics show fewer than 20 converged local starts")
        if "objective" not in optimizer.columns:
            failures.append("Stage-4 optimizer diagnostics are missing objective column")
        elif not params.empty and {"param", "value"}.issubset(params.columns):
            param_obj = params.loc[params["param"] == "objective", "value"]
            if len(param_obj) != 1:
                failures.append("Stage-4 structural parameters are missing a unique objective row")
            else:
                best_obj = float(optimizer["objective"].min())
                if abs(best_obj - float(param_obj.iloc[0])) > 1e-6:
                    failures.append(
                        f"Optimizer best objective {best_obj:.8f} does not match parameter objective {float(param_obj.iloc[0]):.8f}"
                    )
        if "high_input_ate" in optimizer.columns:
            high_input_range = float(optimizer["high_input_ate"].max() - optimizer["high_input_ate"].min())
            if high_input_range > 0.02:
                failures.append(f"High-input ATE varies too much across optimizer starts: range={high_input_range:.6f}")

    if not objective_decomp.empty and not params.empty and {"component", "value"}.issubset(objective_decomp.columns):
        obj_comp = objective_decomp.set_index("component")["value"]
        if "total" not in obj_comp.index:
            failures.append("Stage-4 objective decomposition is missing total row")
        elif {"param", "value"}.issubset(params.columns):
            param_obj = params.loc[params["param"] == "objective", "value"]
            if len(param_obj) == 1 and abs(float(obj_comp.loc["total"]) - float(param_obj.iloc[0])) > 1e-6:
                failures.append(
                    f"Objective decomposition total {float(obj_comp.loc['total']):.8f} does not match parameter objective {float(param_obj.iloc[0]):.8f}"
                )
        hard_penalties = [
            "kenya_high_tau_monotonicity_penalty",
            "kenya_high_tau_scale_penalty",
            "nigeria_execution_monotonicity_penalty",
            "nigeria_execution_scale_penalty",
            "idealized_dominance_penalty",
        ]
        nonzero_hard = {
            k: float(obj_comp.loc[k])
            for k in hard_penalties
            if k in obj_comp.index and abs(float(obj_comp.loc[k])) > 1e-8
        }
        if nonzero_hard:
            failures.append(f"Hard comparative-static penalties bind at preferred solution: {nonzero_hard}")

    if not validation_checks.empty:
        required_validation_checks = {
            "Signal-quality ranking",
            "Assignment-execution ranking",
            "Delivery primitive measured before outcomes",
            "Kenya delivery monotonicity",
            "Nigeria execution monotonicity",
            "Nigeria target coherence",
            "Observed-cell fit",
            "High-input dominance",
        }
        observed_checks = set(validation_checks.get("check", pd.Series(dtype=str)).astype(str))
        missing_validation_checks = sorted(required_validation_checks - observed_checks)
        if missing_validation_checks:
            failures.append("Structural validation checklist missing rows: " + ", ".join(missing_validation_checks))
        if "status" not in validation_checks.columns:
            failures.append("Structural validation checklist missing status column")
        else:
            bad_status = validation_checks[validation_checks["status"].astype(str) != "Pass"]["check"].astype(str).tolist()
            if bad_status:
                failures.append("Structural validation checklist has non-pass rows: " + ", ".join(bad_status))

    if not regularization.empty:
        required_specs = {"preferred", "no_raw_norm", "weak_scale_priors", "no_scale_priors", "no_auxiliary_scale"}
        specs = set(regularization.get("specification", pd.Series(dtype=str)).astype(str))
        missing_specs = sorted(required_specs - specs)
        if missing_specs:
            failures.append("Regularization sensitivity missing specifications: " + ", ".join(missing_specs))
        if "idealized_high_rho_high_omega_high_tau" in regularization.columns:
            min_high_reg = float(regularization["idealized_high_rho_high_omega_high_tau"].min())
            if min_high_reg <= 0.0:
                failures.append(f"High-input ATE is non-positive in regularization sensitivity: min={min_high_reg:.6f}")

    if not social_channel.empty:
        required_social_specs = {"preferred_free_rank_weight", "rank_weight_fixed_zero"}
        social_specs = set(social_channel.get("specification", pd.Series(dtype=str)).astype(str))
        missing_social_specs = sorted(required_social_specs - social_specs)
        if missing_social_specs:
            failures.append("Social-channel sensitivity missing specifications: " + ", ".join(missing_social_specs))
        required_social_cols = {
            "omega_r",
            "peer_rank_weighted_rmse",
            "max_abs_std_itt_error",
            "idealized_high_rho_high_omega_high_tau",
            "nigeria_rho_tau",
        }
        missing_social_cols = required_social_cols - set(social_channel.columns)
        if missing_social_cols:
            failures.append("Social-channel sensitivity missing columns: " + ", ".join(sorted(missing_social_cols)))
        elif "rank_weight_fixed_zero" in social_specs:
            fixed = social_channel[social_channel["specification"].astype(str) == "rank_weight_fixed_zero"].iloc[0]
            if abs(float(fixed["omega_r"])) > 1e-10:
                failures.append("Rank-weight-fixed sensitivity did not hold omega_r at zero")
            if float(fixed["idealized_high_rho_high_omega_high_tau"]) <= 0.10:
                failures.append("High-input ATE falls below +0.10 SD when rank weight is fixed to zero")

    linear_activation_objective = float("nan")
    preferred_activation_objective = float("nan")
    linear_assignment_payoff = float("nan")
    if not delivery_activation.empty:
        required_delivery_specs = {"linear", "quadratic", "moderate", "preferred", "steep"}
        delivery_specs = set(delivery_activation.get("scenario", pd.Series(dtype=str)).astype(str))
        missing_delivery_specs = sorted(required_delivery_specs - delivery_specs)
        if missing_delivery_specs:
            failures.append("Delivery-activation sensitivity missing specifications: " + ", ".join(missing_delivery_specs))
        required_delivery_cols = {
            "scenario",
            "tau_power",
            "objective",
            "assignment_payoff_target",
            "assignment_payoff_fitted",
            "idealized_high_rho_high_omega_high_tau",
        }
        missing_delivery_cols = required_delivery_cols - set(delivery_activation.columns)
        if missing_delivery_cols:
            failures.append("Delivery-activation sensitivity missing columns: " + ", ".join(sorted(missing_delivery_cols)))
        elif {"linear", "preferred"}.issubset(delivery_specs):
            linear_row = delivery_activation[delivery_activation["scenario"].astype(str) == "linear"].iloc[0]
            preferred_row = delivery_activation[delivery_activation["scenario"].astype(str) == "preferred"].iloc[0]
            linear_activation_objective = float(linear_row["objective"])
            preferred_activation_objective = float(preferred_row["objective"])
            linear_assignment_payoff = float(linear_row["assignment_payoff_fitted"])
            payoff_target = float(preferred_row["assignment_payoff_target"])
            if linear_activation_objective <= 1.5 * preferred_activation_objective:
                failures.append("Linear delivery activation does not raise the stage-4 objective enough relative to preferred")
            if abs(linear_assignment_payoff - payoff_target) < 0.05:
                failures.append("Linear delivery activation no longer badly misses the assignment-payoff target")
            if float(preferred_row["idealized_high_rho_high_omega_high_tau"]) < 0.14:
                failures.append("Preferred delivery-activation high-input ATE is below +0.14 SD")

    required_common_params = {"lambda", "phi", "omega_r", "chi_N", "chi_V", "tau_power", "kappa_sort"}
    if not parameter_draws.empty:
        required_param_draw_cols = {"draw", "objective", "converged"} | required_common_params
        missing_param_draw_cols = required_param_draw_cols - set(parameter_draws.columns)
        if missing_param_draw_cols:
            failures.append("Stage-4 parameter bootstrap draws missing columns: " + ", ".join(sorted(missing_param_draw_cols)))
        elif int(parameter_draws["draw"].nunique()) < 45:
            failures.append(f"Stage-4 parameter bootstrap has too few unique draws: {int(parameter_draws['draw'].nunique())}")
    if not parameter_uncertainty.empty:
        required_param_uncert_cols = {"param", "draws", "point", "p05", "p95"}
        missing_param_uncert_cols = required_param_uncert_cols - set(parameter_uncertainty.columns)
        if missing_param_uncert_cols:
            failures.append("Stage-4 parameter uncertainty missing columns: " + ", ".join(sorted(missing_param_uncert_cols)))
        else:
            uncertainty_params = set(parameter_uncertainty["param"].astype(str))
            missing_common = sorted(required_common_params - uncertainty_params)
            if missing_common:
                failures.append("Stage-4 parameter uncertainty missing common production parameters: " + ", ".join(missing_common))
            if not params.empty and {"param", "value"}.issubset(params.columns):
                param_points = params.set_index("param")["value"]
                uncertainty_points = parameter_uncertainty.set_index("param")["point"]
                for param in sorted(required_common_params & set(param_points.index) & set(uncertainty_points.index)):
                    if abs(float(param_points.loc[param]) - float(uncertainty_points.loc[param])) > 1e-8:
                        failures.append(f"Stage-4 parameter uncertainty point does not match estimate for {param}")
                low_draw_params = parameter_uncertainty.loc[parameter_uncertainty["draws"].astype(int) < 45, "param"].astype(str).tolist()
                if low_draw_params:
                    failures.append("Stage-4 parameter uncertainty has too few draws for: " + ", ".join(low_draw_params))
                param_unc = parameter_uncertainty.set_index("param")
                for positive_param in ["lambda", "phi"]:
                    if positive_param in param_unc.index and float(param_unc.loc[positive_param, "p05"]) <= 0:
                        failures.append(f"{positive_param} 5th percentile is non-positive in parameter uncertainty")
                if "tau_power" in param_unc.index and float(param_unc.loc["tau_power", "p05"]) <= 1.0:
                    failures.append("Delivery-activation alpha 5th percentile is not above one")

    if not local_identification.empty:
        required_local_cols = {"param", "weighted_sensitivity_norm", "top_market", "top_moment"}
        missing_local_cols = required_local_cols - set(local_identification.columns)
        if missing_local_cols:
            failures.append("Stage-4 local identification missing columns: " + ", ".join(sorted(missing_local_cols)))
        else:
            local_params = set(local_identification["param"].astype(str))
            missing_local_params = sorted(required_common_params - local_params)
            if missing_local_params:
                failures.append("Stage-4 local identification missing parameters: " + ", ".join(missing_local_params))
            weak_rows = local_identification.loc[
                local_identification["weighted_sensitivity_norm"].astype(float) <= 0,
                "param",
            ].astype(str).tolist()
            if weak_rows:
                failures.append("Stage-4 local identification has non-positive sensitivity for: " + ", ".join(weak_rows))
    if not local_identification_summary.empty:
        required_summary_cols = {"n_targets", "n_common_parameters", "rank_tol_1e_minus_4", "condition_number"}
        missing_summary_cols = required_summary_cols - set(local_identification_summary.columns)
        if missing_summary_cols:
            failures.append("Stage-4 local identification summary missing columns: " + ", ".join(sorted(missing_summary_cols)))
        else:
            row = local_identification_summary.iloc[0]
            if int(row["n_targets"]) < 10:
                failures.append("Stage-4 local identification summary has fewer than 10 target moments")
            if int(row["n_common_parameters"]) < 7:
                failures.append("Stage-4 local identification summary has fewer than 7 common parameters")

    high = _scenario_value(cf, "idealized_high_rho_high_omega_high_tau", "ate", failures)
    kenya_obs = _scenario_value(cf, "kenya_observed", "ate", failures)
    nigeria_design = _scenario_value(cf, "nigeria_designed_execution", "ate", failures)
    nigeria_realized = _scenario_value(cf, "nigeria_realized", "ate", failures)
    _check_range("High-input ATE", high, 0.14, 0.23, failures)
    if high <= kenya_obs:
        failures.append("High-input ATE does not exceed observed Kenya ATE")
    if abs(nigeria_design - nigeria_realized) > 0.01:
        failures.append("Nigeria designed-execution counterfactual no longer matches realized Nigeria closely")

    rho_tau_nonadd = _scenario_value(comp, "rho_tau", "complementarity_residual", failures)
    all_three_nonadd = _scenario_value(comp, "rho_omega_tau", "complementarity_residual", failures)
    _check_range("Nigeria rho+tau nonadditive gain", rho_tau_nonadd, 0.07, 0.11, failures)
    _check_range("Nigeria all-three nonadditive gain", all_three_nonadd, 0.08, 0.13, failures)

    assign_high = _scenario_value(decomp, "idealized_high_rho_high_omega_high_tau", "assignment_payoff", failures)
    ate_high = _scenario_value(decomp, "idealized_high_rho_high_omega_high_tau", "ate", failures)
    ate_high_ex_resid = _scenario_value(
        decomp,
        "idealized_high_rho_high_omega_high_tau",
        "ate_excluding_residual",
        failures,
    )
    if ate_high and assign_high / ate_high < 0.7:
        failures.append("High-input ATE is no longer mainly assignment-payoff driven")
    if ate_high_ex_resid < 0.12:
        failures.append("High-input residual-free ATE is below +0.12 SD")

    high_p05 = _scenario_value(uncertainty, "idealized_high_rho_high_omega_high_tau", "p05", failures)
    high_p95 = _scenario_value(uncertainty, "idealized_high_rho_high_omega_high_tau", "p95", failures)
    if high_p05 < 0.05:
        failures.append("High-input conditional 5th percentile is below +0.05 SD")

    combined_high_p05 = _scenario_value(combined_uncertainty, "idealized_high_rho_high_omega_high_tau", "p05", failures)
    combined_high_p95 = _scenario_value(combined_uncertainty, "idealized_high_rho_high_omega_high_tau", "p95", failures)
    if combined_high_p05 < 0.03:
        failures.append("High-input combined-uncertainty 5th percentile is below +0.03 SD")

    kenya_high_tau = _scenario_value(cf, "kenya_high_tau", "ate", failures)
    kenya_high_tau_p05 = _scenario_value(uncertainty, "kenya_high_tau", "p05", failures)
    kenya_high_tau_p95 = _scenario_value(uncertainty, "kenya_high_tau", "p95", failures)
    nigeria_rho_tau_ate = _scenario_value(decomp, "nigeria_rho_tau", "ate", failures)
    nigeria_all_three_ate = _scenario_value(decomp, "nigeria_all_three", "ate", failures)
    nigeria_realized_ex_resid = _scenario_value(decomp, "nigeria_realized", "ate_excluding_residual", failures)
    nigeria_rho_tau_ex_resid = _scenario_value(decomp, "nigeria_rho_tau", "ate_excluding_residual", failures)
    nigeria_all_three_ex_resid = _scenario_value(decomp, "nigeria_all_three", "ate_excluding_residual", failures)
    signal_gain_low_tau = _scenario_value(
        signal_delivery_margins,
        "nigeria_realized",
        "ate_gain_from_nigeria_to_kenya_rho",
        failures,
    )
    signal_gain_high_tau = _scenario_value(
        signal_delivery_margins,
        "nigeria_high_delivery",
        "ate_gain_from_nigeria_to_kenya_rho",
        failures,
    )
    if pd.notna(signal_gain_low_tau) and pd.notna(signal_gain_high_tau):
        _check_range("Signal-quality gain at Nigeria realized tau", signal_gain_low_tau, -0.005, 0.010, failures)
        _check_range("Signal-quality gain at high tau", signal_gain_high_tau, 0.070, 0.110, failures)
        if signal_gain_high_tau <= signal_gain_low_tau + 0.05:
            failures.append(
                "Signal-quality marginal-product diagnostic does not show strong delivery complementarity: "
                f"low={signal_gain_low_tau:.4f}, high={signal_gain_high_tau:.4f}"
            )
    market_high_min = float("nan")
    market_high_max = float("nan")
    if not market_influence.empty and "idealized_high_rho_high_omega_high_tau" in market_influence.columns:
        market_high_min = float(market_influence["idealized_high_rho_high_omega_high_tau"].min())
        market_high_max = float(market_influence["idealized_high_rho_high_omega_high_tau"].max())
    tau_sensitivity_high_min = float("nan")
    tau_sensitivity_high_max = float("nan")
    if not tau_sensitivity.empty and "idealized_high_rho_high_omega_high_tau" in tau_sensitivity.columns:
        tau_sensitivity_high_min = float(tau_sensitivity["idealized_high_rho_high_omega_high_tau"].min())
        tau_sensitivity_high_max = float(tau_sensitivity["idealized_high_rho_high_omega_high_tau"].max())
    kenya_high_thresholds = pd.Series(dtype=float)
    if not delivery_thresholds.empty:
        required_threshold_cols = {
            "scenario",
            "residual",
            "tau_for_0",
            "tau_for_010",
            "tau_for_018",
            "ate_tau_095",
        }
        missing_threshold_cols = required_threshold_cols - set(delivery_thresholds.columns)
        if missing_threshold_cols:
            failures.append("Delivery threshold diagnostics missing columns: " + ", ".join(sorted(missing_threshold_cols)))
        else:
            rows = delivery_thresholds[
                (delivery_thresholds["scenario"].astype(str) == "kenya_high_signal_execution")
                & (delivery_thresholds["residual"].astype(str) == "excluded")
            ]
            if len(rows) != 1:
                failures.append(f"Expected one residual-free Kenya threshold row, found {len(rows)}")
            else:
                kenya_high_thresholds = rows.iloc[0]
                _check_range("Residual-free Kenya high-input tau threshold for +0.10", float(kenya_high_thresholds["tau_for_010"]), 0.80, 0.90, failures)
                _check_range("Residual-free Kenya high-input tau threshold for +0.18", float(kenya_high_thresholds["tau_for_018"]), 0.94, 0.99, failures)
            rows_inc = delivery_thresholds[
                (delivery_thresholds["scenario"].astype(str) == "kenya_high_signal_execution")
                & (delivery_thresholds["residual"].astype(str) == "included")
            ]
            if len(rows_inc) != 1:
                failures.append(f"Expected one residual-included Kenya threshold row, found {len(rows_inc)}")
            else:
                _check_range("Residual-included Kenya high-input tau threshold for +0.18", float(rows_inc.iloc[0]["tau_for_018"]), 0.90, 0.96, failures)

    moment_fit_claim_terms: list[str] = []
    if not fitted_targets.empty and {"market", "moment", "error", "weight"}.issubset(fitted_targets.columns):
        fit_tmp = fitted_targets.copy()
        fit_tmp["std_resid"] = fit_tmp["error"].astype(float) * (fit_tmp["weight"].astype(float) ** 0.5)
        peer_tmp = fit_tmp[fit_tmp["moment"].astype(str) == "peer_rank_beta"].copy()
        itt_tmp = fit_tmp[fit_tmp["moment"].astype(str) == "itt_main"].copy()
        if not peer_tmp.empty and not itt_tmp.empty:
            liberia_peer = float(
                peer_tmp.loc[
                    (peer_tmp["market"].astype(str) == "liberia"),
                    "std_resid",
                ].iloc[0]
            )
            kenya_peer = float(
                peer_tmp.loc[
                    (peer_tmp["market"].astype(str) == "kenya"),
                    "std_resid",
                ].iloc[0]
            )
            max_itt_abs = float(itt_tmp["std_resid"].abs().max())
            moment_fit_claim_terms = [
                "standardized residuals and objective contributions",
                f"Liberia peer/rank moment (${_fmt(liberia_peer, 2)}$)",
                f"Kenya's peer/rank moment (${_fmt_signed(kenya_peer, 2)}$)",
                f"largest ITT residual is only ${_fmt(max_itt_abs, 2)}$ standard errors",
            ]

    manuscript_claim_terms = {
        "high_input_point_estimate": [
            f"${_fmt_signed(high, 3)}$ SD",
            f"${_fmt_signed(high, 2)}$",
        ],
        "high_input_conditional_interval": [
            f"$[{_fmt_signed(high_p05, 3)},{_fmt_signed(high_p95, 3)}]$",
        ],
        "high_input_combined_interval": [
            f"$[{_fmt_signed(combined_high_p05, 3)},{_fmt_signed(combined_high_p95, 3)}]$",
        ],
        "assignment_payoff_decomposition": [
            f"${_fmt_signed(assign_high, 3)}$ SD",
        ],
        "residual_free_component_decomposition": [
            f"${_fmt_signed(ate_high_ex_resid, 3)}$ SD",
            "Setting the Kenya residual to zero",
            "so the result is not a country-residual artifact",
        ],
        "kenya_high_tau_counterfactual": [
            f"${_fmt_signed(kenya_high_tau, 3)}$ SD",
            f"$[{_fmt_signed(kenya_high_tau_p05, 3)},{_fmt_signed(kenya_high_tau_p95, 3)}]$",
        ],
        "nigeria_complementarity_point_estimates": [
            f"${_fmt_signed(nigeria_rho_tau_ate, 3)}$ SD",
            f"${_fmt_signed(nigeria_all_three_ate, 3)}$ SD",
        ],
        "nigeria_nonadditive_components": [
            f"${_fmt_signed(rho_tau_nonadd, 3)}$ SD",
            f"${_fmt_signed(all_three_nonadd, 3)}$ SD",
        ],
        "signal_delivery_marginal_products": [
            r"Table~\ref{tab:struct_signal_delivery_margins}",
            f"worth only ${_fmt_signed(signal_gain_low_tau, 3)}$ SD",
            f"to ${_fmt_signed(signal_gain_high_tau, 3)}$ SD",
            "not a fixed property of the test",
        ],
        "nigeria_residual_invariant_complementarity": [
            "the gain and nonadditive columns are invariant to that residual",
            f"realized Nigeria is ${_fmt_signed(nigeria_realized_ex_resid, 3)}$ SD",
            f"$\\rho+\\tau$ is ${_fmt_signed(nigeria_rho_tau_ex_resid, 3)}$ SD",
            f"all three upgrades are ${_fmt_signed(nigeria_all_three_ex_resid, 3)}$ SD",
            "but the gains are unchanged",
        ],
        "structural_surface_figure": [
            r"Figure~\ref{fig:struct_complementarity_surface}",
            "the return to sorting is activated by delivery",
        ],
        "estimable_structural_map": [
            "The estimable object is the market-level treatment-control contrast",
            r"\label{eq:str_ate_map}",
            r"\lambda \rho\omega\tau^\alpha",
            r"\label{eq:str_dispersion_map}",
            "The model also fits the mechanical sorting first stage separately from the outcome payoff",
        ],
        "stage4_regularization_framing": [
            "market residuals are shrinkage-regularized with a prior standard deviation of 0.25",
            "weak scale normalizations keep the assignment-payoff and social-channel coefficients",
            "These normalizations are not innocuous for magnitudes",
            "hard penalties rule out counterfactual mappings that violate the model's comparative statics",
        ],
        "stage4_discipline_diagnostics": [
            r"Table~\ref{tab:struct_stage4_discipline}",
            r"Table~\ref{tab:struct_stage4_normalizations}",
            r"\input{structural_output/tab_struct_stage4_normalizations.tex}",
            "The hard comparative-static penalties are zero at the optimum",
            "the high-input ATE is stable across starts",
            "reports the exact non-moment terms in the preferred criterion",
        ],
        "parameter_level_identification": [
            "Parameter-level identification follows from this division of moments",
            r"The dispersion equation pins down $\kappa$",
            r"The ITT moments and Kenya assignment-payoff slope jointly discipline $\lambda$ and $\alpha$",
            "the preferred interpretation is therefore a composite social channel",
            "The class-size and grade-dispersion coefficients",
        ],
        "validation_framing": [
            "The structural exercise is disciplined by three requirements",
            "identifying evidence outside the treatment-effect fit",
            r"Table~\ref{tab:struct_validation_checks}",
            r"\input{structural_output/tab_struct_validation_checks.tex}",
        ],
        "tau_calibration_framing": [
            r"Table~\ref{tab:struct_tau_calibration}",
            r"\input{structural_output/tab_struct_tau_calibration.tex}",
            "outcome-free calibration from treatment-relevant process evidence",
        ],
        "tau_sensitivity_framing": [
            r"Table~\ref{tab:struct_tau_sensitivity}",
            r"\input{structural_output/tab_struct_tau_sensitivity.tex}",
            "lower and upper process-to-$\\tau$ mappings",
        ],
        "paper_punchline": [
            "each experiment is missing at least one of the three complementary inputs",
            "delivery fidelity is most valuable when paired with accurate sorting",
        ],
        "headline_scale_framing": [
            "the preferred specification predicts an ATE",
            "positive complementarity is more stable than the exact magnitude",
            "The preferred counterfactual predicts",
            "The broader and more robust lesson is complementarity",
        ],
    }
    if moment_fit_claim_terms:
        manuscript_claim_terms["moment_fit_diagnostics"] = moment_fit_claim_terms
    if pd.notna(linear_activation_objective) and pd.notna(preferred_activation_objective) and pd.notna(linear_assignment_payoff):
        manuscript_claim_terms["delivery_activation_objective_profile"] = [
            f"raises the stage-4 criterion from ${_fmt(preferred_activation_objective, 2)}$ to ${_fmt(linear_activation_objective, 2)}$",
            f"predicts a Kenya assignment-payoff slope of ${_fmt_signed(linear_assignment_payoff, 3)}$",
            "when the target is $+0.008$",
            "more than doubles the criterion",
        ]
    if pd.notna(market_high_min) and pd.notna(market_high_max):
        manuscript_claim_terms["market_influence"] = [
            r"Appendix Table~\ref{tab:struct_market_influence}",
            f"between ${_fmt_signed(market_high_min, 3)}$ and ${_fmt_signed(market_high_max, 3)}$ SD",
            r"the Nigeria $\rho+\tau$ counterfactual is not stable when Nigeria's own stage-4 targets are omitted",
            "The stable claim is therefore the high-input assignment-delivery counterfactual",
        ]
    if pd.notna(tau_sensitivity_high_min) and pd.notna(tau_sensitivity_high_max):
        manuscript_claim_terms["tau_sensitivity_results"] = [
            r"Table~\ref{tab:struct_tau_sensitivity}",
            f"between ${_fmt_signed(tau_sensitivity_high_min, 3)}$ and ${_fmt_signed(tau_sensitivity_high_max, 3)}$ SD",
            r"observed-$\tau$ calibration",
        ]
    if not kenya_high_thresholds.empty:
        manuscript_claim_terms["delivery_thresholds"] = [
            r"Appendix Table~\ref{tab:struct_delivery_thresholds}",
            f"$\\tau \\simeq {_fmt(float(kenya_high_thresholds['tau_for_010']), 2)}$",
            f"$\\tau \\simeq {_fmt(float(kenya_high_thresholds['tau_for_018']), 2)}$",
            "accurate sorting becomes valuable only when treatment-relevant delivery is very high",
        ]
    manuscript_claim_checks = _check_required_text(manuscript_text, manuscript_claim_terms, failures)
    forbidden_phrase_checks = _check_forbidden_text(
        manuscript_text,
        [
            "The model passes all theory-implied validation checks",
            "satisfies all nine restrictions",
            "all nine restrictions",
            "before any outcome moment is used",
            r"\label{eq:smm_objective}",
            r"\subsection{Counterfactual Simulations}",
        ],
        failures,
    )

    if not combined_draws.empty:
        required_combined_cols = {
            "draw",
            "scenario",
            "ate",
            "objective",
            "rho_kenya",
            "rho_liberia",
            "rho_nigeria",
            "omega_nigeria",
            "tau_kenya",
            "tau_liberia",
            "tau_nigeria",
        }
        missing_combined_cols = required_combined_cols - set(combined_draws.columns)
        if missing_combined_cols:
            failures.append("Combined uncertainty draws missing columns: " + ", ".join(sorted(missing_combined_cols)))
        else:
            unique_combined = int(combined_draws["draw"].nunique())
            if unique_combined < 25:
                failures.append(f"Combined uncertainty has too few unique draws: {unique_combined}")
            if not combined_uncertainty.empty and {"scenario", "draws"}.issubset(combined_uncertainty.columns):
                combined_counts = combined_draws.groupby("scenario")["draw"].nunique().to_dict()
                summary_counts = {str(r["scenario"]): int(r["draws"]) for _, r in combined_uncertainty.iterrows()}
                mismatched_combined_counts = {
                    k: (combined_counts[k], summary_counts[k])
                    for k in sorted(set(combined_counts) & set(summary_counts))
                    if int(combined_counts[k]) != int(summary_counts[k])
                }
                if set(combined_counts) != set(summary_counts) or mismatched_combined_counts:
                    failures.append(
                        "Combined uncertainty summary does not match draw file. "
                        f"Draw only: {sorted(set(combined_counts) - set(summary_counts))}; "
                        f"summary only: {sorted(set(summary_counts) - set(combined_counts))}; "
                        f"mismatched counts: {mismatched_combined_counts}"
                    )

    if not bootstrap_draws.empty:
        required_boot_cols = {"draw", "scenario", "ate", "objective", "converged"}
        missing_boot_cols = required_boot_cols - set(bootstrap_draws.columns)
        if missing_boot_cols:
            failures.append("Stage-4 bootstrap draws missing columns: " + ", ".join(sorted(missing_boot_cols)))
        else:
            unique_draws = int(bootstrap_draws["draw"].nunique())
            if unique_draws < 45:
                failures.append(f"Stage-4 bootstrap has too few unique draws: {unique_draws}")
            draw_convergence = bootstrap_draws.groupby("draw")["converged"].all()
            if int(draw_convergence.sum()) < 45:
                failures.append(
                    f"Stage-4 bootstrap has too few fully converged draws: {int(draw_convergence.sum())}"
                )
            if not uncertainty.empty and {"scenario", "draws"}.issubset(uncertainty.columns):
                boot_counts = bootstrap_draws.groupby("scenario")["draw"].nunique().to_dict()
                uncertainty_counts = {
                    str(r["scenario"]): int(r["draws"])
                    for _, r in uncertainty.iterrows()
                }
                if set(boot_counts) != set(uncertainty_counts):
                    failures.append(
                        "Stage-4 uncertainty scenarios do not match bootstrap draw scenarios. "
                        f"Bootstrap only: {sorted(set(boot_counts) - set(uncertainty_counts))}; "
                        f"uncertainty only: {sorted(set(uncertainty_counts) - set(boot_counts))}"
                    )
                mismatched_counts = {
                    k: (boot_counts[k], uncertainty_counts[k])
                    for k in sorted(set(boot_counts) & set(uncertainty_counts))
                    if int(boot_counts[k]) != int(uncertainty_counts[k])
                }
                if mismatched_counts:
                    failures.append(f"Stage-4 uncertainty draw counts mismatch bootstrap file: {mismatched_counts}")

    if not influence.empty:
        if "idealized_high_rho_high_omega_high_tau" not in influence.columns:
            failures.append("Influence sensitivity file is missing high-input column")
        else:
            min_influence_high = float(influence["idealized_high_rho_high_omega_high_tau"].min())
            if min_influence_high < 0.10:
                failures.append("High-input ATE falls below +0.10 SD in target-block influence sensitivity")

    if not market_influence.empty:
        required_market_specs = {"preferred", "drop_kenya", "drop_liberia", "drop_nigeria"}
        market_specs = set(market_influence.get("specification", pd.Series(dtype=str)).astype(str))
        missing_market_specs = sorted(required_market_specs - market_specs)
        if missing_market_specs:
            failures.append("Market influence missing specifications: " + ", ".join(missing_market_specs))
        required_market_cols = {
            "omitted_market",
            "heldout_abs_itt_error_over_se",
            "max_abs_itt_error_over_se",
            "kenya_high_tau",
            "nigeria_rho_tau",
            "idealized_high_rho_high_omega_high_tau",
            "high_input_delta_vs_preferred",
        }
        missing_market_cols = required_market_cols - set(market_influence.columns)
        if missing_market_cols:
            failures.append("Market influence missing columns: " + ", ".join(sorted(missing_market_cols)))
        elif "idealized_high_rho_high_omega_high_tau" in market_influence.columns:
            min_market_high = float(market_influence["idealized_high_rho_high_omega_high_tau"].min())
            if min_market_high < 0.12:
                failures.append("High-input ATE falls below +0.12 SD in market influence sensitivity")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "warnings": warnings,
        "manifest_generated_outputs": len(generated),
        "archived_legacy_outputs": sorted(archived_legacy),
        "manuscript_structural_inputs": manuscript_inputs,
        "checked_claims": {
            "high_input_ate": high,
            "kenya_observed_ate": kenya_obs,
            "nigeria_realized_ate": nigeria_realized,
            "nigeria_designed_execution_ate": nigeria_design,
            "rho_tau_nonadditive_gain": rho_tau_nonadd,
            "all_three_nonadditive_gain": all_three_nonadd,
            "high_input_assignment_component": assign_high,
            "high_input_ate_excluding_residual": ate_high_ex_resid,
            "high_input_conditional_p05": high_p05,
            "high_input_conditional_p95": high_p95,
            "high_input_combined_p05": combined_high_p05,
            "high_input_combined_p95": combined_high_p95,
            "manuscript_claim_checks": manuscript_claim_checks,
            "forbidden_phrase_checks": forbidden_phrase_checks,
            "combined_uncertainty_unique_draws": (
                int(combined_draws["draw"].nunique())
                if not combined_draws.empty and "draw" in combined_draws.columns
                else None
            ),
            "stage4_bootstrap_unique_draws": (
                int(bootstrap_draws["draw"].nunique())
                if not bootstrap_draws.empty and "draw" in bootstrap_draws.columns
                else None
            ),
            "stage4_parameter_bootstrap_unique_draws": (
                int(parameter_draws["draw"].nunique())
                if not parameter_draws.empty and "draw" in parameter_draws.columns
                else None
            ),
            "stage4_local_identification_rank": (
                int(local_identification_summary.iloc[0]["rank_tol_1e_minus_4"])
                if not local_identification_summary.empty and "rank_tol_1e_minus_4" in local_identification_summary.columns
                else None
            ),
            "min_high_input_in_influence_sensitivity": (
                float(influence["idealized_high_rho_high_omega_high_tau"].min())
                if not influence.empty and "idealized_high_rho_high_omega_high_tau" in influence.columns
                else None
            ),
            "min_high_input_in_market_influence": (
                market_high_min
                if pd.notna(market_high_min)
                else None
            ),
            "max_high_input_in_market_influence": (
                market_high_max
                if pd.notna(market_high_max)
                else None
            ),
            "linear_activation_objective": (
                linear_activation_objective
                if pd.notna(linear_activation_objective)
                else None
            ),
            "preferred_activation_objective": (
                preferred_activation_objective
                if pd.notna(preferred_activation_objective)
                else None
            ),
            "linear_activation_assignment_payoff": (
                linear_assignment_payoff
                if pd.notna(linear_assignment_payoff)
                else None
            ),
        },
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if failures:
        print("Structural package verification: FAIL")
        for failure in failures:
            print(f"- {failure}")
        print(f"Wrote diagnostics to {VERIFY_OUT}")
        return 1

    print("Structural package verification: PASS")
    for warning in warnings:
        print(f"Warning: {warning}")
    print(f"Wrote diagnostics to {VERIFY_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
