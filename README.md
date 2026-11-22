# Czy dojadę? — Warszawa

Open-source dashboard do analizy dostępności komunikacji miejskiej w Warszawie, oparty o dane GTFS. Projekt działa lokalnie **bez Dockera**.
# PRZED URUCHOMIENIEM 
Rozpakuj frontend.zip, stwórz nowy folder src, wrzuć do niego frontend i backend 
## Wymagania
- Windows 10/11
- Python 3.10+ (zaznacz opcję dodania Pythona do PATH lub używaj `py`)
- Node.js LTS (npm)
- Internet przy pierwszym uruchomieniu i pobieraniu aktualnych danych GTFS

## Szybkie uruchomienie Windows
1. Zainstaluj Python i Node.js, jeśli nie masz ich na komputerze.
2. Kliknij dwukrotnie `start.bat`. Skrypt otworzy dwa okna terminala, z backendem i frontendem.
3. W przeglądarce otwórz **http://127.0.0.1:5174**.

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
## Rozwiązywanie problemów (Windows)

- Sprawdzenie API: otwórz `http://127.0.0.1:8000/api/health` (powinno zwrócić obiekt JSON z wartością `status: ok`).
- Punkt końcowy przystanków (stops): `http://127.0.0.1:8000/api/stops?limit=10` (powinno zwrócić tablicę JSON).
- Interfejs użytkownika (frontend): `http://127.0.0.1:5174`. Frontend przekierowuje (proxy) zapytania kierowane do `/api` na serwer API.
- Jeśli pobieranie danych GTFS zakończy się niepowodzeniem (z powodu problemów z siecią lub niedostępności źródła), backend automatycznie użyje dołączonych przykładowych danych o przystankach, dzięki czemu aplikacja pozostanie funkcjonalna. Pole `source` w API wskaże, że używane są lokalne, przykładowe dane.
- Jeśli zbiorczy skrypt uruchomieniowy nie utrzymuje otwartych obu okien terminala, uruchom `start-api.bat` oraz `start-frontend.bat` oddzielnie.


## Weryfikacja połączenia z API (Windows)

Interfejs użytkownika (frontend) komunikuje się teraz bezpośrednio z lokalnym API pod adresem `http://127.0.0.1:8000/api`. Funkcja CORS jest włączona dla interfejsu użytkownika na porcie 5174. Sprawdź te adresy URL, gdy działają oba skrypty startowe:

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/api/stops?limit=5`
- Frontend: `http://127.0.0.1:5174`

## Diagnostyka połączenia (wersja bez Dockera)

- Strona: http://127.0.0.1:5174
- Stan API: http://127.0.0.1:8000/api/health
- Przystanki: http://127.0.0.1:8000/api/stops?limit=5
- Linie: http://127.0.0.1:8000/api/routes
- Dokumentacja API: http://127.0.0.1:8000/docs

Frontend wysyła zapytanie pod względnym adresem `/api`. Vite przekazuje je do FastAPI (`127.0.0.1:8000`) przez proxy, dzięki czemu omijamy problemy CORS. Jeżeli strona jest otwarta na porcie 5174, punkt końcowy `/api/routes` powinien odpowiadać na `http://127.0.0.1:5174/api/routes`.

## Nowe funkcje: wyszukiwanie przystanków i mapy tras

- Wyszukaj nazwę przystanku, wybierz sugestię i zobacz numery tras obsługujących ten przystanek.
- Katalog tras można składać i przeszukiwać.
- Kliknięcie trasy ładuje wzór podróży i rysuje jej geometrię na mapie.
- Jeśli w przypadku podróży brakuje pliku „shapes.txt” GTFS, podgląd trasy powraca do współrzędnych przystanku zamówionych z „stop_times.txt”.
- Punkt końcowy: `GET /api/stops/{stop_id}/routes`; punkt końcowy: `GET /api/routes/{route_id}/map`.
