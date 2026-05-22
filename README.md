# Biologic-Echem

A lightweight Python toolkit for loading, processing, and visualising electrochemical data exported from **BioLogic EC-Lab** potentiostats.

Supports both `.xlsx` EC-Lab exports and `.mpr` binary files.

---

## Features

- **Auto-detect half-cycles** from current sign — no reliance on EC-Lab's built-in cycle numbers
- **Specific capacity** (mAh g⁻¹) via accurate current integration with real time steps
- **Multi-rate overlay** — compare 1C / 2C / 5C / 10C / 20C on one publication-ready figure
- **Differential capacity** (dQ/dV) with Gaussian smoothing — reveals phase transitions
- **Cyclic voltammetry** (CV) plotting
- **CSV export** of processed data and summary tables
- Works with both `.xlsx` exports and `.mpr` binary files (via `galvani`)

---

## Repo structure

```
Biologic-Echem/
├── biologic_echem/        # Python package
│   ├── loaders.py         # load_xlsx(), load_mpr(), discover_rate_files()
│   ├── processing.py      # segment_halfcycles(), specific_capacity(), dqdv()
│   └── plotting.py        # plot_vq(), plot_dqdv(), plot_cv(), plot_vt()
├── data/                  # Example .xlsx files (LTO rate-test data)
│   ├── 1C.xlsx
│   ├── 2C.xlsx  …
│   └── 1C-fnl.xlsx
├── notebooks/
│   └── demo_rate_test.ipynb   # Full walkthrough notebook
├── archive/               # Original development notebooks (for reference)
├── requirements.txt
└── setup.py
```

---

## Installation

```bash
git clone https://github.com/Lei-Li-888/Biologic-Echem.git
cd Biologic-Echem
pip install -r requirements.txt
```

To read `.mpr` binary files, also install `galvani`:

```bash
pip install galvani
```

---

## Quick start

### Load and plot a single rate-test file

```python
from biologic_echem import (
    load_xlsx, segment_halfcycles, get_cycle,
    specific_capacity, coulombic_efficiency,
    new_figure, plot_vq, style_axes, DEFAULT_DPI,
)

# 1. Load data
df = load_xlsx("data/1C.xlsx")

# 2. Detect half-cycles automatically
halves = segment_halfcycles(df)

# 3. Extract cycle 2 (charge + discharge)
chg, dis = get_cycle(halves, n=2)

# 4. Compute specific capacity
mass_mg = 0.185          # active material mass in mg
Q_chg = specific_capacity(chg, mass_mg)
Q_dis = specific_capacity(dis, mass_mg)

print(f"Q_dis = {Q_dis[-1]:.1f} mAh/g,  CE = {coulombic_efficiency(Q_chg, Q_dis)*100:.1f} %")

# 5. Plot
fig, ax = new_figure()
plot_vq(ax, Q_chg, chg["E"].values, Q_dis, dis["E"].values)
style_axes(ax, title="1C – Cycle 2", v_lim=(1.0, 3.0))
fig.savefig("1C_cycle2.png", dpi=DEFAULT_DPI, bbox_inches="tight")
```

### Multi-rate comparison

```python
from biologic_echem import discover_rate_files, load_xlsx, segment_halfcycles, get_cycle
from biologic_echem import specific_capacity, new_figure, style_axes
import matplotlib.pyplot as plt

mass_mg = 0.185
fig, ax = new_figure(figsize=(7, 5))

for label, fp in discover_rate_files("data/"):
    df = load_xlsx(fp)
    halves = segment_halfcycles(df)
    chg, dis = get_cycle(halves, n=2)
    Q_dis = specific_capacity(dis, mass_mg)
    ax.plot(Q_dis, dis["E"].values, lw=1.5, label=label)

style_axes(ax, title="Rate Performance", v_lim=(1.0, 3.0))
ax.set_xlabel("Specific Capacity (mAh g⁻¹)")
plt.tight_layout()
plt.savefig("rate_comparison.png", dpi=300, bbox_inches="tight")
```

### Differential capacity (dQ/dV)

```python
from biologic_echem import dqdv, new_figure, plot_dqdv, style_axes

Q_chg = specific_capacity(chg, mass_mg)
Q_dis = specific_capacity(dis, mass_mg)

V_c, dQdV_c = dqdv(Q_chg, chg["E"].values)
V_d, dQdV_d = dqdv(Q_dis, dis["E"].values)

fig, ax = new_figure()
plot_dqdv(ax, V_c, dQdV_c, V_d, dQdV_d)
style_axes(ax, title="dQ/dV — 1C Cycle 2", v_lim=(1.0, 3.0))
```

### Load a `.mpr` binary file

```python
from biologic_echem import load_mpr

df = load_mpr("path/to/experiment.mpr")   # requires: pip install galvani
```

---

## Data format

### `.xlsx` exports (default)

EC-Lab exports with this layout are supported out of the box:

| Row | Content |
|-----|---------|
| 0   | File path (skipped automatically) |
| 1   | Column headers |
| 2+  | Numeric data |

Required columns (flexible name matching, case-insensitive):

| Quantity | Example column names |
|----------|---------------------|
| Time     | `time/s`, `Time (s)` |
| Voltage  | `Ewe/V`, `Ewe/V vs. SCE` |
| Current  | `<I>/mA`, `I/mA` |

### `.mpr` binary files

Pass the path directly to `load_mpr()`.  Only `t`, `E`, and `I` are used — EC-Lab's built-in cycle numbers and Q columns are ignored.

---

## API reference

### `biologic_echem.loaders`

| Function | Description |
|----------|-------------|
| `load_xlsx(path, skip_rows=1)` | Load EC-Lab `.xlsx` → DataFrame(t, E, I) |
| `load_mpr(path)` | Load BioLogic `.mpr` binary → DataFrame(t, E, I) |
| `discover_rate_files(folder, extension, selected)` | Auto-scan and sort rate-test files |

### `biologic_echem.processing`

| Function | Description |
|----------|-------------|
| `segment_halfcycles(df, rolling_window=11, min_points=20)` | Split by current sign |
| `get_cycle(halfcycles, n=2)` | Return (charge, discharge) for cycle *n* |
| `specific_capacity(seg, mass_mg)` | Cumulative capacity in mAh g⁻¹ |
| `coulombic_efficiency(Q_chg, Q_dis)` | CE as a fraction |
| `dqdv(Q, V, dv=0.005, sigma=2.0)` | Differential capacity (V_grid, dQdV) |

### `biologic_echem.plotting`

| Function | Description |
|----------|-------------|
| `new_figure(figsize)` | Create `(fig, ax)` with defaults |
| `plot_vq(ax, Q_chg, V_chg, Q_dis, V_dis, label)` | Voltage vs. capacity |
| `plot_dqdv(ax, V_c, dQdV_c, V_d, dQdV_d, label)` | Differential capacity |
| `plot_cv(ax, V, I, label)` | Cyclic voltammetry |
| `plot_vt(ax, t, V, label)` | Voltage vs. time |
| `plot_it(ax, t, I, label)` | Current vs. time |
| `style_axes(ax, title, legend, v_lim)` | Apply publication styling |

---

## Notebook demo

Open [`notebooks/demo_rate_test.ipynb`](notebooks/demo_rate_test.ipynb) for a complete interactive walkthrough using the included example data.

---

## Example data

The `data/` folder contains LTO (Li₄Ti₅O₁₂) rate-test data collected at 1C, 2C, 5C, 10C, and 20C, with a final 1C re-test (`1C-fnl.xlsx`) to confirm capacity retention.

---

## License

MIT
