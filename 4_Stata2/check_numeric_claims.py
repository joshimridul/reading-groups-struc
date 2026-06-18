#!/usr/bin/env python3

"""Check headline manuscript claims against active generated table outputs.

This script is intentionally narrow. It is not a substitute for reading the
paper; it guards the numeric claims that anchor the current three-country story:
headline ITTs, signal quality, assignment value, attrition and inference,
classroom reallocation, upper/lower track effects, peer/rank diagnostics, and
the main robustness-section claims.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from audit_overleaf_artifacts import DEFAULT_OVERLEAF
from verify_freeze_manifest import DEFAULT_REPO, DEFAULT_REPO_OUTPUT


DEFAULT_ENTRYPOINT = "main_3country_new.structural_edit.tex"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(errors="ignore")


def contains_all(name: str, text: str, snippets: list[str]) -> CheckResult:
    normalized = normalize_spaces(text)
    missing = [snippet for snippet in snippets if normalize_spaces(snippet) not in normalized]
    if missing:
        return CheckResult(name, False, "missing: " + "; ".join(missing[:5]))
    return CheckResult(name, True, f"{len(snippets)} expected snippets present")


def contains_regexes(name: str, text: str, patterns: list[str]) -> CheckResult:
    missing = [pattern for pattern in patterns if not re.search(pattern, text, flags=re.S)]
    if missing:
        return CheckResult(name, False, "missing regex: " + "; ".join(missing[:5]))
    return CheckResult(name, True, f"{len(patterns)} expected regex patterns present")


def row_numbers(table_text: str, row_label: str, occurrence: int = 1) -> list[float]:
    pattern = re.compile(rf"^{re.escape(row_label)}\s*&(?P<body>.*?)\\\\", re.M)
    matches = list(pattern.finditer(table_text))
    if len(matches) < occurrence:
        raise ValueError(f"Row '{row_label}' occurrence {occurrence} not found")
    body = matches[occurrence - 1].group("body")
    return [float(num) for num in re.findall(r"-?\d+(?:\.\d+)?", body)]


def check_exact_numbers(
    name: str,
    table_text: str,
    row_label: str,
    expected: list[float],
    occurrence: int = 1,
    tolerance: float = 0.0005,
) -> CheckResult:
    try:
        actual = row_numbers(table_text, row_label, occurrence)
    except ValueError as exc:
        return CheckResult(name, False, str(exc))
    if len(actual) < len(expected):
        return CheckResult(
            name,
            False,
            f"row has {len(actual)} numbers, expected at least {len(expected)}: {actual}",
        )
    mismatches = []
    for idx, (got, want) in enumerate(zip(actual, expected), start=1):
        if abs(got - want) > tolerance:
            mismatches.append(f"col {idx}: expected {want}, got {got}")
    if mismatches:
        return CheckResult(name, False, "; ".join(mismatches))
    return CheckResult(name, True, f"{row_label}: {actual[:len(expected)]}")


def check_table_snippet(name: str, table_text: str, snippet: str) -> CheckResult:
    if normalize_spaces(snippet) not in normalize_spaces(table_text):
        return CheckResult(name, False, f"missing table snippet: {snippet}")
    return CheckResult(name, True, "expected table snippet present")


def check_signal_weight_floor(
    name: str,
    table_text: str,
    code_texts: list[str],
    floor: float = 0.01,
) -> CheckResult:
    """Verify the code's minimum EB shrinkage weight is not active in current data."""
    r2_values = []
    for line in table_text.splitlines():
        if not line.strip().endswith(r"\\"):
            continue
        numbers = [float(num) for num in re.findall(r"-?\d+(?:\.\d+)?", line)]
        if len(numbers) >= 4:
            r2_values.append(numbers[-1])
    if not r2_values:
        return CheckResult(name, False, "no R^2 values parsed from signal-quality table")
    floor_pattern = f"max(r(rho)^2, {floor:g})"
    missing_floor = [idx + 1 for idx, text in enumerate(code_texts) if floor_pattern not in text]
    if missing_floor:
        return CheckResult(name, False, f"expected EB floor pattern absent in code text(s): {missing_floor}")
    min_r2 = min(r2_values)
    if min_r2 <= floor:
        return CheckResult(
            name,
            False,
            f"minimum reported R^2 {min_r2:.3f} is at or below EB floor {floor:.3f}",
        )
    return CheckResult(name, True, f"minimum reported R^2 {min_r2:.3f} exceeds EB floor {floor:.3f}")


