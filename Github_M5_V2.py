import pyabf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os


def analyze_and_plot_abf_files(start_num, end_num, exclude_nums, file_path_template, excel_path):
    """
    Analyze ABF files and write one sheet per file into a single Excel workbook.
    For each sweep:
      - Current (ch 0): baseline-corrected mean in Range1 and Range3
      - Temp (ch 2): mean in Range1 only
    """
    file_nums = [num for num in range(start_num, end_num + 1) if num not in exclude_nums]
    abf_file_paths = [file_path_template.format(num) for num in file_nums]

    with pd.ExcelWriter(excel_path, engine="xlsxwriter") as writer:
        for abf_file_path in abf_file_paths:
            if not os.path.exists(abf_file_path):
                continue

            abf = pyabf.ABF(abf_file_path)
            file_name = os.path.basename(abf_file_path).replace(".abf", "")

            all_sweeps_results = []

            plt.figure(figsize=(12, 8))

            # analyze up to 13 sweeps (or fewer if file has less)
            for sweepNumber in range(min(13, abf.sweepCount)):
                current_results = analyze_current_for_sweep(abf, sweepNumber)
                temp_results = analyze_temp_for_sweep(abf, sweepNumber)

                merged_dict = {
                    "File Name": file_name,
                    "Sweep Number": sweepNumber,

                    # Current
                    "Current Range 1 Mean": current_results["range1_mean"],
                    "Current Range 3 Mean": current_results["range3_mean"],
                    "Current Difference (R3-R1)": current_results["range3_mean"] - current_results["range1_mean"],

                    # Temp
                    "Temp Range 1 Mean": temp_results["temp_range1_mean"],
                }
                all_sweeps_results.append(merged_dict)

                # Plot baseline-corrected current trace
                plt.plot(current_results["x"], current_results["y_baseline_corrected"],
                         label=f"Sweep {sweepNumber}")

            # Highlight regions: Range1 (0.007–0.009), Range3 (0.1–0.11)
            highlight_regions = [
                (0.007, 0.009, "red"),   # Range 1
                (0.1,   0.11, "blue"),   # Range 3
            ]
            for start, end, color in highlight_regions:
                plt.axvspan(start, end, color=color, alpha=0.05)

            plt.title(f"All Sweeps (Current) in {file_name}")
            plt.ylabel("Current (pA)")
            plt.xlabel("Time (s)")
            plt.legend()
            plt.tight_layout()
            plt.show()
            plt.close()

            # One sheet per file (use last token of file_name)
            df = pd.DataFrame(all_sweeps_results)
            sheet_name = f"Sheet_{file_name.split('_')[-1]}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def analyze_current_for_sweep(abf, sweepNumber):
    """
    Current analysis (channel 0):
      - Baseline: 0–0.0001 s
      - Range 1: 0.007–0.009 s
      - Range 3: 0.1–0.11 s
    """
    abf.setSweep(sweepNumber, channel=0)
    x = abf.sweepX
    y = abf.sweepY

    # Baseline
    baseline_idx = (x >= 0) & (x <= 0.0001)
    baseline = np.mean(y[baseline_idx])

    # Range 1
    r1_idx = (x >= 0.007) & (x <= 0.009)
    range1_mean = np.mean(y[r1_idx] - baseline)

    # Range 3
    r3_idx = (x >= 0.1) & (x <= 0.11)
    range3_mean = np.mean(y[r3_idx] - baseline)

    return {
        "x": x,
        "y_baseline_corrected": y - baseline,
        "range1_mean": range1_mean,
        "range3_mean": range3_mean,
    }


def analyze_temp_for_sweep(abf, sweepNumber):
    """
    Temperature analysis (channel 2):
      - Temp Range 1 Mean: 0.007–0.009 s (no baseline correction)
    If channel 2 does not exist, returns NaN.
    """
    if abf.channelCount < 3:
        print(f"Warning: Channel 2 not available in {abf.abfFilePath}, skipping temperature analysis.")
        return {"temp_range1_mean": np.nan}

    abf.setSweep(sweepNumber, channel=2)
    x = abf.sweepX
    y = abf.sweepY

    idx = (x >= 0.007) & (x <= 0.009)
    temp_range1_mean = np.mean(y[idx])

    return {"temp_range1_mean": temp_range1_mean}


if __name__ == "__main__":
    from datetime import datetime

    start_num = 14
    end_num = 50
    exclude_nums = []
    file_path_template = "/Volumes/T7/Data/20251121/2025_11_21_{:04d}.abf"
    # file_path_template = "/Volumes/T7/Data/TRPM4/20250422/2025_04_22_{:04d}.abf"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"analysis_results_TRPM4_{timestamp}.xlsx"
    excel_path = os.path.join(os.path.expanduser("~/Desktop"), excel_filename)

    analyze_and_plot_abf_files(start_num, end_num, exclude_nums, file_path_template, excel_path)
