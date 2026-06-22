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
import glob
import cdflib
from cdflib.epochs import CDFepoch
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

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

delta_BR = np.abs(BR - B0R)

print("Detecting candidate switchbacks...")
is_above = alpha > 60
is_above = np.nan_to_num(is_above, False)
diff = np.diff(is_above.astype(int))
starts = np.where(diff == 1)[0] + 1
ends = np.where(diff == -1)[0] + 1

if len(is_above) > 0 and is_above[0]:
    starts = np.insert(starts, 0, 0)
if len(is_above) > 0 and is_above[-1]:
    ends = np.append(ends, len(is_above))

candidates = []

for s_idx, e_idx in zip(starts, ends):
    t_start = pd.to_datetime(times_arr[s_idx])
    t_end = pd.to_datetime(times_arr[e_idx-1])
    duration = (t_end - t_start).total_seconds()
    
    if duration < 0.1:
        continue
        
    max_alpha = np.nanmax(alpha[s_idx:e_idx])
    max_dBR = np.nanmax(delta_BR[s_idx:e_idx])
    
    if max_dBR <= 500:
        continue
        
    br_min = np.nanmin(BR[s_idx:e_idx])
    br_max = np.nanmax(BR[s_idx:e_idx])
    mean_bmag = np.nanmean(Bmag[s_idx:e_idx])
    peak_idx = s_idx + np.nanargmax(alpha[s_idx:e_idx])
    
    score = max_alpha * max_dBR
    
    candidates.append({
        'start': t_start,
        'end': t_end,
        'duration': duration,
        'max_alpha': max_alpha,
        'br_min': br_min,
        'br_max': br_max,
        'max_dbr': max_dBR,
        'mean_bmag': mean_bmag,
        'peak_time': times_arr[peak_idx],
        'score': score
    })

# Rank events by score
candidates.sort(key=lambda x: x['score'], reverse=True)

print(f"\n--- Summary ---")
print(f"Total candidate switchbacks: {len(candidates)}")
strong_events = [c for c in candidates if c['max_alpha'] > 90]
print(f"Strong events (alpha > 90°): {len(strong_events)}")

if candidates:
    strongest = candidates[0]
    print(f"Strongest event of the day: Start {strongest['start'].strftime('%H:%M:%S.%f')[:-3]}, Alpha {strongest['max_alpha']:.1f}°, Delta BR {strongest['max_dbr']:.1f} nT, Score {strongest['score']:.0f}")

    print("\n--- Distribution Summary ---")
    durations = [c['duration'] for c in candidates]
    alphas = [c['max_alpha'] for c in candidates]
    print(f"Durations (s): Min {min(durations):.3f}, Max {max(durations):.3f}, Mean {np.mean(durations):.3f}, Median {np.median(durations):.3f}")
    print(f"Max Alphas (°): Min {min(alphas):.1f}, Max {max(alphas):.1f}, Mean {np.mean(alphas):.1f}, Median {np.median(alphas):.1f}")

    print("\n--- Top 20 Events by Score ---")
    for i, c in enumerate(candidates[:20]):
        print(f"[{i+1}] {c['start'].strftime('%H:%M:%S.%f')[:-3]} to {c['end'].strftime('%H:%M:%S.%f')[:-3]} | Dur: {c['duration']:.3f}s | Max Alpha: {c['max_alpha']:.1f} | dBR: {c['max_dbr']:.1f} | BR: {c['br_min']:.1f}/{c['br_max']:.1f} | |B|: {c['mean_bmag']:.1f} | Score: {c['score']:.0f}")

    print("\n--- Generating Plots for Top 5 Events ---")
    for rank, ev in enumerate(candidates[:5]):
        rank += 1
        pt = ev['peak_time']
        s = pt - np.timedelta64(30, 's')
        e = pt + np.timedelta64(30, 's')
        
        mask = (times_arr >= s) & (times_arr <= e)
        zt = times_arr[mask]
        zbr = BR[mask]
        zbt = BT[mask]
        zbn = BN[mask]
        zbmag = Bmag[mask]
        zal = alpha[mask]
        
        fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
        fig.suptitle(f"Top {rank} Event (Peak: {pd.to_datetime(pt).strftime('%H:%M:%S.%f')[:-3]}) | Score: {ev['score']:.0f}", fontsize=14)
        
        axes[0].plot(zt, zbr, 'tab:red', linewidth=0.5)
        axes[0].set_ylabel('$B_R$ (nT)')
        axes[0].grid(True)
        
        axes[1].plot(zt, zbt, 'tab:green', linewidth=0.5)
        axes[1].set_ylabel('$B_T$ (nT)')
        axes[1].grid(True)
        
        axes[2].plot(zt, zbn, 'tab:blue', linewidth=0.5)
        axes[2].set_ylabel('$B_N$ (nT)')
        axes[2].grid(True)
        
        axes[3].plot(zt, zbmag, 'k', linewidth=0.5)
        axes[3].set_ylabel('$|B|$ (nT)')
        axes[3].grid(True)
        
        axes[4].plot(zt, zal, 'm', linewidth=0.5)
        axes[4].axhline(60, color='gray', linestyle='--', label='60°')
        axes[4].axhline(90, color='orange', linestyle='--', label='90°')
        
        # Highlight interval > 60 and > 90
        axes[4].fill_between(zt, 0, 180, where=(zal > 60), color='gray', alpha=0.3, label='> 60°')
        axes[4].fill_between(zt, 0, 180, where=(zal > 90), color='orange', alpha=0.5, label='> 90°')
        
        axes[4].set_ylabel(r'$\alpha$ (deg)')
        axes[4].set_xlabel('Time (UTC)')
        axes[4].legend(loc='upper right')
        axes[4].set_ylim(0, 180)
        axes[4].grid(True)
        
        axes[4].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.tight_layout()
        filename = f'fullday_zoom_Top{rank}_{pd.to_datetime(pt).strftime("%H%M%S")}.png'
        plt.savefig(filename, dpi=300)
        print(f"Saved {filename}")
        plt.close()

print("Analysis complete.")
