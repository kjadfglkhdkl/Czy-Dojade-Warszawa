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
