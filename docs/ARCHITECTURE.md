# Universal Website Data Extractor - System Architecture

This document provides a technical deep-dive into the architectural design, structural patterns, layer boundaries, and execution lifecycles of the **Universal Website Data Extractor**.

---

## 1. High-Level Architecture Overview

The system strictly adheres to **Clean Architecture** principles, ensuring that business domain logic (`crawler/`), data persistence (`db/`), and API controllers (`api/`) are completely decoupled.

```mermaid
flowchart TB
    subgraph ClientLayer["1. Presentation Layer"]
        UI["Vanilla JS Single Page Application (/app)"]
        Swagger["Swagger UI Documentation (/docs)"]
    end

    subgraph APILayer["2. API & Dependency Layer (FastAPI)"]
        Middleware["CORS & Exception Handlers"]
        Router["APIRouter (/api/v1/crawl)"]
        DepInject["Dependency Injection Providers"]
    end

    subgraph ServiceLayer["3. Application Service Layer"]
        CrawlService["CrawlService (Job Orchestration)"]
        ExportService["ExportService (File Generators)"]
    end

    subgraph EngineLayer["4. Crawler Domain Layer"]
        CrawlEngine["CrawlEngine (Async BFS Loop)"]
        FetcherFactory["Fetcher Strategy Interface"]
        HTTPFetcher["Static HTTPX Fetcher"]
        BrowserFetcher["Dynamic Playwright Fetcher"]
        Extractor["HTMLExtractor (BS4 + LXML)"]
    end

    subgraph DBLayer["5. Data Access Layer"]
        CrawlRepo["CrawlRepository DAO"]
        PageRepo["PageRepository DAO"]
        Postgres[(PostgreSQL / SQLite Storage)]
    end

    ClientLayer --> Middleware --> Router --> DepInject
    DepInject --> CrawlService & ExportService
    CrawlService --> CrawlEngine
    CrawlEngine --> FetcherFactory
    FetcherFactory --> HTTPFetcher & BrowserFetcher
    HTTPFetcher & BrowserFetcher --> Extractor
    Extractor --> PageRepo
    CrawlEngine --> CrawlRepo
    CrawlRepo & PageRepo --> Postgres
    ExportService --> PageRepo
```

---

## 2. Layer Responsibilities & Component Directory

```
src/
├── core/         # Core system settings, logging formatters, and domain exceptions.
├── db/           # Declarative ORM models (SQLAlchemy 2.0) and Repository DAOs.
├── utils/        # URL normalization, domain scoping, and validation functions.
├── schemas/      # Pydantic V2 data validation and response DTOs.
├── crawler/      # Crawler engine, static/dynamic fetcher strategies, and HTML parser.
├── application/  # High-level business use cases (CrawlService, ExportService).
└── api/          # FastAPI routes, dependency injection, and exception handlers.
```

### Architectural Layer Isolation Matrix

| Layer | Component | Dependencies | Responsibility |
| :--- | :--- | :--- | :--- |
| **Core** | `config.py`, `exceptions.py` | Pydantic Settings | System configurations & domain exception classes. |
| **Database** | `models/`, `repositories/` | SQLAlchemy Async | Persistent entity definitions and database CRUD queries. |
| **Utils** | `url_utils.py` | urllib.parse | Pure helper functions for URL validation and normalization. |
| **Domain** | `crawler/` | BS4, HTTPX, Playwright | Page fetching, HTML structural parsing, and BFS crawling logic. |
| **Application** | `services/` | Domain + DB DAOs | High-level orchestrators for background jobs and file exports. |
| **API Layer** | `endpoints/`, `main.py` | Application Services | HTTP request routing, input validation, and response delivery. |

---

## 3. Asynchronous Execution Lifecycles

