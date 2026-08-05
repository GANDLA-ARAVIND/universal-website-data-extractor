# Engineering Decisions & Architectural Rationale

This document details the engineering principles, architectural patterns, technology selections, and technical trade-offs behind the **Universal Website Data Extractor**.

---

## 1. Project Vision

### Problem Statement
Simple web scraping scripts written with basic BeautifulSoup or Requests calls are typically brittle, tightly coupled, single-threaded, and unmaintainable. They fail when encountering dynamic JavaScript rendering, lack domain scoping controls, store data haphazardly, and offer no structured monitoring or data exports.

### Solution
The **Universal Website Data Extractor** is built as a production-grade software engineering application. It decouples network retrieval, feature parsing, job state orchestration, and relational data persistence using **Clean Architecture**.

### Target Use Cases
- Engineers requiring structured datasets (headings, paragraphs, tables, images, links) from public web domains.
- Data pipelines needing standard JSON, CSV, or Markdown exports.
- Resume/Portfolio demonstration of backend architecture, async concurrency, ORM modeling, and API design.

---

## 2. Core Engineering Goals

1. **Clean Architecture & Separation of Concerns**: Decouple domain logic from frameworks, UI, and external libraries.
2. **Asynchronous Non-Blocking I/O**: Utilize Python's `asyncio` to handle HTTP fetching, DOM parsing, and database transactions without thread blocking.
3. **Pluggable Fetching Strategy**: Provide transparent switching between high-throughput static HTTP requests (`httpx`) and headless browser rendering (`playwright`).
4. **Reliable Relational Persistence**: Use SQLAlchemy 2.0 Async with normalized entity schemas supporting both PostgreSQL and SQLite.
5. **Zero-Framework Responsive UI**: Provide a clean, lightweight Single Page Application (SPA) using standard HTML5, CSS3, and ES6+ Vanilla JavaScript.

---

## 3. Technology Decisions & Trade-offs

### Language: Python 3.11+
- **Why**: Excellent ecosystem for web parsing (`BeautifulSoup`, `lxml`), native `asyncio` support, and strong typing via Pydantic.
- **Trade-off**: Lower single-thread CPU execution speed compared to Go or Rust, mitigated by non-blocking I/O for network-bound workloads.

### Backend: FastAPI
- **Why**: Native ASGI performance, automatic OpenAPI/Swagger generation, standard Pydantic validation, and dependency injection framework.
- **Alternatives**: Flask (WSGI, synchronous), Django (heavyweight for an API-first service).

### Web Fetchers: HTTPX & Playwright
- **HTTPX**: Used for static HTML pages. Fast, lightweight, asynchronous.
- **Playwright**: Used for dynamic JavaScript SPAs (React, Vue, Angular). Launches headless Chromium to render the client DOM.
- **Trade-off**: Playwright consumes significantly more CPU/RAM and has higher latency per page compared to HTTPX. Providing a toggle switch allows users to choose the optimal engine per job.

### HTML Parsing: BeautifulSoup4 with LXML
- **Why**: `lxml` C-bindings provide high-speed HTML parsing with tolerant handling of malformed web markup, with automatic fallback to standard `html.parser`.

### Database: PostgreSQL & SQLAlchemy 2.0 Async (with SQLite fallback)
- **PostgreSQL (`asyncpg`)**: Production-grade relational database with JSONB support, strict foreign keys, and non-blocking drivers.
- **SQLite (`aiosqlite`)**: Supported via `USE_SQLITE=true` in `.env` for zero-dependency local development and testing.

### Frontend: Vanilla JavaScript, HTML5, Vanilla CSS3
- **Why**: Zero build steps (no npm, Webpack, or Vite required), lightweight asset size (<50KB total), fast loading, and broad browser compatibility.
- **Trade-off**: Manual DOM updates compared to reactive frameworks like React, mitigated by modular DOM renderer functions in `app.js`.

---

## 4. Architectural Patterns

### Clean Architecture
Divided into isolated layers:
- `core/`: Application settings (`Pydantic BaseSettings`), logging, and domain exceptions.
- `db/`: ORM entities (`CrawlJob`, `ExtractedPage`, `PageLink`, `PageImage`, `CrawlStatistic`) and async database session management.
- `crawler/`: Fetcher strategies, HTML feature extractor, and `CrawlEngine` BFS loop.
- `application/`: High-level business use cases (`CrawlService`, `ExportService`).
- `api/`: REST endpoints and dependency injection providers.

### Repository Pattern (`CrawlRepository`, `PageRepository`)
Abstracts database operations away from the crawler engine and API routes. Switching database drivers or modifying queries requires zero changes to core business logic.

### Strategy Pattern (`BaseFetcher`, `StaticFetcher`, `DynamicFetcher`)
Defines a unified interface `async fetch(url: str) -> FetchResult`. The `CrawlEngine` interacts strictly with `BaseFetcher`, making fetcher implementations completely interchangeable.

### Dependency Injection
FastAPI's `Depends()` injects database sessions (`get_async_db`) and service instances (`get_crawl_service`, `get_export_service`), managing resource lifecycles cleanly.

---

## 5. Crawling Decisions

### Breadth-First-Search (BFS) Traversal
- **Why**: BFS explores pages level-by-level (depth 0 -> depth 1 -> depth 2), ensuring that shallow, high-value pages are indexed before deep subpages.
- **Implementation**: Uses Python's `collections.deque` holding `(current_url, current_depth)` tuples.

