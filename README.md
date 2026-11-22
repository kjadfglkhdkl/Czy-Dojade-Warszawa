# Czy dojadę? — Warszawa

Open-source dashboard do analizy dostępności komunikacji miejskiej w Warszawie, oparty o dane GTFS. Projekt działa lokalnie **bez Dockera**.
# PRZED URUCHOMIENIEM 
Odpakuj frontend.zip, stwórz nowy folder src, wrzuć do niego frontend i backend 
## Wymagania
- Windows 10/11
- Python 3.10+ (zaznacz opcję dodania Pythona do PATH lub używaj `py`)
- Node.js LTS (npm)
- Internet przy pierwszym uruchomieniu i pobieraniu aktualnych danych GTFS

## Szybkie uruchomienie Windows
1. Rozpakuj ZIP.
2. Zainstaluj Python i Node.js, jeśli nie masz ich na komputerze.
3. Kliknij dwukrotnie `start.bat`. Skrypt otworzy dwa okna terminala, z backendem i frontendem.
4. W przeglądarce otwórz **http://127.0.0.1:5174**.

Przy pierwszym uruchomieniu backend utworzy środowisko Python i zainstaluje zależności. Frontend pobierze paczki npm. To może chwilę potrwać.

## Uruchomienie ręczne
### API (terminal 1)
```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app
```
API: http://127.0.0.1:8000  
Dokumentacja Swagger: http://127.0.0.1:8000/docs

### Frontend (terminal 2)
```powershell
cd frontend
npm install
npm run dev
```
Frontend: http://127.0.0.1:5174

## API
- `GET /api/health` — status serwera
- `GET /api/stats` — statystyki danych
- `GET /api/stops?search=&limit=` — wyszukiwanie przystanków
- `GET /api/routes` — lista tras
- `GET /api/nearest?lat=&lon=&radius_m=` — przystanki w promieniu
- `GET /api/districts` — endpoint dzielnic (obecnie placeholder)

## Dane
Feed GTFS Warszawa pobierany przez skrypt `scripts/download_gtfs.py`. Jeżeli pobranie nie powiedzie się, aplikacja wykorzystuje przykładowy zestaw danych do demonstracji.

## Testy backendu
W folderze `backend` (po aktywacji `.venv`):
```powershell
pytest
```

## Uwaga
GTFS to rozkład statyczny — nie pokazuje na żywo opóźnień. Odległości są liczone w linii prostej, a nie jako trasa piesza. Sprawdź licencję/warunki feedu i wymagania atrybucji przed publicznym wdrożeniem.

## Troubleshooting (Windows)

- API check: open `http://127.0.0.1:8000/api/health` (should return JSON and `status: ok`).
- Stops endpoint: `http://127.0.0.1:8000/api/stops?limit=10` (should return a JSON array).
- Frontend: `http://127.0.0.1:5174`. Frontend proxies `/api` requests to the API server.
- If GTFS download fails (network or source unavailable), backend automatically uses the bundled sample stops so the app remains usable. The API's `source` field will indicate offline sample data.
- Run `start-api.bat` and `start-frontend.bat` separately if the combined launcher doesn't keep both terminals open.


## API connection check (Windows)

The frontend now calls the local API directly at `http://127.0.0.1:8000/api`. CORS is enabled for the frontend on port 5174. Check these URLs while both start scripts are running:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/stops?limit=5`
- Frontend: `http://127.0.0.1:5174`

## Diagnostyka połączenia (wersja bez Dockera)

- Strona: http://127.0.0.1:5174
- API status: http://127.0.0.1:8000/api/health
- Przystanki: http://127.0.0.1:8000/api/stops?limit=5
- Linie: http://127.0.0.1:8000/api/routes
- Dokumentacja API: http://127.0.0.1:8000/docs

Frontend wysyła zapytania pod względnym adresem `/api`. Vite przekazuje je do FastAPI (`127.0.0.1:8000`) przez proxy, dzięki czemu omijamy problemy CORS. Jeśli strona jest otwarta na porcie 5174, endpoint `/api/routes` powinien odpowiadać na `http://127.0.0.1:5174/api/routes`.

## New features: stop-route search and route maps

- Search a stop name, select a suggestion, and see route numbers serving it.
- Route catalog is collapsible and searchable.
- Clicking a route loads a trip pattern and draws its geometry on the map.
- When GTFS `shapes.txt` is missing for a trip, route preview falls back to ordered stop coordinates from `stop_times.txt`.
- Endpoint: `GET /api/stops/{stop_id}/routes`; endpoint: `GET /api/routes/{route_id}/map`.
