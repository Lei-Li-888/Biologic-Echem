"""
biologic_echem
==============
A lightweight toolkit for loading, processing, and visualising
electrochemical data from BioLogic potentiostats.

Typical workflow
----------------
>>> from biologic_echem import load_xlsx, segment_halfcycles, get_cycle
>>> from biologic_echem import specific_capacity, dqdv
>>> from biologic_echem import new_figure, plot_vq, style_axes

>>> df = load_xlsx("data/1C.xlsx")
>>> halves = segment_halfcycles(df)
>>> chg, dis = get_cycle(halves, n=2)
>>> Q_chg = specific_capacity(chg, mass_mg=2.5)
>>> Q_dis = specific_capacity(dis, mass_mg=2.5)

>>> fig, ax = new_figure()
>>> plot_vq(ax, Q_chg, chg["E"].values, Q_dis, dis["E"].values, label="1C")
>>> style_axes(ax, title="Rate Test – Cycle 2", v_lim=(1.0, 3.0))
>>> fig.savefig("1C_rate.png", dpi=300, bbox_inches="tight")
"""

from .loaders import load_mpr, load_xlsx, discover_rate_files
from .processing import (
    segment_halfcycles,
    get_cycle,
    specific_capacity,
    coulombic_efficiency,
    dqdv,
)
from .plotting import (
    new_figure,
    plot_vq,
    plot_dqdv,
    plot_cv,
    plot_vt,
    plot_it,
    style_axes,
    CHARGE_COLOR,
    DISCHARGE_COLOR,
    DEFAULT_DPI,
    DEFAULT_FIGSIZE,
)

__all__ = [
    # loaders
    "load_mpr",
    "load_xlsx",
    "discover_rate_files",
    # processing
    "segment_halfcycles",
    "get_cycle",
    "specific_capacity",
    "coulombic_efficiency",
    "dqdv",
    # plotting
    "new_figure",
    "plot_vq",
    "plot_dqdv",
    "plot_cv",
    "plot_vt",
    "plot_it",
    "style_axes",
    "CHARGE_COLOR",
    "DISCHARGE_COLOR",
    "DEFAULT_DPI",
    "DEFAULT_FIGSIZE",
]

__version__ = "0.1.0"
