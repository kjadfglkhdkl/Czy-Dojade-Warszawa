from collections import Counter, defaultdict
from datetime import date, datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .data import load_data, normalize_stop, distance_m

DATA = {}
STOPS = []
ROUTES = []
STOP_BY_ID = {}
ROUTE_BY_ID = {}
TRIP_BY_ID = {}
TRIPS_BY_ROUTE = defaultdict(list)
STOP_TIMES_BY_STOP = defaultdict(list)
STOP_TIMES_BY_TRIP = defaultdict(list)
SHAPES_BY_ID = defaultdict(list)
STOP_CHILDREN_BY_PARENT = defaultdict(list)
CALENDAR_BY_SERVICE = {}
CALENDAR_EXCEPTIONS = defaultdict(dict)

@asynccontextmanager
async def lifespan(app):
    global DATA, STOPS, ROUTES, STOP_BY_ID, ROUTE_BY_ID, TRIP_BY_ID, TRIPS_BY_ROUTE, STOP_TIMES_BY_STOP, STOP_TIMES_BY_TRIP, SHAPES_BY_ID, STOP_CHILDREN_BY_PARENT, CALENDAR_BY_SERVICE, CALENDAR_EXCEPTIONS
    DATA = load_data()
    STOPS = [s for row in DATA["stops"] if (s := normalize_stop(row))]
    STOP_BY_ID = {s["stop_id"].strip(): s for s in STOPS if s["stop_id"]}
    STOP_CHILDREN_BY_PARENT = defaultdict(list)
    for stop in STOPS:
        parent_id = stop.get("parent_station", "")
        if parent_id and parent_id in STOP_BY_ID:
            STOP_CHILDREN_BY_PARENT[parent_id].append(stop["stop_id"])
    ROUTES = DATA["routes"]
    ROUTE_BY_ID = {(r.get("route_id", "") or "").strip(): r for r in ROUTES if (r.get("route_id", "") or "").strip()}
    TRIP_BY_ID = {(t.get("trip_id", "") or "").strip(): t for t in DATA.get("trips", []) if (t.get("trip_id", "") or "").strip()}
    TRIPS_BY_ROUTE = defaultdict(list)
    for trip in DATA.get("trips", []):
        TRIPS_BY_ROUTE[(trip.get("route_id", "") or "").strip()].append(trip)
    STOP_TIMES_BY_STOP = defaultdict(list)
    STOP_TIMES_BY_TRIP = defaultdict(list)
    for row in DATA.get("stop_times", []):
        STOP_TIMES_BY_STOP[(row.get("stop_id", "") or "").strip()].append(row)
        STOP_TIMES_BY_TRIP[(row.get("trip_id", "") or "").strip()].append(row)
    for rows in list(STOP_TIMES_BY_STOP.values()) + list(STOP_TIMES_BY_TRIP.values()):
        rows.sort(key=lambda r: int(r.get("stop_sequence", 0) or 0))
    CALENDAR_BY_SERVICE = {(row.get("service_id", "") or "").strip(): row for row in DATA.get("calendar", [])}
    CALENDAR_EXCEPTIONS = defaultdict(dict)
    for row in DATA.get("calendar_dates", []):
        service_id = (row.get("service_id", "") or "").strip()
        date_key = (row.get("date", "") or "").strip()
        exception_type = (row.get("exception_type", "") or "").strip()
        if service_id and date_key and exception_type in {"1", "2"}:
            CALENDAR_EXCEPTIONS[date_key][service_id] = exception_type
    SHAPES_BY_ID = defaultdict(list)
    for shape in DATA.get("shapes", []):
        try:
            SHAPES_BY_ID[shape.get("shape_id", "")].append((int(shape.get("shape_pt_sequence", 0)), float(shape["shape_pt_lat"]), float(shape["shape_pt_lon"])))
        except (ValueError, KeyError, TypeError):
            continue
    for rows in SHAPES_BY_ID.values():
        rows.sort(key=lambda r: r[0])
    yield

app = FastAPI(title="Czy dojade? Warszawa API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"], allow_methods=["GET"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "source": DATA.get("source", "loading"), "stops_loaded": len(STOPS)}

@app.get("/api/stats")
def stats():
    return {"stops": len(STOPS), "routes": len(ROUTES), "trips": len(DATA.get("trips", [])), "source": DATA.get("source", "loading"), "stops_with_service": len(STOP_TIMES_BY_STOP), "station_groups": len(STOP_CHILDREN_BY_PARENT)}

@app.get("/api/stops")
def stops(search: str = "", limit: int = Query(default=1500, ge=1, le=10000)):
    rows = STOPS
    if search.strip():
        needle = search.strip().casefold()
        rows = [s for s in rows if needle in s["name"].casefold() or needle in s["stop_id"].casefold()]
    return rows[:limit]

