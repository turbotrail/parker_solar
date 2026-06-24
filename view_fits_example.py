import os
import glob
import sys

try:
    from astropy.io import fits
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
except ImportError:
    print("Missing required libraries. Please install them first by running:")
    print("pip install astropy matplotlib")
    sys.exit(1)

# Directory where the FITS files are saved
data_dir = "wispr_20241224_data"
fits_files = glob.glob(os.path.join(data_dir, "*.fits"))

if not fits_files:
    print(f"No FITS files found in the '{data_dir}' directory.")
    sys.exit(1)

# Grab the very first file as an example
example_file = fits_files[0]
print(f"Opening file: {example_file}\n")

# Open the FITS file
with fits.open(example_file) as hdul:
    # Print out the structure of the FITS file
    print("FITS File Structure:")
    hdul.info()
    print("\n")
    
    # Find the first HDU (Header Data Unit) that contains a 2D image array
    image_data = None
    for hdu in hdul:
        if hdu.data is not None and len(hdu.data.shape) == 2:
            image_data = hdu.data
            print(f"Found 2D image data with shape: {image_data.shape}")
            break
            
    if image_data is None:
        print("Could not find any 2D image data in this FITS file.")
        sys.exit(1)

# Create a plot to visualize the FITS image
plt.figure(figsize=(10, 8))

# We use LogNorm here because astronomical data often has a very high dynamic range.
# 'origin=lower' is standard for FITS images to orient them correctly.
plt.imshow(image_data, cmap='gray', origin='lower', norm=LogNorm())

plt.colorbar(label='Pixel Brightness')
plt.title(f"WISPR Observation: {os.path.basename(example_file)}")
plt.tight_layout()

# This will pop up an interactive window with the image
plt.show()
