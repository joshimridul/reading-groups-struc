#!/usr/bin/env python3
"""Build standardized summary figures for the three-country paper.

The inputs below are copied from the active manuscript tables. This script does
not estimate new effects; it turns reported moments into reader-facing figures.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parents[1] / "structural_output"
OUT.mkdir(exist_ok=True)

COLORS = {
    "signal": "#2A9D8F",
    "execution": "#4E5D6C",
    "delivery": "#E9C46A",
    "effect": "#1F4E79",
    "negative": "#B4453C",
    "neutral": "#6F6F6F",
    "light": "#E8EEF2",
}


def setup():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.dpi": 200,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#D9DEE3",
            "grid.linewidth": 0.7,
        }
    )


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)


def fig_experiment_map():
    countries = ["Liberia", "Kenya", "Nigeria"]
    primitives = {
        "Signal quality $\\rho$": [0.055, 0.533, 0.121],
        "Assignment execution $\\omega$": [1.00, 1.00, 0.84],
        "Delivery fidelity $\\tau$": [0.38, 0.50, 0.31],
    }
    effects = np.array([-0.212, 0.031, 0.093])
    ses = np.array([0.135, 0.053, 0.133])
    ci = 1.96 * ses

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.8, 3.15),
        gridspec_kw={"width_ratios": [1.48, 1.0], "wspace": 0.44},
    )

    ax = axes[0]
    y = np.arange(len(countries))
    offsets = [-0.22, 0.0, 0.22]
    colors = [COLORS["signal"], COLORS["execution"], COLORS["delivery"]]
    for (label, values), off, color in zip(primitives.items(), offsets, colors):
        ax.barh(y + off, values, height=0.18, color=color, label=label)
        for yy, val in zip(y + off, values):
            ax.text(min(val + 0.025, 1.03), yy, f"{val:.2f}", va="center", fontsize=7)

    ax.set_yticks(y)
    ax.set_yticklabels(countries)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Primitive value")
    ax.set_title("A. Realized organizational inputs")
    ax.legend(loc="lower center", bbox_to_anchor=(0.52, -0.34), frameon=False, ncol=3)

    ax = axes[1]
    ax.axvline(0, color="#5B5B5B", linewidth=0.9)
    effect_colors = [COLORS["negative"], COLORS["neutral"], COLORS["effect"]]
    for yy, est, half, color in zip(y, effects, ci, effect_colors):
        ax.errorbar(
            est,
            yy,
            xerr=half,
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.2,
            capsize=3,
            markersize=5,
        )
        ax.text(est + (0.03 if est >= 0 else -0.03), yy - 0.18, f"{est:+.2f}", ha="left" if est >= 0 else "right", fontsize=8)

    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.invert_yaxis()
    ax.set_xlim(-0.55, 0.42)
    ax.set_xlabel("ITT, SD units")
    ax.set_title("B. Observed treatment effects", pad=12)
    ax.grid(axis="y", visible=False)
    fig.suptitle("Three experiments occupy different implementation cells", y=1.05, fontsize=11)
    fig.subplots_adjust(bottom=0.22)
    save(fig, "fig_experiment_map.pdf")


def fig_firststage_payoff():
    countries = ["Kenya", "Liberia", "Nigeria"]
    dispersion = np.array([-0.262, 0.013, 0.054])
    disp_se = np.array([0.022, 0.038, 0.030])

    labels = ["Movers", "Stayers", "T x mover", "Predicted gain"]
    payoff = np.array([0.030, 0.035, -0.000, 0.008])
    payoff_se = np.array([0.053, 0.073, 0.082, 0.068])

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.1), gridspec_kw={"wspace": 0.42})

    ax = axes[0]
    x = np.arange(len(countries))
    bars = ax.bar(x, dispersion, color=[COLORS["effect"], COLORS["neutral"], COLORS["negative"]], width=0.58)
    ax.errorbar(x, dispersion, yerr=1.96 * disp_se, fmt="none", ecolor="#222222", capsize=3, linewidth=1.0)
    ax.axhline(0, color="#5B5B5B", linewidth=0.9)
    for bar, val in zip(bars, dispersion):
        ax.text(bar.get_x() + bar.get_width() / 2, val + (0.018 if val >= 0 else -0.035), f"{val:+.2f}", ha="center", va="bottom" if val >= 0 else "top", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(countries)
    ax.set_ylabel("Effect on within-class dispersion")
    ax.set_title("A. Sorting first stage")
    ax.set_ylim(-0.34, 0.14)

    ax = axes[1]
    y = np.arange(len(labels))
    ax.axvline(0, color="#5B5B5B", linewidth=0.9)
    ax.errorbar(payoff, y, xerr=1.96 * payoff_se, fmt="o", color=COLORS["effect"], ecolor=COLORS["effect"], capsize=3, markersize=5)
    for yy, val in zip(y, payoff):
        ax.text(0.215, yy, f"{val:+.3f}", va="center", ha="right", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(-0.18, 0.24)
    ax.set_xlabel("Effect, SD units")
    ax.set_title("B. Kenya payoff tests")
    ax.grid(axis="y", visible=False)

    fig.suptitle("Kenya sorts successfully, but the observed assignment payoff is near zero", y=1.03, fontsize=11)
    save(fig, "fig_firststage_payoff.pdf")


def fig_counterfactual_ladder():
    scenarios = [
        ("Kenya observed", 0.030, -0.066, 0.117, "Observed"),
        ("Liberia observed", -0.176, -0.337, -0.006, "Observed"),
        ("Nigeria realized", 0.056, -0.148, 0.244, "Observed"),
        ("Kenya high delivery", 0.155, 0.028, 0.206, "Counterfactual"),
        ("High input", 0.187, 0.058, 0.222, "Counterfactual"),
    ]
    gains = [
        ("$G$ only", 0.001, 0.000),
        ("$\\omega$ only", 0.000, 0.000),
        ("$\\tau$ only", 0.059, 0.000),
        ("$G+\\tau$", 0.147, 0.087),
        ("All three", 0.161, 0.102),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(7.7, 3.25), gridspec_kw={"width_ratios": [1.15, 1.0], "wspace": 0.48})

    ax = axes[0]
    y = np.arange(len(scenarios))
    ax.axvline(0, color="#5B5B5B", linewidth=0.9)
    for yy, (label, est, lo, hi, group) in zip(y, scenarios):
        color = COLORS["effect"] if group == "Counterfactual" else COLORS["neutral"]
        if "Liberia" in label:
            color = COLORS["negative"]
        ax.errorbar(est, yy, xerr=[[est - lo], [hi - est]], fmt="o", color=color, ecolor=color, capsize=3, markersize=5)
        ax.text(est + (0.025 if est >= 0 else -0.025), yy, f"{est:+.3f}", ha="left" if est >= 0 else "right", va="center", fontsize=8)
    ax.set_yticks(y)
    ax.set_yticklabels([s[0] for s in scenarios])
    ax.invert_yaxis()
    ax.set_xlim(-0.40, 0.28)
    ax.set_xlabel("Model-predicted ATE, SD units")
    ax.set_title("A. Observed cells and high-input benchmarks")
    ax.grid(axis="y", visible=False)

    ax = axes[1]
    x = np.arange(len(gains))
    total = np.array([g[1] for g in gains])
    nonadd = np.array([g[2] for g in gains])
    base = total - nonadd
    ax.bar(x, base, color=COLORS["delivery"], label="Additive gain")
    ax.bar(x, nonadd, bottom=base, color=COLORS["signal"], label="Nonadditive gain")
    ax.axhline(0, color="#5B5B5B", linewidth=0.9)
    for xx, val in zip(x, total):
        ax.text(xx, val + 0.008, f"{val:+.3f}", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([g[0] for g in gains])
    ax.set_ylabel("Gain over realized Nigeria")
    ax.set_title("B. Primitive upgrades in Nigeria")
    ax.set_ylim(0, 0.19)
    ax.legend(frameon=False, loc="upper left")
    fig.suptitle("Counterfactual gains require joint assignment value and delivery fidelity", y=1.03, fontsize=11)
    save(fig, "fig_counterfactual_ladder.pdf")


def fig_track_position_allcountries():
    countries = ["Kenya", "Liberia", "Nigeria"]
    lower = np.array([0.046, -0.019, 0.007])
    lower_se = np.array([0.137, 0.181, 0.152])
    higher = np.array([0.023, -0.348, 0.246])
    higher_se = np.array([0.044, 0.154, 0.129])

    fig, ax = plt.subplots(figsize=(5.7, 3.0))
    y = np.arange(len(countries))
    ax.axvline(0, color="#5B5B5B", linewidth=0.9)

    series = [
        (lower, lower_se, -0.12, "Lower track", COLORS["neutral"], "o"),
        (higher, higher_se, 0.12, "Higher track", COLORS["effect"], "s"),
    ]
    for estimates, ses, offset, label, color, marker in series:
        ax.errorbar(
            estimates,
            y + offset,
            xerr=1.96 * ses,
            fmt=marker,
            color=color,
            ecolor=color,
            elinewidth=1.2,
            capsize=3,
            markersize=4.8,
            label=label,
        )
        for yy, estimate in zip(y + offset, estimates):
            ax.text(
                estimate + (0.025 if estimate >= 0 else -0.025),
                yy,
                f"{estimate:+.2f}",
                ha="left" if estimate >= 0 else "right",
                va="center",
                fontsize=8,
            )

    ax.set_yticks(y)
    ax.set_yticklabels(countries)
    ax.invert_yaxis()
    ax.set_xlim(-0.75, 0.62)
    ax.set_xlabel("Treatment effect, SD units")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.60, 1.16), ncol=2)
    save(fig, "fig_track_position_allcountries.pdf")


if __name__ == "__main__":
    setup()
    fig_experiment_map()
    fig_firststage_payoff()
    fig_counterfactual_ladder()
    fig_track_position_allcountries()
    print(f"Wrote figures to {OUT}")
