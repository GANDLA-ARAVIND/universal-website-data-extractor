/**
 * Universal Website Data Extractor - Frontend App Controller
 * Pure Vanilla JavaScript ES6 Async Client
 */

document.addEventListener('DOMContentLoaded', () => {
    // API BASE CONFIGURATION
    const API_BASE = '/api/v1';

    // DOM ELEMENTS - FORM & TABS
    const crawlForm = document.getElementById('crawl-form');
    const modeTabs = document.querySelectorAll('.mode-tabs .tab-btn');
    const singleUrlContainer = document.getElementById('single-url-container');
    const batchUrlContainer = document.getElementById('batch-url-container');
    const targetUrlInput = document.getElementById('target-url');
    const batchUrlsInput = document.getElementById('batch-urls');
    const csvFileInput = document.getElementById('csv-file-input');
    const maxDepthInput = document.getElementById('max-depth');
    const maxPagesInput = document.getElementById('max-pages');
    const renderJsInput = document.getElementById('render-js');
    const startBtn = document.getElementById('start-btn');

    // UI SECTIONS & CARDS
    const emptyState = document.getElementById('empty-state');
    const previewCard = document.getElementById('preview-card');
    const progressCard = document.getElementById('progress-card');
    const batchProgressCard = document.getElementById('batch-progress-card');
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

    // BATCH PROGRESS BINDINGS
    const batchStatusPill = document.getElementById('batch-status-pill');
    const batchProgressStatusText = document.getElementById('batch-progress-status-text');
    const batchTotalSites = document.getElementById('batch-total-sites');
    const batchCompletedSites = document.getElementById('batch-completed-sites');
    const batchRunningSites = document.getElementById('batch-running-sites');
    const batchFailedSites = document.getElementById('batch-failed-sites');
    const batchProgressBarFill = document.getElementById('batch-progress-bar-fill');
    const batchJobsTableBody = document.getElementById('batch-jobs-table-body');
    const retryFailedBtn = document.getElementById('retry-failed-btn');

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
    let currentMode = 'single'; // 'single' | 'batch'
    let currentJobId = null;
    let currentBatchId = null;
    let pollInterval = null;
    let timerInterval = null;
    let startTime = 0;
    let maxPagesLimit = 50;
    let rawExtractedPages = [];

    // -------------------------------------------------------------------------
    // 1. EVENT LISTENERS & MODE TABS
    // -------------------------------------------------------------------------
    modeTabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            modeTabs.forEach((t) => t.classList.remove('active'));
            tab.classList.add('active');
            currentMode = tab.getAttribute('data-mode');

            if (currentMode === 'batch') {
                hideElement(singleUrlContainer);
                showElement(batchUrlContainer);
                targetUrlInput.removeAttribute('required');
                batchUrlsInput.setAttribute('required', 'true');
            } else {
                hideElement(batchUrlContainer);
                showElement(singleUrlContainer);
                batchUrlsInput.removeAttribute('required');
                targetUrlInput.setAttribute('required', 'true');
            }
        });
    });

    if (csvFileInput) {
        csvFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (event) => {
                const text = event.target.result;
                const lines = text
                    .split(/\r?\n/)
                    .map((l) => l.trim())
                    .filter((l) => l.startsWith('http://') || l.startsWith('https://'));
                if (lines.length > 0) {
                    batchUrlsInput.value = lines.join('\n');
                } else {
                    alert('No valid HTTP/HTTPS URLs found in uploaded CSV file.');
                }
            };
            reader.readAsText(file);
        });
    }

    crawlForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (currentMode === 'single') {
            await startCrawlJob();
        } else {
            await startBatchCrawlJob();
        }
    });

    retryBtn.addEventListener('click', () => {
        hideElement(errorCard);
        if (currentMode === 'single') {
            startCrawlJob();
        } else {
            startBatchCrawlJob();
        }
    });

    if (retryFailedBtn) {
        retryFailedBtn.addEventListener('click', async () => {
            if (currentBatchId) {
                await retryFailedBatchWebsites(currentBatchId);
            }
        });
    }

    viewResultsBtn.addEventListener('click', () => {
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    });

    if (viewExportBtn) {
        viewExportBtn.addEventListener('click', () => {
            exportSection.scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Consolidated Export Buttons Listener (Single vs Batch)
    document.querySelectorAll('#export-section .export-btn').forEach((btn) => {
        btn.addEventListener('click', async () => {
            const format = btn.getAttribute('data-format');
            if (currentBatchId && format) {
                await downloadBatchExport(currentBatchId, format);
            } else if (currentJobId && format) {
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

    // -------------------------------------------------------------------------
    // 2. SINGLE WEBSITE CRAWL INITIATION & POLLING
    // -------------------------------------------------------------------------
    async function startCrawlJob() {
        const seedUrl = targetUrlInput.value.trim();
        const maxDepth = parseInt(maxDepthInput.value, 10);
        const maxPages = parseInt(maxPagesInput.value, 10);
        const renderJs = renderJsInput.checked;

        maxPagesLimit = maxPages;
        currentBatchId = null;

        resetUI();
        disableForm(true);

        showLivePreview(seedUrl, maxPages, renderJs);
        showElement(progressCard);
        logConsole(`Initializing single crawl job for ${seedUrl}...`, 'info');

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
    // 3. BATCH WEBSITE CRAWL INITIATION & POLLING
    // -------------------------------------------------------------------------
    async function startBatchCrawlJob() {
        const rawUrlsText = batchUrlsInput.value.trim();
        const urls = rawUrlsText
            .split(/\r?\n/)
            .map((u) => u.trim())
            .filter((u) => u.length > 0);

        if (urls.length === 0) {
            alert('Please enter at least one valid website URL.');
            return;
        }

        const maxDepth = parseInt(maxDepthInput.value, 10);
        const maxPages = parseInt(maxPagesInput.value, 10);
        const renderJs = renderJsInput.checked;

        currentJobId = null;
        resetUI();
        disableForm(true);

        showElement(batchProgressCard);
        hideElement(retryFailedBtn);

        try {
            const response = await fetch(`${API_BASE}/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    urls: urls,
                    max_depth: maxDepth,
                    max_pages: maxPages,
                    render_js: renderJs,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to initiate batch crawl job.');
            }

            const data = await response.json();
            currentBatchId = data.id;
            updateBatchUI(data);

            startBatchPolling(currentBatchId);
        } catch (err) {
            showErrorState(err.message);
            disableForm(false);
        }
    }

    function startBatchPolling(batchId) {
        clearInterval(pollInterval);
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/batch/${batchId}`);
                if (!response.ok) return;

                const batch = await response.json();
                updateBatchUI(batch);

                if (['COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED'].includes(batch.status)) {
                    stopPolling();
                    await handleBatchSuccess(batchId);
                }
            } catch (err) {
                console.error('Batch polling error:', err);
            }
        }, 1500);
    }

    function updateBatchUI(batch) {
        batchTotalSites.textContent = batch.total_urls;
        batchCompletedSites.textContent = batch.completed_urls;
        batchRunningSites.textContent = batch.running_urls;
        batchFailedSites.textContent = batch.failed_urls;

        batchProgressBarFill.style.width = `${batch.progress_percentage}%`;
        batchProgressStatusText.textContent = `BATCH ${batch.status}`;

        if (batch.failed_urls > 0) {
            showElement(retryFailedBtn);
        }

        // Render Child Jobs Table
        batchJobsTableBody.innerHTML = '';
        batch.jobs.forEach((j) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><a href="${j.seed_url}" target="_blank" class="code-font">${j.seed_url}</a></td>
                <td><span class="pill ${j.status === 'COMPLETED' ? 'success' : j.status === 'FAILED' ? 'error' : 'info'}">${j.status}</span></td>
                <td>${j.max_pages}</td>
                <td>--</td>
                <td>--</td>
                <td>--</td>
            `;
            batchJobsTableBody.appendChild(tr);
        });
    }

    async function retryFailedBatchWebsites(batchId) {
        hideElement(retryFailedBtn);
        try {
            const response = await fetch(`${API_BASE}/batch/${batchId}/retry`, {
                method: 'POST',
            });
            if (response.ok) {
                const batch = await response.json();
                updateBatchUI(batch);
                startBatchPolling(batchId);
            }
        } catch (err) {
            console.error('Retry failed batch error:', err);
        }
    }

    async function handleBatchSuccess(batchId) {
        try {
            const resStats = await fetch(`${API_BASE}/batch/${batchId}/statistics`);
            if (resStats.ok) {
                const bStats = await resStats.json();
                statPages.textContent = bStats.total_pages;
                statImages.textContent = bStats.total_images;
                statLinks.textContent = bStats.total_links;
                statDuration.textContent = `${bStats.total_duration_sec}s`;
                summaryDurationText.textContent = `Batch processed ${bStats.total_websites} websites (${bStats.total_pages} pages) in ${bStats.total_duration_sec}s.`;
            }
        } catch (err) {
            console.error('Fetch batch stats error:', err);
        }

        showElement(completionCard);
        showElement(statsSection);
        showElement(exportSection);
        disableForm(false);
    }

    // -------------------------------------------------------------------------
    // 4. SUCCESS HANDLER & DATA FETCHING (SINGLE CRAWL)
    // -------------------------------------------------------------------------
    async function handleCrawlSuccess(jobId) {
        logConsole('✓ Crawl completed successfully!', 'success');
        updateProgressUI('COMPLETED', { max_pages: maxPagesLimit });

        const stats = await fetchStatistics(jobId);
        if (stats) {
            statPages.textContent = stats.pages_crawled;
            statImages.textContent = stats.total_images;
            statLinks.textContent = stats.total_links;
            statDuration.textContent = `${stats.total_duration_sec}s`;
            summaryDurationText.textContent = `Processed ${stats.pages_crawled} pages in ${stats.total_duration_sec} seconds.`;
        }

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
    // 5. EXPORT DOWNLOAD HELPERS
    // -------------------------------------------------------------------------
    async function downloadExport(jobId, format) {
        try {
            const response = await fetch(`${API_BASE}/crawl/${jobId}/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: format }),
            });

            if (!response.ok) throw new Error('Export download failed.');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `crawl_export_${jobId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert(`Failed to download ${format.toUpperCase()} export: ${err.message}`);
        }
    }

    async function downloadBatchExport(batchId, format) {
        try {
            const response = await fetch(`${API_BASE}/batch/${batchId}/export`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: format }),
            });

            if (!response.ok) throw new Error('Batch export download failed.');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `batch_export_${batchId.slice(0, 8)}.${format === 'markdown' ? 'md' : format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert(`Failed to download batch ${format.toUpperCase()} export: ${err.message}`);
        }
    }

    // -------------------------------------------------------------------------
    // 6. UI RENDERERS & HELPERS
    // -------------------------------------------------------------------------
    function showLivePreview(urlStr, maxPages, renderJs) {
        try {
            const urlObj = new URL(urlStr);
            previewFavicon.src = `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=64`;
            previewDomain.textContent = urlObj.hostname;
        } catch {
            previewDomain.textContent = urlStr;
        }
        previewTitle.textContent = 'Initiating web fetch...';
        previewDesc.textContent = 'Extracting metadata, headings, paragraphs, and media assets...';
        previewMaxPages.textContent = `Max Pages: ${maxPages}`;
        previewMode.textContent = `Mode: ${renderJs ? 'Playwright JS' : 'Static HTML'}`;
        showElement(previewCard);
    }

    function updateFaviconPreview(firstPage) {
        if (firstPage.title) previewTitle.textContent = firstPage.title;
        if (firstPage.meta_description) previewDesc.textContent = firstPage.meta_description;
    }

    function updateProgressUI(status, job) {
        progressStatusText.textContent = status;
        if (job.pages_crawled !== undefined) {
            progressPagesCount.textContent = `${job.pages_crawled} / ${job.max_pages || maxPagesLimit}`;
            const pct = Math.min(100, Math.round((job.pages_crawled / (job.max_pages || maxPagesLimit)) * 100));
            progressBarFill.style.width = `${pct}%`;
        }
    }

    function filterAndRenderResults() {
        if (!resultsContainer) return;
        const query = (searchInput?.value || '').toLowerCase().trim();
        const sortBy = sortSelect?.value || 'default';

        let filtered = rawExtractedPages.filter((p) => {
            const titleMatch = (p.title || '').toLowerCase().includes(query);
            const urlMatch = (p.url || '').toLowerCase().includes(query);
            const descMatch = (p.meta_description || '').toLowerCase().includes(query);
            return titleMatch || urlMatch || descMatch;
        });

        if (sortBy === 'title') {
            filtered.sort((a, b) => (a.title || '').localeCompare(b.title || ''));
        } else if (sortBy === 'status') {
            filtered.sort((a, b) => a.status_code - b.status_code);
        } else if (sortBy === 'latency') {
            filtered.sort((a, b) => a.response_time_ms - b.response_time_ms);
        }

        resultsContainer.innerHTML = '';
        if (filtered.length === 0) {
            resultsContainer.innerHTML = '<div class="empty-results">No pages match your search query.</div>';
            return;
        }

        filtered.forEach((p, idx) => {
            const item = document.createElement('div');
            item.className = 'result-item';
            item.innerHTML = `
                <div class="result-item-header">
                    <span class="result-index">#${idx + 1}</span>
                    <a href="${p.url}" target="_blank" class="result-title">${p.title || 'Untitled Page'}</a>
                    <span class="pill ${p.status_code === 200 ? 'success' : 'info'}">${p.status_code} OK</span>
                </div>
                <div class="result-url-bar">${p.url}</div>
                ${p.meta_description ? `<p class="result-desc">${p.meta_description}</p>` : ''}
            `;
            resultsContainer.appendChild(item);
        });
    }

    function resetUI() {
        stopPolling();
        stopTimer();
        hideElement(emptyState);
        hideElement(previewCard);
        hideElement(progressCard);
        hideElement(batchProgressCard);
        hideElement(completionCard);
        hideElement(errorCard);
        hideElement(statsSection);
        hideElement(resultsSection);
        hideElement(exportSection);

        progressBarFill.style.width = '0%';
        batchProgressBarFill.style.width = '0%';
        elapsedTimeText.textContent = '00:00';
        activityLog.innerHTML = '';
    }

    function disableForm(disabled) {
        startBtn.disabled = disabled;
        targetUrlInput.disabled = disabled;
        batchUrlsInput.disabled = disabled;
        maxDepthInput.disabled = disabled;
        maxPagesInput.disabled = disabled;
        renderJsInput.disabled = disabled;
    }

    function showErrorState(msg) {
        hideElement(progressCard);
        hideElement(batchProgressCard);
        errorMessage.textContent = msg;
        showElement(errorCard);
    }

    function logConsole(msg, type = 'info') {
        const timeStr = new Date().toLocaleTimeString();
        const div = document.createElement('div');
        div.className = `log-line log-${type}`;
        div.innerHTML = `<span class="log-time">[${timeStr}]</span> ${msg}`;
        activityLog.appendChild(div);
        activityLog.scrollTop = activityLog.scrollHeight;
    }

    function startTimer() {
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsedMs = Date.now() - startTime;
            const sec = Math.floor(elapsedMs / 1000) % 60;
            const min = Math.floor(elapsedMs / 60000);
            elapsedTimeText.textContent = `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
        }, 1000);
    }

    function stopTimer() {
        clearInterval(timerInterval);
    }

    function stopPolling() {
        clearInterval(pollInterval);
    }

    function showElement(el) {
        if (el) el.classList.remove('hidden');
    }

    function hideElement(el) {
        if (el) el.classList.add('hidden');
    }
});
