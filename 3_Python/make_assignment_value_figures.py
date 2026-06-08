#!/usr/bin/env python3
"""Build paper-ready assignment-value diagnostics from control-trained gains."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "3_Python" / "output" / "control_trained_gains"
STRUCT_DIR = ROOT / "3_Python" / "output" / "structural_smm"
LATEX_DIR = STRUCT_DIR / "latex"
PAPER_DIR = ROOT / "structural_output"

COUNTRIES = ["kenya", "liberia", "nigeria"]
LABELS = {"kenya": "Kenya", "liberia": "Liberia", "nigeria": "Nigeria"}


def fmt_num(x: float) -> str:
    return f"{x:.3f}"


def main() -> None:
    LATEX_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.8), sharey=True)

    for ax, country in zip(axes, COUNTRIES):
        path = IN_DIR / f"{country}_predicted_gains.parquet"
        df = pd.read_parquet(path)
        df = df.dropna(subset=["mismatch_grade", "mismatch_designed"]).copy()
        df["gain"] = df["mismatch_grade"] - df["mismatch_designed"]

        eps = 1e-6
        lower = float((df["gain"] > eps).mean())
        higher = float((df["gain"] < -eps).mean())
        unchanged = float((df["gain"].abs() <= eps).mean())
        rows.append(
            {
                "country": LABELS[country],
                "n": int(len(df)),
                "grade_mismatch": float(df["mismatch_grade"].mean()),
                "diagnostic_mismatch": float(df["mismatch_designed"].mean()),
                "mean_reduction": float(df["gain"].mean()),
                "share_lower": lower,
                "share_higher": higher,
                "share_unchanged": unchanged,
            }
        )

        pooled = pd.concat(
            [
                pd.DataFrame({"mismatch": df["mismatch_grade"], "rule": "Grade"}),
                pd.DataFrame({"mismatch": df["mismatch_designed"], "rule": "Diagnostic"}),
            ],
            ignore_index=True,
        )
        xmax = float(pooled["mismatch"].quantile(0.98))
        bins = 28
        for rule, color in [("Grade", "#4E79A7"), ("Diagnostic", "#E15759")]:
            vals = pooled.loc[pooled["rule"] == rule, "mismatch"].clip(upper=xmax)
            ax.hist(
                vals,
                bins=bins,
                range=(0, xmax),
                density=True,
                histtype="step",
                linewidth=1.8,
                color=color,
                label=rule,
            )
        ax.set_title(LABELS[country])
        ax.set_xlabel("Predicted squared mismatch")
        ax.axvline(df["mismatch_grade"].mean(), color="#4E79A7", linestyle=":", linewidth=1.2)
        ax.axvline(df["mismatch_designed"].mean(), color="#E15759", linestyle=":", linewidth=1.2)

    axes[0].set_ylabel("Density")
    axes[-1].legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(STRUCT_DIR / "fig_assignment_mismatch_distributions.pdf")
    fig.savefig(PAPER_DIR / "fig_assignment_mismatch_distributions.pdf")
    plt.close(fig)

    out = pd.DataFrame(rows)
    out.to_csv(STRUCT_DIR / "assignment_value_summary.csv", index=False)

    lines = [
        r"\begin{table}[H]",
        r"\centering",
        r"\caption{Predicted Mismatch Under Grade and Diagnostic Assignment}",
        r"\label{tab:assignment_value_summary}",
        r"\begin{threeparttable}",
        r"\footnotesize",
        r"\begin{tabular}[t]{lrrrrrrr}",
        r"\toprule",
        r" & N & Grade & Diagnostic & Reduction & Lower & Higher & Same \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{row['country']} & {row['n']} & {fmt_num(row['grade_mismatch'])} "
            f"& {fmt_num(row['diagnostic_mismatch'])} & {fmt_num(row['mean_reduction'])} "
            f"& {100 * row['share_lower']:.1f}\\% & {100 * row['share_higher']:.1f}\\% "
            f"& {100 * row['share_unchanged']:.1f}\\% \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\begin{tablenotes}[para,flushleft]",
            r"\footnotesize",
            (
                r"\item \textit{Notes:} The table uses the control-trained assignment-gain "
                r"objects described in the text. ``Grade'' is the mean squared distance between "
                r"the baseline ability proxy and the grade-level instructional target. "
                r"``Diagnostic'' replaces the grade target with the intended diagnostic-assigned "
                r"track target. ``Reduction'' is Grade minus Diagnostic, so positive values mean "
                r"the diagnostic rule lowers predicted mismatch. Lower, Higher, and Same report "
                r"the share of students whose predicted mismatch falls, rises, or is unchanged. "
                r"Nigeria uses the designed assignment rule; realized-assignment failures enter "
                r"the implementation diagnostics separately."
            ),
            r"\end{tablenotes}",
            r"\end{threeparttable}",
            r"\end{table}",
            "",
        ]
    )
    table_text = "\n".join(lines)
    (LATEX_DIR / "tab_assignment_value_summary.tex").write_text(table_text, encoding="utf-8")
    (PAPER_DIR / "tab_assignment_value_summary.tex").write_text(table_text, encoding="utf-8")


if __name__ == "__main__":
    main()
