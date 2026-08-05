/**
 * Universal Website Data Extractor - Frontend App Controller
 * Pure Vanilla JavaScript ES6 Async Client
 */

document.addEventListener('DOMContentLoaded', () => {
    // API BASE CONFIGURATION
    const API_BASE = '/api/v1';

    // DOM ELEMENTS
    const crawlForm = document.getElementById('crawl-form');
    const targetUrlInput = document.getElementById('target-url');
    const maxDepthInput = document.getElementById('max-depth');
    const maxPagesInput = document.getElementById('max-pages');
    const renderJsInput = document.getElementById('render-js');
    const startBtn = document.getElementById('start-btn');

    // UI SECTIONS & CARDS
    const emptyState = document.getElementById('empty-state');
    const previewCard = document.getElementById('preview-card');
    const progressCard = document.getElementById('progress-card');
    const completionCard = document.getElementById('completion-card');
    const errorCard = document.getElementById('error-card');
    const statsSection = document.getElementById('stats-section');
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('results-container');
    const exportSection = document.getElementById('export-section');

    // SEARCH & SORT CONTROLS
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');

    // PREVIEW & PROGRESS BINDINGS
    const previewFavicon = document.getElementById('preview-favicon');
    const previewDomain = document.getElementById('preview-domain');
    const previewTitle = document.getElementById('preview-title');
    const previewDesc = document.getElementById('preview-desc');
    const previewMaxPages = document.getElementById('preview-max-pages');
    const previewMode = document.getElementById('preview-mode');

    const statusPill = document.getElementById('status-pill');
    const loaderIcon = document.getElementById('loader-icon');
    const progressStatusText = document.getElementById('progress-status-text');
    const elapsedTimeText = document.getElementById('elapsed-time');
    const progressPagesCount = document.getElementById('progress-pages-count');
    const progressDepth = document.getElementById('progress-depth');
    const progressLatency = document.getElementById('progress-latency');
    const currentProcessingUrl = document.getElementById('current-processing-url');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const activityLog = document.getElementById('activity-log');

    const summaryDurationText = document.getElementById('summary-duration-text');
    const errorMessage = document.getElementById('error-message');
    const retryBtn = document.getElementById('retry-btn');
    const viewResultsBtn = document.getElementById('view-results-btn');
    const viewExportBtn = document.getElementById('view-export-btn');

    // STATS BINDINGS
    const statPages = document.getElementById('stat-pages');
    const statImages = document.getElementById('stat-images');
    const statLinks = document.getElementById('stat-links');
    const statDuration = document.getElementById('stat-duration');

    // APP STATE
    let currentJobId = null;
    let pollInterval = null;
    let timerInterval = null;
    let startTime = 0;
    let maxPagesLimit = 50;
    let rawExtractedPages = [];

    // -------------------------------------------------------------------------
    // 1. EVENT LISTENERS & NAVIGATION
    // -------------------------------------------------------------------------
    crawlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await startCrawlJob();
    });

    retryBtn.addEventListener('click', () => {
        hideElement(errorCard);
        startCrawlJob();
    });

    viewResultsBtn.addEventListener('click', () => {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    });

    if (viewExportBtn) {
        viewExportBtn.addEventListener('click', () => {
            exportSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Single Consolidated Export Buttons Listener
    document.querySelectorAll('#export-section .export-btn').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            const format = btn.getAttribute('data-format');
            if (currentJobId && format) {
                await downloadExport(currentJobId, format);
            }
        });
    });

    // Real-Time Search & Sort Listeners
    if (searchInput) {
        searchInput.addEventListener('input', filterAndRenderResults);
    }
    if (sortSelect) {
        sortSelect.addEventListener('change', filterAndRenderResults);
    }

    // Sticky Nav Link Active State Tracking
    const navLinks = document.querySelectorAll('.nav-link');
    window.addEventListener('scroll', () => {
        let currentSection = '';
        const sections = document.querySelectorAll('section[id]');
        sections.forEach(sec => {
            const secTop = sec.offsetTop - 100;
            if (window.scrollY >= secTop) {
                currentSection = sec.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${currentSection}`) {
                link.classList.add('active');
            }
        });
    });

    // -------------------------------------------------------------------------
    // 2. MAIN CRAWL INITIATION & POLLING
    // -------------------------------------------------------------------------
    async function startCrawlJob() {
        const seedUrl = targetUrlInput.value.trim();
        const maxDepth = parseInt(maxDepthInput.value, 10);
        const maxPages = parseInt(maxPagesInput.value, 10);
        const renderJs = renderJsInput.checked;

        maxPagesLimit = maxPages;

        resetUI();
        disableForm(true);

        showLivePreview(seedUrl, maxPages, renderJs);
        showElement(progressCard);
        logConsole(`Initializing crawl job for ${seedUrl}...`, 'info');

        try {
            const response = await fetch(`${API_BASE}/crawl`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: seedUrl,
                    max_depth: maxDepth,
                    max_pages: maxPages,
                    render_js: renderJs,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to initiate crawl job.');
            }

            const data = await response.json();
            currentJobId = data.id;
            logConsole(`✓ Job created successfully [ID: ${currentJobId.slice(0, 8)}]`, 'success');
            logConsole(`✓ Crawl Strategy: ${renderJs ? 'Playwright Headless Browser' : 'HTTPX Static Fetcher'}`, 'info');

            startTimer();
            startPolling(currentJobId);

        } catch (err) {
            logConsole(`❌ Error initiating crawl: ${err.message}`, 'error');
            showErrorState(err.message);
            disableForm(false);
        }
    }

    function startPolling(jobId) {
        clearInterval(pollInterval);

        pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/crawl/${jobId}`);
                if (!response.ok) return;

                const job = await response.json();

                if (job.status === 'RUNNING') {
                    updateProgressUI('RUNNING', job);
                } else if (job.status === 'COMPLETED') {
                    stopPolling();
                    stopTimer();
                    await handleCrawlSuccess(jobId);
                } else if (job.status === 'FAILED') {
                    stopPolling();
                    stopTimer();
                    showErrorState('The crawl job encountered an unexpected failure during execution.');
                    logConsole('❌ Job execution failed.', 'error');
                    disableForm(false);
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 1500);
    }

    // -------------------------------------------------------------------------
    // 3. SUCCESS HANDLER & DATA FETCHING
    // -------------------------------------------------------------------------
    async function handleCrawlSuccess(jobId) {
        logConsole('✓ Crawl completed successfully!', 'success');
        updateProgressUI('COMPLETED', { max_pages: maxPagesLimit });

        // 1. Fetch Statistics
        const stats = await fetchStatistics(jobId);
        if (stats) {
            statPages.textContent = stats.pages_crawled;
            statImages.textContent = stats.total_images;
            statLinks.textContent = stats.total_links;
            statDuration.textContent = `${stats.total_duration_sec}s`;
            summaryDurationText.textContent = `Processed ${stats.pages_crawled} pages in ${stats.total_duration_sec} seconds.`;
        }

        // 2. Fetch Extracted Pages Results
        const resultsData = await fetchResults(jobId);
        if (resultsData && resultsData.data) {
            rawExtractedPages = resultsData.data;
            filterAndRenderResults();
            if (rawExtractedPages.length > 0) {
                updateFaviconPreview(rawExtractedPages[0]);
            }
        }

        showElement(completionCard);
        showElement(statsSection);
        showElement(resultsSection);
        showElement(exportSection);
        disableForm(false);
    }

    async function fetchStatistics(jobId) {
        try {
            const res = await fetch(`${API_BASE}/crawl/${jobId}/statistics`);
            return res.ok ? await res.json() : null;
        } catch {
            return null;
        }
    }

    async function fetchResults(jobId) {
        try {
            const res = await fetch(`${API_BASE}/crawl/${jobId}/results?page=1&limit=100`);
            return res.ok ? await res.json() : null;
        } catch {
            return null;
        }
    }

    // -------------------------------------------------------------------------
    // 4. EXPORT DOWNLOAD HANDLER
    // -------------------------------------------------------------------------
    async function downloadExport(jobId, format) {
        logConsole(`Generating ${format.toUpperCase()} export file...`, 'info');
        try {
            const response = await fetch(`${API_BASE}/crawl/${jobId}/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format }),
            });

            if (!response.ok) throw new Error('Export generation failed.');

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `crawl_export_${jobId}.${format === 'markdown' ? 'md' : format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);

            logConsole(`✓ Downloaded export: crawl_export_${jobId}.${format}`, 'success');
        } catch (err) {
            logConsole(`❌ Export failed: ${err.message}`, 'error');
        }
    }

    // -------------------------------------------------------------------------
    // 5. SEARCH, SORT & DOM RENDERERS
    // -------------------------------------------------------------------------
    function filterAndRenderResults() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const sortBy = sortSelect ? sortSelect.value : 'url';

        let filtered = rawExtractedPages.filter(p => {
            if (!query) return true;
            const titleMatch = (p.title || '').toLowerCase().includes(query);
            const urlMatch = (p.url || '').toLowerCase().includes(query);
            const descMatch = (p.meta_description || '').toLowerCase().includes(query);
            return titleMatch || urlMatch || descMatch;
        });

        // Dynamic Sorting
        filtered.sort((a, b) => {
            if (sortBy === 'url') return (a.url || '').localeCompare(b.url || '');
            if (sortBy === 'title') return (a.title || '').localeCompare(b.title || '');
            if (sortBy === 'response_time') return (b.response_time_ms || 0) - (a.response_time_ms || 0);
            if (sortBy === 'links') return (b.links_count || 0) - (a.links_count || 0);
            if (sortBy === 'images') return (b.images_count || 0) - (a.images_count || 0);
            return 0;
        });

        renderResults(filtered);
    }

    function renderResults(pages) {
        resultsContainer.innerHTML = '';

        if (pages.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-state"><p class="text-muted">No pages match your search query.</p></div>';
            return;
        }

        pages.forEach((p) => {
            const card = document.createElement('div');
            card.className = 'result-card';

            const headingsCount = Object.values(p.headings || {}).flat().length;
            let pageDomain = '';
            try { pageDomain = new URL(p.url).hostname; } catch {}

            const faviconUrl = pageDomain ? `https://www.google.com/s2/favicons?domain=${pageDomain}&sz=32` : '';

            card.innerHTML = `
                <div class="result-card-header">
                    <div>
                        <div class="result-title-row">
                            ${faviconUrl ? `<img src="${faviconUrl}" class="result-favicon" alt="Icon">` : ''}
                            <a href="${escapeHtml(p.url)}" target="_blank" class="result-url">${escapeHtml(p.url)}</a>
                        </div>
                        <h4 class="result-title">${escapeHtml(p.title || 'Untitled Page')}</h4>
                    </div>
                    <div class="result-pills">
                        <span class="pill ${p.status_code >= 200 && p.status_code < 300 ? 'status-200' : 'status-error'}">${p.status_code} OK</span>
                        <span class="pill info">Depth: ${p.depth}</span>
                        <span class="pill info">${p.response_time_ms}ms</span>
                    </div>
                </div>
                ${p.meta_description ? `<p class="result-meta-desc">${escapeHtml(p.meta_description)}</p>` : ''}

                <!-- ACCORDIONS -->
                ${renderAccordion('Headings', `${headingsCount} headings`, renderHeadingsContent(p.headings))}
                ${renderAccordion('Paragraphs', `${(p.paragraphs || []).length} paragraphs`, renderListContent(p.paragraphs))}
                ${renderAccordion('Lists', `${(p.lists || []).length} lists`, renderListsContent(p.lists))}
                ${renderAccordion('Tables', `${(p.tables || []).length} tables`, renderTablesContent(p.tables))}
                ${renderAccordion('Images', `${p.images_count} images`, renderImagesContent(p.images || []))}
            `;

            resultsContainer.appendChild(card);
        });
    }

    function renderAccordion(title, badgeText, contentHtml) {
        if (!contentHtml || contentHtml.trim() === '') return '';
        return `
            <details>
                <summary>${title} (${badgeText})</summary>
                <div class="accordion-body">${contentHtml}</div>
            </details>
        `;
    }

    function renderHeadingsContent(headings) {
        if (!headings || Object.keys(headings).length === 0) return '';
        let html = '<ul class="content-list">';
        for (const [tag, list] of Object.entries(headings)) {
            list.forEach(txt => {
                html += `<li><strong>${tag.toUpperCase()}:</strong> ${escapeHtml(txt)}</li>`;
            });
        }
        html += '</ul>';
        return html;
    }

    function renderListContent(items) {
        if (!items || items.length === 0) return '';
        let html = '<ul class="content-list">';
        items.forEach(txt => {
            html += `<li>${escapeHtml(txt)}</li>`;
        });
        html += '</ul>';
        return html;
    }

    function renderListsContent(lists) {
        if (!lists || lists.length === 0) return '';
        let html = '';
        lists.forEach((sublist, idx) => {
            html += `<p><strong>List #${idx + 1}</strong></p><ul class="content-list">`;
            sublist.forEach(item => {
                html += `<li>${escapeHtml(item)}</li>`;
            });
            html += '</ul><br>';
        });
        return html;
    }

    function renderTablesContent(tables) {
        if (!tables || tables.length === 0) return '';
        let html = '';
        tables.forEach((tbl, idx) => {
            html += `<p><strong>Table #${idx + 1}</strong></p><ul class="content-list">`;
            tbl.forEach(row => {
                html += `<li>${escapeHtml(row.join(' | '))}</li>`;
            });
            html += '</ul><br>';
        });
        return html;
    }

    function renderImagesContent(images) {
        if (!images || images.length === 0) return '';
        let html = '<div class="image-grid">';
        images.forEach(img => {
            html += `
                <div class="image-item">
                    <img src="${escapeHtml(img.image_url)}" alt="${escapeHtml(img.alt_text || '')}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'80\'><rect width=\'100%\' height=\'100%\' fill=\'%23e2e8f0\'/></svg>'">
                    <div class="image-alt">${escapeHtml(img.alt_text || 'No Alt Text')}</div>
                </div>
            `;
        });
        html += '</div>';
        return html;
    }

    // -------------------------------------------------------------------------
    // 6. UTILITY FUNCTIONS & UI STATE RESET
    // -------------------------------------------------------------------------
    function showLivePreview(url, maxPages, renderJs) {
        try {
            const parsed = new URL(url);
            previewFavicon.src = `https://www.google.com/s2/favicons?domain=${parsed.hostname}&sz=64`;
            previewDomain.textContent = parsed.hostname;
            previewTitle.textContent = 'Not Available';
            previewDesc.textContent = 'Not Available';
            if (previewMaxPages) previewMaxPages.textContent = `Max Pages: ${maxPages}`;
            if (previewMode) previewMode.textContent = `Mode: ${renderJs ? 'Playwright JS' : 'Static HTML'}`;
            showElement(previewCard);
        } catch {
            hideElement(previewCard);
        }
    }

    function updateFaviconPreview(firstPage) {
        if (firstPage) {
            previewTitle.textContent = firstPage.title && firstPage.title.trim() ? firstPage.title : 'Not Available';
            previewDesc.textContent = firstPage.meta_description && firstPage.meta_description.trim() ? firstPage.meta_description : 'Not Available';
        }
    }

    function updateProgressUI(status, job) {
        if (status === 'RUNNING') {
            const crawled = job.pages ? job.pages.length : 0;
            progressPagesCount.textContent = `${crawled} / ${job.max_pages || maxPagesLimit}`;
            currentProcessingUrl.textContent = job.seed_url || 'Processing pages...';

            if (job.pages && job.pages.length > 0) {
                const lastPage = job.pages[job.pages.length - 1];
                if (progressDepth) progressDepth.textContent = `Depth ${lastPage.depth}`;
                if (progressLatency) progressLatency.textContent = `${lastPage.response_time_ms} ms`;
                if (lastPage.url) currentProcessingUrl.textContent = lastPage.url;
            }

            const pct = Math.min(100, Math.round((crawled / (job.max_pages || maxPagesLimit)) * 100));
            progressBarFill.style.width = `${pct}%`;

            if (crawled > 0) {
                logConsole(`✓ Processed ${crawled} page(s)...`, 'info');
            }
        } else if (status === 'COMPLETED') {
            progressBarFill.style.width = '100%';
            progressPagesCount.textContent = `${job.max_pages || maxPagesLimit} / ${job.max_pages || maxPagesLimit}`;
            if (statusPill) statusPill.className = 'status-pill completed';
            if (loaderIcon) {
                loaderIcon.className = 'success-icon';
                loaderIcon.textContent = '✓';
            }
            if (progressStatusText) progressStatusText.textContent = 'COMPLETED';
        }
    }

    function logConsole(message, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        const time = new Date().toLocaleTimeString();
        line.textContent = `[${time}] ${message}`;
        activityLog.appendChild(line);
        activityLog.scrollTop = activityLog.scrollHeight;
    }

    function startTimer() {
        startTime = Date.now();
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            const seconds = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
            const secs = (seconds % 60).toString().padStart(2, '0');
            elapsedTimeText.textContent = `${mins}:${secs}`;
        }, 1000);
    }

    function stopTimer() {
        clearInterval(timerInterval);
    }

    function stopPolling() {
        clearInterval(pollInterval);
    }

    function resetUI() {
        stopPolling();
        stopTimer();
        hideElement(emptyState);
        hideElement(completionCard);
        hideElement(errorCard);
        hideElement(statsSection);
        hideElement(resultsSection);
        hideElement(exportSection);
        progressBarFill.style.width = '0%';
        elapsedTimeText.textContent = '00:00';
        activityLog.innerHTML = '';
        resultsContainer.innerHTML = '';
        rawExtractedPages = [];
        if (searchInput) searchInput.value = '';

        if (statusPill) statusPill.className = 'status-pill running';
        if (loaderIcon) {
            loaderIcon.className = 'pulse-dot';
            loaderIcon.textContent = '';
        }
        if (progressStatusText) progressStatusText.textContent = 'FETCHING & EXTRACTING';
        if (progressDepth) progressDepth.textContent = 'Depth 0';
        if (progressLatency) progressLatency.textContent = '-- ms';
    }

    function showErrorState(msg) {
        errorMessage.textContent = msg;
        hideElement(progressCard);
        showElement(errorCard);
    }

    function disableForm(disabled) {
        startBtn.disabled = disabled;
        targetUrlInput.disabled = disabled;
        maxDepthInput.disabled = disabled;
        maxPagesInput.disabled = disabled;
        renderJsInput.disabled = disabled;

        if (disabled) {
            startBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Crawling in Progress...</span>';
        } else {
            startBtn.innerHTML = '<span class="btn-icon">🚀</span><span class="btn-text">Start Crawling</span>';
        }
    }

    function showElement(el) { if (el) el.classList.remove('hidden'); }
    function hideElement(el) { if (el) el.classList.add('hidden'); }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
