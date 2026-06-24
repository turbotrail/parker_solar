# WISPR Data Download Instructions

To efficiently download all the FITS files from the Parker Solar Probe WISPR instrument directly from the NRL servers, you can use the `wget` command-line utility. 

This is much faster and more reliable than downloading files one by one through a browser.

## The Download Command

Run the following command in your terminal:

```bash
wget -r -np -c -nH --cut-dirs=6 -P wispr_20241224_data -A fits "https://wispr.nrl.navy.mil/data/rel/fits/L3/orbit22/20241224/"
```

```wget -r -np -c -nH --cut-dirs=6 -P wispr_20241224_data_lw -A fits https://wispr.nrl.navy.mil/data/rel/fits/LW/orbit22/20241224/```

### Understanding the Flags:

* `-r` : **Recursive**. Instructs `wget` to download all files in the directory.
* `-np` : **No Parent**. Crucial when downloading recursively; it stops `wget` from going backwards up the directory tree and downloading the entire website by mistake.
* `-c` : **Continue**. If your download is interrupted, running the exact same command again will skip the fully downloaded files and resume any partially downloaded ones.
* `-nH` : **No Host Directories**. Prevents `wget` from creating a folder named `wispr.nrl.navy.mil` on your computer.
* `--cut-dirs=6` : **Cut Directories**. Prevents `wget` from recreating the deeply nested server folder structure (`/data/rel/fits/L3/orbit22/20241224/`).
* `-P wispr_20241224_data` : **Directory Prefix**. Neatly saves all the files directly into a local folder named `wispr_20241224_data`.
* `-A fits` : **Accept List**. Ensures only files ending in `.fits` are downloaded, ignoring HTML index files.

## Prerequisites

If you are on a Mac and the command fails because `wget` is not recognized, you can install it via Homebrew:

```bash
brew install wget
```
