# Universal Website Data Extractor - Developer Onboarding & Setup Guide

Welcome to the developer setup guide for the **Universal Website Data Extractor**. This document provides step-by-step instructions to configure, run, test, and troubleshoot the project on a fresh development machine.

---

## 1. System Requirements & Prerequisites

Before setting up the project, ensure your environment meets the following requirements:

| Tool / Requirement | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `3.11.0+` | Core programming language runtime. |
| **Git** | `2.30+` | Version control system. |
| **SQLite** | Included with Python | Default zero-configuration database driver (`aiosqlite`). |
| **PostgreSQL** *(Optional)* | `14.0+` | Production database server (used when `USE_SQLITE=false`). |
| **Playwright** | Chromium driver | Headless browser engine for JavaScript rendering. |

---

## 2. Obtain Source Code

Download or clone the project repository into your local working directory and navigate to the project root:

```text
e:/web-scraper/
```

---

## 3. Create Virtual Environment

Creating an isolated Python virtual environment ensures that project dependencies do not conflict with system-wide Python packages.

### Create Environment
```bash
python -m venv .venv
```

### Activate Environment

#### On Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
.venv\Scripts\activate.bat
```

#### On Linux / macOS:
```bash
source .venv/bin/activate
```

---

## 4. Install Dependencies & Playwright Browsers

### Step A: Install Package Dependencies
Install the application and development dependencies in editable mode:

```bash
pip install -e .[dev]
```

### Step B: Install Playwright Chromium Driver
The crawler uses Playwright for dynamic JavaScript rendering. Install the headless Chromium browser binary:

```bash
playwright install chromium
```

---

## 5. Configure Environment Variables

The application reads configuration parameters from `.env`. A template is provided in `.env.example`.

Copy `.env.example` to create `.env`:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

### Environment Variable Reference

| Variable | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `PROJECT_NAME` | Optional | `Universal Website Data Extractor` | Title displayed in OpenAPI docs. |
| `VERSION` | Optional | `0.1.0` | Release version string. |
| `DEBUG` | Optional | `true` | Enables debug logging and SQL query echo. |
| `API_V1_STR` | Optional | `/api/v1` | Base route prefix for APIs. |
| `USE_SQLITE` | Required | `true` | Set `true` for instant SQLite execution. |
| `SQLITE_DB_PATH` | Optional | `./web_scraper.db` | Relative file path for local SQLite storage. |
| `POSTGRES_SERVER` | Optional | `localhost` | PostgreSQL host address. |
| `POSTGRES_PORT` | Optional | `5432` | PostgreSQL port number. |
| `POSTGRES_USER` | Optional | `postgres` | PostgreSQL username. |
| `POSTGRES_PASSWORD` | Optional | `postgres_password` | PostgreSQL user password. |
| `POSTGRES_DB` | Optional | `web_scraper_db` | PostgreSQL database name. |
| `DEFAULT_MAX_DEPTH` | Optional | `2` | Default crawl depth limit (0-10). |
| `DEFAULT_MAX_PAGES` | Optional | `50` | Default page count limit (1-500). |
| `DEFAULT_CRAWL_DELAY_SEC` | Optional | `0.5` | Politeness delay between HTTP requests (sec). |
| `FETCH_TIMEOUT_SEC` | Optional | `15.0` | HTTP request timeout threshold (sec). |
| `PLAYWRIGHT_HEADLESS` | Optional | `true` | Launches Chromium in headless background mode. |

---

## 6. Database Setup

### Option A: SQLite (Recommended Default)
The application is pre-configured with `USE_SQLITE=true` in `.env`. SQLite requires **zero manual database server installation**. The database file (`./web_scraper.db`) is automatically created when the backend starts up.

### Option B: PostgreSQL (Optional Production Setup)
To use PostgreSQL instead of SQLite:

1. Ensure PostgreSQL service is running on `localhost:5432`.
2. Create target database: `web_scraper_db`.
3. Update `.env`:
   ```ini
   USE_SQLITE=false
   POSTGRES_SERVER="localhost"
   POSTGRES_PORT=5432
   POSTGRES_USER="postgres"
   POSTGRES_PASSWORD="your_actual_password"
   POSTGRES_DB="web_scraper_db"
   ```

---

## 7. Run the Application

Start the local Uvicorn ASGI server:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Startup Output
```text
INFO:     Will watch for changes in these directories: ['E:\\web-scraper']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process using WatchFiles
INFO:     Started server process
INFO:     Waiting for application startup.
2026-08-05 10:00:00 | INFO     | web_scraper:lifespan:32 - Initializing database tables...
2026-08-05 10:00:00 | INFO     | web_scraper:lifespan:35 - Database tables initialized successfully.
INFO:     Application startup complete.
```

### Access URLs
- 🖥️ **SaaS Web Dashboard**: `http://localhost:8000/app`
- 📖 **Interactive Swagger UI**: `http://localhost:8000/docs`
- 📄 **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 8. Verification Checklist

Run through these quick checks to ensure everything is operating correctly:

- [ ] **Backend Health Check**: Open `http://localhost:8000/` in browser; returns `{"status": "online", ...}`.
- [ ] **Swagger UI**: Open `http://localhost:8000/docs`; loads interactive API documentation.
- [ ] **Web Dashboard**: Open `http://localhost:8000/app`; loads single-page SaaS interface.
- [ ] **Test Crawl**: Enter `https://news.ycombinator.com`, set max depth 1, pages 5, and click **Start Crawling**.
- [ ] **Data Export**: After crawl completion, click **Export JSON** to verify file download.

---

## 9. Running Automated Tests

The repository includes a unit and integration test suite built with Pytest and `pytest-asyncio`.

### Run Complete Test Suite
```bash
pytest -v
```

### Expected Output
```text
tests/integration/test_crawl_api.py .....                                [ 41%]
tests/unit/test_html_extractor.py .                                      [ 50%]
tests/unit/test_url_utils.py ......                                      [100%]

============================= 12 passed in 18.26s =============================
```

---

## 10. Common Errors & Troubleshooting

### Issue 1: `Playwright package is not installed` or browser fails to launch
- **Cause**: Playwright browser binaries are missing.
- **Solution**: Run `playwright install chromium` in your activated virtual environment.

### Issue 2: `asyncpg.exceptions.InvalidPasswordError`
- **Cause**: Application is trying to connect to PostgreSQL with incorrect password credentials.
- **Solution**: Set `USE_SQLITE=true` in `.env` for zero-config local testing, or update `POSTGRES_PASSWORD` with your local PostgreSQL password.

### Issue 3: `Address already in use` (Port 8000 occupied)
- **Cause**: Another process is already running on port 8000.
- **Solution**: Change port when running Uvicorn: `uvicorn src.main:app --reload --port 8001`.

---

## 11. Frequently Asked Questions (FAQ)

### Q: Why is SQLite enabled by default?
**A**: To allow developers, reviewers, and hiring managers to run and evaluate the application instantly without needing to install or configure PostgreSQL.

### Q: When should PostgreSQL be used?
**A**: In production environments requiring high concurrent database reads/writes and distributed worker access.

### Q: Why does the first Playwright crawl take slightly longer?
**A**: Playwright initializes headless Chromium browser instances lazily on the first request. Subsequent fetches reuse active browser contexts.