@app.get("/api/routes")
def routes():
    return [_route_public(r) for r in ROUTES]

def _route_public(r):
    return {"route_id": r.get("route_id", ""), "short_name": r.get("route_short_name", ""), "long_name": r.get("route_long_name", ""), "route_type": str(r.get("route_type", "")).strip(), "route_color": r.get("route_color", ""), "route_text_color": r.get("route_text_color", "")}

def _ordered_trip_stops(trip_id):
    trip_rows = STOP_TIMES_BY_TRIP.get(trip_id, [])
    return [STOP_BY_ID[row["stop_id"]] for row in trip_rows if row.get("stop_id") in STOP_BY_ID]

def related_stop_ids(stop_id: str, stop_by_id: dict, children_by_parent: dict):
    """Return the selected GTFS stop plus child platforms if selected stop is a station."""
    if stop_id not in stop_by_id:
        return []
    related = [stop_id]
    related.extend(children_by_parent.get(stop_id, []))
    return list(dict.fromkeys(related))

@app.get("/api/stops/{stop_id}/routes")
def routes_at_stop(stop_id: str):
    if stop_id not in STOP_BY_ID:
        return {"stop": None, "routes": [], "matched_stop_ids": [], "message": "Stop ID not found in loaded GTFS stops."}
    matched_stop_ids = related_stop_ids(stop_id, STOP_BY_ID, STOP_CHILDREN_BY_PARENT)
    route_trips = defaultdict(set)
    route_directions = defaultdict(set)
    # Aggregate parent station and child platform IDs; GTFS stop_times commonly
    # reference platform IDs rather than a parent station ID.
    for related_id in matched_stop_ids:
        for stop_time in STOP_TIMES_BY_STOP.get(related_id, []):
            trip_id = (stop_time.get("trip_id", "") or "").strip()
            trip = TRIP_BY_ID.get(trip_id)
            if not trip:
                continue
            route_id = (trip.get("route_id", "") or "").strip()
            if route_id not in ROUTE_BY_ID:
                continue
            route_trips[route_id].add(trip_id)
            headsign = (trip.get("trip_headsign", "") or "").strip()
            if headsign:
                route_directions[route_id].add(headsign)
    result = []
    for route_id in sorted(route_trips, key=lambda rid: (ROUTE_BY_ID.get(rid, {}).get("route_short_name", "").casefold(), rid)):
        route = ROUTE_BY_ID.get(route_id)
        if route:
            result.append({**_route_public(route), "directions": sorted(route_directions[route_id]), "trip_count": len(route_trips[route_id])})
    return {"stop": STOP_BY_ID[stop_id], "routes": result, "matched_stop_ids": matched_stop_ids, "matched_platforms": len(matched_stop_ids)}

def _service_active(service_id: str, service_date: date) -> bool:
    date_key = service_date.strftime("%Y%m%d")
    exception = CALENDAR_EXCEPTIONS.get(date_key, {}).get(service_id)
    if exception == "1":
        return True
    if exception == "2":
        return False
    row = CALENDAR_BY_SERVICE.get(service_id)
    if not row:
        # Some incomplete/offline feeds have no calendar files; don't hide their timetable.
        return not CALENDAR_BY_SERVICE and not CALENDAR_EXCEPTIONS
    try:
        start = datetime.strptime(row.get("start_date", ""), "%Y%m%d").date()
        end = datetime.strptime(row.get("end_date", ""), "%Y%m%d").date()
    except ValueError:
        return False
    if not start <= service_date <= end:
        return False
    weekday_key = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][service_date.weekday()]
    return row.get(weekday_key, "0") == "1"


def _time_seconds(value: str) -> int:
    try:
        h, m, sec = (int(part) for part in value.split(":"))
        return h * 3600 + m * 60 + sec
    except (ValueError, AttributeError):
        return 10**9


def _time_display(value: str) -> str:
    try:
        h, m, _ = (int(part) for part in value.split(":"))
        return f"{h:02d}:{m:02d}"
    except (ValueError, AttributeError):
        return value


