import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# ===== Change these paths to match your system =====
file_path = '/path/to/input/Book1.xlsx'                 # raw data
out_path  = '/path/to/output/TPPO_normalized_Prism.xlsx'  # output Excel

# -------- Hill function definition --------
def hill_eq(x, Imax, EC50, nH):
    # I(x) = Imax / (1 + (EC50/x)^nH)
    return Imax / (1.0 + (EC50 / x)**nH)


def analyze_sheet(sheet_idx, invert_sign=False, label=''):
    """
    For one sheet:
    - Read concentration and current values
    - Compute mean and SEM
    - Optionally invert current sign (for inward currents)
    - Fit Hill equation
    - Normalize by fitted Imax
    """
    df = pd.read_excel(file_path, sheet_name=sheet_idx, header=None)

    # First column: concentration; remaining columns: current values
    conc = df.iloc[:, 0].to_numpy(dtype=float)
    currents = df.iloc[:, 1:].to_numpy(dtype=float)

    # For inward currents (negative), flip the sign if requested
    if invert_sign:
        currents = -currents

    # Sort by concentration, just in case
    order = np.argsort(conc)
    conc = conc[order]
    currents = currents[order, :]

    # Mean / SEM across replicates
    mean_I = np.nanmean(currents, axis=1)
    n_per_conc = np.sum(~np.isnan(currents), axis=1)
    sd_I = np.nanstd(currents, axis=1, ddof=1)
    sem_I = sd_I / np.sqrt(n_per_conc)

    # Initial guess for Hill fit
    Imax0 = np.max(mean_I)
    half = Imax0 / 2
    EC50_0 = conc[np.argmin(np.abs(mean_I - half))]
    nH0 = 1.0
    p0 = [Imax0, EC50_0, nH0]
    bounds = ([0, 0, 0], [np.inf, np.inf, 5])

    # Curve fitting
    popt, pcov = curve_fit(hill_eq, conc, mean_I, p0=p0, bounds=bounds)
    Imax_fit, EC50_fit, nH_fit = popt

    print(f"\n=== {label} ===")
    print(f"Imax_fit = {Imax_fit:.3f}")
    print(f"EC50_fit = {EC50_fit:.3g} µM")
    print(f"Hill nH  = {nH_fit:.3f}")

    # Normalize by fitted Imax
    I_norm = mean_I / Imax_fit
    sem_norm = sem_I / Imax_fit

    # Smooth normalized fit curve
    x_smooth = np.logspace(np.log10(conc.min()), np.log10(conc.max()), 200)
    fit_norm = hill_eq(x_smooth, *popt) / Imax_fit

    # Return everything needed for summary and plotting/Prism
    return {
        'conc': conc,
        'mean_I': mean_I,
        'sem_I': sem_I,
        'I_norm': I_norm,
        'sem_norm': sem_norm,
        'x_smooth': x_smooth,
        'fit_norm': fit_norm,
        'params': (Imax_fit, EC50_fit, nH_fit),
    }


# -------- Analyze two sheets (+100 mV / -100 mV) --------
res_p = analyze_sheet(sheet_idx=0, invert_sign=False, label='+100 mV')
res_n = analyze_sheet(sheet_idx=1, invert_sign=True,  label='-100 mV')

# -------- 1) Summary table for Prism --------
# Assumes the same concentration set for both conditions
df_summary = pd.DataFrame({
    'Conc_uM'         : res_p['conc'],
    'I_mean_+100mV'   : res_p['mean_I'],
    'SEM_+100mV'      : res_p['sem_I'],
    'I_norm_+100mV'   : res_p['I_norm'],
    'SEM_norm_+100mV' : res_p['sem_norm'],
    'I_mean_-100mV'   : res_n['mean_I'],
    'SEM_-100mV'      : res_n['sem_I'],
    'I_norm_-100mV'   : res_n['I_norm'],
    'SEM_norm_-100mV' : res_n['sem_norm'],
})

# -------- 2) Fit-curve table (optional: for plotting the fitted curves in Prism) --------
df_fit = pd.DataFrame({
    'x_smooth_uM'      : res_p['x_smooth'],
    'fit_norm_+100mV'  : res_p['fit_norm'],
    'fit_norm_-100mV'  : res_n['fit_norm'],
})

# -------- 3) Save to Excel --------
with pd.ExcelWriter(out_path) as writer:
    df_summary.to_excel(writer, sheet_name='summary', index=False)
    df_fit.to_excel(writer, sheet_name='fit_curves', index=False)

print(f"\nExcel file saved to: {out_path}")

# (Optional) Plot to visually check the dose–response and fits
fig, ax = plt.subplots()

ax.errorbar(
    res_p['conc'], res_p['I_norm'], yerr=res_p['sem_norm'],
    fmt='o', capsize=3, label='+100 mV'
)
ax.plot(res_p['x_smooth'], res_p['fit_norm'], '-')

ax.errorbar(
    res_n['conc'], res_n['I_norm'], yerr=res_n['sem_norm'],
    fmt='s', capsize=3, label='-100 mV'
)
ax.plot(res_n['x_smooth'], res_n['fit_norm'], '--')

ax.set_xscale('log')
ax.set_xlabel('TPPO (µM)')
ax.set_ylabel('Normalized current (I / Imax_fit)')
ax.set_ylim(0, 1.2)
ax.legend()
ax.set_title('TPPO dose–response @ 37 °C, 100 nM Ca²⁺')

plt.tight_layout()
plt.show()
