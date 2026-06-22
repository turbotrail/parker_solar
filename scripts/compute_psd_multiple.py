# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "cdflib",
#     "matplotlib",
#     "numpy",
#     "pandas",
#     "scipy"
# ]
# ///

import os
import glob
import cdflib
from cdflib.epochs import CDFepoch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import welch

data_dir = r"c:\Users\Jeyaprakash S\Documents\GitHub\parker_solar\data"
cdf_files = sorted(glob.glob(os.path.join(data_dir, "*20241224*.cdf")))

all_times = []
all_b_rtn = []

print("Loading data for full day 2024-12-24...")
for file in cdf_files:
    try:
        cdf = cdflib.CDF(file)
        epoch = cdf.varget("epoch_mag_RTN")
        b_rtn = cdf.varget("psp_fld_l2_mag_RTN")
        times = CDFepoch.to_datetime(epoch)
        all_times.append(times)
        all_b_rtn.append(b_rtn)
        print(f"Loaded {os.path.basename(file)}")
    except Exception as e:
        print(f"Error reading {file}: {e}")

if not all_times:
    print("No data loaded. Check data_dir and files.")
    exit(1)

times_arr = np.concatenate(all_times)
b_rtn_arr = np.concatenate(all_b_rtn)

df = pd.DataFrame(b_rtn_arr, columns=['BR', 'BT', 'BN'], index=times_arr)

intervals = [
    ("2024-12-24 10:00:00", "2024-12-24 10:20:00", "10:00"),
    ("2024-12-24 11:50:00", "2024-12-24 12:10:00", "11:50"),
    ("2024-12-24 14:00:00", "2024-12-24 14:20:00", "14:00 (Quiet)"),
    ("2024-12-24 16:30:00", "2024-12-24 16:50:00", "16:30"),
    ("2024-12-24 16:35:00", "2024-12-24 16:45:00", "16:35 (Switchback)"),
    ("2024-12-24 20:00:00", "2024-12-24 20:20:00", "20:00")
]

fs = 293
results = []
psd_data = {}

print("\nProcessing intervals...")
for start, end, label in intervals:
    df_sub = df.loc[start:end].copy()
    if len(df_sub) == 0:
        continue
        
    df_sub['BR_fluc'] = df_sub['BR'] - df_sub['BR'].rolling(10000).mean()
    df_sub['BT_fluc'] = df_sub['BT'] - df_sub['BT'].rolling(10000).mean()
    df_sub['BN_fluc'] = df_sub['BN'] - df_sub['BN'].rolling(10000).mean()
    df_sub.dropna(inplace=True)
    
    slopes = {}
    psds = {}
    for comp in ['BR', 'BT', 'BN']:
        f, Pxx = welch(
            df_sub[f'{comp}_fluc'].to_numpy(),
            fs=fs,
            nperseg=65536
        )
        mask = (f > 0.01) & (f < 10)
        slope, _ = np.polyfit(np.log10(f[mask]), np.log10(Pxx[mask]), 1)
        slopes[comp] = slope
        psds[comp] = (f, Pxx)
        
    results.append({
        'Time': label,
        'BR': slopes['BR'],
        'BT': slopes['BT'],
        'BN': slopes['BN']
    })
    psd_data[label] = psds

print("\n--- PSD Slopes Summary ---")
print(f"{'Time':<20} | {'BR':<8} | {'BT':<8} | {'BN':<8}")
print("-" * 50)
for r in results:
    print(f"{r['Time']:<20} | {r['BR']:>6.2f}   | {r['BT']:>6.2f}   | {r['BN']:>6.2f}")

# Plot comparison between Quiet (14:00) and Switchback (16:35)
quiet_label = "14:00 (Quiet)"
sb_label = "16:35 (Switchback)"

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
components = ['BR', 'BT', 'BN']

for i, comp in enumerate(components):
    ax = axes[i]
    
    if quiet_label in psd_data:
        fq, Pxx_q = psd_data[quiet_label][comp]
        sq = next(r[comp] for r in results if r['Time'] == quiet_label)
        ax.loglog(fq, Pxx_q, label=f'Quiet (slope={sq:.2f})', color='tab:blue', alpha=0.8)
        
    if sb_label in psd_data:
        fsb, Pxx_sb = psd_data[sb_label][comp]
        ssb = next(r[comp] for r in results if r['Time'] == sb_label)
        # Offset switchback PSD slightly for visual clarity if needed, but plotting directly is better for absolute power comp
        ax.loglog(fsb, Pxx_sb, label=f'Switchback (slope={ssb:.2f})', color='tab:red', alpha=0.8)

    # Reference -5/3 line
    mask = (fq > 0.01) & (fq < 10)
    fq_mask = fq[mask]
    ref_slope = -5/3
    mid_idx = len(fq_mask) // 2
    # Align roughly with quiet data
    ref_intercept = np.log10(Pxx_q[mask][mid_idx]) - ref_slope * np.log10(fq_mask[mid_idx])
    ref_line = 10**(ref_intercept + ref_slope * np.log10(fq_mask))
    ax.loglog(fq_mask, ref_line, 'k:', linewidth=2, label='-5/3 (Kolmogorov)')
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel(f'PSD {comp} ($nT^2/Hz$)')
    ax.set_title(f'{comp} PSD Comparison')
    ax.legend()
    ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.set_xlim([1e-3, fs/2])

plt.suptitle('PSD Comparison: Quiet vs Switchback-Rich Intervals\n2024-12-24', fontsize=16)
plt.tight_layout()
plt.savefig('psd_comparison.png', dpi=300)
print("\nSaved psd_comparison.png")
