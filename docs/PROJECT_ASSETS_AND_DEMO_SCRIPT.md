# Universal Website Data Extractor - Project Assets & Demo Script

This document provides visual asset guidelines, screenshot placeholders, and a **2–3 minute video presentation demo script** for showcasing the **Universal Website Data Extractor** to technical recruiters, hiring managers, and interviewers.

---

## 1. Project Asset Specifications

When creating visual assets for your portfolio website, GitHub repository, or LinkedIn posts, capture screenshots at a resolution of **1920x1080 (1080p)** in light mode.

### Asset Folder Structure
Save captured images into the following repository path:

```text
docs/
├── screenshots/
│   ├── 01_home_configuration.png     # Hero section & configuration inputs
│   ├── 02_crawl_progress_console.png # Live progress card & activity console
│   ├── 03_statistics_dashboard.png   # 4 modern statistics metrics cards
│   ├── 04_results_accordions.png     # Search bar, sort dropdown & result cards
│   └── 05_dataset_export.png         # Export dataset section buttons
└── diagrams/
    ├── system_architecture.png       # High-level Clean Architecture diagram
    └── database_er_diagram.png       # Relational database ER diagram
```

---

## 2. Professional 2–3 Minute Demo Script

### Video Recording Setup
- **Resolution**: 1920x1080 (60 FPS)
- **Audio**: Crisp microphone input with background noise suppression
- **Browser**: Fullscreen Chrome window displaying `http://localhost:8000/app`

---

### Act 1: Introduction & Problem Statement (0:00 - 0:30)

**[Visual: Full screen view of http://localhost:8000/app]**

> **Speaker**:
> "Hi! Today I'm demonstrating the **Universal Website Data Extractor**—an asynchronous web crawling and structural data extraction platform built with Python 3.11, FastAPI, Playwright, BeautifulSoup4, SQLAlchemy 2.0 Async, PostgreSQL, and a zero-framework Vanilla JavaScript Single Page Application.
> 
> Most scraping scripts are single-threaded, fragile, and fail when encountering client-rendered JavaScript applications. This project addresses those limitations by decoupling network fetching, HTML parsing, background task orchestration, and relational data persistence using Clean Architecture."

---

### Act 2: initiating a Crawl & Real-Time Monitoring (0:30 - 1:15)

**[Visual: Cursor types `https://news.ycombinator.com`, sets max depth to 2, max pages to 20, toggles Playwright JS rendering, and clicks 'Start Crawling']**

> **Speaker**:
> "Let's submit a seed URL—`https://news.ycombinator.com`. We'll set max crawl depth to 2 and max pages to 20. Notice the toggle for **Playwright JS Rendering**. The system uses the Strategy Pattern to switch between a high-speed static HTTPX fetcher and a headless Chromium browser using Playwright for dynamic SPAs.
> 
> As soon as I click **Start Crawling**, the FastAPI backend returns an immediate HTTP 202 Accepted response with a job ID, delegating the crawl loop to an asynchronous background task.
> 
> Notice the **Website Information Card** resolving the site's favicon, domain name, and initial metadata. Below it, the **Live Progress Card** displays real-time depth, response latency, current processing URL, and an animated progress bar. The **Live Activity Console** streams timestamped milestones directly to the screen."

---

### Act 3: Extracted Results, Search & Dynamic Sorting (1:15 - 1:50)

**[Visual: Scroll down to Statistics Grid and Extracted Web Pages section. Type 'Hacker' into search box, change Sort dropdown to 'Response Time']**

> **Speaker**:
> "Now that the crawl status has transitioned to **COMPLETED**, the **Statistics Dashboard** highlights total pages crawled, images extracted, links discovered, and total execution duration.
> 
> In the **Extracted Pages** section, each result card displays the page title, URL, HTTP 200 OK status pill, depth, and response time. Content is organized into clean expandable accordions for Headings, Paragraphs, Lists, Tables, and Images.
> 
> We can also use the real-time search box to instantly filter extracted pages by title or URL without re-querying the backend, or sort pages dynamically by response latency or link count."

---

### Act 4: Multi-Format Data Exports & Architecture Conclusion (1:50 - 2:30)

**[Visual: Scroll down to Export Dataset section and click 'Export JSON', showing browser file download `crawl_export.json`]**

> **Speaker**:
> "Finally, in the **Export Dataset** section, we can export our entire structured dataset with a single click. Supported formats include **JSON**, **CSV**, and **Markdown**. Clicking **Export JSON** streams the generated dataset directly through the browser.
> 
> Under the hood, the backend uses **SQLAlchemy 2.0 Async** ORM with non-blocking drivers, supporting both PostgreSQL and zero-config SQLite. Pydantic V2 guarantees boundary validation, preventing SSRF or invalid URL schemes.
> 
> Thank you for watching! The source code, complete documentation, and architectural specifications are available on GitHub."

---

## 3. Demo Video Recording Checklist

- [ ] Clear terminal history and ensure `uvicorn` is running cleanly without errors.
- [ ] Confirm `USE_SQLITE=true` or PostgreSQL database service is active.
- [ ] Test target website URL before recording to ensure fast response latency.
- [ ] Record video in 1080p resolution with smooth cursor movements.
- [ ] Upload final recording to YouTube (Unlisted) or Loom to embed in portfolio links.
