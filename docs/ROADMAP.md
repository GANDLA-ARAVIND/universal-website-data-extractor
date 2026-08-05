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
- [x] **Multi-Format Exports**: Downloadable dataset exports in **JSON**, **CSV**, and **Markdown** (`.md`).
- [x] **SaaS Single Page Dashboard (`/app`)**:
  - Live activity console logging real-time crawl events.
  - Dynamic website favicon, title, and description preview card.
  - Dedicated progress card with live depth, latency, and animated progress bar.
  - Instant client-side searching and dynamic sorting.
  - Accordion result views for structured elements.
  - Minimalist sticky navigation bar and single export action section.

---

## Phase 2 (Expanded Export Formats - Future Work)

*Planned enhancements to expand human-readable and analytical data outputs.*

- [ ] **PDF Report Export**: Render styled PDF documents of extracted pages and image catalogs.
- [ ] **Microsoft Word (`.docx`) Export**: Format datasets into Word documents with structured tables.
- [ ] **Excel (`.xlsx`) Export**: Multi-tab workbook generation separating pages, links, and media assets.

---

## Phase 3 (Enterprise Scaling & Operations - Future Work)

*Architectural upgrades for multi-tenant, distributed production deployment.*

- [ ] **Distributed Task Queue**: Replace FastAPI `BackgroundTasks` with **Celery** workers and **Redis** brokers for horizontal crawler scaling.
- [ ] **Distributed Deduplication**: Store visited URL sets in **Redis Sets** across multi-node clusters.
- [ ] **JWT Authentication**: User account registration, API key management, and tenant data isolation.
- [ ] **Crawl Scheduling**: Cron-based recurring crawl jobs.
- [ ] **Containerization**: `Dockerfile` and `docker-compose.yml` defining FastAPI, Celery, Redis, and PostgreSQL containers.
- [ ] **Automated CI/CD**: GitHub Actions workflow running Pytest test suites and code quality linters on pull requests.
- [ ] **Robots.txt & Sitemap Integration**: Automatic parsing of target website `robots.txt` rules and `sitemap.xml` URL discovery.

---

## Phase 4 (AI Integration & Vector Pipeline - Future Work)

*Integrations for Artificial Intelligence pipelines and Retrieval-Augmented Generation (RAG).*

- [ ] **RAG Dataset Export**: Pre-chunked, token-aware JSON exports formatted for vector stores (LangChain, LlamaIndex, Pinecone, ChromaDB).
- [ ] **LLM Page Summarization**: Automated AI-generated summaries of scraped web page content.
- [ ] **Semantic Search**: Embedding generation over extracted text for natural language semantic querying.
