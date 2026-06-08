"""
utils.py — Shared helpers for regression, table formatting, and plotting.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams.update({"figure.dpi": 150, "savefig.bbox": "tight",
                      "font.size": 11, "axes.titlesize": 13})


# ── Regression ───────────────────────────────────────────────────────────────

def ols_cluster(y, X, cluster, add_const=True):
    """
    OLS with cluster-robust SEs.

    Stata equivalent:
        reg y x1 x2, vce(cluster clustervar)

    Parameters
    ----------
    y : Series — dependent variable
    X : DataFrame — regressors (without constant unless add_const=False)
    cluster : Series — cluster identifier (aligned with y)
    add_const : bool — prepend a constant column

    Returns
    -------
    statsmodels RegressionResultsWrapper
    """
    mask = y.notna() & X.notna().all(axis=1) & cluster.notna()
    y_, X_, cl_ = y[mask], X[mask], cluster[mask]
    if add_const:
        X_ = sm.add_constant(X_)
    model = sm.OLS(y_, X_)
    return model.fit(cov_type="cluster", cov_kwds={"groups": cl_})


def stars(pval):
    """Return significance stars for a p-value."""
    if pd.isna(pval):
        return ""
    if pval < 0.01:
        return "***"
    if pval < 0.05:
        return "**"
    if pval < 0.10:
        return "*"
    return ""


def coef_str(result, var, fmt=".3f"):
    """Format coefficient with stars."""
    b = result.params[var]
    p = result.pvalues[var]
    return f"{b:{fmt}}{stars(p)}"


def se_str(result, var, fmt=".3f"):
    """Format SE in parentheses."""
    return f"({result.bse[var]:{fmt}})"


# ── Leave-self-out group means ───────────────────────────────────────────────

def leave_self_out_mean(df, group_cols, value_col):
    """
    Compute leave-self-out mean of `value_col` within groups defined by
    `group_cols`. Returns a Series aligned with df.

    Stata equivalent:
        bys group: egen total = total(value)
        bys group: egen count = count(value)
        gen loo_mean = (total - value) / (count - 1)
    """
    grp = df.groupby(group_cols)[value_col]
    total = grp.transform("sum")
    count = grp.transform("count")
    own = df[value_col].fillna(0)
    own_present = df[value_col].notna().astype(int)
    return (total - own) / (count - own_present).replace(0, np.nan)


# ── Standardisation ──────────────────────────────────────────────────────────

def standardise_by_grade(df, col, control_mask):
    """
    Standardise `col` using control-group mean and SD within each grade.

    Stata equivalent:
        summ score if grade==g & treat==0
        gen std_score = (score - r(mean)) / r(sd)
        ... (repeated per grade)
    """
    out = pd.Series(np.nan, index=df.index, name=f"std_{col}")
    for g in sorted(df["grade"].dropna().unique()):
        ctrl_g = control_mask & (df["grade"] == g)
        mu = df.loc[ctrl_g, col].mean()
        sd = df.loc[ctrl_g, col].std()
        grade_mask = df["grade"] == g
        if sd is None or sd == 0 or pd.isna(sd):
            continue
        out[grade_mask] = (df.loc[grade_mask, col] - mu) / sd
    return out


# ── Fixed-effect dummies ─────────────────────────────────────────────────────

def strata_fe(strata_col, prefix="s", drop_first=True):
    """Create strata fixed-effect dummies (equivalent to absorb(strata))."""
    return pd.get_dummies(strata_col, prefix=prefix, drop_first=drop_first,
                          dtype=float)


def decile_treat_fe(bl_dec, treat, drop_first=True):
    """Create decile x treatment cell FE (equivalent to i.s_decile##T_j).

    Requires that bl_dec and treat contain no NaN values.
    """
    cell_id = bl_dec.astype(int) * 10 + treat.astype(int)
    return pd.get_dummies(cell_id, prefix="dtfe", drop_first=drop_first,
                          dtype=float)


# ── Printing / table helpers ─────────────────────────────────────────────────

def print_sample_log(label, n):
    """Print a sample-restriction step."""
    print(f"  {label:.<60s} N = {n:,d}")