@app.get("/api/stops/{stop_id}/departures")
def departures(stop_id: str, date_value: str = Query(default=None, alias="date"), route_id: str = "", limit: int = Query(default=100, ge=1, le=500)):
    if stop_id not in STOP_BY_ID:
        return {"stop": None, "date": date_value, "departures": [], "message": "Stop ID not found in loaded GTFS stops."}
    try:
        service_date = datetime.strptime(date_value, "%Y-%m-%d").date() if date_value else date.today()
    except ValueError:
        return {"stop": STOP_BY_ID[stop_id], "date": date_value, "departures": [], "message": "Invalid date. Use YYYY-MM-DD."}
    matched_ids = related_stop_ids(stop_id, STOP_BY_ID, STOP_CHILDREN_BY_PARENT)
    departures_list = []
    for matched_id in matched_ids:
        for row in STOP_TIMES_BY_STOP.get(matched_id, []):
            trip_id = (row.get("trip_id", "") or "").strip()
            trip = TRIP_BY_ID.get(trip_id)
            if not trip:
                continue
            service_id = (trip.get("service_id", "") or "").strip()
            if service_id and not _service_active(service_id, service_date):
                continue
            rid = (trip.get("route_id", "") or "").strip()
            if route_id and rid != route_id:
                continue
            departure_time = (row.get("departure_time", "") or row.get("arrival_time", "")).strip()
            if not departure_time:
                continue
            route = ROUTE_BY_ID.get(rid, {})
            departures_list.append({
                "trip_id": trip_id,
                "route_id": rid,
                "route_short_name": route.get("route_short_name", ""),
                "route_long_name": route.get("route_long_name", ""),
                "route_type": route.get("route_type", ""),
                "route_color": route.get("route_color", ""),
                "headsign": (trip.get("trip_headsign", "") or "").strip(),
                "stop_id": matched_id,
                "stop_name": STOP_BY_ID.get(matched_id, {}).get("name", ""),
                "departure_time": departure_time,
                "departure_display": _time_display(departure_time),
                "arrival_time": (row.get("arrival_time", "") or "").strip(),
                "stop_sequence": row.get("stop_sequence", ""),
            })
    departures_list.sort(key=lambda item: (_time_seconds(item["departure_time"]), item["route_short_name"], item["trip_id"]))
    source = DATA.get("source", "")
    return {"stop": STOP_BY_ID[stop_id], "date": service_date.isoformat(), "matched_stop_ids": matched_ids, "source": source, "calendar_available": bool(CALENDAR_BY_SERVICE or CALENDAR_EXCEPTIONS), "departures": departures_list[:limit], "total": len(departures_list), "message": "No scheduled departures for this stop/date/route." if not departures_list else ""}


@app.get("/api/diagnostics/linkage")
def linkage_diagnostics():
    stop_time_rows = sum(len(rows) for rows in STOP_TIMES_BY_STOP.values())
    known_stop_time_rows = sum(1 for rows in STOP_TIMES_BY_TRIP.values() for row in rows if row.get("stop_id", "") in STOP_BY_ID)
    return {"source": DATA.get("source", "unknown"), "stops": len(STOP_BY_ID), "routes": len(ROUTE_BY_ID), "trips": len(TRIP_BY_ID), "stop_time_rows": stop_time_rows, "stop_times_with_known_stops": known_stop_time_rows, "stops_with_stop_times": len(STOP_TIMES_BY_STOP), "stations_with_child_platforms": len(STOP_CHILDREN_BY_PARENT)}

@app.get("/api/routes/{route_id}/map")
def route_map(route_id: str):
    route = ROUTE_BY_ID.get(route_id)
    if not route:
        return {"route": None, "trips": []}
    mapped_trips = []
    seen_patterns = set()
    for trip in TRIPS_BY_ROUTE.get(route_id, []):
        trip_id = trip.get("trip_id", "")
        shape_id = trip.get("shape_id", "")
        shape = SHAPES_BY_ID.get(shape_id, [])
        coordinates = [[lat, lon] for _, lat, lon in shape]
        itinerary = _ordered_trip_stops(trip_id)
        if not coordinates:
            coordinates = [[s["lat"], s["lon"]] for s in itinerary]
        if len(coordinates) < 2:
            continue
        pattern_key = (trip.get("shape_id", ""), trip.get("trip_headsign", ""), tuple(s["stop_id"] for s in itinerary))
        if pattern_key in seen_patterns:
            continue
        seen_patterns.add(pattern_key)
        mapped_trips.append({"trip_id": trip_id, "headsign": trip.get("trip_headsign", ""), "coordinates": coordinates, "stops": itinerary})
        # Return only a small number of unique route patterns, not all daily departures.
        if len(mapped_trips) >= 8:
            break
    return {"route": _route_public(route), "trips": mapped_trips}

@app.get("/api/nearest")
def nearest(lat: float, lon: float, radius_m: float = Query(default=800, ge=50, le=5000)):
    result = []
    for stop in STOPS:
        d = distance_m(lat, lon, stop["lat"], stop["lon"])
        if d <= radius_m:
            result.append({**stop, "distance_m": round(d)})
    return sorted(result, key=lambda x: x["distance_m"])

@app.get("/api/districts")
def districts():
    return {"available": False, "message": "District boundary data is not included in the GTFS feed. Add a verified public boundary dataset to enable this endpoint.", "items": []}
