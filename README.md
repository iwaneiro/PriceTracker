# Smart Price Tracker

An automated web application for tracking e-commerce product prices (e.g., Notino) featuring an intuitive UI and interactive price history charts.

---

## Key Features

* **Automated Price Scraping:** Uses `curl_cffi` with native TLS/JA3 cryptographic fingerprint impersonation (Chrome/Safari) and `BeautifulSoup4`, enabling lightning-fast data extraction and bypassing Anti-Bot systems (e.g., Cloudflare Turnstile) without running heavy headless browsers.
* **Interactive Price History Charts:** Line charts generated with **Chart.js** — displayed both as mini sparkline trend indicators on product cards and in a detailed modal view.
* **Background Synchronization:** An integrated **APScheduler** background job automatically checks and records current prices for all tracked products every 2 hours.
* **Fault Tolerance & Race Condition Handling:** Safe PostgreSQL writes with automatic database conflict resolution (`IntegrityError`) and dedicated scraping error logging (`ErrorLog`).
* **Clean UI (Vanilla JS/CSS):** A lightweight frontend served directly from the FastAPI backend with no build step or heavy frameworks required — ready to run immediately after container startup.
---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | Python 3.12, FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| **Scraper** | `curl_cffi` (Chrome/Safari TLS impersonation) & `BeautifulSoup4` |
| **Database** | PostgreSQL 15 (Alpine) |
| **Background Jobs** | APScheduler (BackgroundScheduler) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js 4.4 |
| **Infrastructure** | Docker & Docker Compose |

---

## Quick Start

### Prerequisites

* **Docker** and **Docker Compose** installed.
  
### 1. Run the Application

In the root directory of the project, start the containers in the background:

```bash
docker compose up --build -d
```

### 2. Open in Your Browser
Once the build is complete, access the application at:

* 🌐 **Price tracker UI:** http://localhost:8000
* 📖 **API Documentation (Swagger):** http://localhost:8000/docs