def render_results(results: list[CheckResult]) -> None:
    for result in results:
        status = "PASS" if result.ok else "BLOCK"
        print(f"[{status}] {result.name}: {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--overleaf-dir", type=Path, default=DEFAULT_OVERLEAF)
    parser.add_argument("--repo-output-dir", type=Path, default=DEFAULT_REPO_OUTPUT)
    parser.add_argument("--entrypoint", default=DEFAULT_ENTRYPOINT)
    args = parser.parse_args()

    manuscript = read_text(args.overleaf_dir / args.entrypoint)
    output = args.repo_output_dir
    code = {
        "clean_liberia": read_text(args.repo_root / "4_Stata2/00_clean_liberia.do"),
        "clean_kenya": read_text(args.repo_root / "4_Stata2/00_clean_kenya.do"),
        "assignment": read_text(args.repo_root / "4_Stata2/04c_assignment_channel_tests.do"),
        "robustness": read_text(args.repo_root / "4_Stata2/06_robustness.do"),
    }
    tables = {
        "itt": read_text(output / "tab_pooled_itt.tex"),
        "signal": read_text(output / "tab_signal_quality.tex"),
        "signal_alt": read_text(output / "tab_signal_quality_alt.tex"),
        "upper_lower": read_text(output / "tab_pooled_upper_lower.tex"),
        "classroom": read_text(output / "tab_classroom_reallocation.tex"),
        "assignment_payoff": read_text(output / "tab_assignment_payoff_kenya.tex"),
        "dispersion": read_text(output / "tab_dispersion_firststage.tex"),
        "lib_sample": read_text(output / "lib_sampleflow.tex"),
        "ke_sample": read_text(output / "ke_sampleflow.tex"),
        "lib_attrition": read_text(output / "lib_attrition.tex"),
        "ke_attrition": read_text(output / "ke_attrition.tex"),
        "rnr_attrition": read_text(output / "tab_rnr_attrition_bounds.tex"),
        "peer": read_text(output / "tab_peer_effects.tex"),
        "peer_exact": read_text(output / "tab_peer_effects_exact_kenya.tex"),
        "suffstat_ke": read_text(output / "tab_suffstat_kenya.tex"),
        "suffstat_lib": read_text(output / "tab_suffstat_liberia.tex"),
        "classsize_ctrl": read_text(output / "tab_classsize_ctrl.tex"),
        "ceiling": read_text(output / "tab_ceiling.tex"),
        "score_variance": read_text(output / "tab_score_variance.tex"),
        "spec_robust": read_text(output / "tab_spec_robust.tex"),
        "lee_bounds": read_text(output / "tab_rnr_attrition_bounds.tex"),
    }

    results = [
        check_exact_numbers("ITT coefficients", tables["itt"], "Treatment", [0.031, -0.212]),
        check_exact_numbers("ITT sample sizes", tables["itt"], "N", [4954, 3154]),
        contains_all(
            "ITT inference prose",
            manuscript,
            [
                r"In Liberia, grouping reduces endline scores by $0.212$ SD ($p = 0.12$).",
                r"In Kenya, the effect is near zero ($0.031$ SD, $p = 0.56$).",
            ],
        ),
        check_table_snippet(
            "Kenya precision prose",
            manuscript,
            r"students with larger predicted assignment gains do not benefit more, and movers do not outperform stayers",
        ),
        check_exact_numbers("Signal quality Kenya grade 1", tables["signal"], "Kenya", [1, 2190, 0.713, 0.509]),
        check_signal_weight_floor(
            "EB shrinkage floor is nonbinding",
            tables["signal"],
            [code["clean_liberia"], code["clean_kenya"]],
        ),
        check_table_snippet(
            "Signal quality Kenya grade 2",
            tables["signal"],
            r"& 2 & 2005 &  0.748 &  0.559 \\",
        ),
        check_exact_numbers("Signal quality Liberia grade 1", tables["signal"], "Liberia", [1, 411, 0.247, 0.061]),
        check_table_snippet(
            "Signal quality Liberia grade 4",
            tables["signal"],
            r"& 4 & 348 &  0.255 &  0.065 \\",
        ),
        check_exact_numbers(
            "Alternative signal quality",
            tables["signal_alt"],
            "Incremental R-squared",
            [0.523, 0.050],
        ),
        check_exact_numbers(
            "Alternative rank persistence",
            tables["signal_alt"],
            "Within-grade rank persistence",
            [0.684, 0.242],
        ),
        contains_all(
            "Signal quality prose",
            manuscript,
            [
                r"Kenya is the high-signal case, with an incremental $R^2$ of $0.52$.",
                r"Liberia is the low-signal case, with $R^2$ between $0.03$ and $0.07$.",
            ],
        ),
        check_exact_numbers("Liberia sample flow analytic", tables["lib_sample"], "Analytic sample", [2249, 2535, 4784]),
        check_exact_numbers("Liberia sample flow endline", tables["lib_sample"], "With endline score", [1482, 1672, 3154]),
        check_exact_numbers("Kenya sample flow analytic", tables["ke_sample"], "Analytic sample", [6117, 985, 7102]),
        check_exact_numbers("Kenya sample flow endline", tables["ke_sample"], "With endline score", [4195, 759, 4954]),
        contains_all(
            "Sample-flow prose",
            manuscript,
            [
                r"Tables~\ref{tab:lib_sumstats}, \ref{tab:ke_sumstats}, and \ref{tab:ng_sumstats} report country-level summary statistics",
                r"Tables~\ref{tab:lib_sampleflow}, \ref{tab:ke_sampleflow}, and \ref{tab:ng_sampleflow} trace sample construction",
            ],
        ),
        check_table_snippet(
            "Liberia attrition overall",
            tables["rnr_attrition"],
            r"Liberia & endline & 0.340 & 0.341 &  0.000 & -0.212 & -0.214 & [-0.212, -0.212] \\",
        ),
        check_table_snippet(
            "Kenya attrition overall",
            tables["rnr_attrition"],
            r"Kenya & T3 endline & 0.229 & 0.314 & -0.075 &  0.031 &  0.028 & [-0.023,  0.154] \\",
        ),
        contains_all(
            "Attrition prose",
            manuscript,
            [
                r"Attrition does not explain the Kenya or Liberia findings.",
                r"Kenya's treatment arm has lower attrition than control, but IPW adjustment leaves the ITT at $+0.028$ SD and Lee bounds include zero.",
                r"Liberia attrition is balanced, and the IPW estimate remains $-0.214$ SD.",
            ],
        ),
        check_exact_numbers(
            "Upper/lower Liberia upper total",
            tables["upper_lower"],
            "Higher-track effect",
            [0.023, -0.348],
        ),
        check_table_snippet(
            "Upper/lower prose",
            manuscript,
            r"In Liberia, the negative effect is concentrated in the upper track ($-0.348$ SD, $p = 0.03$).",
        ),
        check_exact_numbers(
            "Classroom class size",
            tables["classroom"],
            "Class size",
            [20.88, 17.99, 32.19, 42.16],
        ),
        check_exact_numbers(
            "Classroom squared misfit",
            tables["classroom"],
            "Squared track target misfit",
            [1.352, 0.419, 1.519, 0.639],
        ),
        contains_all(
            "Classroom reallocation prose",
            manuscript,
            [
                r"In Kenya, the diagnostic rule lowers average predicted squared mismatch from 0.982 to 0.569",
                r"The classroom reallocation evidence then shows whether predictive content translated into realized grouping.",
            ],
        ),
        check_table_snippet(
            "Liberia class-size prose",
            manuscript,
            r"class sizes increase from 32 to 42 students",
        ),
        check_exact_numbers("Assignment-payoff movers", tables["assignment_payoff"], "Movers ITT", [0.030, 0.053, 1816]),
        check_exact_numbers("Assignment-payoff stayers", tables["assignment_payoff"], "Stayers ITT", [0.035, 0.073, 3138]),
        check_exact_numbers(
            "Assignment-payoff mover interaction",
            tables["assignment_payoff"],
            r"Treatment \(\times\) mover",
            [0.000, 0.082, 4954],
        ),
        check_exact_numbers(
            "Assignment-payoff G1 distance",
            tables["assignment_payoff"],
            r"G1 movers up: Treatment \(\times\) cutoff distance",
            [0.005, 0.017, 1286],
        ),
        check_exact_numbers(
            "Assignment-payoff G2 distance",
            tables["assignment_payoff"],
            r"G2 movers down: Treatment \(\times\) cutoff distance",
            [-0.006, 0.023, 530],
        ),
        check_exact_numbers(
            "Assignment-payoff predicted gain",
            tables["assignment_payoff"],
            r"Treatment \(\times\) predicted assignment gain (1 SD)",
            [0.008, 0.068, 4954],
        ),
        check_exact_numbers("Assignment-payoff mismatch proxy", tables["assignment_payoff"], "Mismatch proxy", [-0.008, 0.011, 4195]),
        check_exact_numbers(
            "Assignment-payoff mismatch with mean BL",
            tables["assignment_payoff"],
            "Mismatch proxy + school-grade mean BL",
            [-0.002, 0.011, 4195],
        ),
        contains_regexes(
            "Assignment-payoff code guardrail",
            code["assignment"],
            [
                r"gen mover_up\s+= grade == 1 & score_bl >\s+\$ke_cutoff_g1",
                r"gen mover_down = grade == 2 & score_bl <= \$ke_cutoff_g2",
                r"gen mover\s+= mover_up \| mover_down",
                r"ib0\.treat##ib0\.mover",
                r"i\.treat##c\.move_dist",
                r"egen assign_gain_z = std\(assign_gain\)",
                r"i\.treat##c\.assign_gain_z",
                r"tab_assignment_payoff_kenya\.tex",
            ],
        ),
        check_table_snippet(
            "Assignment-payoff prose",
            manuscript,
            r"the mover ITT is 0.030 SD, the stayer ITT is 0.035 SD, and the treatment-by-mover interaction is essentially zero",
        ),
        check_table_snippet(
            "Predicted assignment-gain prose",
            manuscript,
            r"An omnibus predicted-assignment-gain index also has a near-zero interaction with treatment: 0.008 SD per one standard deviation of predicted assignment gain (SE $=0.068$).",
        ),
        check_table_snippet(
            "Dispersion Kenya full sample",
            tables["dispersion"],
            r"Full Sample &  0.663 &  -0.257*** & 7102",
        ),
        check_table_snippet(
            "Dispersion Liberia full sample",
            tables["dispersion"],
            r"Full Sample &  0.542 &  -0.022 & 4784",
        ),
        contains_all(
            "Dispersion prose",
            manuscript,
            [
                r"Kenya is the clean first-stage success: within-class dispersion compresses substantially",
                r"within-class dispersion barely compresses because the diagnostic carries too little information",
            ],
        ),
        check_exact_numbers("Approximate peer/rank coefficients", tables["peer"], "Peer mean EB ability", [-0.133, -0.048]),
        check_table_snippet(
            "Exact peer/rank Kenya attenuation",
            tables["peer_exact"],
            r"Peer mean EB ability &  -0.133** &  -0.136** &   0.001 &  -0.009 &  -0.003 \\",
        ),
        check_exact_numbers(
            "Exact BH expected-exposure controls",
            tables["peer_exact"],
            r"Exact $\mu_i^{BH}$ control",
            [-0.177, -0.166],
        ),
        check_table_snippet(
            "Peer/rank prose",
            manuscript,
            r"This adverse composite is large enough to matter, but Appendix Table~\ref{tab:peer_effects_exact_kenya} shows that exact control-function and recentered specifications are close to zero.",
        ),
        check_table_snippet(
            "Exact peer/rank prose",
            manuscript,
            r"The correct interpretation is therefore not that a clean adverse peer effect explains Kenya's null.",
        ),
        check_table_snippet(
            "Kenya accounting peer contribution",
            tables["suffstat_ke"],
            r"Peer/rank contribution ($\hat{\zeta} \times \Delta\bar{\theta}$) & \multicolumn{2}{c}{ -0.037 (  0.019)} \\",
        ),
        check_table_snippet(
            "Liberia accounting class size",
            tables["suffstat_lib"],
            r"$\Delta$ class size (T $-$ C) &    11.4 \\",
        ),
        check_exact_numbers(
            "Class-size-control upper totals",
            tables["classsize_ctrl"],
            "Upper track total",
            [0.023, 0.021, -0.348, -0.345],
        ),
        check_exact_numbers(
            "Class-size-control interactions",
            tables["classsize_ctrl"],
            r"T $\times$ Upper",
            [-0.023, -0.023, -0.328, -0.237],
        ),
        contains_all(
            "Class-size-control prose",
            manuscript,
            [
                r"Class-size changes do not explain the main track-position results.",
                r"In Kenya and Liberia, adding realized class size leaves the upper-track estimates essentially unchanged",
            ],
        ),
        check_exact_numbers("Ceiling robustness treatment row", tables["ceiling"], "Treatment", [0.031, 0.040, 0.022]),
        check_exact_numbers("Ceiling robustness sample sizes", tables["ceiling"], "N", [4954, 4954, 4471]),
        check_exact_numbers("Ceiling robustness censored observations", tables["ceiling"], "Right-censored obs.", [176]),
        contains_all(
            "Ceiling robustness prose",
            manuscript,
            [
                r"Ceiling effects also do not explain the null or positive estimates.",
                r"Kenya's ITT remains close to zero under Tobit and trimmed-OLS specifications",
            ],
        ),
        check_table_snippet(
            "Score-variance table values",
            tables["score_variance"],
            r"Treatment &  -0.228*** &   0.137*",
        ),
        check_table_snippet(
            "Score-variance table offset",
            tables["score_variance"],
            r"Treatment &   0.239*** &  -0.082",
        ),
        contains_all(
            "Score-variance prose",
            manuscript,
            [
                r"In Kenya, treatment shifts variance from within-class to between-class components, as expected under successful sorting, without increasing aggregate score variance.",
                r"In Liberia, within-class variance rises rather than falls, consistent with weak sorting and organizational disruption.",
            ],
        ),
        check_exact_numbers(
            "Specification robustness baseline",
            tables["spec_robust"],
            "Baseline (EB + strata FE)",
            [0.031, 0.053, -0.212, 0.135],
        ),
        check_exact_numbers(
            "Specification robustness raw baseline",
            tables["spec_robust"],
            "Raw baseline score control",
            [0.031, 0.053, -0.212, 0.135],
        ),
        check_exact_numbers(
            "Specification robustness no baseline",
            tables["spec_robust"],
            "No baseline control",
            [0.110, 0.071, -0.240, 0.139],
        ),
        check_table_snippet(
            "Specification robustness p-values",
            tables["spec_robust"],
            r"Wild cluster bootstrap $p$-value & \multicolumn{2}{c}{0.622} & \multicolumn{2}{c}{0.126} \\",
        ),
        contains_all(
            "Specification robustness prose",
            manuscript,
            [
                r"The Kenya estimate is stable under the two controlled specifications and remains statistically indistinguishable from zero under all specifications.",
                r"The Liberia estimate remains negative throughout.",
            ],
        ),
        check_table_snippet(
            "Lee bounds Kenya row",
            tables["lee_bounds"],
            r"Kenya & T3 endline & 0.229 & 0.314 & -0.075 &  0.031 &  0.028 & [-0.023,  0.154] \\",
        ),
        check_table_snippet(
            "Lee bounds Liberia row",
            tables["lee_bounds"],
            r"Liberia & endline & 0.340 & 0.341 &  0.000 & -0.212 & -0.214 & [-0.212, -0.212] \\",
        ),
        check_table_snippet(
            "Lee bounds Nigeria T2 row",
            tables["lee_bounds"],
            r"Nigeria & T2 ETE & 0.309 & 0.323 &  0.001 &  0.146 &  0.137 & [ 0.146,  0.180] \\",
        ),
        check_table_snippet(
            "Lee bounds Nigeria T3 row",
            tables["lee_bounds"],
            r"Nigeria & T3 ETE & 0.350 & 0.490 & -0.135 &  0.105 &  0.111 & [-0.126,  0.298] \\",
        ),
        contains_regexes(
            "Lee bounds code-method guardrail",
            code["robustness"],
            [
                r"keep if finsamp.*?gen attrit = !has_el",
                r"local attr_diff = ``study'_attr_t' - ``study'_attr_c'",
                r"if `attr_diff' > 0 \{.*?local trim_arm 0.*?local trim_frac = `attr_diff' / \(1 - ``study'_attr_c'\)",
                r"else if `attr_diff' < 0 \{.*?local trim_arm 1.*?local trim_frac = -`attr_diff' / \(1 - ``study'_attr_t'\)",
                r"Lower bound: trim highest scores from the less-attrited arm.*?drop if treat == `trim_arm' & std_score_el > `cutoff_upper'",
                r"Upper bound: trim lowest scores from the less-attrited arm.*?drop if treat == `trim_arm' & std_score_el < `cutoff_lower'",
            ],
        ),
        check_table_snippet(
            "Lee bounds table methods note",
            tables["lee_bounds"],
            "Lee bounds trim the lower-attrition arm to equalize response rates",
        ),
        contains_all(
            "Lee bounds prose",
            manuscript,
            [
                r"Kenya's treatment arm has lower attrition than control, but IPW adjustment leaves the ITT at $+0.028$ SD and Lee bounds include zero.",
                r"T2 endterm bounds are tightly positive, $[0.146,0.180]$, while T3 endterm bounds are wide, $[-0.126,0.298]$.",
            ],
        ),
    ]

    print("Numeric prose-claim checks")
    render_results(results)

    if all(result.ok for result in results):
        print("\nNumeric prose-claim checks passed")
        return 0

    print("\nNumeric prose-claim checks failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
