# Data Dictionary

**Document ID:** DAT-001  
**Version:** 1.0  
**Author:** Tomasz Krasula
**Date:** 2026-11-19

| Pole | Nazwa pliku | Znaczenie |
|---|---|---|
| stop_id | stops.txt | Unikalny identyfikator przystanku |
| stop_name | stops.txt | Nazwa przystanku |
| stop_lat | stops.txt | Szerokość geograficzna |
| stop_lon | stops.txt | Długość geograficzna |
| route_id | routes.txt | Identyfikator trasy |
| route_short_name | routes.txt | Publiczne oznaczenie trasy |
| route_long_name | routes.txt | Opis trasy |
| route_type | routes.txt | Kod środka transportu (według standardu GTFS) |
| trip_id | trips.txt | Identyfikator kursu |
| stop_times | stop_times.txt | Zaplanowane zdarzenia na przystankach |

Liczby odnoszą się do rekordów w całym zbiorze danych (feedzie). Zbiór może zawierać duplikaty, dane dla wielu peronów lub przystanki położone poza granicami Warszawy. Przed wyciągnięciem wniosków mających znaczenie dla polityki miejskiej należy zweryfikować dane.