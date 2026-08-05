# Portfolio Showcase & Technical Interview Preparation Guide

This document provides ready-to-use resume content, social media descriptions, portfolio summaries, interview pitches, and **20 in-depth technical interview questions and answers** covering the architecture and implementation of the **Universal Website Data Extractor**.

---

## 1. Resume Content (ATS-Optimized)

### Project Title
**Universal Website Data Extractor** | *Python, FastAPI, Playwright, BeautifulSoup4, SQLAlchemy Async, PostgreSQL, Vanilla JS*

### Short Description
Engineered a production-grade, asynchronous web crawling and structural data extraction platform capable of rendering static HTML and dynamic JavaScript SPAs, persisting normalized relational datasets, and delivering on-demand multi-format exports (JSON, CSV, Markdown).

### High-Impact Resume Bullet Points
- **Architected scalable async crawler**: Designed a Clean Architecture web extraction engine in Python using FastAPI and `asyncio`, enabling non-blocking BFS domain-isolated traversal across static and dynamic Single Page Applications (SPAs).
- **Engineered dual-engine fetching strategy**: Implemented Strategy Pattern fetchers using `httpx` for high-throughput static fetching and `playwright` (headless Chromium) for dynamic JavaScript rendering, lowering page latency while maintaining full DOM extraction capability.
- **Implemented non-blocking ORM persistence**: Built a dual database storage layer using SQLAlchemy 2.0 Async (`asyncpg` for PostgreSQL, `aiosqlite` for zero-config local dev), storing extracted page headings, text, media, and links with cascading integrity constraints.
- **Developed responsive SaaS frontend & export pipeline**: Created a zero-framework Vanilla JS single-page interface with real-time log activity console, instant client-side search/filtering, and streamable multi-format dataset exporters (JSON, CSV, Markdown).

---

## 2. GitHub & Social Media Descriptions

### GitHub Repository Description
> Asynchronous web crawler and structural data extraction engine built with Python 3.11+, FastAPI, Playwright, BeautifulSoup4, SQLAlchemy 2.0 Async, PostgreSQL, and Vanilla JS SPA. Supports static/dynamic page crawling, domain scoping, and multi-format exports (JSON/CSV/MD).

### LinkedIn Project Post
> 🚀 **Project Launch: Universal Website Data Extractor**
> 
> I built an asynchronous web crawling and structural data extraction engine using **FastAPI**, **Playwright**, **BeautifulSoup4**, **SQLAlchemy 2.0 Async**, **PostgreSQL**, and **Vanilla JavaScript**.
> 
> Key Architectural Highlights:
> 🔹 **Clean Architecture**: Complete decoupling of presentation, application services, crawler domain engine, and database repositories.
> 🔹 **Pluggable Fetching Strategy**: Seamlessly switch between high-speed static fetching (`HTTPX`) and dynamic JavaScript DOM rendering (`Playwright`).
> 🔹 **Structural Extraction**: Automatically parses headings, paragraphs, lists, tables, media assets, and internal/external hyperlinks.
> 🔹 **Async Relational Storage**: Powered by SQLAlchemy 2.0 Async with dual support for PostgreSQL and SQLite.
> 🔹 **SaaS Single Page Dashboard**: Real-time activity console, client-side search/sorting, and streamable exports in JSON, CSV, and Markdown formats.
> 
> Check out the GitHub repository and documentation! 💻🔥

---

## 3. Portfolio Website Copy

### Project Overview
The Universal Website Data Extractor is a full-stack asynchronous web crawling platform built to transform unstructured web pages into structured, relational datasets.

### Technologies Used
- **Backend**: Python 3.11+, FastAPI, Pydantic V2, Uvicorn
- **Scraping Engines**: Playwright (Headless Chromium), BeautifulSoup4, LXML, HTTPX
- **Async & Concurrency**: `asyncio`
- **Database & Persistence**: PostgreSQL, SQLite, SQLAlchemy 2.0 Async ORM (`asyncpg`, `aiosqlite`)
- **Frontend**: HTML5, CSS3 (Custom Variables & Flex/Grid), ES6+ Vanilla JavaScript

