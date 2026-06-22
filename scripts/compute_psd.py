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

# Convert to pandas DataFrame with datetime index for easier filtering
df = pd.DataFrame(b_rtn_arr, columns=['BR', 'BT', 'BN'], index=times_arr)

# Filter time range: 11:50–12:10 UTC
start_time = "2024-12-24 11:50:00"
end_time = "2024-12-24 12:10:00"
print(f"Filtering data between {start_time} and {end_time}...")
df_sub = df.loc[start_time:end_time].copy()

print(f"Filtered data points: {len(df_sub)}")

if len(df_sub) == 0:
    print("No data found in the specified time range.")
    exit(1)

# Remove local background using rolling mean (as specified: window=10000)
print("Removing rolling mean background (window=10000)...")
df_sub['BR_fluc'] = df_sub['BR'] - df_sub['BR'].rolling(10000).mean()
df_sub['BT_fluc'] = df_sub['BT'] - df_sub['BT'].rolling(10000).mean()
df_sub['BN_fluc'] = df_sub['BN'] - df_sub['BN'].rolling(10000).mean()

# Drop NaNs resulting from rolling window
df_sub.dropna(inplace=True)

fs = 293

# Calculate Welch PSD
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
components = ['BR', 'BT', 'BN']
colors = ['r', 'g', 'b']

for i, comp in enumerate(components):
    f, Pxx = welch(
        df_sub[f'{comp}_fluc'].to_numpy(),
        fs=fs,
        nperseg=65536
    )
    
    # Fit for frequencies between 0.01 and 10 Hz
    mask = (f > 0.01) & (f < 10)
    f_mask = f[mask]
    Pxx_mask = Pxx[mask]
    
    slope, intercept = np.polyfit(
        np.log10(f_mask),
        np.log10(Pxx_mask),
        1
    )
    
    print(f"PSD slope for {comp} = {slope:.2f}")
    
    ax = axes[i]
    ax.loglog(f, Pxx, label=f'PSD {comp}', color=colors[i])
    
    # Plot the fit
    fit_line = 10**(intercept + slope * np.log10(f_mask))
    ax.loglog(f_mask, fit_line, 'k--', linewidth=2, label=f'Fit slope = {slope:.2f}')
    
    # Add -5/3 line for comparison (Kolmogorov)
    ref_slope = -5/3
    mid_idx = len(f_mask) // 2
    # Anchor the reference line to the midpoint of the fit
    ref_intercept = np.log10(Pxx_mask[mid_idx]) - ref_slope * np.log10(f_mask[mid_idx])
    ref_line = 10**(ref_intercept + ref_slope * np.log10(f_mask))
    ax.loglog(f_mask, ref_line, 'gray', linestyle=':', linewidth=2, label='-5/3 (Kolmogorov)')
    
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel(f'PSD {comp} ($nT^2/Hz$)')
    ax.set_title(f'{comp} Fluctuation PSD\nSlope = {slope:.2f}')
    ax.legend()
    ax.grid(True, which='both', ls='--', alpha=0.5)
    ax.set_xlim([1e-3, fs/2])

plt.suptitle('Power Spectral Density (PSD) of PSP Magnetic Fluctuations\n2024-12-24 11:50 - 12:10 UTC', fontsize=16)
plt.tight_layout()
plt.savefig('psd_analysis.png', dpi=300)
print("Saved psd_analysis.png")
