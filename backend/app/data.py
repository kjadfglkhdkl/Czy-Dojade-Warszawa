import csv
import io
import math
import os
import urllib.request
import zipfile
from pathlib import Path

GTFS_URL = os.getenv("GTFS_URL", "https://mkuran.pl/gtfs/warsaw.zip")
# Default to a writable folder inside the project (works on Windows, too).
DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parents[1] / "data")))
ZIP_PATH = DATA_DIR / "warsaw.zip"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

def _read_csv_from_zip(zf, filename):
    try:
        raw = zf.read(filename)
    except KeyError:
        return []
    text = raw.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))

def download_feed():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Fetch to a temporary file first so a partial download won't poison the cache.
    if not ZIP_PATH.exists() or ZIP_PATH.stat().st_size < 1000:
        request = urllib.request.Request(GTFS_URL, headers={"User-Agent": "CzyDojadeWarszawa/1.0"})
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = response.read()
        if len(payload) < 1000:
            raise ValueError("GTFS download was unexpectedly small")
        temp_path = ZIP_PATH.with_suffix(".tmp")
        temp_path.write_bytes(payload)
        try:
            with zipfile.ZipFile(temp_path) as zf:
                if "stops.txt" not in zf.namelist():
                    raise ValueError("Downloaded GTFS ZIP has no stops.txt")
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        temp_path.replace(ZIP_PATH)
    return ZIP_PATH

def _sample_data():
    def load(name):
        with (SAMPLE_DIR / name).open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return {
        "stops": load("stops.txt"),
        "routes": load("routes.txt"),
        "trips": load("trips.txt"),
        "stop_times": load("stop_times.txt"),
        "calendar": load("calendar.txt") if (SAMPLE_DIR / "calendar.txt").exists() else [],
        "calendar_dates": load("calendar_dates.txt") if (SAMPLE_DIR / "calendar_dates.txt").exists() else [],
        "shapes": [],
        "source": "sample data (offline fallback)",
    }

def load_data():
    try:
        path = download_feed()
        with zipfile.ZipFile(path) as zf:
            stops = _read_csv_from_zip(zf, "stops.txt")
            routes = _read_csv_from_zip(zf, "routes.txt")
            trips = _read_csv_from_zip(zf, "trips.txt")
            stop_times = _read_csv_from_zip(zf, "stop_times.txt")
            shapes = _read_csv_from_zip(zf, "shapes.txt")
            calendar = _read_csv_from_zip(zf, "calendar.txt")
            calendar_dates = _read_csv_from_zip(zf, "calendar_dates.txt")
            if not stops:
                raise ValueError("GTFS feed contains no stops")
            # Validate that the stops have usable coordinates.
            valid = [r for r in stops if normalize_stop(r)]
            if not valid:
                raise ValueError("GTFS stops have no valid coordinates")
            return {"stops": stops, "routes": routes, "trips": trips, "stop_times": stop_times, "calendar": calendar, "calendar_dates": calendar_dates, "shapes": shapes, "source": "live GTFS feed"}
    except Exception as exc:
        print(f"GTFS download/read failed; using sample dataset: {exc}")
        return _sample_data()

def distance_m(lat1, lon1, lat2, lon2):
    earth_radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return earth_radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize_stop(row):
    try:
        lat, lon = float(row.get("stop_lat", "")), float(row.get("stop_lon", ""))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return {
        "stop_id": (row.get("stop_id", "") or "").strip(),
        "name": row.get("stop_name", "Unnamed stop"),
        "lat": lat,
        "lon": lon,
        "code": row.get("stop_code", ""),
        "parent_station": (row.get("parent_station", "") or "").strip(),
        "location_type": (row.get("location_type", "") or "").strip(),
    }
