import os
import pyabf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def analyze_and_plot_abf_files(start_num, end_num, exclude_nums, file_path_template):
    """
    Analyze ABF files:
    - Current (channel 0): baseline correction + mean in Range1 and Range3
    - Temperature (channel 2): mean in Range1 only
    - Plot baseline-corrected current traces
    - Save sweep0 and sweep1 results into Excel
    """
    file_nums = [n for n in range(start_num, end_num + 1) if n not in exclude_nums]
    results = []

    for num in file_nums:
        abf_path = file_path_template.format(num)
        if not os.path.exists(abf_path):
            continue

        abf = pyabf.ABF(abf_path)
        file_name = os.path.basename(abf_path).replace(".abf", "")

        plt.figure(figsize=(12, 8))

        for sweep in range(abf.sweepCount):
            cur = analyze_current(abf, sweep)
            tmp = analyze_temp(abf, sweep)

            results.append({
                "File Name": file_name,
                "Sweep Number": sweep,

                # Current
                "Current Range 1 Mean": cur["range1"],
                "Current Range 3 Mean": cur["range3"],
                "Current Difference (R3-R1)": cur["range3"] - cur["range1"],

                # Temp
                "Temp Range 1 Mean": tmp["temp_range1"],
            })

            plt.plot(cur["x"], cur["y_bc"], label=f"Sweep {sweep}")

        # Highlight ranges
        highlight = [
            (0.03, 0.034, 'red'),   # Range 1
            (0.22, 0.23, 'blue')    # Range 3
        ]
        for start, end, color in highlight:
            plt.axvspan(start, end, color=color, alpha=0.05)

        plt.title(f"All Sweeps (Current) – {file_name}")
        plt.xlabel("Time (s)")
        plt.ylabel("Current (pA)")
        plt.legend()
        plt.tight_layout()
        plt.show()
        plt.close()

    save_to_excel(results)


def analyze_current(abf, sweep):
    """
    Current analysis:
    - Baseline: 0–0.0001 s
    - Range 1: 0.03–0.034 s
    - Range 3: 0.22–0.23 s
    """
    abf.setSweep(sweep, channel=0)
    x = abf.sweepX
    y = abf.sweepY

    baseline_idx = (x >= 0) & (x <= 0.0001)
    baseline = np.mean(y[baseline_idx])

    r1_idx = (x >= 0.03) & (x <= 0.034)
    r3_idx = (x >= 0.22) & (x <= 0.23)

    r1 = np.mean(y[r1_idx] - baseline)
    r3 = np.mean(y[r3_idx] - baseline)

    return {
        "x": x,
        "y_bc": y - baseline,
        "range1": r1,
        "range3": r3,
    }


def analyze_temp(abf, sweep):
    """
    Temperature analysis:
    - Range 1 only (0.03–0.034 s)
    """
    abf.setSweep(sweep, channel=2)
    x = abf.sweepX
    y = abf.sweepY

    idx = (x >= 0.03) & (x <= 0.034)
    return {"temp_range1": np.mean(y[idx])}


def save_to_excel(results):
    """
    Save results:
    - Sweep 0 → sheet1
    - Sweep 1 → sheet2
    """
    from datetime import datetime
    df = pd.DataFrame(results)

    df0 = df[df["Sweep Number"] == 0].copy()
    df1 = df[df["Sweep Number"] == 1].copy()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.expanduser(f"~/Desktop/analysis_{timestamp}.xlsx")

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        df0.to_excel(writer, sheet_name="sheet1", index=False)
        df1.to_excel(writer, sheet_name="sheet2", index=False)

    print(f"Saved to: {excel_path}")


if __name__ == "__main__":
    start_num = 0
    end_num = 10
    exclude_nums = []
    file_path_template = "/Volumes/T7/Data/20251112/2025_11_12_{:04d}.abf"

    analyze_and_plot_abf_files(start_num, end_num, exclude_nums, file_path_template)
