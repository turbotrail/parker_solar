import os
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

class DirectoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.files = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    href = attr[1]
                    # Filter for typical data files (you can add other extensions if needed)
                    if href.endswith('.fits'):
                        self.files.append(href)

def download_files(url, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    print(f"Fetching directory listing from {url}...")
    
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch directory: {e}")
        return

    parser = DirectoryParser()
    parser.feed(html)
    
    file_links = parser.files
            
    if not file_links:
        print("No .fits files found to download.")
        return

    print(f"Found {len(file_links)} files to download.")
    
    for idx, filename in enumerate(file_links, 1):
        file_url = urljoin(url, filename)
        file_path = os.path.join(target_dir, filename)
        
        # Skip if already downloaded
        if os.path.exists(file_path):
            print(f"[{idx}/{len(file_links)}] Skipping {filename}, already exists.")
            continue
            
        print(f"[{idx}/{len(file_links)}] Downloading {filename}...")
        try:
            urllib.request.urlretrieve(file_url, file_path)
        except Exception as e:
            print(f"Error downloading {filename}: {e}")

if __name__ == "__main__":
    target_url = "https://wispr.nrl.navy.mil/data/rel/fits/L3/orbit22/20241224/"
    # Change the local folder name here if you want it to download elsewhere
    local_folder = "wispr_20241224_data" 
    download_files(target_url, local_folder)
    print("Download process completed.")