### A. HTTP Request Processing Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant ASGI as FastAPI / Uvicorn
    participant Handler as Exception Handler
    participant Endpoint as REST Controller
    participant Service as CrawlService
    participant Task as Background Task

    Client->>ASGI: HTTP Request POST /api/v1/crawl
    ASGI->>Handler: Validate Input Schema
    alt Invalid Schema / URL
        Handler-->>Client: HTTP 400 / 422 JSON Error
    else Valid Payload
        ASGI->>Endpoint: Invoke Endpoint Handler
        Endpoint->>Service: initiate_crawl(request, background_tasks)
        Service->>Service: Create Job Record (PENDING)
        Service->>Task: Dispatch _run_crawl_in_background
        Endpoint-->>Client: HTTP 202 Accepted {job_id, status: "PENDING"}
    end
```

---

### B. Asynchronous Crawl Execution Lifecycle

```mermaid
flowchart TD
    Start([Background Task Initiated]) --> CreateEngine[Instantiate CrawlEngine]
    CreateEngine --> SelectStrategy{render_js Flag?}
    
    SelectStrategy -->|True| InitPlaywright[Initialize Dynamic Playwright Fetcher]
    SelectStrategy -->|False| InitHTTPX[Initialize Static HTTPX Fetcher]
    
    InitPlaywright --> InitFrontier[Initialize BFS Queue & Visited Set]
    InitHTTPX --> InitFrontier
    InitFrontier --> CheckQueue{Queue Empty OR Max Pages Reached?}
    
    CheckQueue -->|No| PopURL[Pop Next URL & Depth from Queue]
    PopURL --> FetchHTML[Execute Fetcher Strategy]
    
    FetchHTML --> CheckStatus{Status 200 OK?}
    CheckStatus -->|Yes| ParseHTML[HTMLExtractor Parsing]
    ParseHTML --> SaveDB[PageRepository: Save Page, Links & Images]
    SaveDB --> CheckDepth{Current Depth < Max Depth?}
    
    CheckDepth -->|Yes| DiscoverLinks[Filter & Enqueue Discovered Same-Domain Links]
    CheckDepth -->|No| Delay[Apply Polite Crawl Delay]
    DiscoverLinks --> Delay
    
    CheckStatus -->|No| LogError[Log Failure Metric]
    LogError --> Delay
    Delay --> CheckQueue
    
    CheckQueue -->|Yes| SaveStats[CrawlRepository: Save Final Statistics]
    SaveStats --> SetComplete[Update Job Status: COMPLETED]
    SetComplete --> CloseFetcher[Close Fetcher Connections]
    CloseFetcher --> End([Crawl Task Completed])
```

---

### C. Data Export Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as REST Controller
    participant ExportSvc as ExportService
    participant Registry as ExporterRegistry
    participant Strategy as Strategy Exporter (PDF / DOCX / XLSX / JSON / CSV / MD)
    participant PageRepo as PageRepository DAO

    Client->>API: POST /api/v1/crawl/{job_id}/export {format: "pdf"}
    API->>ExportSvc: generate_export(job_id, format)
    ExportSvc->>PageRepo: get_all_pages_for_job(job_id)
    PageRepo-->>ExportSvc: List[ExtractedPage]
    ExportSvc->>Registry: get(format)
    Registry-->>ExportSvc: PdfExporter Strategy Instance
    ExportSvc->>Strategy: export(pages, job, stats)
    Strategy-->>ExportSvc: (raw_bytes, filename, media_type)
    ExportSvc-->>API: Stream Payload
    API-->>Client: HTTP 200 OK (Content-Disposition: attachment)
```

---

## 4. Architectural Boundaries & System Trade-offs

1. **Async Concurrency vs Thread Pools**:
   - The application relies on native `asyncio` non-blocking I/O. Network-bound operations (fetching pages, executing SQL queries) yield control without blocking OS threads.
2. **Strategy Pattern Isolation**:
   - Decouples `StaticFetcher` (`httpx`) and `DynamicFetcher` (`playwright`) behind `BaseFetcher`. The `CrawlEngine` operates independently of which browser/client engine is active.
3. **Database Session Scoping**:
   - Background tasks create an isolated `AsyncSessionFactory()` instance rather than sharing request-scoped sessions, avoiding asynchronous session closure errors during long-running crawls.
