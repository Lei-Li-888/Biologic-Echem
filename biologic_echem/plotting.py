"""
Standard electrochemical plots.

All plot_* functions accept a Matplotlib ``Axes`` object as the first
argument so they compose naturally with any figure layout.

Colour scheme:
  charge     #E05A4E  (muted red)
  discharge  #4A90D9  (muted blue)
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes


CHARGE_COLOR = "#E05A4E"
DISCHARGE_COLOR = "#4A90D9"

DEFAULT_FIGSIZE = (6.2, 4.6)
DEFAULT_DPI = 300


# ---------------------------------------------------------------------------
# Figure factory
# ---------------------------------------------------------------------------

def new_figure(figsize: tuple[float, float] = DEFAULT_FIGSIZE) -> tuple[Figure, Axes]:
    """Return a ``(fig, ax)`` pair with publication-ready defaults."""
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


# ---------------------------------------------------------------------------
# Individual plot functions
# ---------------------------------------------------------------------------

def plot_vq(
    ax: Axes,
    Q_chg: np.ndarray,
    V_chg: np.ndarray,
    Q_dis: np.ndarray,
    V_dis: np.ndarray,
    label: str = "",
    lw: float = 1.5,
    chg_color: str = CHARGE_COLOR,
    dis_color: str = DISCHARGE_COLOR,
) -> None:
    """Voltage vs. specific capacity (charge and discharge on the same axes).

    Parameters
    ----------
    ax:          Matplotlib Axes.
    Q_chg/V_chg: Specific capacity (mAh g⁻¹) and voltage arrays for the charge half-cycle.
    Q_dis/V_dis: Same for the discharge half-cycle.
    label:       Prefix appended to "charge" / "discharge" in the legend.
    """
    prefix = f"{label} " if label else ""
    ax.plot(Q_chg, V_chg, color=chg_color, lw=lw, label=f"{prefix}charge")
    ax.plot(Q_dis, V_dis, color=dis_color, lw=lw, label=f"{prefix}discharge")
    ax.set_xlabel("Specific Capacity (mAh g⁻¹)")
    ax.set_ylabel("Voltage (V)")


def plot_dqdv(
    ax: Axes,
    V_chg_grid: np.ndarray,
    dQdV_chg: np.ndarray,
    V_dis_grid: np.ndarray,
    dQdV_dis: np.ndarray,
    label: str = "",
    lw: float = 1.5,
    chg_color: str = CHARGE_COLOR,
    dis_color: str = DISCHARGE_COLOR,
) -> None:
    """Differential capacity dQ/dV vs. voltage.

    Parameters
    ----------
    ax:                      Matplotlib Axes.
    V_chg_grid / dQdV_chg:  Voltage grid and dQ/dV for the charge half-cycle.
    V_dis_grid / dQdV_dis:  Same for the discharge half-cycle.
    label:                   Prefix appended to legend entries.
    """
    prefix = f"{label} " if label else ""
    ax.plot(V_chg_grid, dQdV_chg, color=chg_color, lw=lw, label=f"{prefix}charge")
    ax.plot(V_dis_grid, dQdV_dis, color=dis_color, lw=lw, label=f"{prefix}discharge")
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("dQ/dV (mAh g⁻¹ V⁻¹)")


def plot_cv(
    ax: Axes,
    V: np.ndarray,
    I: np.ndarray,
    label: str = "",
    lw: float = 1.5,
    color: str | None = None,
) -> None:
    """Cyclic voltammetry: current vs. voltage.

    Parameters
    ----------
    ax:     Matplotlib Axes.
    V:      Voltage array (V).
    I:      Current array (mA).
    label:  Legend label.
    color:  Line colour (defaults to the default Matplotlib colour cycle).
    """
    kwargs = {"lw": lw}
    if color is not None:
        kwargs["color"] = color
    ax.plot(V, I, label=label or None, **kwargs)
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("Voltage (V)")
    ax.set_ylabel("Current (mA)")


def plot_vt(
    ax: Axes,
    t: np.ndarray,
    V: np.ndarray,
    label: str = "",
    lw: float = 1.5,
    color: str | None = None,
) -> None:
    """Voltage vs. time.

    Parameters
    ----------
    ax:     Matplotlib Axes.
    t:      Time array in **seconds** (converted to hours internally).
    V:      Voltage array (V).
    label:  Legend label.
    """
    kwargs = {"lw": lw}
    if color is not None:
        kwargs["color"] = color
    ax.plot(t / 3600.0, V, label=label or None, **kwargs)
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Voltage (V)")


def plot_it(
    ax: Axes,
    t: np.ndarray,
    I: np.ndarray,
    label: str = "",
    lw: float = 1.5,
    color: str | None = None,
) -> None:
    """Current vs. time.

    Parameters
    ----------
    ax:     Matplotlib Axes.
    t:      Time array in **seconds** (converted to hours internally).
    I:      Current array (mA).
    label:  Legend label.
    """
    kwargs = {"lw": lw}
    if color is not None:
        kwargs["color"] = color
    ax.plot(t / 3600.0, I, label=label or None, **kwargs)
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Current (mA)")


# ---------------------------------------------------------------------------
# Axes styling
# ---------------------------------------------------------------------------

def style_axes(
    ax: Axes,
    title: str = "",
    legend: bool = True,
    v_lim: tuple[float, float] | None = None,
    fontsize: int = 10,
) -> None:
    """Apply publication-style formatting to *ax*.

    Parameters
    ----------
    ax:       Matplotlib Axes.
    title:    Optional title string.
    legend:   Whether to show the legend.
    v_lim:    ``(v_min, v_max)`` voltage / y-axis limits, or ``None``.
    fontsize: Base font size for tick labels.
    """
    if title:
        ax.set_title(title, fontsize=fontsize + 1)
    if legend and ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, fontsize=fontsize - 1)
    if v_lim is not None:
        ax.set_ylim(v_lim)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="in", labelsize=fontsize - 1)
