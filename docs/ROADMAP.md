# Universal Website Data Extractor - System Roadmap

This document outlines the phased development roadmap for the **Universal Website Data Extractor**, clearly separating currently implemented features (**Phase 1 MVP**) from future planned architectural enhancements.

---

## Phase 1 ✅ (Current Implemented MVP)

*All features listed in Phase 1 are 100% implemented, tested, and verified in the codebase.*

### Core System Features
- [x] **URL Validation & Scope**: Enforces HTTP/HTTPS public scheme checks and same-domain traversal.
- [x] **Configurable Crawl Bounds**: Support for user-defined `max_depth` (0-10) and `max_pages` (1-500).
- [x] **Pluggable Dual Fetchers**:
  - `StaticFetcher` using `httpx` for high-throughput static HTML pages.
  - `DynamicFetcher` using `playwright` (headless Chromium) for rendering JavaScript SPAs.
- [x] **Structural Feature Extraction**:
  - Metadata: Title, Meta Description.
  - Structural Content: Headings (`H1`–`H6`), Paragraphs, Lists (`<ul>`, `<ol>`), Tables (`<table>`).
  - Media & Links: Images with `alt` text, internal and external links.
- [x] **Canonical Normalization & Deduplication**: Fragment stripping (`#anchor`), host lowercasing, query parameter sorting, and set-based URL deduplication.
- [x] **Async Relational Persistence**:
  - SQLAlchemy 2.0 Async ORM with cascading delete constraints.
  - Dual database engine support: PostgreSQL (`asyncpg`) & zero-config SQLite (`aiosqlite`).
- [x] **Multi-Format Exports**: Downloadable dataset exports in **JSON**, **CSV**, **Markdown** (`.md`), **PDF** (`.pdf`), **Microsoft Word** (`.docx`), and **Microsoft Excel** (`.xlsx`).
- [x] **SaaS Single Page Dashboard (`/app`)**:
  - Live activity console logging real-time crawl events.
  - Dynamic website favicon, title, and description preview card.
  - Dedicated progress card with live depth, latency, and animated progress bar.
  - Instant client-side searching and dynamic sorting.
  - Accordion result views for structured elements.
  - Minimalist sticky navigation bar and 6-format dataset export action section.

---

## Phase 2 ✅ (Human Readable Document Exporters)

*All document exporter strategies in Phase 2 are 100% implemented, tested, and verified in the codebase.*

- [x] **PDF Report Export (`.pdf`)**: Professional report with cover page, site summary table, statistics, table of contents, page sections, and dynamic two-pass canvas footers (`Page X of Y`).
- [x] **Microsoft Word Export (`.docx`)**: Native Word typography styles (`Heading 1`, `Heading 2`, `Heading 3`), executive summary table, bullet lists, and structured tables.
- [x] **Microsoft Excel Export (`.xlsx`)**: Multi-tab workbook (**Overview**, **Pages**, **Links**, **Images**, **Statistics**), bold styled headers, frozen top rows, auto-filters, and auto-column width sizing.

---

## Phase 3 ✅ (Multi-Website Batch Crawling Engine)

*Multi-website batch crawling is 100% implemented, verified with tests, and documented.*

- [x] **Multi-Website Batch Engine (`POST /api/v1/batch`)**: Concurrently crawl multiple target websites within a single batch.
- [x] **CSV & Multi-Line URL Import**: Input target URLs via multi-line text input or uploaded `.csv` files.
- [x] **Bounded Concurrency Control**: Configurable `MAX_CONCURRENT_BATCH_JOBS` via `.env` utilizing `asyncio.Semaphore`.
- [x] **Resilient Failure Isolation**: Child website failures do not crash the batch (`PARTIALLY_COMPLETED` status).
- [x] **Selective Batch Retry**: Re-trigger background crawling **only** for child jobs with status `FAILED`.
- [x] **Domain-Segmented Exports**: Multi-website exports across all 6 formats (**JSON**, **CSV**, **Markdown**, **PDF**, **DOCX**, **XLSX**).
- [x] **Dashboard Mode Selector**: Dual-tab UI (**Single Website** | **Batch Websites**) with per-website progress table.

---

## Phase 4 (Distributed Workers & Cloud Operations - Future Work)

*Planned enhancements for distributed enterprise deployment.*

- [ ] **Redis / Celery Worker Queue**: Asynchronous distributed task queue for web crawler workers.
- [ ] **S3 / Cloud Storage Artifact Sync**: Store exported datasets in AWS S3 / Google Cloud Storage.
- [ ] **API Key Rate Limiting & Auth**: OAuth2 / API Key authorization middleware. visited URL sets in **Redis Sets** across multi-node clusters.
- [ ] **JWT Authentication**: User account registration, API key management, and tenant data isolation.
- [ ] **Crawl Scheduling**: Cron-based recurring crawl jobs.
- [ ] **Containerization**: `Dockerfile` and `docker-compose.yml` defining FastAPI, Celery, Redis, and PostgreSQL containers.
- [ ] **Automated CI/CD**: GitHub Actions workflow running Pytest test suites and code quality linters on pull requests.
---

## Phase 4 (AI Integration & Vector Pipeline - Future Work)

*Integrations for Artificial Intelligence pipelines and Retrieval-Augmented Generation (RAG).*

- [ ] **RAG Dataset Export**: Pre-chunked, token-aware JSON exports formatted for vector stores (LangChain, LlamaIndex, Pinecone, ChromaDB).
- [ ] **LLM Page Summarization**: Automated AI-generated summaries of scraped web page content.
- [ ] **Semantic Search**: Embedding generation over extracted text for natural language semantic querying.