### Engineering Challenges Solved
1. **Event Loop & Background Session Contexts**: Solved FastAPI background task session lifetime conflicts by creating isolated database session factories within background worker threads.
2. **Canonical Link Normalization**: Avoided duplicate crawl loops by implementing URL normalization (stripping `#anchors`, lowercasing hostnames, and sorting query parameters).

---

## 4. Technical Interview Pitches

### 30-Second Elevator Pitch
> "I built the Universal Website Data Extractor—an asynchronous web crawling platform built with Python, FastAPI, Playwright, and SQLAlchemy Async. It handles both static HTML pages and heavy JavaScript Single Page Applications using a Strategy Pattern fetcher, extracts structural data like headings, tables, and media, persists them into PostgreSQL or SQLite using non-blocking ORM models, and provides a responsive Vanilla JS dashboard with instant search and multi-format dataset exports."

### 2-Minute Technical Walkthrough
> "When designing this project, my goal was to move beyond single-threaded web scraping scripts and build a production-grade backend system following Clean Architecture.
> 
> When a user submits a target URL on the web dashboard, the FastAPI REST controller validates the input using Pydantic and returns an immediate HTTP 202 Accepted response with a job ID, delegating the crawl loop to an asynchronous background task.
> 
> The core `CrawlEngine` executes a Breadth-First-Search (BFS) traversal while enforcing domain scoping and canonical URL deduplication. It utilizes a Strategy Pattern for fetching: for static sites, it uses lightweight HTTPX requests, while for dynamic SPAs, it launches a headless Chromium instance using Playwright.
> 
> Extracted HTML content is parsed using BeautifulSoup4 with LXML C-bindings, extracting headings, paragraphs, lists, tables, images, and links. All records are saved non-blockingly using SQLAlchemy 2.0 Async into PostgreSQL or SQLite. Users can monitor progress via an auto-scrolling live activity console and download streamable dataset exports in JSON, CSV, or Markdown."

---

## 5. 20 Technical Interview Questions & Detailed Answers

### Q1: Why did you choose FastAPI over Flask or Django?
**Answer**: FastAPI was chosen because it natively supports Python `asyncio` (ASGI), allowing asynchronous network I/O operations (fetching web pages and database queries) without blocking OS threads. Additionally, FastAPI provides automatic Pydantic input validation and OpenAPI/Swagger documentation out of the box.

### Q2: How does the dual-engine fetching strategy work?
**Answer**: It uses the Strategy Pattern with a common abstract base class `BaseFetcher` defining `async def fetch(url: str) -> FetchResult`. `StaticFetcher` uses `httpx` for high-throughput static HTML pages, while `DynamicFetcher` launches headless Chromium via `Playwright` to render client-side JavaScript SPAs.

### Q3: How do you prevent infinite crawl loops and duplicate link visits?
**Answer**: Through canonical URL normalization (`normalize_url`) and an in-memory visited set (`visited_urls`). Normalization converts hostnames to lowercase, strips URL fragments (`#anchor`), sorts query parameters (`?a=1&b=2`), and strips trailing slashes before checking set membership.

### Q4: Why did you select Breadth-First Search (BFS) over Depth-First Search (DFS)?
**Answer**: BFS processes web pages level-by-level (depth 0 -> depth 1 -> depth 2). For website data extraction, BFS ensures shallow, high-importance domain pages are indexed first before descending into deep pagination sublinks.

### Q5: How do background tasks run without blocking HTTP responses in FastAPI?
**Answer**: The endpoint returns an immediate `HTTP 202 Accepted` response with the job ID and registers `_run_crawl_in_background` with FastAPI's `BackgroundTasks`. The ASGI event loop yields execution to the background task while remaining responsive to new incoming HTTP requests.

### Q6: How did you handle database session scoping for background tasks?
**Answer**: Request-scoped sessions (`get_async_db`) close when the HTTP request finishes. In background tasks, `CrawlService` creates a dedicated session from `AsyncSessionFactory()` inside an `async with` context manager, ensuring the session stays open for the full duration of the crawl.

### Q7: Why use SQLAlchemy 2.0 Async ORM instead of raw SQL queries?
**Answer**: SQLAlchemy 2.0 provides type-safe ORM entities, relationship mapping (`relationship()`), and dialect abstractions. It seamlessly supports both PostgreSQL (`asyncpg`) for production and SQLite (`aiosqlite`) for zero-config local development without rewriting queries.

