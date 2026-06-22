# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "cdflib"
# ]
# ///

import cdflib
import sys
from cdflib.epochs import CDFepoch

data_dir = r"c:\Users\Jeyaprakash S\Documents\GitHub\parker_solar\data"
import glob, os
cdf_files = sorted(glob.glob(os.path.join(data_dir, "*.cdf")))
cdf = cdflib.CDF(cdf_files[0])
epoch = cdf.varget("epoch_mag_RTN")
times = CDFepoch.to_datetime(epoch[0:5])
print(type(times))
if isinstance(times, list):
    print("Is list")
    print(type(times[0]))
    print(times[0])
elif hasattr(times, 'dtype'):
    print("Is numpy array")
    print(times.dtype)
    print(times[0])
else:
    print(type(times[0]))
