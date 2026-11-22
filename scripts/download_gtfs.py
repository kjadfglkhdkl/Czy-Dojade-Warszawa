
import os
import urllib.request
from pathlib import Path

URL = os.getenv("GTFS_URL", "https://mkuran.pl/gtfs/warsaw.zip")
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DEST = DATA_DIR / "warsaw.zip"

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading GTFS from {URL}")
    urllib.request.urlretrieve(URL, DEST)
    print(f"Saved to {DEST}")

if __name__ == "__main__":
    main()
