# Smart Price Tracker

Automatyczna aplikacja webowa do monitorowania cen produktów w sklepach internetowych (np. Notino.pl) z intuicyjnym interfejsem graficznym i interaktywnymi wykresami historii zmian cen.

---

## Główna funkcjonalność

* **Automatyczne pobieranie cen (Scraping):** Wykorzystuje bibliotekę `curl_cffi` z natywną impersonacją kryptograficznych podpisów TLS/JA3 prawdziwych przeglądarek (Chrome / Safari) oraz `BeautifulSoup4`, co pozwala na błyskawiczne pobieranie danych i omijanie systemów Anti-Bot (np. Cloudflare Turnstile) bez konieczności uruchamiania ciężkich przeglądarek.
* **Interaktywne wykresy historii cen:** Wykresy liniowe generowane przy pomocy **Chart.js** – zarówno na kartach produktów (mini-wykresy *sparkline* z trendem zmiany ceny), jak i w szczegółowym oknie modalnym.
* **Cykliczna synchronizacja w tle:** Zintegrowany harmonogram **APScheduler** automatycznie sprawdza i zapisuje aktualne ceny wszystkich śledzonych produktów co 2 godziny.
* **Odporność na błędy i Race Conditions:** Bezpieczny zapis do bazy PostgreSQL z automatyczną obsługą konfliktów (`IntegrityError`) oraz logowaniem błędów scrapowania do osobnej tabeli (`ErrorLog`).
* **Czysty interfejs (Vanilla JS/CSS):** Lekki frontend bez konieczności budowania czy instalowania ciężkich frameworków – gotowy do działania od razu po uruchomieniu serwera API.

---

## Stack technologiczny

| Warstwa | Technologie                                                 |
| :--- |:------------------------------------------------------------|
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy, Pydantic, Uvicorn         |
| **Scraper** | curl_cffi (impersonacja TLS Chrome/Safari) & BeautifulSoup4 |
| **Baza danych** | PostgreSQL 15 (Alpine)                                      |
| **Zadania w tle** | APScheduler (BackgroundScheduler)                           |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js 4.4               |
| **Infrastruktura** | Docker & Docker Compose                                     |

---

## Szybki start

### Wymagania wstępne

* Zainstalowany **Docker** oraz **Docker Compose**.

### 1. Uruchomienie aplikacji

W głównym katalogu projektu uruchom kontenery:

```bash
docker compose up --build -d
```

### 2. Otwórz aplikację w przeglądarce

Po zakończeniu budowania przejdź do jednego z poniższych adresów:

* 🌐 **Tropiciel cen:** http://localhost:8000
* 📖 **Dokumentacja API (Swagger):** http://localhost:8000/docs