### Q8: How does the application support both PostgreSQL and SQLite?
**Answer**: Through configuration flagging (`USE_SQLITE=true`). In SQLite mode, SQLAlchemy uses `sqlite+aiosqlite://` with `CHAR(32)` UUID compatibility types. In PostgreSQL mode, it uses `postgresql+asyncpg://` with native PostgreSQL UUIDs and JSONB columns.

### Q9: How are cascading deletes configured in the database models?
**Answer**: Foreign keys on `extracted_pages`, `page_links`, `page_images`, and `crawl_statistics` are defined with `ForeignKey(..., ondelete="CASCADE")` alongside SQLAlchemy `cascade="all, delete-orphan"` relationships. Deleting a `CrawlJob` automatically purges all associated child records.

### Q10: How does the HTML extraction layer handle malformed or invalid HTML markup?
**Answer**: `HTMLExtractor` uses BeautifulSoup4 initialized with the `lxml` parser engine (`lxml` C-bindings). `lxml` is extremely fault-tolerant with malformed DOM trees and falls back to Python's native `html.parser` if `lxml` is unavailable.

### Q11: What is the purpose of Pydantic V2 validation in your request schemas?
**Answer**: Pydantic validates request boundaries before executing logic. For example, `CrawlCreateRequest` validates that target URLs use valid `http://` or `https://` schemes, preventing Server-Side Request Forgery (SSRF) or arbitrary scheme execution (e.g. `file://` or `ftp://`).

### Q12: How are data exports generated and delivered to the client?
**Answer**: `ExportService` queries all extracted pages for a job ID and formats them into JSON, CSV, or Markdown in memory. The REST endpoint returns a FastAPI `StreamingResponse` with header `Content-Disposition: attachment`, initiating a native browser file download.

### Q13: Why did you choose Vanilla JavaScript over React for the frontend?
**Answer**: To keep the MVP lightweight, zero-dependency, and instantly runnable without Node.js build tools (npm/webpack). The single-page application uses modular ES6 JavaScript for DOM updates, live console logging, searching, and sorting.

### Q14: How does the live activity console update in real time?
**Answer**: As the `CrawlEngine` traverses pages, it logs timestamped status messages. The frontend polls `GET /api/v1/crawl/{job_id}` every 1.5 seconds, appending logs to an auto-scrolling terminal box element (`#activity-log`).

### Q15: How does client-side searching and sorting work without re-querying the backend?
**Answer**: Upon crawl completion, `app.js` fetches all extracted page records into an in-memory array (`rawExtractedPages`). Input events on `#search-input` and `#sort-select` immediately filter and sort this array in JavaScript and re-render the card DOM elements.

### Q16: How do you enforce polite crawling behavior toward target web servers?
**Answer**: By configuring `DEFAULT_CRAWL_DELAY_SEC` (default 0.5s). Between consecutive page fetches, the `CrawlEngine` calls `await asyncio.sleep(self.crawl_delay)`, preventing HTTP rate-limiting or Denial of Service (DoS) conditions on target hosts.

### Q17: What security measures prevent Server-Side Request Forgery (SSRF)?
**Answer**: Target URLs are strictly validated using `validate_public_url` in Pydantic schemas, enforcing `http` or `https` schemes and rejecting internal/local protocol schemes (`file://`, `gopher://`, `dict://`).

### Q18: What are the current performance bottlenecks in the MVP?
**Answer**: Single-node execution and in-memory queue management. If crawling thousands of pages, in-memory BFS queues and visited sets consume server RAM, and Playwright browser instances consume significant CPU per page.

### Q19: How would you scale this architecture for millions of pages in production?
**Answer**: By introducing **Celery** workers for distributed task execution, **Redis** for distributed URL queues and visited set deduplication, and a pool of headless browser nodes or proxy rotators.

### Q20: What did you learn about Clean Architecture during this project?
**Answer**: Layer separation pays off during refactoring. Decoupling fetcher implementations behind `BaseFetcher` allowed adding Playwright alongside HTTPX without modifying `CrawlEngine` or database schemas.
