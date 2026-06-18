# ephys-analysis-scripts

A collection of lightweight Python utilities for electrophysiology data processing, ABF file parsing, and dose–response curve analysis. Developed to support general ion-channel patch–clamp workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
<!-- Replace XXXXXXX with your Zenodo record ID once the DOI is minted -->
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

## Overview

This repository bundles three standalone scripts used in routine patch–clamp analysis:

- **Batch ABF analysis** — read Axon `.abf` files, baseline-correct current traces, extract mean current over user-defined time windows, pull a parallel temperature channel, plot every sweep, and export the results to Excel.
- **Dose–response fitting** — fit the Hill equation to concentration–current data, report `Imax`, `EC50`, and the Hill coefficient, and produce Prism-ready normalized tables.

Each script is self-contained and depends only on the standard scientific Python stack plus [`pyabf`](https://swharden.com/pyabf/). Paths and analysis windows are set at the top of each file (or in the `__main__` block) so they can be adapted to a new dataset without touching the analysis logic.

## Contents

| File | Purpose |
| --- | --- |
| `Github_M5_V1.py` | Batch ABF analysis. Splits results by sweep (sweep 0 → `sheet1`, sweep 1 → `sheet2`). Time windows: Range 1 = 0.03–0.034 s, Range 3 = 0.22–0.23 s. |
| `Github_M5_V2.py` | Batch ABF analysis, one Excel sheet per file (up to 13 sweeps). Time windows: Range 1 = 0.007–0.009 s, Range 3 = 0.1–0.11 s. Gracefully skips temperature when channel 2 is absent. |
| `GIt-hub_HillEq.py` | Hill-equation dose–response fitting from an Excel sheet; normalizes to fitted `Imax` and exports summary + fit-curve tables for GraphPad Prism. |

## Requirements

- Python 3.8+
- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `pyabf` (ABF scripts only)
- `xlsxwriter` (Excel export)

```bash
pip install numpy pandas matplotlib scipy pyabf xlsxwriter
```

## Usage

### ABF batch analysis (`Github_M5_V1.py` / `Github_M5_V2.py`)

Both scripts iterate over a numbered range of ABF files, baseline-correct the current channel (channel 0) against the first 0.1 ms, average the signal over two time windows, and report the difference between them (`Range 3 − Range 1`). The mean of the temperature channel (channel 2) over Range 1 is recorded alongside.

Edit the parameters in the `__main__` block:

```python
start_num = 14
end_num   = 50
exclude_nums = []                 # file numbers to skip
file_path_template = "/Volumes/T7/Data/20251121/2025_11_21_{:04d}.abf"
```

The `{:04d}` placeholder is replaced by each file number (e.g. `..._0014.abf`). Each file produces a per-sweep plot with the two integration windows shaded, and a timestamped workbook is written to the Desktop:

- `Github_M5_V1.py` → `analysis_<timestamp>.xlsx` (sweep 0 and sweep 1 in separate sheets)
- `Github_M5_V2.py` → `analysis_results_TRPM4_<timestamp>.xlsx` (one sheet per file)

Each row contains: `File Name`, `Sweep Number`, `Current Range 1 Mean`, `Current Range 3 Mean`, `Current Difference (R3-R1)`, and `Temp Range 1 Mean`.

> **Channel layout assumed:** channel 0 = current (pA), channel 2 = temperature. Adjust the window bounds and channel indices to match your acquisition protocol.

### Hill-equation dose–response (`GIt-hub_HillEq.py`)

Fits

```
I(x) = Imax / (1 + (EC50 / x)^nH)
```

to concentration–current data read from an Excel file (first column = concentration in µM, remaining columns = current replicates). The script analyzes two sheets — by default a `+100 mV` and a `−100 mV` condition — averages replicates, computes SEM, fits the Hill equation, and normalizes each curve to its fitted `Imax`. For inward currents the sign can be flipped with `invert_sign=True`.

Set the paths at the top of the file:

```python
file_path = '/path/to/input/Book1.xlsx'
out_path  = '/path/to/output/TPPO_normalized_Prism.xlsx'
```

Outputs an Excel workbook with two sheets:

- `summary` — mean current, SEM, normalized current, and normalized SEM for each condition
- `fit_curves` — a smooth log-spaced fitted curve for plotting in Prism

Fitted `Imax`, `EC50`, and `nH` are printed to the console, and a log-scale dose–response plot is shown for a quick visual check.

## Citation

If you use these scripts in your work, please cite the archived release:

> Lee, J. (2026). *ephys-analysis-scripts* (v1.0.1). Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

## License

Released under the [MIT License](LICENSE).
