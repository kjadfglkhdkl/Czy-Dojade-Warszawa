from collections import Counter, defaultdict
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

@asynccontextmanager
async def lifespan(app):
    global DATA, STOPS, ROUTES, STOP_BY_ID, ROUTE_BY_ID, TRIP_BY_ID, TRIPS_BY_ROUTE, STOP_TIMES_BY_STOP, STOP_TIMES_BY_TRIP, SHAPES_BY_ID
    DATA = load_data()
    STOPS = [s for row in DATA["stops"] if (s := normalize_stop(row))]
    STOP_BY_ID = {s["stop_id"]: s for s in STOPS}
    ROUTES = DATA["routes"]
    ROUTE_BY_ID = {r.get("route_id", ""): r for r in ROUTES}
    TRIP_BY_ID = {t.get("trip_id", ""): t for t in DATA.get("trips", [])}
    TRIPS_BY_ROUTE = defaultdict(list)
    for trip in DATA.get("trips", []):
        TRIPS_BY_ROUTE[trip.get("route_id", "")].append(trip)
    STOP_TIMES_BY_STOP = defaultdict(list)
    STOP_TIMES_BY_TRIP = defaultdict(list)
    for row in DATA.get("stop_times", []):
        STOP_TIMES_BY_STOP[row.get("stop_id", "")].append(row)
        STOP_TIMES_BY_TRIP[row.get("trip_id", "")].append(row)
    for rows in list(STOP_TIMES_BY_STOP.values()) + list(STOP_TIMES_BY_TRIP.values()):
        rows.sort(key=lambda r: int(r.get("stop_sequence", 0) or 0))
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
    return {"stops": len(STOPS), "routes": len(ROUTES), "trips": len(DATA.get("trips", [])), "source": DATA.get("source", "loading")}

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

@app.get("/api/stops/{stop_id}/routes")
def routes_at_stop(stop_id: str):
    if stop_id not in STOP_BY_ID:
        return {"stop": None, "routes": []}
    route_trip_ids = set()
    for stop_time in STOP_TIMES_BY_STOP.get(stop_id, []):
        trip = TRIP_BY_ID.get(stop_time.get("trip_id", ""))
        if trip:
            route_trip_ids.add(trip.get("route_id", ""))
    result = []
    for route_id in sorted(route_trip_ids, key=lambda rid: (ROUTE_BY_ID.get(rid, {}).get("route_short_name", ""))):
        route = ROUTE_BY_ID.get(route_id)
        if not route:
            continue
        trip_ids = [t.get("trip_id") for t in TRIPS_BY_ROUTE.get(route_id, [])]
        # Summarize route directions from trips that actually visit the chosen stop.
        directions = sorted({TRIP_BY_ID[st.get("trip_id", "")].get("trip_headsign", "") for st in STOP_TIMES_BY_STOP[stop_id] if TRIP_BY_ID.get(st.get("trip_id", ""), {}).get("route_id") == route_id and TRIP_BY_ID.get(st.get("trip_id", ""), {}).get("trip_headsign")})
        result.append({**_route_public(route), "directions": directions, "trip_count": len(trip_ids)})
    return {"stop": STOP_BY_ID[stop_id], "routes": result}

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