### Domain Scoping & Canonical Normalization
- Enforces same-domain crawling by comparing normalized top-level hostnames (`is_same_domain`).
- Strips URL fragments (`#anchor`), converts hostnames to lowercase, sorts query parameters (`?a=1&b=2`), and strips trailing slashes to prevent duplicate crawls.

### Polite Crawl Delay
- Enforces an asynchronous `await asyncio.sleep(crawl_delay)` between consecutive requests to prevent overwhelming target web servers.

---

## 6. Database Decisions

### Schema Normalization
- `crawl_jobs`: Tracks job lifecycle (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), configuration, and timestamps.
- `extracted_pages`: Stores page metadata, title, description, headings, paragraphs, lists, and tables as JSONB/JSON.
- `page_links`: Stores discovered internal/external hyperlinks with anchor text.
- `page_images`: Stores extracted image URLs and `alt` text.
- `crawl_statistics`: Tracks aggregate metrics (`pages_crawled`, `failed_pages`, `total_images`, `total_links`, `total_duration_sec`).

### Cascading Deletes
All child tables (`extracted_pages`, `page_links`, `page_images`, `crawl_statistics`) define `ForeignKey(..., ondelete="CASCADE")`, ensuring clean data purging when a job is deleted.

---

## 7. API Decisions

### Asynchronous Endpoint Execution
`POST /api/v1/crawl` returns `202 Accepted` immediately, delegating the crawl loop to FastAPI's `BackgroundTasks`. This keeps HTTP responses fast and prevents gateway timeouts.

### Short Polling vs WebSockets
- **Decision**: Short polling (`GET /api/v1/crawl/{job_id}` every 1.5s) was selected for the MVP.
- **Rationale**: Dramatically simplifies client-side state management without requiring persistent WebSocket connection handling or reconnect logic.

### Streamed File Exports
`POST /api/v1/crawl/{job_id}/export` formats datasets in-memory and returns a `StreamingResponse` with `Content-Disposition: attachment`, allowing native browser file downloads.

---

## 8. Frontend Decisions

### Single Page Application (SPA)
Consolidates configuration, live progress, live activity console, statistics, search/sorting, result accordions, and export actions into a single fluid page.

### Live Activity Console
Appends timestamped log lines to an auto-scrolling terminal box (`#activity-log`), giving users visibility into crawl milestones (*Connecting*, *Fetched page*, *Discovered links*, *Saved data*).

### Client-Side Search & Sorting
Allows instant filtering by title/URL/content and sorting by *URL*, *Title*, *Response Time*, *Links Count*, or *Images Count* without re-fetching data from the backend.

---

## 9. Error Handling & Validation

### Strict Input Boundary Validation
`CrawlCreateRequest` validates target URLs using a custom Pydantic validator (`validate_public_url`), rejecting invalid schemes (e.g. `ftp://`, `file://`, `javascript:`) before network requests are initiated.

### Custom Exception Hierarchy
Extends `BaseAppException` into `InvalidURLException` (HTTP 400), `CrawlJobNotFoundException` (HTTP 404), and `ExportException` (HTTP 400), handled globally by FastAPI's `exception_handler`.

---

## 10. Performance & Resource Allocation

### Asynchronous Concurrency
Network I/O operations execute concurrently using `asyncio`, allowing latency-bound HTTP requests to run efficiently.

### Memory Considerations
URL set deduplication and BFS queues are bounded by `max_pages` and `max_depth` configuration parameters to prevent uncontrolled memory growth.

---

## 11. Security Considerations

### Server-Side Request Forgery (SSRF) Prevention
Validates target URL schemes to enforce public HTTP and HTTPS protocols only.

### CORS Middleware
Configured in `src/main.py` allowing cross-origin requests from web dashboards.

### Deferred Authentication
Authentication (JWT / API Keys) was intentionally excluded from the MVP scope to focus on core crawling mechanics and data extraction.

---

## 12. Solved Engineering Challenges

1. **Playwright Event Loop Integration**: Running Playwright browser instances within Python's `asyncio` event loop required lazy browser initialization (`_ensure_browser`) and explicit browser context closing to prevent resource leaks.
2. **Database Session Scoping in Background Tasks**: FastAPI background tasks outlive the original HTTP request session context. Solved by instantiating an isolated `AsyncSessionFactory` within `_run_crawl_in_background`.
3. **Canonical Link Resolution**: Relative links (e.g., `<a href="../about">`) are resolved against the base page URL using `urllib.parse.urljoin` before normalization.

---

## 13. Lessons Learned

- **Decoupling Parsing from Traversal**: Isolating `HTMLExtractor` into a pure, side-effect-free class simplified unit testing with Pytest.
- **SQLite Fallback Value**: Supporting SQLite via `aiosqlite` drastically simplified local development and CI testing environments.

---

## 14. Future Architectural Evolution

The Clean Architecture foundation enables future enterprise scaling:
- **Distributed Crawler Queue**: Replacing FastAPI `BackgroundTasks` with **Celery** workers and **Redis** queues.
- **Distributed Deduplication**: Moving in-memory visited sets to **Redis Sets**.
- **JWT Authentication**: Securing API endpoints with user accounts and project isolation.
- **Robots.txt & Sitemap Parsing**: Automatically parsing `sitemap.xml` for URL discovery.
- **Containerization**: Packaging backend, Playwright dependencies, and PostgreSQL into `docker-compose.yml`.
