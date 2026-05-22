"""
Data loaders for BioLogic potentiostat files.

Supports:
  - .mpr  binary files via galvani
  - .xlsx exports from EC-Lab software

All loaders return a DataFrame with three standardized columns:
  t  (float)  time in seconds
  E  (float)  working-electrode voltage in V
  I  (float)  current in mA
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(col: str) -> str:
    return str(col).strip().lower()


def _find_col(df: pd.DataFrame, patterns: list[str]) -> str | None:
    """Return the first column whose lowercase name contains any pattern."""
    for col in df.columns:
        norm = _normalize(col)
        for pat in patterns:
            if pat in norm:
                return col
    return None


def _extract_tei(df: pd.DataFrame) -> pd.DataFrame:
    """Pick t/E/I columns by name pattern and return a clean 3-column DataFrame."""
    t_col = _find_col(df, ["time/s", "time (s)", "test time", "time"])
    e_col = _find_col(df, ["ewe/v", "voltage", "ecell", "potential"])
    i_col = _find_col(df, ["<i>/ma", "i/ma", "current", "control/ma"])

    missing = [
        name
        for name, col in [("time", t_col), ("voltage", e_col), ("current", i_col)]
        if col is None
    ]
    if missing:
        raise ValueError(
            f"Could not find columns for: {', '.join(missing)}.\n"
            f"Available columns: {list(df.columns)}"
        )

    out = pd.DataFrame(
        {
            "t": pd.to_numeric(df[t_col], errors="coerce"),
            "E": pd.to_numeric(df[e_col], errors="coerce"),
            "I": pd.to_numeric(df[i_col], errors="coerce"),
        }
    )
    return (
        out.replace([np.inf, -np.inf], np.nan)
        .dropna()
        .sort_values("t")
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Public loaders
# ---------------------------------------------------------------------------

def load_mpr(path: str | Path) -> pd.DataFrame:
    """Load a BioLogic .mpr binary file.

    Requires the ``galvani`` package (``pip install galvani``).

    Parameters
    ----------
    path:
        Path to the .mpr file.

    Returns
    -------
    DataFrame with columns ``t`` (s), ``E`` (V), ``I`` (mA).
    """
    try:
        from galvani import BioLogic
    except ImportError as exc:
        raise ImportError(
            "galvani is required to read .mpr files.\n"
            "Install it with:  pip install galvani"
        ) from exc

    raw = pd.DataFrame(BioLogic.MPRfile(str(path)).data)
    return _extract_tei(raw)


def load_xlsx(path: str | Path, skip_rows: int = 1) -> pd.DataFrame:
    """Load a BioLogic EC-Lab .xlsx export.

    EC-Lab places the file path on row 0 before the column headers, so
    ``skip_rows=1`` is the default.  Adjust if your export is different.

    Parameters
    ----------
    path:
        Path to the .xlsx file.
    skip_rows:
        Number of rows to skip before the header row (default 1).

    Returns
    -------
    DataFrame with columns ``t`` (s), ``E`` (V), ``I`` (mA).
    """
    df = pd.read_excel(path, skiprows=skip_rows, header=0)
    df.columns = [str(c).strip() for c in df.columns]
    return _extract_tei(df)


# ---------------------------------------------------------------------------
# File discovery helpers
# ---------------------------------------------------------------------------

import re


def discover_rate_files(
    folder: str | Path,
    extension: str = "*.xlsx",
    selected: list[str] | None = None,
) -> list[tuple[str, Path]]:
    """Scan *folder* and return rate-test files sorted by C-rate.

    Files are identified by the pattern ``<number>c`` in the stem (case-
    insensitive).  A ``-f`` suffix marks the final re-test at 1C.

    Parameters
    ----------
    folder:
        Directory to search.
    extension:
        Glob pattern for file extension (default ``*.xlsx``).
    selected:
        If given, only return files whose auto-detected label is in this list,
        e.g. ``["1C", "5C", "10C"]``.

    Returns
    -------
    List of ``(label, path)`` tuples, sorted from lowest to highest C-rate
    with the ``-final`` file appended last.
    """
    folder = Path(folder)
    regular: list[tuple[float, str, Path]] = []
    final: list[tuple[str, Path]] = []

    for fp in folder.glob(extension):
        stem = fp.stem.lower().strip()
        if re.fullmatch(r"\d+(\.\d+)?c-f(nl)?", stem):
            m = re.match(r"(\d+(\.\d+)?)c", stem)
            label = (m.group(1) if m else stem) + "C-final"
            final.append((label, fp))
        elif re.fullmatch(r"\d+(\.\d+)?c", stem):
            num = float(re.match(r"(\d+(\.\d+)?)c", stem).group(1))
            label = (str(int(num)) if num == int(num) else str(num)) + "C"
            regular.append((num, label, fp))

    regular.sort(key=lambda x: x[0])
    result: list[tuple[str, Path]] = [(lbl, fp) for _, lbl, fp in regular] + final

    if selected is not None:
        result = [(lbl, fp) for lbl, fp in result if lbl in selected]

    return result
