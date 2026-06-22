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

# Directory containing CDF files
data_dir = r"c:\Users\Jeyaprakash S\Documents\GitHub\parker_solar\data"

# Select specific files
target_files = [
    "psp_fld_l2_mag_rtn_2024122406_v02.cdf",
    "psp_fld_l2_mag_rtn_2024122412_v02.cdf"
]

cdf_files = [os.path.join(data_dir, f) for f in target_files]

all_times = []
all_B_R = []
all_B_T = []
all_B_N = []
all_B_mag = []

for file in cdf_files:
    try:
        cdf = cdflib.CDF(file)
        
        # Read epoch (time)
        epoch = cdf.varget("epoch_mag_RTN")
        # Read magnetic field vector (RTN)
        b_rtn = cdf.varget("psp_fld_l2_mag_RTN")
        
        # Convert TT2000 epoch to datetime objects
        times = CDFepoch.to_datetime(epoch)
        all_times.append(times)
            
        all_B_R.append(b_rtn[:, 0])
        all_B_T.append(b_rtn[:, 1])
        all_B_N.append(b_rtn[:, 2])
        
        # Calculate magnitude
        b_mag = np.linalg.norm(b_rtn, axis=1)
        all_B_mag.append(b_mag)
        
        print(f"Successfully processed {os.path.basename(file)}")
    except Exception as e:
        print(f"Error processing {os.path.basename(file)}: {e}")

if not all_B_R:
    print("No data was successfully processed.")
    exit(1)

# Concatenate arrays
times_arr = np.concatenate(all_times)
B_R = np.concatenate(all_B_R)
B_T = np.concatenate(all_B_T)
B_N = np.concatenate(all_B_N)
B_mag = np.concatenate(all_B_mag)

print(f"Plotting {len(times_arr)} points at full cadence...")

# Plotting
plt.figure(figsize=(15, 10))

# Plot B_R
ax1 = plt.subplot(4, 1, 1)
plt.plot(times_arr, B_R, label='$B_R$ (Radial)', color='tab:red', linewidth=0.5)
plt.ylabel('$B_R$ (nT)')
plt.title('Parker Solar Probe Magnetic Field (RTN) - Specific Dec 24 Data')
plt.grid(True)
plt.legend(loc='upper right')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Plot B_T
ax2 = plt.subplot(4, 1, 2)
plt.plot(times_arr, B_T, label='$B_T$ (Tangential)', color='tab:green', linewidth=0.5)
plt.ylabel('$B_T$ (nT)')
plt.grid(True)
plt.legend(loc='upper right')
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Plot B_N
ax3 = plt.subplot(4, 1, 3)
plt.plot(times_arr, B_N, label='$B_N$ (Normal)', color='tab:blue', linewidth=0.5)
plt.ylabel('$B_N$ (nT)')
plt.grid(True)
plt.legend(loc='upper right')
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Plot |B|
ax4 = plt.subplot(4, 1, 4)
plt.plot(times_arr, B_mag, label='$|B|$ (Magnitude)', color='k', linewidth=0.5)
plt.ylabel('$|B|$ (nT)')
plt.xlabel('Time (UTC)')
plt.grid(True)
plt.legend(loc='upper right')
ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

plt.tight_layout()
output_path = r"c:\Users\Jeyaprakash S\Documents\GitHub\parker_solar\switchbacks_plot_specific.png"
plt.savefig(output_path, dpi=300)
print(f"Plot saved successfully as {output_path}")
