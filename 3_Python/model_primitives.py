"""
model_primitives.py
===================
Minimal structural primitives for first-pass cross-country SMM.

This module keeps the model deliberately parsimonious and reduced-form anchored:
- rho_m and tau_m are latent-quality primitives in [0,1]
- zeta_m is the peer/rank composite loading
- exec_m is assignment execution quality in [0,1]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
import numpy as np


MARKETS = ("kenya", "liberia", "nigeria")


def logistic(x: np.ndarray | float) -> np.ndarray | float:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class NaturalParams:
    rho: Dict[str, float]
    tau: Dict[str, float]
    exec_q: Dict[str, float]
    zeta: Dict[str, float]
    alpha0: float
    alpha_rho: float
    alpha_tau: float
    alpha_soc: float
    alpha_exec: float
    disp0: float
    disp_rho: float
    disp_exec: float
    peer0: float
    peer_rho: float
    peer_exec: float


def unpack_params(raw: np.ndarray) -> NaturalParams:
    """
    Transform unconstrained optimizer vector to natural-scale parameters.
    """
    if raw.shape[0] != 23:
        raise ValueError(f"Expected 23 parameters, got {raw.shape[0]}")

    i = 0
    rho_raw = raw[i : i + 3]
    i += 3
    tau_raw = raw[i : i + 3]
    i += 3
    exec_raw = raw[i : i + 3]
    i += 3
    zeta_raw = raw[i : i + 3]
    i += 3

    rho = {m: float(logistic(rho_raw[j])) for j, m in enumerate(MARKETS)}
    tau = {m: float(logistic(tau_raw[j])) for j, m in enumerate(MARKETS)}
    exec_q = {m: float(logistic(exec_raw[j])) for j, m in enumerate(MARKETS)}
    zeta = {m: float(zeta_raw[j]) for j, m in enumerate(MARKETS)}

    alpha0, alpha_rho, alpha_tau, alpha_soc, alpha_exec = map(float, raw[i : i + 5])
    i += 5
    disp0, disp_rho, disp_exec = map(float, raw[i : i + 3])
    i += 3
    peer0, peer_rho, peer_exec = map(float, raw[i : i + 3])

    return NaturalParams(
        rho=rho,
        tau=tau,
        exec_q=exec_q,
        zeta=zeta,
        alpha0=alpha0,
        alpha_rho=alpha_rho,
        alpha_tau=alpha_tau,
        alpha_soc=alpha_soc,
        alpha_exec=alpha_exec,
        disp0=disp0,
        disp_rho=disp_rho,
        disp_exec=disp_exec,
        peer0=peer0,
        peer_rho=peer_rho,
        peer_exec=peer_exec,
    )


def nigeria_impl_moments(par: NaturalParams) -> Dict[str, float]:
    """
    Nigeria implementation moments implied by execution quality.
    """
    rho = par.rho["nigeria"]
    ex = par.exec_q["nigeria"]
    # Fixed-shape implementation mapping to avoid overfitting.
    spearman = rho * ex
    p_two = logistic(1.8 - 3.0 * ex)
    p_yel = logistic(-0.8 + 2.0 * ex)
    p_miss = logistic(-1.2 + 1.6 * (1.0 - ex))
    return {
        "spearman_placement_to_group_treat_target": float(spearman),
        "share_treat_academies_two_groups_or_less_target": float(p_two),
        "share_treat_academies_with_any_yellow_target": float(p_yel),
        "share_treat_missing_group_record_target": float(p_miss),
        # Also map computed-sample analogues through same regime block.
        "share_treat_academies_two_groups_or_less": float(p_two),
        "share_treat_academies_with_any_yellow": float(p_yel),
        "share_treat_missing_group_record": float(p_miss),
        "spearman_placement_to_group_treat": float(spearman),
    }


def market_outcome_itt(par: NaturalParams, market: str) -> float:
    return float(
        par.alpha0
        + par.alpha_rho * par.rho[market]
        + par.alpha_tau * par.tau[market]
        + par.alpha_soc * par.zeta[market]
        + par.alpha_exec * par.exec_q[market]
    )


def market_dispersion(par: NaturalParams, market: str) -> float:
    return float(
        par.disp0
        + par.disp_rho * (1.0 - par.rho[market])
        + par.disp_exec * (1.0 - par.exec_q[market])
    )


def market_peer_shift(par: NaturalParams, market: str) -> float:
    return float(
        par.peer0
        + par.peer_rho * par.rho[market]
        + par.peer_exec * (1.0 - par.exec_q[market])
    )
