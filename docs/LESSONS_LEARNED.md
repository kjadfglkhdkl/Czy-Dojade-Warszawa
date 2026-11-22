# Wyciągnięte wnioski

**Identyfikator dokumentu:** LRN-001
**Wersja:** 1.0
**Autor:** Tomasz Krasula
**Data:** 2026-11-19

## Co zadziałało dobrze
- Zastosowanie standardowego formatu danych GTFS
- Rozdzielenie API od warstwy frontendowej
- Uruchamianie aplikacji w kontenerach
- Wykorzystanie niewielkich zestawów danych testowych (fixtures)

## Co nie zadziałało
- Podejście oparte na technologii Docker (wymaga zmiany na inne rozwiązanie)
- Niektóre połączenia z API we wcześniejszych wersjach

## Co zrobiłbym inaczej
- Wcześniejsza walidacja kolumn w danych wejściowych
- Ustalenie kontraktów API przed rozpoczęciem integracji frontendu
- Nadanie priorytetu stworzeniu niewielkiego produktu minimalnie użytecznego (MVP)
- Przetestowanie procesu uruchamiania na innym komputerze

## Rekomendacje
- Zapewnienie widoczności informacji o autorstwie oraz licencji danych
- Unikanie dodawania dużych archiwów danych do repozytorium
- Regularne testowanie procesu odświeżania danych
- Uczciwe dokumentowanie ograniczeń systemu