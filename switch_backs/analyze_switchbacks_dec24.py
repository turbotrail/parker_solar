# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "cdflib",
#     "matplotlib",
#     "numpy",
#     "pandas"
# ]
# ///

import os
import cdflib
from cdflib.epochs import CDFepoch
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

data_dir = r"c:\Users\Jeyaprakash S\Documents\GitHub\parker_solar\data"
target_files = [
    "psp_fld_l2_mag_rtn_2024122406_v02.cdf",
    "psp_fld_l2_mag_rtn_2024122412_v02.cdf"
]
cdf_files = [os.path.join(data_dir, f) for f in target_files]

all_times = []
all_b_rtn = []

print("Loading data...")
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

times_arr = np.concatenate(all_times)
b_rtn_arr = np.concatenate(all_b_rtn)

# Filter for the broadest range first to save memory: 11:50 to 12:10 UTC
start_time = np.datetime64('2024-12-24T11:50:00')
end_time = np.datetime64('2024-12-24T12:10:00')
mask = (times_arr >= start_time) & (times_arr <= end_time)

times = times_arr[mask]
BR = b_rtn_arr[mask, 0]
BT = b_rtn_arr[mask, 1]
BN = b_rtn_arr[mask, 2]

print(f"Extracted {len(times)} points for 11:50-12:10 analysis.")

# Compute Bmag and theta
Bmag = np.sqrt(BR**2 + BT**2 + BN**2)

with np.errstate(invalid='ignore', divide='ignore'):
    cos_theta = BR / Bmag
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.degrees(np.arccos(cos_theta))

def detect_intervals(t_arr, th_arr, br_arr, threshold):
    is_above = th_arr > threshold
    diff = np.diff(is_above.astype(int))
    starts = np.where(diff == 1)[0] + 1
    ends = np.where(diff == -1)[0] + 1
    
    if is_above[0]:
        starts = np.insert(starts, 0, 0)
    if is_above[-1]:
        ends = np.append(ends, len(is_above))
        
    intervals = []
    # baseline BR before interval (using mean of entire period as reference)
    br_mean = np.nanmean(br_arr)
    
    for s, e in zip(starts, ends):
        t_start = pd.to_datetime(t_arr[s])
        t_end = pd.to_datetime(t_arr[e-1])
        duration = (t_end - t_start).total_seconds()
        
        # skip micro noise (less than 0.05 seconds)
        if duration < 0.05:
            continue
            
        max_th = np.nanmax(th_arr[s:e])
        min_br = np.nanmin(br_arr[s:e])
        br_excursion = min_br - br_mean
        
        intervals.append({
            'start_time': t_start,
            'end_time': t_end,
            'duration_sec': duration,
            'max_theta': max_th,
            'br_excursion_nT': br_excursion
        })
    return intervals

print("\n--- Candidate Switchbacks (Theta > 120) ---")
intervals_120 = detect_intervals(times, theta, BR, 120)
for i, inv in enumerate(intervals_120):
    print(f"[{i+1}] Start: {inv['start_time'].strftime('%H:%M:%S.%f')[:-3]} | End: {inv['end_time'].strftime('%H:%M:%S.%f')[:-3]} | Dur: {inv['duration_sec']:.3f}s | Max Theta: {inv['max_theta']:.1f}° | BR Excursion: {inv['br_excursion_nT']:.1f} nT")

print("\n--- Candidate Switchbacks (Theta > 140) ---")
intervals_140 = detect_intervals(times, theta, BR, 140)
for i, inv in enumerate(intervals_140):
    print(f"[{i+1}] Start: {inv['start_time'].strftime('%H:%M:%S.%f')[:-3]} | End: {inv['end_time'].strftime('%H:%M:%S.%f')[:-3]} | Dur: {inv['duration_sec']:.3f}s | Max Theta: {inv['max_theta']:.1f}° | BR Excursion: {inv['br_excursion_nT']:.1f} nT")

# Plotting Function
def plot_interval(t_arr, br_arr, bt_arr, bn_arr, bmag_arr, th_arr, start_str, end_str, label):
    s = np.datetime64(start_str)
    e = np.datetime64(end_str)
    m = (t_arr >= s) & (t_arr <= e)
    
    t = t_arr[m]
    br = br_arr[m]
    bt = bt_arr[m]
    bn = bn_arr[m]
    b = bmag_arr[m]
    th = th_arr[m]
    
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"Parker Solar Probe - High Res Switchback Analysis ({label})", fontsize=16)
    
    axes[0].plot(t, br, 'tab:red', linewidth=0.5)
    axes[0].set_ylabel('$B_R$ (nT)')
    axes[0].grid(True)
    
    axes[1].plot(t, bt, 'tab:green', linewidth=0.5)
    axes[1].set_ylabel('$B_T$ (nT)')
    axes[1].grid(True)
    
    axes[2].plot(t, bn, 'tab:blue', linewidth=0.5)
    axes[2].set_ylabel('$B_N$ (nT)')
    axes[2].grid(True)
    
    axes[3].plot(t, b, 'k', linewidth=0.5)
    axes[3].set_ylabel('$|B|$ (nT)')
    axes[3].grid(True)
    
    axes[4].plot(t, th, 'm', linewidth=0.5)
    axes[4].axhline(120, color='gray', linestyle='--', label='120°')
    axes[4].axhline(140, color='orange', linestyle='--', label='140°')
    axes[4].set_ylabel(r'$\theta$ (deg)')
    axes[4].set_xlabel('Time (UTC)')
    axes[4].legend(loc='upper right')
    axes[4].grid(True)
    
    axes[4].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.tight_layout()
    output_name = f'switchbacks_analysis_{label.replace(":", "").replace("-", "_")}.png'
    plt.savefig(output_name, dpi=300)
    print(f"Saved plot: {output_name}")
    plt.close()

# 11:50–12:10 UTC
plot_interval(times, BR, BT, BN, Bmag, theta, '2024-12-24T11:50:00', '2024-12-24T12:10:00', '1150_1210')
# 11:58–12:00 UTC
plot_interval(times, BR, BT, BN, Bmag, theta, '2024-12-24T11:58:00', '2024-12-24T12:00:00', '1158_1200')
# 11:59:00–11:59:30 UTC
plot_interval(times, BR, BT, BN, Bmag, theta, '2024-12-24T11:59:00', '2024-12-24T11:59:30', '115900_115930')

print("Analysis complete.")
