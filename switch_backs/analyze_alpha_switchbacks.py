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

print(f"Total points loaded: {len(times_arr)}")

BR = b_rtn_arr[:, 0]
BT = b_rtn_arr[:, 1]
BN = b_rtn_arr[:, 2]
Bmag = np.sqrt(BR**2 + BT**2 + BN**2)

print("Calculating 60s rolling background field...")
cadence_hz = 293
window_size = int(60 * cadence_hz)

B0R = pd.Series(BR).rolling(window_size, center=True).mean().values
B0T = pd.Series(BT).rolling(window_size, center=True).mean().values
B0N = pd.Series(BN).rolling(window_size, center=True).mean().values

B0mag = np.sqrt(B0R**2 + B0T**2 + B0N**2)
dot = BR*B0R + BT*B0T + BN*B0N

with np.errstate(invalid='ignore', divide='ignore'):
    cos_alpha = dot / (Bmag * B0mag)
    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
    alpha = np.degrees(np.arccos(cos_alpha))

def detect_intervals(t, br, al, threshold, label):
    is_above = al > threshold
    is_above = np.nan_to_num(is_above, False)
    diff = np.diff(is_above.astype(int))
    starts = np.where(diff == 1)[0] + 1
    ends = np.where(diff == -1)[0] + 1
    
    if len(is_above) > 0 and is_above[0]:
        starts = np.insert(starts, 0, 0)
    if len(is_above) > 0 and is_above[-1]:
        ends = np.append(ends, len(is_above))
        
    intervals = []
    print(f"\n--- {label} Candidate Switchbacks (Alpha > {threshold}°) ---")
    
    for s_idx, e_idx in zip(starts, ends):
        t_start = pd.to_datetime(t[s_idx])
        t_end = pd.to_datetime(t[e_idx-1])
        duration = (t_end - t_start).total_seconds()
        
        if duration < 0.1: # Skip micro-noise
            continue
            
        max_alpha = np.nanmax(al[s_idx:e_idx])
        br_min = np.nanmin(br[s_idx:e_idx])
        br_max = np.nanmax(br[s_idx:e_idx])
        peak_idx = s_idx + np.nanargmax(al[s_idx:e_idx])
        
        intervals.append({
            'start': t_start,
            'end': t_end,
            'duration': duration,
            'max_alpha': max_alpha,
            'br_min': br_min,
            'br_max': br_max,
            'peak_time': t[peak_idx],
            'label': label
        })
        print(f"Start: {t_start.strftime('%H:%M:%S.%f')[:-3]} | End: {t_end.strftime('%H:%M:%S.%f')[:-3]} | Dur: {duration:.3f}s | Max Alpha: {max_alpha:.1f}° | BR min/max: {br_min:.1f} / {br_max:.1f}")
        
    return intervals

def plot_overview(t, br, bt, bn, bmag, al, label, out_prefix):
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(f"PSP Alpha Switchback Analysis ({label})", fontsize=16)
    
    axes[0].plot(t, br, 'tab:red', linewidth=0.5)
    axes[0].set_ylabel('$B_R$ (nT)')
    axes[0].grid(True)
    
    axes[1].plot(t, bt, 'tab:green', linewidth=0.5)
    axes[1].set_ylabel('$B_T$ (nT)')
    axes[1].grid(True)
    
    axes[2].plot(t, bn, 'tab:blue', linewidth=0.5)
    axes[2].set_ylabel('$B_N$ (nT)')
    axes[2].grid(True)
    
    axes[3].plot(t, bmag, 'k', linewidth=0.5)
    axes[3].set_ylabel('$|B|$ (nT)')
    axes[3].grid(True)
    
    axes[4].plot(t, al, 'm', linewidth=0.5)
    axes[4].axhline(60, color='gray', linestyle='--', label='60°')
    axes[4].axhline(90, color='orange', linestyle='--', label='90°')
    axes[4].set_ylabel(r'$\alpha$ (deg)')
    axes[4].set_xlabel('Time (UTC)')
    axes[4].legend(loc='upper right')
    axes[4].grid(True)
    
    axes[4].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.tight_layout()
    filename = f'{out_prefix}_{label.replace(":", "").replace("-", "_")}.png'
    plt.savefig(filename, dpi=300)
    print(f"Saved {filename}")
    plt.close()

analysis_ranges = [
    ('2024-12-24T10:25:00', '2024-12-24T10:35:00', '1025_1035'),
    ('2024-12-24T11:50:00', '2024-12-24T12:10:00', '1150_1210'),
    ('2024-12-24T16:35:00', '2024-12-24T16:45:00', '1635_1645')
]

all_events = []

for start_str, end_str, label in analysis_ranges:
    s = np.datetime64(start_str)
    e = np.datetime64(end_str)
    mask = (times_arr >= s) & (times_arr <= e)
    
    t = times_arr[mask]
    br = BR[mask]
    bt = BT[mask]
    bn = BN[mask]
    b = Bmag[mask]
    al = alpha[mask]
    
    plot_overview(t, br, bt, bn, b, al, label, "alpha_overview")
    
    events_60 = detect_intervals(t, br, al, 60, f"{label} (>60)")
    events_90 = detect_intervals(t, br, al, 90, f"{label} (>90)")
    
    all_events.extend(events_90) # We'll rank the top events by max_alpha from the >90 detections

# Sort events by max_alpha and take top 10
all_events.sort(key=lambda x: x['max_alpha'], reverse=True)
top_10 = all_events[:10]

print("\n--- Zooming on Top 10 Highest Alpha Events ---")
for rank, ev in enumerate(top_10):
    rank += 1
    pt = ev['peak_time']
    # exact +- 30 seconds around peak
    s = pt - np.timedelta64(30, 's')
    e = pt + np.timedelta64(30, 's')
    
    mask = (times_arr >= s) & (times_arr <= e)
    zt = times_arr[mask]
    zbr = BR[mask]
    zbt = BT[mask]
    zbn = BN[mask]
    zbmag = Bmag[mask]
    zal = alpha[mask]
    
    plot_overview(zt, zbr, zbt, zbn, zbmag, zal, f"Top{rank}_{pd.to_datetime(pt).strftime('%H%M%S')}", "alpha_zoom")

print("Analysis complete.")
