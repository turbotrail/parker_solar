import cdflib
import matplotlib.pyplot as plt
import numpy as np
import datetime
import os

# Set up matplotlib backend
plt.switch_backend('Agg')

# The file downloaded by the user
cdf_path = 'magplasma/psp_coho1hr_merged_mag_plasma_20241201_v01.cdf'

if not os.path.exists(cdf_path):
    print(f"Error: Could not find {cdf_path}")
    exit(1)

# Open the CDF file
print(f"Reading {cdf_path}...")
cdf_file = cdflib.CDF(cdf_path)

# Extract Epoch (Time) and convert to Python datetime objects
epochs = cdf_file.varget('Epoch')
times = cdflib.cdfepoch.to_datetime(epochs)

# Extract the data variables
# 'protonDensity' is highly correlated to the brightness seen in WISPR
density = cdf_file.varget('protonDensity')
# 'ProtonSpeed' is the solar wind velocity (km/s)
speed = cdf_file.varget('ProtonSpeed')
# 'B' is total magnetic field strength (nT)
b_field = cdf_file.varget('B')
# Distance from sun (AU)
distance = cdf_file.varget('radialDistance')

# CDF files use 'fill values' for missing data (usually huge negative numbers like -1e31)
# We will mask out any wildly invalid numbers
def clean_data(arr):
    # Mask values less than 0 or completely unrealistic (like 1e30)
    arr = np.where(arr < 0, np.nan, arr)
    arr = np.where(arr > 1e10, np.nan, arr)
    return arr

density = clean_data(density)
speed = clean_data(speed)
b_field = clean_data(b_field)

# Plotting
print("Generating plot...")
# Create a figure with 3 stacked subplots sharing the X-axis (time)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
fig.suptitle('Parker Solar Probe: Hourly Mag & Plasma (December 2024)', fontsize=16, fontweight='bold')

# Plot 1: Solar Wind Velocity
ax1.plot(times, speed, color='darkorange', linewidth=2)
ax1.set_ylabel('Proton Speed (km/s)', fontweight='bold')
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.set_title('Solar Wind Speed')

# Plot 2: Proton Density
ax2.plot(times, density, color='dodgerblue', linewidth=2)
ax2.set_ylabel('Density (cm⁻³)', fontweight='bold')
ax2.set_yscale('log') # Density often spans orders of magnitude
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_title('Proton Density (Log Scale)')

# Plot 3: Magnetic Field
ax3.plot(times, b_field, color='crimson', linewidth=2)
ax3.set_ylabel('Total B-Field (nT)', fontweight='bold')
ax3.set_xlabel('Date (Dec 2024)', fontweight='bold')
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.set_title('Magnetic Field Strength')

# Format x-axis nicely to show dates
fig.autofmt_xdate()
plt.tight_layout()

# Save the plot
output_file = 'coho_dec2024_plot.png'
plt.savefig(output_file, dpi=200, bbox_inches='tight')
plt.close(fig)

print(f"Plot successfully saved to {output_file}")
