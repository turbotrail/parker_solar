import os
import glob
import sys
import numpy as np
from tqdm import tqdm

try:
    from astropy.io import fits
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    import imageio
except ImportError as e:
    print(f"Missing required libraries: {e}")
    sys.exit(1)

plt.switch_backend('Agg')

def create_animation(data_dir, camera_pattern, output_filename, camera_name):
    # Find all FITS files matching the specific camera ID
    fits_files = sorted(glob.glob(os.path.join(data_dir, f"*{camera_pattern}")))

    if not fits_files:
        print(f"No {camera_name} camera FITS files found in {data_dir}.")
        return

    wispr_cmap = plt.get_cmap('afmhot')
    print(f"\n--- Animating {len(fits_files)} frames for WISPR {camera_name} Camera ---")

    writer = imageio.get_writer(output_filename, fps=15, codec='libx264', quality=8)
    fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
    im = None

    print(f"Calculating stable brightness bounds for {camera_name}...")
    sample_files = fits_files[::max(1, len(fits_files)//10)]
    vmin_list, vmax_list = [], []

    for f in sample_files:
        try:
            with fits.open(f) as hdul:
                data = hdul[0].data
                if data is not None:
                    data = data.astype(float)
                    data[np.isinf(data)] = np.nan
                    # Ignore corrupted/empty frames for bounds calculation
                    if np.nanstd(data) > 1e-15:
                        vmin_list.append(np.nanpercentile(data, 10))
                        vmax_list.append(np.nanpercentile(data, 99))
        except Exception:
            pass

    if not vmin_list:
        print(f"Could not compute bounds for {camera_name}. Skipping.")
        return

    # Use median bounds from the sampled frames to prevent flickering
    global_vmin = np.nanmedian(vmin_list)
    global_vmax = np.nanmedian(vmax_list)
    if global_vmin <= 0:
        global_vmin = 1e-14

    print(f"Global bounds: {global_vmin:.2e} to {global_vmax:.2e}")
    
    for f in tqdm(fits_files, desc=f"Rendering {camera_name}"):
        try:
            with fits.open(f) as hdul:
                data = hdul[0].data
                if data is None or len(data.shape) != 2:
                    continue
                    
                data = data.astype(float)
                data[np.isinf(data)] = np.nan
                
                # Check for completely black/NaN frames
                if np.nanmax(data) <= 0 or np.nanstd(data) < 1e-15:
                    continue
                    
                obs_time = hdul[0].header.get('DATE-OBS', os.path.basename(f))
                
                # Clip data so the LogNorm function doesn't crash on negative values
                data = np.clip(data, global_vmin, global_vmax)
                
                if im is None:
                    im = ax.imshow(data, cmap=wispr_cmap, origin='lower', norm=LogNorm(vmin=global_vmin, vmax=global_vmax))
                    plt.colorbar(im, ax=ax, label='Pixel Brightness')
                else:
                    im.set_data(data)
                
                ax.set_title(f"Parker Solar Probe WISPR ({camera_name}): {obs_time}")
                
                fig.canvas.draw()
                # Extract image as numpy array without the alpha channel
                image = np.array(fig.canvas.buffer_rgba())[..., :3]
                
                writer.append_data(image)
        except Exception:
            pass # Skip corrupted frames silently to keep output clean

    writer.close()
    plt.close(fig)
    print(f"Animation saved as {output_filename}")


if __name__ == "__main__":
    # Pointing this directly to the new LW folder you are downloading
    data_directory = "wispr_20241224_data_lw"
    
    if not os.path.exists(data_directory):
        print(f"Waiting for {data_directory} to be created...")
        os.makedirs(data_directory, exist_ok=True)
    
    # 1. Generate Inner Camera Animation
    create_animation(
        data_dir=data_directory, 
        camera_pattern="_1211.fits", 
        output_filename="wispr_lw_inner_animation.mp4",
        camera_name="Inner"
    )
    
    # 2. Generate Outer Camera Animation
    create_animation(
        data_dir=data_directory, 
        camera_pattern="_2222.fits", 
        output_filename="wispr_lw_outer_animation.mp4",
        camera_name="Outer"
    )
    
    print("\nAll done! Both Inner and Outer LW animations have been generated.")
