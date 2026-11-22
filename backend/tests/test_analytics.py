from app.data import distance_m, normalize_stop

def test_distance_same_point_is_zero():
    assert distance_m(52.2, 21.0, 52.2, 21.0) == 0

def test_distance_warsaw_points_reasonable():
    d = distance_m(52.2297, 21.0122, 52.2200, 21.0100)
    assert 900 < d < 1200

def test_normalize_stop_valid():
    stop = normalize_stop({"stop_id": "a", "stop_name": "Stop", "stop_lat": "52.2", "stop_lon": "21.0"})
    assert stop["name"] == "Stop"
    assert stop["lat"] == 52.2

def test_normalize_stop_invalid_coordinate():
    assert normalize_stop({"stop_lat": "abc", "stop_lon": "21"}) is None


def test_related_stop_ids_includes_child_platforms_for_parent_station():
    from app.main import related_stop_ids
    stops = {"station": {"stop_id": "station"}, "platform_a": {"stop_id": "platform_a"}, "platform_b": {"stop_id": "platform_b"}}
    children = {"station": ["platform_a", "platform_b"]}
    assert related_stop_ids("station", stops, children) == ["station", "platform_a", "platform_b"]


def test_related_stop_ids_for_platform_returns_only_selected_platform():
    from app.main import related_stop_ids
    stops = {"station": {"stop_id": "station"}, "platform_a": {"stop_id": "platform_a"}}
    children = {"station": ["platform_a"]}
    assert related_stop_ids("platform_a", stops, children) == ["platform_a"]


def test_related_stop_ids_unknown_stop_is_empty():
    from app.main import related_stop_ids
    assert related_stop_ids("missing", {}, {}) == []


def test_api_routes_at_parent_station_aggregates_child_platforms(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as api
    fixture = {
        "stops": [
            {"stop_id": "station", "stop_name": "Test Station", "stop_lat": "52.2", "stop_lon": "21.0", "location_type": "1"},
            {"stop_id": "platform_a", "stop_name": "Platform A", "stop_lat": "52.201", "stop_lon": "21.001", "parent_station": "station", "location_type": "0"},
            {"stop_id": "platform_b", "stop_name": "Platform B", "stop_lat": "52.202", "stop_lon": "21.002", "parent_station": "station", "location_type": "0"},
        ],
        "routes": [{"route_id": "r1", "route_short_name": "17", "route_type": "0"}],
        "trips": [{"trip_id": "trip1", "route_id": "r1", "trip_headsign": "Test Direction", "shape_id": ""}],
        "stop_times": [{"trip_id": "trip1", "stop_id": "platform_a", "stop_sequence": "1"}],
        "shapes": [], "source": "test fixture",
    }
    monkeypatch.setattr(api, "load_data", lambda: fixture)
    with TestClient(api.app) as client:
        response = client.get("/api/stops/station/routes")
        assert response.status_code == 200
        payload = response.json()
        assert payload["matched_stop_ids"] == ["station", "platform_a", "platform_b"]
        assert [r["short_name"] for r in payload["routes"]] == ["17"]
        assert payload["routes"][0]["directions"] == ["Test Direction"]


def test_api_departures_endpoint_filters_by_calendar_and_returns_times(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as api
    fixture = {
        "stops": [{"stop_id": "s", "stop_name": "Test Stop", "stop_lat": "52.2", "stop_lon": "21.0"}],
        "routes": [{"route_id": "r", "route_short_name": "17", "route_type": "0"}],
        "trips": [{"trip_id": "t", "route_id": "r", "service_id": "weekday", "trip_headsign": "Test Direction", "shape_id": ""}],
        "stop_times": [{"trip_id": "t", "stop_id": "s", "stop_sequence": "1", "arrival_time": "08:10:00", "departure_time": "08:10:00"}],
        "calendar": [{"service_id": "weekday", "monday": "1", "tuesday": "0", "wednesday": "0", "thursday": "0", "friday": "0", "saturday": "0", "sunday": "0", "start_date": "20260101", "end_date": "20261231"}],
        "calendar_dates": [], "shapes": [], "source": "test fixture",
    }
    monkeypatch.setattr(api, "load_data", lambda: fixture)
    with TestClient(api.app) as client:
        monday = client.get("/api/stops/s/departures?date=2026-11-23")
        tuesday = client.get("/api/stops/s/departures?date=2026-11-24")
        assert monday.status_code == 200
        assert monday.json()["departures"][0]["departure_display"] == "08:10"
        assert monday.json()["departures"][0]["route_short_name"] == "17"
        assert tuesday.json()["departures"] == []
