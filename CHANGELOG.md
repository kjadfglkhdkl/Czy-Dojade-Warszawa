# Changelog
## 0.1.0
- Naprawienie łączenia z API
- Usunięcie metody z dockerem, zastąpenie ją inną, lepszą.
## 0.20
- Naprawienie błędu z portem localhost-owym
- Lekkie poprawki w plikach python
## 0.3.0
- Naprawienie błędnego wczytywania modułów w `start.bat`
- Dodanie funkcjonalności linii
## 1.0
- Możliwość wyszukiwania przystanku oraz wyświetlanie tras go obsługujących na podstawie danych GTFS (pliki `stop_times` i `trips`).
- Możliwość zwinięcia ogólnego katalogu tras.
- Wyświetlanie przebiegu trasy na mapie; w przypadku braku pliku `shapes.txt` geometria jest generowana na podstawie sekwencji współrzędnych przystanków.
- Wybór wariantu/kierunku przejazdu i wyświetlenie listy przystanków dla danej trasy.
- Ulepszony przykładowy zestaw danych offline do celów demonstracyjnych.
