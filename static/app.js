/**
 * Website Intelligence Platform — Production Frontend Application (Phase 5 Integrated)
 * Manages client-side routing, authentication state, real API communications,
 * live job monitoring, analysis workspace rendering, history, and exports.
 */

// Global Application State
window.currentUser = null;
window.userProjects = [];
window.activeProjectId = null;
window.currentAnalysisJobId = null;
window.currentAnalysisBatchId = null;

let singleCrawlPollInterval = null;
let batchCrawlPollInterval = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Render Lucide Icons
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons();
    }

    // View Mapping & Breadcrumbs Titles
    const VIEW_NAMES = {
        'landing': 'Product Overview',
        'dashboard': 'Dashboard',
        'single-crawl': 'Single Crawl',
        'batch-crawl': 'Batch Crawl',
        'analysis': 'Website Analysis',
        'history': 'Crawl History',
        'settings': 'Settings',
        'ai-workspace': 'AI Workspace'
    };

    // DOM Elements
    const sidebar = document.getElementById('sidebar');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const breadcrumbCurrent = document.getElementById('breadcrumb-current');
    const navItems = document.querySelectorAll('.nav-item[data-view]');
    const pageViews = document.querySelectorAll('.page-view');

    // Command Palette Elements
    const cmdTriggerBtn = document.getElementById('cmd-trigger-btn');
    const cmdBackdrop = document.getElementById('command-palette-backdrop');
    const cmdSearchInput = document.getElementById('cmd-search-input');
    const cmdItems = document.querySelectorAll('.cmd-item');
    let selectedCmdIndex = -1;

    // --------------------------------------------------------------------------
    // 1. Client-Side Hash Router & View Change Listener
    // --------------------------------------------------------------------------
    async function navigateToView(viewId) {
        if (!VIEW_NAMES[viewId]) {
            viewId = 'dashboard';
        }

        // Update Nav Link Active States
        navItems.forEach(item => {
            if (item.getAttribute('data-view') === viewId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Switch Visible Page View Container
        pageViews.forEach(view => {
            if (view.id === `view-${viewId}`) {
                view.classList.add('active');
            } else {
                view.classList.remove('active');
            }
        });

        // Update Breadcrumb Text
        if (breadcrumbCurrent) {
            breadcrumbCurrent.textContent = VIEW_NAMES[viewId];
        }

        // Close Mobile Sidebar if Open
        if (sidebar) {
            sidebar.classList.remove('mobile-open');
        }

        // Scroll Canvas to Top
        const canvas = document.querySelector('.main-canvas');
        if (canvas) {
            canvas.scrollTop = 0;
        }

        // Clear Polling Intervals on Navigation
        if (viewId !== 'single-crawl' && singleCrawlPollInterval) {
            clearInterval(singleCrawlPollInterval);
            singleCrawlPollInterval = null;
        }
        if (viewId !== 'batch-crawl' && batchCrawlPollInterval) {
            clearInterval(batchCrawlPollInterval);
            batchCrawlPollInterval = null;
        }

        // View-Specific Initializers
        if (viewId === 'dashboard') {
            await window.loadDashboardData();
        } else if (viewId === 'history') {
            await window.loadHistoryData();
        } else if (viewId === 'analysis') {
            await window.loadAnalysisWorkspace(window.currentAnalysisJobId, window.currentAnalysisBatchId);
        } else if (viewId === 'settings') {
            window.loadSettingsView();
        } else if (viewId === 'ai-workspace') {
            await window.loadAiWorkspaceView();
        }

        if (window.lucide) window.lucide.createIcons();
    }

    function handleHashChange() {
        const hash = window.location.hash.replace('#', '') || 'dashboard';
        navigateToView(hash);
    }

    window.addEventListener('hashchange', handleHashChange);

    // --------------------------------------------------------------------------
    // 2. Mobile Drawer Toggle
    // --------------------------------------------------------------------------
    if (mobileMenuToggle && sidebar) {
        mobileMenuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebar.classList.toggle('mobile-open');
        });

        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('mobile-open') && !sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        });
    }

    // --------------------------------------------------------------------------
    // 3. Global Command Palette
    // --------------------------------------------------------------------------
    function openCommandPalette() {
        if (!cmdBackdrop) return;
        cmdBackdrop.classList.add('open');
        selectedCmdIndex = -1;
        updateCmdSelection();
        setTimeout(() => {
            if (cmdSearchInput) {
                cmdSearchInput.value = '';
                cmdSearchInput.focus();
                filterCmdItems('');
            }
        }, 50);
    }

    function closeCommandPalette() {
        if (!cmdBackdrop) return;
        cmdBackdrop.classList.remove('open');
    }

    if (cmdTriggerBtn) {
        cmdTriggerBtn.addEventListener('click', openCommandPalette);
    }

    if (cmdBackdrop) {
        cmdBackdrop.addEventListener('click', (e) => {
            if (e.target === cmdBackdrop) {
                closeCommandPalette();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;

        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (cmdBackdrop && cmdBackdrop.classList.contains('open')) {
                closeCommandPalette();
            } else {
                openCommandPalette();
            }
            return;
        }

        if (e.key === '/' && !isInput) {
            e.preventDefault();
            openCommandPalette();
            return;
        }

        if (e.key === 'Escape' && cmdBackdrop && cmdBackdrop.classList.contains('open')) {
            closeCommandPalette();
            return;
        }

        if (cmdBackdrop && cmdBackdrop.classList.contains('open')) {
            const visibleItems = Array.from(cmdItems).filter(item => item.style.display !== 'none');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (visibleItems.length > 0) {
                    selectedCmdIndex = (selectedCmdIndex + 1) % visibleItems.length;
                    updateCmdSelection(visibleItems);
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (visibleItems.length > 0) {
                    selectedCmdIndex = (selectedCmdIndex - 1 + visibleItems.length) % visibleItems.length;
                    updateCmdSelection(visibleItems);
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (selectedCmdIndex >= 0 && selectedCmdIndex < visibleItems.length) {
                    executeCmdItem(visibleItems[selectedCmdIndex]);
                }
            }
        }
    });

    if (cmdSearchInput) {
        cmdSearchInput.addEventListener('input', (e) => {
            filterCmdItems(e.target.value.toLowerCase().trim());
        });
    }

    function filterCmdItems(query) {
        let visibleCount = 0;
        cmdItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (!query || text.includes(query)) {
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });
        selectedCmdIndex = visibleCount > 0 ? 0 : -1;
        updateCmdSelection();
    }

    function updateCmdSelection(visibleItems) {
        const items = visibleItems || Array.from(cmdItems).filter(item => item.style.display !== 'none');
        cmdItems.forEach(item => item.classList.remove('selected'));
        if (selectedCmdIndex >= 0 && selectedCmdIndex < items.length) {
            items[selectedCmdIndex].classList.add('selected');
            items[selectedCmdIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    function executeCmdItem(item) {
        const action = item.getAttribute('data-action');
        const target = item.getAttribute('data-target');
        closeCommandPalette();
        if (action === 'nav' && target) {
            window.location.hash = target;
        } else if (action === 'ai') {
            window.location.hash = 'ai-workspace';
        }
    }

    cmdItems.forEach(item => {
        item.addEventListener('click', () => executeCmdItem(item));
    });

    // --------------------------------------------------------------------------
    // 4. Initialize Auth & Router Startup
    // --------------------------------------------------------------------------
    await window.initAuthSession();
    handleHashChange();
});

// ============================================================================
// AUTHENTICATION & WORKSPACE PROJECT MANAGER
// ============================================================================
window.initAuthSession = async function () {
    const authContainer = document.getElementById('header-auth-container');
    const projectContainer = document.getElementById('header-project-container');

    try {
        const user = await API.auth.me();
        window.currentUser = user;

        if (authContainer) {
            authContainer.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 12px; font-weight: 600; color: var(--text-primary);">${user.email}</span>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="window.handleLogout()">
                        <i data-lucide="log-out" style="width: 14px; height: 14px;"></i>
                        <span>Logout</span>
                    </button>
                </div>
            `;
        }

        await window.loadUserProjects();
    } catch (err) {
        window.currentUser = null;
        window.activeProjectId = null;

        if (authContainer) {
            authContainer.innerHTML = `
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.showAuthModal()">
                    <i data-lucide="user" style="width: 14px; height: 14px;"></i>
                    <span>Sign In</span>
                </button>
            `;
        }

        if (projectContainer) {
            projectContainer.style.display = 'none';
        }
    }

    if (window.lucide) window.lucide.createIcons();
};

window.handleLogout = async function () {
    try {
        await API.auth.logout();
        window.showToast({ type: 'info', title: 'Logged Out', message: 'User session ended successfully.' });
    } catch (err) {
        console.error(err);
    }
    await window.initAuthSession();
};

window.showAuthModal = function () {
    let activeMode = 'login'; // 'login' or 'register'

    const modalBody = document.createElement('div');
    modalBody.innerHTML = `
        <div class="tabs-container" style="margin-bottom: 16px;">
            <div class="tab-item active" id="auth-tab-login" style="cursor: pointer;">Sign In</div>
            <div class="tab-item" id="auth-tab-register" style="cursor: pointer;">Create Account</div>
        </div>
        <form id="auth-form" style="display: flex; flex-direction: column; gap: 14px;">
            <div class="form-field">
                <label class="form-label">Email Address</label>
                <input type="email" id="auth-email" class="input-text" placeholder="user@example.com" required>
            </div>
            <div class="form-field">
                <label class="form-label">Password</label>
                <input type="password" id="auth-password" class="input-text" placeholder="Minimum 8 characters" required minlength="8">
            </div>
            <div id="auth-error-msg" class="form-error-msg" style="display: none; font-size: 12px; color: var(--status-error);"></div>
            <button type="submit" id="auth-submit-btn" class="btn btn-primary btn-md" style="margin-top: 8px;">
                <span>Sign In</span>
            </button>
        </form>
    `;

    const modal = window.UI.modal({
        title: 'Platform Authentication',
        content: modalBody,
        actions: [],
    });

    const tabLogin = modalBody.querySelector('#auth-tab-login');
    const tabRegister = modalBody.querySelector('#auth-tab-register');
    const submitBtn = modalBody.querySelector('#auth-submit-btn');
    const errorMsg = modalBody.querySelector('#auth-error-msg');
    const form = modalBody.querySelector('#auth-form');

    tabLogin.addEventListener('click', () => {
        activeMode = 'login';
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        submitBtn.querySelector('span').textContent = 'Sign In';
        errorMsg.style.display = 'none';
    });

    tabRegister.addEventListener('click', () => {
        activeMode = 'register';
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
        submitBtn.querySelector('span').textContent = 'Create Account';
        errorMsg.style.display = 'none';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = modalBody.querySelector('#auth-email').value.trim();
        const password = modalBody.querySelector('#auth-password').value;

        submitBtn.classList.add('loading');
        errorMsg.style.display = 'none';

        try {
            if (activeMode === 'register') {
                await API.auth.register(email, password);
                window.showToast({ type: 'success', title: 'Account Created', message: 'Signing in...' });
            }
            await API.auth.login(email, password);
            window.showToast({ type: 'success', title: 'Authentication Successful', message: `Welcome ${email}` });

            modal.classList.remove('open');
            setTimeout(() => modal.remove(), 150);

            await window.initAuthSession();
        } catch (err) {
            submitBtn.classList.remove('loading');
            errorMsg.textContent = err.message || 'Authentication failed. Please check credentials.';
            errorMsg.style.display = 'block';
        }
    });
};

window.loadUserProjects = async function () {
    const projectContainer = document.getElementById('header-project-container');
    const selectEl = document.getElementById('header-project-select');

    if (!window.currentUser || !projectContainer || !selectEl) return;

    try {
        const res = await API.projects.list(1, 100);
        window.userProjects = res.data || [];

        selectEl.innerHTML = `<option value="">Default (No Project)</option>`;
        window.userProjects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            if (p.id === window.activeProjectId) opt.selected = true;
            selectEl.appendChild(opt);
        });

        const newOpt = document.createElement('option');
        newOpt.value = "__create_new__";
        newOpt.textContent = "+ Create New Project...";
        selectEl.appendChild(newOpt);

        projectContainer.style.display = 'flex';

        selectEl.onchange = (e) => {
            const val = e.target.value;
            if (val === '__create_new__') {
                selectEl.value = window.activeProjectId || '';
                window.showCreateProjectModal();
            } else {
                window.activeProjectId = val || null;
                window.showToast({ type: 'info', title: 'Active Workspace Changed', message: val ? `Project selected` : 'Unassigned workspace' });
            }
        };
    } catch (err) {
        console.error("Failed to load user projects", err);
    }
};

window.showCreateProjectModal = function () {
    const body = document.createElement('div');
    body.innerHTML = `
        <form id="create-project-form" style="display: flex; flex-direction: column; gap: 14px;">
            <div class="form-field">
                <label class="form-label">Project Name</label>
                <input type="text" id="proj-name-input" class="input-text" placeholder="e.g. SaaS Competitors Audit" required minlength="1">
            </div>
            <div class="form-field">
                <label class="form-label">Description (Optional)</label>
                <textarea id="proj-desc-input" class="textarea-control" rows="3" placeholder="Notes or description..."></textarea>
            </div>
        </form>
    `;

    const modal = window.UI.modal({
        title: 'Create Workspace Project',
        content: body,
        actions: [
            {
                label: 'Create Project',
                variant: 'primary',
                onClick: async () => {
                    const name = body.querySelector('#proj-name-input').value.trim();
                    const desc = body.querySelector('#proj-desc-input').value.trim();

                    if (!name) return;

                    try {
                        const proj = await API.projects.create(name, desc);
                        window.activeProjectId = proj.id;
                        window.showToast({ type: 'success', title: 'Project Created', message: `Project '${name}' initialized.` });
                        await window.loadUserProjects();
                    } catch (err) {
                        window.showToast({ type: 'error', title: 'Project Creation Failed', message: err.message });
                    }
                }
            }
        ]
    });
};

// ============================================================================
// DASHBOARD REAL DATA LOADER
// ============================================================================
window.loadDashboardData = async function () {
    try {
        const jobsRes = await API.crawl.list({ page: 1, pageSize: 50 });
        const jobs = jobsRes.data || [];

        const completedCount = jobs.filter(j => j.status === 'COMPLETED').length;
        const totalJobs = jobs.length;
        const successRate = totalJobs > 0 ? ((completedCount / totalJobs) * 100).toFixed(1) : '100.0';

        // Summary bar
        const statsBar = document.querySelector('.canvas-container .page-view#view-dashboard > div[style*="margin-bottom: 24px;"]');
        if (statsBar) {
            statsBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 6px;">
                    <i data-lucide="bar-chart-2" style="width:14px; height:14px; color: var(--accent-primary);"></i>
                    <span><strong>Total Crawls:</strong> ${totalJobs}</span>
                </div>
                <span style="color: var(--border-strong);">•</span>
                <div><strong>Completed:</strong> ${completedCount}</div>
                <span style="color: var(--border-strong);">•</span>
                <div><strong>Success Rate:</strong> <span style="color: var(--status-success); font-weight: 600;">${successRate}%</span></div>
                <span style="color: var(--border-strong);">•</span>
                <div><strong>Projects:</strong> ${window.userProjects ? window.userProjects.length : 0}</div>
            `;
        }

        // Recent Jobs Table / List
        const recentJobsSlot = document.getElementById('dashboard-recent-jobs-list');
        if (recentJobsSlot) {
            recentJobsSlot.innerHTML = '';
            if (jobs.length === 0) {
                recentJobsSlot.appendChild(window.createEmptyState({
                    icon: 'globe',
                    title: 'No Crawl Jobs Executed Yet',
                    description: 'Initiate a Single Crawl or Multi-Website Batch Crawl to inspect live extraction activity.',
                    actionText: 'Start First Crawl',
                    onAction: () => { window.location.hash = 'single-crawl'; }
                }));
            } else {
                jobs.slice(0, 5).forEach(job => {
                    const card = document.createElement('div');
                    card.className = 'card card-interactive';
                    card.style.marginBottom = '8px';
                    card.style.padding = '12px 16px';
                    card.style.display = 'flex';
                    card.style.alignItems = 'center';
                    card.style.justifyContent = 'space-between';

                    const statusBadgeClass = job.status === 'COMPLETED' ? 'badge-success' : (job.status === 'FAILED' ? 'badge-danger' : 'badge-info');

                    card.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <i data-lucide="globe" style="width:16px; height:16px; color: var(--accent-primary);"></i>
                            <div>
                                <div style="font-weight: 600; font-size: 13px; color: var(--text-primary);">${job.seed_url}</div>
                                <div style="font-size: 11px; color: var(--text-muted);">${new Date(job.created_at).toLocaleString()} • Mode: ${job.crawl_mode}</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span class="badge ${statusBadgeClass}">${job.status}</span>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); window.openAnalysisForJob('${job.id}')">
                                View Analysis
                            </button>
                        </div>
                    `;
                    recentJobsSlot.appendChild(card);
                });
            }
        }
    } catch (err) {
        console.error("Error loading dashboard data:", err);
    }
    if (window.lucide) window.lucide.createIcons();
};

// ============================================================================
// SINGLE CRAWL WORKFLOW STATE MANAGER (REAL BACKEND INTEGRATION)
// ============================================================================
window.startSingleCrawlWorkflow = async function () {
    const urlInput = document.getElementById('single-url-input');
    const depthSelect = document.getElementById('single-depth-select');
    const pagesSelect = document.getElementById('single-pages-select');
    const renderJsToggle = document.getElementById('single-render-js-toggle');

    const seedUrl = urlInput ? urlInput.value.trim() : '';
    if (!seedUrl || (!seedUrl.startsWith('http://') && !seedUrl.startsWith('https://'))) {
        window.showToast({ type: 'error', title: 'Invalid Target URL', message: 'Please enter a valid HTTP or HTTPS website URL.' });
        return;
    }

    const state1 = document.getElementById('single-crawl-state-1');
    const state2 = document.getElementById('single-crawl-state-2');
    const state3 = document.getElementById('single-crawl-state-3');

    if (state1) state1.style.display = 'none';
    if (state2) state2.style.display = 'block';
    if (state3) state3.style.display = 'none';

    document.getElementById('single-live-url').textContent = seedUrl;

    const consoleBox = document.getElementById('single-console-logs');
    if (consoleBox) consoleBox.innerHTML = '';

    function logConsole(msg, type = 'info') {
        if (!consoleBox) return;
        const timeStr = new Date().toTimeString().split(' ')[0];
        const line = document.createElement('div');
        line.className = 'console-log-line';
        line.innerHTML = `<span class="console-time">[${timeStr}]</span><span class="console-${type}">${msg}</span>`;
        consoleBox.appendChild(line);
        consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    logConsole(`Submitting Single Crawl job to REST API (/api/v1/crawl)...`, 'info');

    try {
        const job = await API.crawl.create({
            url: seedUrl,
            maxDepth: parseInt(depthSelect.value),
            maxPages: parseInt(pagesSelect.value),
            renderJs: renderJsToggle.checked,
            projectId: window.activeProjectId,
        });

        document.getElementById('single-live-job-id').textContent = job.id.substring(0, 8) + '...';
        logConsole(`Job initialized with UUID: ${job.id}. Status: PENDING`, 'success');
        window.showToast({ type: 'info', title: 'Crawl Job Dispatched', message: `Job ID: ${job.id}` });

        clearInterval(singleCrawlPollInterval);

        const startTime = Date.now();

        singleCrawlPollInterval = setInterval(async () => {
            try {
                const currentJob = await API.crawl.get(job.id);
                const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(1);
                document.getElementById('single-live-elapsed').textContent = `${elapsedSec}s`;

                if (currentJob.status === 'RUNNING') {
                    logConsole(`Extractor active on target domain... Status: RUNNING (${elapsedSec}s)`, 'info');
                    document.getElementById('single-live-progress-fill').style.width = `50%`;
                }

                if (currentJob.status === 'COMPLETED') {
                    clearInterval(singleCrawlPollInterval);
                    document.getElementById('single-live-progress-fill').style.width = `100%`;
                    logConsole(`Crawl Job ${job.id} COMPLETED cleanly. Fetching statistics...`, 'success');

                    const stats = await API.crawl.statistics(job.id).catch(() => ({ pages_crawled: 1, total_images: 0, total_links: 0 }));

                    document.getElementById('live-stat-pages').textContent = stats.pages_crawled || 1;
                    document.getElementById('live-stat-images').textContent = stats.total_images || 0;
                    document.getElementById('live-stat-links').textContent = stats.total_links || 0;

                    setTimeout(() => {
                        if (state2) state2.style.display = 'none';
                        if (state3) state3.style.display = 'block';

                        document.getElementById('complete-target-url').textContent = seedUrl;
                        document.getElementById('complete-duration').textContent = `${stats.total_duration_sec || elapsedSec}s`;
                        document.getElementById('complete-stat-pages').textContent = stats.pages_crawled || 1;
                        document.getElementById('complete-stat-images').textContent = stats.total_images || 0;

                        window.currentAnalysisJobId = job.id;
                        window.currentAnalysisBatchId = null;

                        window.showToast({ type: 'success', title: 'Crawl Completed', message: `Successfully extracted target URL.` });
                    }, 500);
                } else if (currentJob.status === 'FAILED') {
                    clearInterval(singleCrawlPollInterval);
                    logConsole(`Crawl Job ${job.id} FAILED.`, 'error');
                    window.showToast({ type: 'error', title: 'Crawl Failed', message: 'Target domain crawl encountered an error.' });
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 1500);

    } catch (err) {
        window.showToast({ type: 'error', title: 'Crawl Submission Error', message: err.message });
        window.resetSingleCrawlWorkflow();
    }
};

window.cancelSingleCrawlWorkflow = function () {
    clearInterval(singleCrawlPollInterval);
    window.showToast({ type: 'warning', title: 'Crawl Cancelled', message: 'Single crawl job monitoring stopped.' });
    window.resetSingleCrawlWorkflow();
};

window.resetSingleCrawlWorkflow = function () {
    clearInterval(singleCrawlPollInterval);
    const state1 = document.getElementById('single-crawl-state-1');
    const state2 = document.getElementById('single-crawl-state-2');
    const state3 = document.getElementById('single-crawl-state-3');

    if (state1) state1.style.display = 'block';
    if (state2) state2.style.display = 'none';
    if (state3) state3.style.display = 'none';
};

// ============================================================================
// BATCH CRAWL WORKFLOW STATE MANAGER (REAL BACKEND INTEGRATION)
// ============================================================================
window.handleBatchFileSelect = function (event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        const text = e.target.result;
        const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
        const urls = lines.filter(l => l.startsWith('http://') || l.startsWith('https://'));
        if (urls.length > 0) {
            const txtarea = document.getElementById('batch-urls-textarea');
            if (txtarea) txtarea.value = urls.join('\n');
            window.showToast({ type: 'success', title: 'File Parsed Successfully', message: `Extracted ${urls.length} target URLs from ${file.name}` });
        } else {
            window.showToast({ type: 'warning', title: 'No Valid URLs Found', message: 'The uploaded file did not contain HTTP or HTTPS URLs.' });
        }
    };
    reader.readAsText(file);
};

window.startBatchCrawlWorkflow = async function () {
    const txtarea = document.getElementById('batch-urls-textarea');
    const depthSelect = document.getElementById('batch-depth-select');
    const pagesSelect = document.getElementById('batch-pages-select');
    const renderJsToggle = document.getElementById('batch-render-js-toggle');

    const urlsRaw = txtarea ? txtarea.value.trim().split('\n').map(u => u.trim()).filter(u => u.length > 0) : [];
    if (urlsRaw.length === 0) {
        window.showToast({ type: 'error', title: 'No Target URLs Entered', message: 'Please enter at least one target website URL.' });
        return;
    }

    const state1 = document.getElementById('batch-crawl-state-1');
    const state2 = document.getElementById('batch-crawl-state-2');
    const state3 = document.getElementById('batch-crawl-state-3');

    if (state1) state1.style.display = 'none';
    if (state2) state2.style.display = 'block';
    if (state3) state3.style.display = 'none';

    const consoleBox = document.getElementById('batch-console-logs');
    if (consoleBox) consoleBox.innerHTML = '';

    function logBatchConsole(msg, type = 'info') {
        if (!consoleBox) return;
        const timeStr = new Date().toTimeString().split(' ')[0];
        const line = document.createElement('div');
        line.className = 'console-log-line';
        line.innerHTML = `<span class="console-time">[${timeStr}]</span><span class="console-${type}">${msg}</span>`;
        consoleBox.appendChild(line);
        consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    logBatchConsole(`Initiating multi-website batch crawl for ${urlsRaw.length} targets...`, 'info');

    try {
        const batch = await API.batch.create({
            urls: urlsRaw,
            maxDepth: parseInt(depthSelect.value),
            maxPages: parseInt(pagesSelect.value),
            renderJs: renderJsToggle.checked,
            projectId: window.activeProjectId,
        });

        const batchIdEl = document.getElementById('batch-live-id');
        if (batchIdEl) batchIdEl.textContent = batch.id.substring(0, 8) + '...';

        logBatchConsole(`Batch Job #${batch.id} created with ${batch.total_urls} URLs. Status: PENDING`, 'success');
        window.showToast({ type: 'info', title: 'Batch Crawl Initiated', message: `Batch ID: ${batch.id}` });

        clearInterval(batchCrawlPollInterval);

        batchCrawlPollInterval = setInterval(async () => {
            try {
                const currentBatch = await API.batch.get(batch.id);

                const fillBar = document.getElementById('batch-live-progress-fill');
                if (fillBar) fillBar.style.width = `${currentBatch.progress_percentage}%`;

                logBatchConsole(`Batch Progress: ${currentBatch.progress_percentage}% (${currentBatch.completed_urls}/${currentBatch.total_urls} Completed)`, 'info');

                if (currentBatch.status === 'COMPLETED' || currentBatch.status === 'PARTIALLY_COMPLETED' || currentBatch.status === 'FAILED') {
                    clearInterval(batchCrawlPollInterval);
                    logBatchConsole(`Batch execution completed. Status: ${currentBatch.status}`, 'success');

                    setTimeout(() => {
                        if (state2) state2.style.display = 'none';
                        if (state3) state3.style.display = 'block';

                        window.currentAnalysisBatchId = batch.id;
                        window.currentAnalysisJobId = null;

                        window.showToast({ type: 'success', title: 'Batch Crawl Completed', message: 'Multi-website dataset ready for analysis.' });
                    }, 600);
                }
            } catch (err) {
                console.error("Batch Polling error:", err);
            }
        }, 2000);

    } catch (err) {
        window.showToast({ type: 'error', title: 'Batch Submission Error', message: err.message });
        window.resetBatchCrawlWorkflow();
    }
};

window.cancelBatchCrawlWorkflow = function () {
    clearInterval(batchCrawlPollInterval);
    window.showToast({ type: 'warning', title: 'Batch Cancelled', message: 'Batch crawl monitoring stopped.' });
    window.resetBatchCrawlWorkflow();
};

window.resetBatchCrawlWorkflow = function () {
    clearInterval(batchCrawlPollInterval);
    const state1 = document.getElementById('batch-crawl-state-1');
    const state2 = document.getElementById('batch-crawl-state-2');
    const state3 = document.getElementById('batch-crawl-state-3');

    if (state1) state1.style.display = 'block';
    if (state2) state2.style.display = 'none';
    if (state3) state3.style.display = 'none';
};

// ============================================================================
// WEBSITE ANALYSIS WORKSPACE SERVICES (REAL DATASET RENDERING & EXPORTS)
// ============================================================================
window.loadAnalysisWorkspace = async function (jobId, batchId) {
    const targetJobId = jobId || window.currentAnalysisJobId;
    const targetBatchId = batchId || window.currentAnalysisBatchId;

    if (!targetJobId && !targetBatchId) {
        return;
    }

    try {
        let dataset = null;
        let job = null;

        if (targetJobId) {
            dataset = await API.crawl.dataset(targetJobId);
            job = await API.crawl.get(targetJobId);
        } else if (targetBatchId) {
            const bDataset = await API.batch.dataset(targetBatchId);
            dataset = bDataset.websites && bDataset.websites.length > 0 && bDataset.websites[0].dataset ? bDataset.websites[0].dataset : null;
            job = await API.batch.get(targetBatchId);
        }

        if (!dataset) return;

        const websiteInfo = dataset.website_info || {};
        const seedUrl = websiteInfo.seed_url || dataset.seed_url || '';
        let domainName = websiteInfo.domain || '';
        if (!domainName && seedUrl) {
            try { domainName = new URL(seedUrl).hostname; } catch (e) { domainName = seedUrl; }
        }

        // Render Header Metadata
        const siteNameEl = document.getElementById('analysis-site-name');
        const targetUrlEl = document.getElementById('analysis-target-url');
        const jsonCodeEl = document.getElementById('analysis-json-code');

        if (siteNameEl) siteNameEl.textContent = domainName || 'Website Analysis';
        if (targetUrlEl && seedUrl) {
            targetUrlEl.textContent = seedUrl;
            targetUrlEl.href = seedUrl;
        }

        if (jsonCodeEl) {
            jsonCodeEl.textContent = JSON.stringify(dataset, null, 2);
        }

        // Overview tab stats
        const stats = dataset.statistics || dataset.stats || {};
        const summary = dataset.summary || {};
        const pages = dataset.pages || [];

        const statPagesEl = document.querySelector('#analysis-tab-overview .card-stat-val');
        if (statPagesEl) statPagesEl.textContent = stats.pages_crawled || pages.length;

        // Bind Export Download Buttons inside Analysis
        const btnHeaderPdf = document.querySelector('#view-analysis button[onclick*="ycombinator_report.pdf"]');
        if (btnHeaderPdf) {
            btnHeaderPdf.onclick = () => window.triggerExportDownload(targetJobId || targetBatchId, 'pdf', !!targetBatchId);
        }
        const btnHeaderDataset = document.querySelector('#view-analysis button[onclick*="ycombinator_dataset.json"]');
        if (btnHeaderDataset) {
            btnHeaderDataset.onclick = () => window.triggerExportDownload(targetJobId || targetBatchId, 'json', !!targetBatchId);
        }

        // Render Pages Tab List
        const pagesContainer = document.querySelector('#analysis-tab-pages .master-list-panel div[style*="display: flex; flex-direction: column"]');
        if (pagesContainer && pages.length > 0) {
            pagesContainer.innerHTML = '';
            pages.forEach((p, idx) => {
                const node = document.createElement('div');
                node.className = `tree-node ${idx === 0 ? 'active' : ''}`;
                node.style.flexDirection = 'column';
                node.style.alignItems = 'flex-start';
                node.style.cursor = 'pointer';

                node.innerHTML = `
                    <div style="font-weight: 600; color: var(--text-primary); word-break: break-word; overflow-wrap: break-word;">${p.title || 'Untitled Page'}</div>
                    <div style="font-size: 11px; color: var(--text-muted); word-break: break-all; overflow-wrap: anywhere;">${p.url}</div>
                    <div style="display: flex; gap: 6px; margin-top: 4px;">
                        <span class="badge badge-success">${p.status_code || 200} OK</span>
                        <span class="badge badge-neutral">Depth ${p.depth || 1}</span>
                    </div>
                `;

                node.onclick = () => {
                    pagesContainer.querySelectorAll('.tree-node').forEach(n => n.classList.remove('active'));
                    node.classList.add('active');
                    window.renderPageDetailPanel(p);
                };

                pagesContainer.appendChild(node);
            });

            // Initial detail render
            window.renderPageDetailPanel(pages[0]);
        }

    } catch (err) {
        console.error("Error loading analysis workspace:", err);
    }

    if (window.lucide) window.lucide.createIcons();
};

window.renderPageDetailPanel = function (page) {
    const detailPanel = document.querySelector('#analysis-tab-pages .detail-view-panel');
    if (!detailPanel || !page) return;

    const headings = page.headings || {};
    let headingsHTML = '';
    for (const [tag, items] of Object.entries(headings)) {
        if (Array.isArray(items)) {
            items.forEach(h => {
                headingsHTML += `<div style="word-break: break-word; overflow-wrap: break-word;"><strong>${tag.toUpperCase()}:</strong> ${h}</div>`;
            });
        }
    }

    const paragraphs = page.paragraphs || [];
    const textSnippet = paragraphs.slice(0, 3).join(' ');

    detailPanel.innerHTML = `
        <div style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; word-break: break-word; overflow-wrap: break-word;">${page.title || 'Extracted Page'}</div>
        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 16px; word-break: break-all; overflow-wrap: anywhere;">URL: <code style="word-break: break-all; overflow-wrap: anywhere;">${page.url}</code></div>

        <div style="margin-bottom: 20px;">
            <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">Extracted Headings (H1-H6)</div>
            <div style="background-color: var(--bg-app); padding: 12px; border-radius: 6px; font-size: 12px; line-height: 1.6; word-break: break-word; overflow-wrap: break-word;">
                ${headingsHTML || '<em>No heading tags extracted from this page.</em>'}
            </div>
        </div>

        <div>
            <div style="font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">Clean Text Paragraph Snippet</div>
            <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.6; background-color: var(--bg-app); padding: 12px; border-radius: 6px; word-break: break-word; overflow-wrap: break-word;">
                ${textSnippet || '<em>No body text paragraphs extracted.</em>'}
            </p>
        </div>
    `;
};

window.switchAnalysisTab = function (tabName, btnEl) {
    const allPanes = document.querySelectorAll('.analysis-tab-pane');
    allPanes.forEach(pane => pane.style.display = 'none');

    const activePane = document.getElementById(`analysis-tab-${tabName}`);
    if (activePane) activePane.style.display = 'block';

    if (btnEl && btnEl.parentNode) {
        const siblings = btnEl.parentNode.querySelectorAll('.tab-item');
        siblings.forEach(s => s.classList.remove('active'));
        btnEl.classList.add('active');
    }

    if (window.lucide) window.lucide.createIcons();
};

window.triggerExportDownload = async function (id, format, isBatch = false) {
    if (!id) {
        window.showToast({ type: 'error', title: 'Export Failed', message: 'No active job or batch selected.' });
        return;
    }

    window.showLoading({ message: `Generating ${format.toUpperCase()} Export File...`, subtext: 'Compiling dataset formatting' });

    try {
        const result = isBatch ? await API.batch.export(id, format) : await API.crawl.export(id, format);
        window.hideLoading();

        const blobUrl = window.URL.createObjectURL(result.blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = result.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);

        window.showToast({ type: 'success', title: 'File Export Ready', message: `Downloaded ${result.filename}` });
    } catch (err) {
        window.hideLoading();
        window.showToast({ type: 'error', title: 'Export Failed', message: err.message });
    }
};

// ============================================================================
// CRAWL HISTORY WORKSPACE SERVICES (REAL BACKEND INTEGRATION)
// ============================================================================
window.loadHistoryData = async function () {
    const cardsView = document.getElementById('history-cards-view');
    const emptySlot = document.getElementById('history-empty-slot');

    if (!cardsView) return;

    const searchVal = (document.getElementById('history-search-input')?.value || '').trim();
    const modeVal = document.getElementById('history-mode-filter')?.value || 'ALL';
    const statusVal = document.getElementById('history-status-filter')?.value || 'ALL';

    try {
        const res = await API.crawl.list({
            page: 1,
            pageSize: 50,
            status: statusVal,
            crawlMode: modeVal,
            search: searchVal,
        });

        const jobs = res.data || [];
        cardsView.innerHTML = '';

        if (jobs.length === 0) {
            if (emptySlot) {
                emptySlot.innerHTML = '';
                emptySlot.appendChild(window.createEmptyState({
                    icon: 'history',
                    title: 'No Crawl History Matches Found',
                    description: 'No historical crawl jobs match your active search term or filter criteria.',
                    actionText: 'Reset Search & Filters',
                    onAction: () => {
                        if (document.getElementById('history-search-input')) document.getElementById('history-search-input').value = '';
                        if (document.getElementById('history-mode-filter')) document.getElementById('history-mode-filter').value = 'ALL';
                        if (document.getElementById('history-status-filter')) document.getElementById('history-status-filter').value = 'ALL';
                        window.loadHistoryData();
                    }
                }));
                emptySlot.style.display = 'block';
            }
        } else {
            if (emptySlot) emptySlot.style.display = 'none';

            jobs.forEach(job => {
                const card = document.createElement('div');
                card.className = 'card history-card';
                card.style.marginBottom = '12px';
                card.style.padding = '16px 20px';

                const statusClass = job.status === 'COMPLETED' ? 'badge-success' : (job.status === 'FAILED' ? 'badge-danger' : 'badge-info');

                card.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <input type="checkbox" class="history-item-checkbox" value="${job.id}" onchange="window.updateBulkSelectState()">
                            <div>
                                <div style="font-weight: 600; font-size: 14px; color: var(--text-primary);">${job.seed_url}</div>
                                <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">
                                    ID: <code>${job.id}</code> • Created: ${new Date(job.created_at).toLocaleString()} • Mode: ${job.crawl_mode}
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span class="badge ${statusClass}">${job.status}</span>
                            <button type="button" class="btn btn-primary btn-sm" onclick="window.analyzeCurrentCrawlWithAi('${job.id}')">
                                <i data-lucide="sparkles" style="width: 14px; height: 14px;"></i> Analyze with AI ✨
                            </button>
                            <button type="button" class="btn btn-secondary btn-sm" onclick="window.openAnalysisForJob('${job.id}')">
                                <i data-lucide="bar-chart-2" style="width: 14px; height: 14px;"></i> Open Analysis
                            </button>
                        </div>
                    </div>
                `;
                cardsView.appendChild(card);
            });
        }
    } catch (err) {
        console.error("Failed to load history data:", err);
    }

    if (window.lucide) window.lucide.createIcons();
};

window.openAnalysisForJob = function (jobId) {
    window.currentAnalysisJobId = jobId;
    window.currentAnalysisBatchId = null;
    window.location.hash = 'analysis';
};

window.filterHistoryItems = function () {
    window.loadHistoryData();
};

window.setHistoryViewMode = function (mode) {
    const cardsView = document.getElementById('history-cards-view');
    const timelineView = document.getElementById('history-timeline-view');
    const btnCards = document.getElementById('btn-history-cards-view');
    const btnTimeline = document.getElementById('btn-history-timeline-view');

    if (mode === 'cards') {
        if (cardsView) cardsView.style.display = 'flex';
        if (timelineView) timelineView.style.display = 'none';
        if (btnCards) btnCards.classList.add('active');
        if (btnTimeline) btnTimeline.classList.remove('active');
    } else {
        if (cardsView) cardsView.style.display = 'none';
        if (timelineView) timelineView.style.display = 'block';
        if (btnCards) btnCards.classList.remove('active');
        if (btnTimeline) btnTimeline.classList.add('active');
    }
};

window.updateBulkSelectState = function () {
    const checkboxes = document.querySelectorAll('.history-item-checkbox:checked');
    const btnBulkDelete = document.getElementById('btn-bulk-delete');
    if (btnBulkDelete) {
        if (checkboxes.length > 0) {
            btnBulkDelete.removeAttribute('disabled');
            btnBulkDelete.innerHTML = `<i data-lucide="trash-2" style="width: 14px; height: 14px;"></i><span>Delete Selected (${checkboxes.length})</span>`;
        } else {
            btnBulkDelete.setAttribute('disabled', 'true');
            btnBulkDelete.innerHTML = `<i data-lucide="trash-2" style="width: 14px; height: 14px;"></i><span>Delete Selected</span>`;
        }
        if (window.lucide) window.lucide.createIcons();
    }
};

// ============================================================================
// SETTINGS WORKSPACE SERVICES
// ============================================================================
window.loadSettingsView = function () {
    if (window.lucide) window.lucide.createIcons();
};

window.switchSettingsCategory = function (category, btnEl) {
    const allPanes = document.querySelectorAll('.settings-pane');
    allPanes.forEach(pane => pane.style.display = 'none');

    const activePane = document.getElementById(`settings-pane-${category}`);
    if (activePane) activePane.style.display = 'block';

    if (btnEl && btnEl.parentNode) {
        const siblings = btnEl.parentNode.querySelectorAll('.settings-nav-item');
        siblings.forEach(s => s.classList.remove('active'));
        btnEl.classList.add('active');
    }

    if (window.lucide) window.lucide.createIcons();
};

window.filterShortcuts = function () {
    const query = (document.getElementById('shortcut-search-input')?.value || '').toLowerCase().trim();
    const rows = document.querySelectorAll('.shortcut-row');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (!query || text.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
};

// ============================================================================
// GLOBAL UI NOTIFICATIONS & HELPERS
// ============================================================================
window.showToast = function ({ type = 'info', title = '', message = '', duration = 4000 }) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const iconMap = {
        success: 'check-circle-2',
        error: 'alert-circle',
        warning: 'alert-triangle',
        info: 'info'
    };

    const iconName = iconMap[type] || 'info';

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');

    toast.innerHTML = `
        <i data-lucide="${iconName}" class="toast-icon"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-message">${message}</div>` : ''}
        </div>
        <button type="button" class="toast-close-btn" aria-label="Close notification">
            <i data-lucide="x" style="width: 14px; height: 14px;"></i>
        </button>
    `;

    container.appendChild(toast);

    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons({ props: {}, nameAttr: 'data-lucide', attrs: {}, element: toast });
    }

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    const closeBtn = toast.querySelector('.toast-close-btn');
    let timer = null;

    function dismissToast() {
        if (timer) clearTimeout(timer);
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 250);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', dismissToast);
    }

    if (duration > 0) {
        timer = setTimeout(dismissToast, duration);
    }
};

window.showLoading = function ({ message = 'Processing Request...', subtext = 'Please wait while the platform processes your task.', percentage = null } = {}) {
    const backdrop = document.getElementById('loading-overlay-backdrop');
    const msgEl = document.getElementById('loading-message');
    const subEl = document.getElementById('loading-subtext');
    const progressContainer = document.getElementById('loading-progress-container');
    const progressFill = document.getElementById('loading-progress-fill');

    if (!backdrop) return;

    if (msgEl) msgEl.textContent = message;
    if (subEl) subEl.textContent = subtext;

    if (percentage !== null && percentage >= 0 && progressContainer && progressFill) {
        progressContainer.style.display = 'block';
        progressFill.style.width = `${Math.min(100, Math.max(0, percentage))}%`;
    } else if (progressContainer) {
        progressContainer.style.display = 'none';
    }

    backdrop.classList.add('open');
};

window.hideLoading = function () {
    const backdrop = document.getElementById('loading-overlay-backdrop');
    if (backdrop) {
        backdrop.classList.remove('open');
    }
};

window.createEmptyState = function ({ icon = 'folder-open', title = 'No Items Found', description = 'There is currently no data to display.', actionText = null, onAction = null }) {
    const card = document.createElement('div');
    card.className = 'empty-state-card';

    card.innerHTML = `
        <div class="empty-state-icon-wrapper">
            <i data-lucide="${icon}" style="width: 24px; height: 24px;"></i>
        </div>
        <div class="empty-state-title">${title}</div>
        <div class="empty-state-desc">${description}</div>
        ${actionText ? `<button type="button" class="btn-header-primary empty-state-action-btn">${actionText}</button>` : ''}
    `;

    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons({ props: {}, nameAttr: 'data-lucide', attrs: {}, element: card });
    }

    if (actionText && onAction) {
        const actionBtn = card.querySelector('.empty-state-action-btn');
        if (actionBtn) {
            actionBtn.addEventListener('click', onAction);
        }
    }

    return card;
};

window.createErrorState = function ({ icon = 'alert-triangle', title = 'An Error Occurred', description = 'Failed to execute operation. Please check your connection.', errorCode = null, onRetry = null }) {
    const card = document.createElement('div');
    card.className = 'error-state-card';

    card.innerHTML = `
        <div class="error-state-icon-wrapper">
            <i data-lucide="${icon}" style="width: 24px; height: 24px;"></i>
        </div>
        <div class="error-state-title">${title}</div>
        ${errorCode ? `<div class="error-state-code">ERROR_CODE: ${errorCode}</div>` : ''}
        <div class="error-state-desc">${description}</div>
        ${onRetry ? `<button type="button" class="btn-header-primary error-state-retry-btn" style="background-color: var(--text-primary);"><i data-lucide="rotate-cw" style="width: 14px; height: 14px;"></i> Retry Operation</button>` : ''}
    `;

    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        lucide.createIcons({ props: {}, nameAttr: 'data-lucide', attrs: {}, element: card });
    }

    if (onRetry) {
        const retryBtn = card.querySelector('.error-state-retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', onRetry);
        }
    }

    return card;
};

// --------------------------------------------------------------------------
// AI Intelligence Insights Hub Handlers
// --------------------------------------------------------------------------
window.runAiAnalysis = async function () {
    const jobId = window.currentAnalysisJobId;
    if (!jobId) {
        window.showToast({ type: 'warning', title: 'No Crawl Job Loaded', message: 'Please select or run a crawl job first.' });
        return;
    }

    const btn = document.getElementById('btn-generate-ai-analysis');
    const container = document.getElementById('ai-analysis-container');
    const output = document.getElementById('ai-analysis-output');
    const sources = document.getElementById('ai-analysis-sources');
    const badge = document.getElementById('ai-execution-badge');

    if (btn) btn.disabled = true;
    if (container) container.style.display = 'block';
    if (output) output.innerHTML = '<em>Generating AI Executive Summary & Major Topics...</em>';
    if (sources) sources.innerHTML = '';

    try {
        const res = await API.ai.analyzeCrawl(jobId);
        if (badge) badge.innerText = `${res.execution_path} Mode`;
        if (output) output.innerText = res.analysis || 'No analysis text returned.';

        if (sources && res.sources && res.sources.length > 0) {
            sources.innerHTML = '<strong>Grounding Sources:</strong> ' + res.sources.map(s => `<a href="${s.url}" target="_blank" style="color: var(--accent-primary); text-decoration: underline; margin-right: 12px;">${s.page_title || s.url}</a>`).join('');
        }
        window.showToast({ type: 'success', title: 'AI Analysis Complete', message: `Dataset analyzed using ${res.execution_path} strategy.` });
    } catch (err) {
        console.error('Failed to run AI analysis:', err);
        if (output) output.innerText = `Failed to generate AI analysis: ${err.message}`;
        window.showToast({ type: 'error', title: 'AI Analysis Failed', message: err.message });
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.runPrepareRag = async function () {
    const jobId = window.currentAnalysisJobId;
    if (!jobId) {
        window.showToast({ type: 'warning', title: 'No Crawl Job Loaded', message: 'Please select or run a crawl job first.' });
        return;
    }

    const btn = document.getElementById('btn-prepare-rag');
    if (btn) btn.disabled = true;

    window.showToast({ type: 'info', title: 'Indexing RAG Embeddings', message: 'Generating semantic chunks & vector embeddings...' });

    try {
        const res = await API.ai.prepareRag(jobId);
        window.showToast({ type: 'success', title: 'RAG Indexing Complete', message: `Indexed ${res.chunks_indexed} document chunks into vector store.` });
    } catch (err) {
        console.error('Failed to index RAG embeddings:', err);
        window.showToast({ type: 'error', title: 'RAG Indexing Failed', message: err.message });
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.runAiQuery = async function () {
    const jobId = window.currentAnalysisJobId;
    if (!jobId) {
        window.showToast({ type: 'warning', title: 'No Crawl Job Loaded', message: 'Please select or run a crawl job first.' });
        return;
    }

    const input = document.getElementById('ai-question-input');
    const question = input ? input.value.trim() : '';

    if (!question) {
        window.showToast({ type: 'warning', title: 'Empty Question', message: 'Please enter a question.' });
        return;
    }

    const btn = document.getElementById('btn-ask-ai');
    const container = document.getElementById('ai-query-container');
    const answer = document.getElementById('ai-query-answer');
    const sources = document.getElementById('ai-query-sources');

    if (btn) btn.disabled = true;
    if (container) container.style.display = 'block';
    if (answer) answer.innerHTML = '<em>Searching dataset context and synthesizing grounded answer...</em>';
    if (sources) sources.innerHTML = '';

    try {
        const res = await API.ai.queryCrawl(jobId, question);
        if (answer) answer.innerText = res.answer || 'No answer generated.';

        if (sources && res.sources && res.sources.length > 0) {
            sources.innerHTML = '<strong>Grounding Sources:</strong> ' + res.sources.map(s => `<a href="${s.url}" target="_blank" style="color: var(--accent-primary); text-decoration: underline; margin-right: 10px;">${s.page_title || s.url} ${s.heading ? `(${s.heading})` : ''}</a>`).join('');
        }
        window.showToast({ type: 'success', title: 'Answer Synthesized', message: `Grounded in dataset (${res.execution_path})` });
    } catch (err) {
        console.error('Failed to query AI:', err);
        if (answer) answer.innerText = `Failed to get AI answer: ${err.message}`;
        window.showToast({ type: 'error', title: 'AI Query Failed', message: err.message });
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.aiConversations = {};

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

window.analyzeCurrentCrawlWithAi = function(jobId, batchId = null) {
    if (jobId) window.currentAnalysisJobId = jobId;
    if (batchId) window.currentAnalysisBatchId = batchId;
    window.location.hash = 'ai-workspace';
};

window.selectAiWorkspaceJob = function(jobId) {
    if (!jobId) return;
    window.currentAnalysisJobId = jobId;
    window.currentAnalysisBatchId = null;
    window.loadAiWorkspaceView();
};

window.loadAiWorkspaceView = async function () {
    const targetEl = document.getElementById('ai-workspace-context-target');
    const idEl = document.getElementById('ai-workspace-context-id');
    const selectorContainer = document.getElementById('ai-workspace-job-selector-container');
    const selector = document.getElementById('ai-workspace-job-selector');
    
    // Populate job selector dropdown from recent completed crawl history if available
    try {
        const historyRes = await API.crawl.list({ page: 1, pageSize: 20, status: 'COMPLETED' });
        if (selector && historyRes && historyRes.items) {
            selector.innerHTML = '<option value="">-- Select a completed crawl --</option>' +
                historyRes.items.map(j => `<option value="${j.id}" ${j.id === window.currentAnalysisJobId ? 'selected' : ''}>${escapeHtml(j.seed_url)} (${new Date(j.created_at).toLocaleTimeString()})</option>`).join('');
            if (selectorContainer) selectorContainer.style.display = 'block';
        }
    } catch(e) {
        console.warn('Could not load history for AI job selector', e);
    }

    const jobId = window.currentAnalysisJobId;
    const batchId = window.currentAnalysisBatchId;

    if (!jobId && !batchId) {
        if (targetEl) targetEl.textContent = 'No active crawl job loaded';
        if (idEl) idEl.textContent = 'Select a completed crawl from the dropdown above or run a new crawl.';
        window.renderAiChatMessages();
        return;
    }

    if (batchId && !jobId) {
        if (targetEl) targetEl.textContent = `Batch Job #${batchId.substring(0, 8)}`;
        if (idEl) idEl.textContent = `Multi-Website Batch Dataset`;
        window.renderAiChatMessages();
        return;
    }

    try {
        const job = await API.crawl.get(jobId);
        if (targetEl) targetEl.textContent = job.seed_url;
        if (idEl) idEl.textContent = `Job ID: ${job.id} | Status: ${job.status} | Mode: ${job.crawl_mode}`;
        if (selector && jobId) selector.value = jobId;
    } catch (err) {
        if (targetEl) targetEl.textContent = `Job ID: ${jobId.substring(0, 8)}...`;
        if (idEl) idEl.textContent = 'Active Crawl Context';
    }

    window.renderAiChatMessages();
};

window.renderAiChatMessages = function() {
    const container = document.getElementById('ai-chat-messages');
    if (!container) return;

    const contextId = window.currentAnalysisJobId || window.currentAnalysisBatchId || 'global';
    const history = window.aiConversations[contextId] || [];

    if (history.length === 0) {
        const seedUrl = document.getElementById('ai-workspace-context-target')?.textContent || 'this website';
        container.innerHTML = `
            <div style="text-align: center; padding: 32px 16px; background-color: var(--bg-hover); border-radius: 12px; border: 1px dashed var(--border-subtle);">
                <div style="width: 48px; height: 48px; border-radius: 50%; background-color: var(--accent-light); color: var(--accent-primary); display: flex; align-items: center; justify-content: center; margin: 0 auto 12px;">
                    <i data-lucide="sparkles" style="width: 24px; height: 24px;"></i>
                </div>
                <div style="font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">Ask AI Assistant</div>
                <div style="font-size: 13px; color: var(--text-muted); max-width: 480px; margin: 0 auto 18px;">
                    Ask questions naturally about <strong>${escapeHtml(seedUrl)}</strong>. Answers are strictly grounded in extracted website content.
                </div>
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-muted); margin-bottom: 10px;">Suggested Questions:</div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;" id="ai-chat-suggested-chips">
                    <button type="button" class="btn btn-outline btn-sm" onclick="window.sendAiChatMessage('What is this website about?');">What is this website about?</button>
                    <button type="button" class="btn btn-outline btn-sm" onclick="window.sendAiChatMessage('What are the main sections and topics?');">What are the main sections?</button>
                    <button type="button" class="btn btn-outline btn-sm" onclick="window.sendAiChatMessage('Summarize key information found.');">Summarize key information</button>
                    <button type="button" class="btn btn-outline btn-sm" onclick="window.sendAiChatMessage('List key resources or links.');">List key resources</button>
                </div>
            </div>
        `;
        if (window.lucide) window.lucide.createIcons();
        return;
    }

    container.innerHTML = history.map(msg => {
        if (msg.role === 'user') {
            return `
                <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
                    <div style="max-width: 80%; background: linear-gradient(135deg, var(--accent-primary), #2563eb); color: #ffffff; padding: 12px 16px; border-radius: 16px 16px 2px 16px; font-size: 14px; line-height: 1.5; box-shadow: var(--shadow-sm);">
                        ${escapeHtml(msg.text)}
                    </div>
                </div>
            `;
        } else {
            const sourcesHtml = (msg.sources && msg.sources.length > 0)
                ? `<div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--border-subtle); font-size: 12px; color: var(--text-muted);">
                    <strong>Grounding Sources:</strong><br>
                    ${msg.sources.map(s => `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener" style="color: var(--accent-primary); text-decoration: underline; margin-right: 12px; display: inline-block; margin-top: 4px;">• ${escapeHtml(s.page_title || s.url)} ${s.heading ? `(${escapeHtml(s.heading)})` : ''}</a>`).join('')}
                   </div>`
                : '';

            const modeBadge = msg.executionPath
                ? `<span class="badge badge-subtle font-mono" style="font-size: 10px; margin-bottom: 8px; display: inline-block;">Mode: ${escapeHtml(msg.executionPath)} ${msg.retrievedCount ? `(Retrieved ${msg.retrievedCount} sections)` : ''}</span>`
                : '';

            return `
                <div style="display: flex; gap: 12px; margin-bottom: 20px;">
                    <div style="width: 34px; height: 34px; border-radius: 50%; background-color: var(--accent-light); color: var(--accent-primary); display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                        <i data-lucide="sparkles" style="width: 18px; height: 18px;"></i>
                    </div>
                    <div style="max-width: 85%; background-color: var(--bg-hover); border: 1px solid var(--border-subtle); padding: 14px 18px; border-radius: 2px 16px 16px 16px; font-size: 14px; line-height: 1.6; color: var(--text-primary); box-shadow: var(--shadow-sm);">
                        ${modeBadge}
                        <div style="white-space: pre-line;">${escapeHtml(msg.text)}</div>
                        ${sourcesHtml}
                    </div>
                </div>
            `;
        }
    }).join('');

    container.scrollTop = container.scrollHeight;
    if (window.lucide) window.lucide.createIcons();
};

window.sendAiChatMessage = async function(questionOverride = null) {
    const input = document.getElementById('ai-chat-input');
    const question = (questionOverride || (input ? input.value : '')).trim();
    if (!question) {
        window.showToast({ type: 'warning', title: 'Empty Question', message: 'Please enter a question.' });
        return;
    }

    const jobId = window.currentAnalysisJobId;
    const batchId = window.currentAnalysisBatchId;

    if (!jobId && !batchId) {
        window.showToast({ type: 'warning', title: 'No Crawl Loaded', message: 'Please select a completed crawl first.' });
        return;
    }

    const contextId = jobId || batchId;
    if (!window.aiConversations[contextId]) {
        window.aiConversations[contextId] = [];
    }

    // Append user message
    window.aiConversations[contextId].push({ role: 'user', text: question });
    if (input) input.value = '';
    window.renderAiChatMessages();

    // Disable input controls & show thinking state
    const btn = document.getElementById('btn-ai-chat-send');
    if (btn) btn.disabled = true;
    if (input) input.disabled = true;

    // Show temporary thinking bubble
    const container = document.getElementById('ai-chat-messages');
    if (container) {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.id = 'ai-thinking-indicator';
        thinkingDiv.style.cssText = 'display: flex; gap: 12px; margin-bottom: 20px;';
        thinkingDiv.innerHTML = `
            <div style="width: 34px; height: 34px; border-radius: 50%; background-color: var(--accent-light); color: var(--accent-primary); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                <i data-lucide="refresh-cw" class="spin" style="width: 18px; height: 18px;"></i>
            </div>
            <div style="background-color: var(--bg-hover); border: 1px solid var(--border-subtle); padding: 12px 16px; border-radius: 2px 16px 16px 16px; font-size: 13px; color: var(--text-muted);">
                AI is thinking and synthesizing grounded answer...
            </div>
        `;
        container.appendChild(thinkingDiv);
        container.scrollTop = container.scrollHeight;
        if (window.lucide) window.lucide.createIcons();
    }

    // Build history payload for backend
    const apiHistory = window.aiConversations[contextId].slice(0, -1).map(m => ({
        role: m.role,
        content: m.text
    }));

    try {
        let res;
        if (jobId) {
            res = await API.ai.queryCrawl(jobId, question, apiHistory);
        } else {
            res = await API.ai.queryBatch(batchId, question, apiHistory);
        }

        const thinkingEl = document.getElementById('ai-thinking-indicator');
        if (thinkingEl) thinkingEl.remove();

        window.aiConversations[contextId].push({
            role: 'assistant',
            text: res.answer || 'No answer returned.',
            sources: res.sources || [],
            executionPath: res.execution_path || 'DIRECT_AI',
            retrievedCount: res.retrieved_chunks_count || 0
        });

        window.renderAiChatMessages();
    } catch (err) {
        const thinkingEl = document.getElementById('ai-thinking-indicator');
        if (thinkingEl) thinkingEl.remove();

        window.aiConversations[contextId].push({
            role: 'assistant',
            text: `Unable to synthesize answer: ${err.message}`,
            sources: [],
            executionPath: 'ERROR'
        });

        window.renderAiChatMessages();
        window.showToast({ type: 'error', title: 'AI Query Failed', message: err.message });
    } finally {
        if (btn) btn.disabled = false;
        if (input) {
            input.disabled = false;
            input.focus();
        }
    }
};
