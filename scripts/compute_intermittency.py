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
from scipy.stats import kurtosis

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
    except Exception as e:
        print(f"Error reading {file}: {e}")

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

print("\n--- Kurtosis of dBR ---")
print(f"{'Time Window':<20} | {'Kurtosis (Fisher=False)'}")
print("-" * 45)

for start, end, label in intervals:
    df_sub = df.loc[start:end]
    if len(df_sub) < 2: continue
    
    br_vals = df_sub['BR'].values
    dBR = br_vals[1:] - br_vals[:-1]
    
    k = kurtosis(dBR, fisher=False)
    print(f"{label:<20} | {k:>8.2f}")


# ----------------------------------------------------
# Structure Function Analysis (Quiet vs Switchback)
# ----------------------------------------------------
print("\nComputing Structure Functions for Quiet vs Switchback intervals...")

quiet_int = ("2024-12-24 14:00:00", "2024-12-24 14:20:00", "14:00 (Quiet)")
sb_int = ("2024-12-24 16:35:00", "2024-12-24 16:45:00", "16:35 (Switchback)")

# tau values in points (cadence ~ 293 Hz)
# Let's use tau from roughly 0.1s to 10s (approx 30 points to 3000 points)
taus = np.logspace(np.log10(30), np.log10(3000), 15).astype(int)
taus = np.unique(taus)
p_vals = [1, 2, 3, 4, 5, 6]

results_sf = {}

for start, end, label in [quiet_int, sb_int]:
    df_sub = df.loc[start:end]
    br_vals = df_sub['BR'].values
    
    sf_matrix = np.zeros((len(p_vals), len(taus)))
    
    for i, tau in enumerate(taus):
        # Calculate increment delta B(tau)
        delta_B = np.abs(br_vals[tau:] - br_vals[:-tau])
        
        for j, p in enumerate(p_vals):
            sf_matrix[j, i] = np.nanmean(delta_B ** p)
            
    # Fit slopes (zeta_p)
    zeta_p = []
    # Fit over the whole range of tau selected (assuming it's in the inertial range)
    for j, p in enumerate(p_vals):
        log_tau = np.log10(taus)
        log_sf = np.log10(sf_matrix[j, :])
        slope, intercept = np.polyfit(log_tau, log_sf, 1)
        zeta_p.append(slope)
        
    results_sf[label] = {
        'zeta': zeta_p,
        'sf': sf_matrix
    }

# Plot Zeta_p vs p
fig, ax = plt.subplots(figsize=(8, 6))

q_label = quiet_int[2]
sb_label = sb_int[2]

ax.plot(p_vals, results_sf[q_label]['zeta'], 'o-', color='tab:blue', label=q_label)
ax.plot(p_vals, results_sf[sb_label]['zeta'], 's-', color='tab:red', label=sb_label)

# Kolmogorov scaling: zeta_p = p/3
kolmogorov = [p/3 for p in p_vals]
ax.plot(p_vals, kolmogorov, 'k--', label='Kolmogorov (p/3)')

ax.set_xlabel('Order p')
ax.set_ylabel(r'$\zeta_p$')
ax.set_title(r'Structure Function Scaling Exponents $\zeta_p$ vs $p$')
ax.legend()
ax.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('intermittency_comparison.png', dpi=300)
print("Saved intermittency_comparison.png")
