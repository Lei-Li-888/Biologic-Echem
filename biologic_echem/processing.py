"""
Electrochemical data processing.

Covers:
  - Half-cycle segmentation by current sign
  - Cycle extraction
  - Specific capacity (mAh g⁻¹) via current integration
  - Differential capacity (dQ/dV) analysis
  - Coulombic efficiency
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Half-cycle segmentation
# ---------------------------------------------------------------------------

def segment_halfcycles(
    df: pd.DataFrame,
    rolling_window: int = 11,
    min_points: int = 20,
) -> list[pd.DataFrame]:
    """Split a charge-discharge dataset into alternating half-cycles.

    Uses median smoothing on the current to avoid spurious splits from noise.
    Short segments (< ``min_points``) are merged into their neighbours.

    Parameters
    ----------
    df:
        DataFrame with columns ``t`` (s), ``E`` (V), ``I`` (mA).
    rolling_window:
        Points for current-smoothing median filter.
    min_points:
        Minimum half-cycle length; shorter ones are merged.

    Returns
    -------
    List of DataFrames, each representing one half-cycle (charge or discharge).
    """
    I = pd.Series(df["I"].values, dtype=float)
    I_smooth = I.rolling(rolling_window, center=True, min_periods=1).median()
    sign = np.sign(I_smooth.to_numpy()).astype(float)

    # Forward-fill zeros
    for k in range(1, len(sign)):
        if sign[k] == 0:
            sign[k] = sign[k - 1]
    if len(sign) > 0 and sign[0] == 0:
        for k in range(1, len(sign)):
            if sign[k] != 0:
                sign[0] = sign[k]
                break

    # Build raw segment list [(start_idx, end_idx, sign), ...]
    segs: list[tuple[int, int, float]] = []
    start = 0
    cur = sign[0] if len(sign) > 0 else 1.0
    for k in range(1, len(sign)):
        if sign[k] != cur:
            segs.append((start, k, cur))
            start, cur = k, sign[k]
    segs.append((start, len(sign), cur))

    segs = _merge_short(segs, min_points)
    return [df.iloc[s:e].reset_index(drop=True) for s, e, _ in segs]


def _merge_short(
    segs: list[tuple[int, int, float]],
    min_points: int,
) -> list[tuple[int, int, float]]:
    if len(segs) <= 1:
        return segs
    changed = True
    while changed and len(segs) > 1:
        changed = False
        merged: list[tuple[int, int, float]] = []
        i = 0
        while i < len(segs):
            s, e, sg = segs[i]
            if e - s < min_points:
                changed = True
                if i == 0 and len(segs) > 1:
                    # merge forward
                    ns, ne, nsg = segs[i + 1]
                    segs[i + 1] = (s, ne, nsg)
                    i += 1
                elif merged:
                    # merge backward
                    ps, pe, psg = merged[-1]
                    merged[-1] = (ps, e, psg)
                    i += 1
                else:
                    merged.append((s, e, sg))
                    i += 1
            else:
                merged.append((s, e, sg))
                i += 1
        segs = merged
    return segs


# ---------------------------------------------------------------------------
# Cycle extraction
# ---------------------------------------------------------------------------

def get_cycle(
    halfcycles: list[pd.DataFrame],
    n: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the charge and discharge halves of the *n*-th full cycle.

    Cycles are 1-indexed: cycle 1 is the first charge+discharge pair.

    Parameters
    ----------
    halfcycles:
        Output from :func:`segment_halfcycles`.
    n:
        Which cycle to extract (1-indexed).

    Returns
    -------
    ``(charge_half, discharge_half)`` DataFrames.

    Raises
    ------
    ValueError
        If there are not enough half-cycles for the requested cycle.
    """
    required = 2 * n
    if len(halfcycles) < required:
        raise ValueError(
            f"Requested cycle {n} but only {len(halfcycles) // 2} complete "
            f"cycles found ({len(halfcycles)} half-cycles)."
        )
    idx = 2 * (n - 1)
    return halfcycles[idx], halfcycles[idx + 1]


# ---------------------------------------------------------------------------
# Capacity and energy
# ---------------------------------------------------------------------------

def specific_capacity(seg: pd.DataFrame, mass_mg: float) -> np.ndarray:
    """Compute cumulative specific capacity (mAh g⁻¹) for one half-cycle.

    Integrates |I| * dt using the actual (non-uniform) time steps.

    Parameters
    ----------
    seg:
        Half-cycle DataFrame with columns ``t`` (s) and ``I`` (mA).
    mass_mg:
        Active material mass in milligrams.

    Returns
    -------
    Array of specific capacity values in mAh g⁻¹, same length as *seg*.
    """
    t = seg["t"].to_numpy(dtype=float)
    I = seg["I"].to_numpy(dtype=float)

    dt = np.diff(t, prepend=t[0])
    dt = np.clip(dt, 0, None)       # guard against backward timestamps
    dQ = np.abs(I) * dt / 3600.0    # mAh increments
    return np.cumsum(dQ) / (mass_mg / 1000.0)


def coulombic_efficiency(Q_charge: np.ndarray, Q_discharge: np.ndarray) -> float:
    """Return coulombic efficiency as a fraction (e.g. 0.985 = 98.5 %).

    Parameters
    ----------
    Q_charge, Q_discharge:
        Specific-capacity arrays from :func:`specific_capacity`.
    """
    q_chg = Q_charge[-1] if len(Q_charge) > 0 else 0.0
    q_dis = Q_discharge[-1] if len(Q_discharge) > 0 else 0.0
    if q_chg == 0:
        return float("nan")
    return q_dis / q_chg


# ---------------------------------------------------------------------------
# Differential capacity (dQ/dV)
# ---------------------------------------------------------------------------

def dqdv(
    Q: np.ndarray,
    V: np.ndarray,
    dv: float = 0.005,
    sigma: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute differential capacity dQ/dV vs. voltage.

    Interpolates onto a uniform voltage grid, computes the gradient, then
    applies Gaussian smoothing.  Peak positions in the dQ/dV plot correspond
    to electrochemical phase transitions.

    Parameters
    ----------
    Q:
        Specific capacity array (mAh g⁻¹).
    V:
        Voltage array (V), same length as *Q*.
    dv:
        Voltage grid spacing in volts (default 5 mV).
    sigma:
        Gaussian smoothing standard deviation in volts.

    Returns
    -------
    ``(V_grid, dQdV)`` — uniform voltage grid and smoothed dQ/dV values.
    """
    try:
        from scipy.ndimage import gaussian_filter1d
    except ImportError as exc:
        raise ImportError(
            "scipy is required for dQ/dV analysis.  "
            "Install it with:  pip install scipy"
        ) from exc

    # Sort by voltage and remove duplicates
    order = np.argsort(V)
    Vs, Qs = V[order], Q[order]
    _, ui = np.unique(Vs, return_index=True)
    Vs, Qs = Vs[ui], Qs[ui]

    if len(Vs) < 5:
        return Vs, np.zeros_like(Vs)

    V_grid = np.arange(Vs[0], Vs[-1], dv)
    Q_interp = np.interp(V_grid, Vs, Qs)
    dQdV = np.gradient(Q_interp, V_grid)
    sigma_pts = max(1, sigma / dv)
    return V_grid, gaussian_filter1d(dQdV, sigma=sigma_pts)
