/**
 * Centralized API Client Module for Website Intelligence Platform.
 * Communicates with backend REST API V1 endpoints under /api/v1.
 */

window.API = (function () {
    const BASE_URL = '/api/v1';

    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const defaultHeaders = {
            'Accept': 'application/json',
        };

        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            defaultHeaders['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
            credentials: 'include', // Include HTTP-only session cookies
        };

        try {
            const response = await fetch(url, config);

            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            // Handle File Blob Streams (for exports)
            if (options.responseType === 'blob') {
                if (!response.ok) {
                    const errData = await response.json().catch(() => ({ detail: 'Export generation failed.' }));
                    throw new Error(errData.detail || 'Export generation failed.');
                }
                const blob = await response.blob();
                const disposition = response.headers.get('Content-Disposition') || '';
                let filename = 'download';
                const match = disposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) {
                    filename = match[1];
                }
                return { blob, filename };
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                const errorMessage = data.detail || data.message || `Request failed with status ${response.status}`;
                const err = new Error(errorMessage);
                err.status = response.status;
                err.type = data.type;
                err.error_type = data.error_type;
                throw err;
            }

            return data;
        } catch (err) {
            console.error(`API Error on [${options.method || 'GET'} ${url}]:`, err);
            throw err;
        }
    }

    return {
        auth: {
            register: (email, password) => request('/auth/register', { method: 'POST', body: { email, password } }),
            login: (email, password) => request('/auth/login', { method: 'POST', body: { email, password } }),
            logout: () => request('/auth/logout', { method: 'POST' }),
            me: () => request('/auth/me', { method: 'GET' }),
        },
        projects: {
            create: (name, description) => request('/projects', { method: 'POST', body: { name, description } }),
            list: (page = 1, pageSize = 20) => request(`/projects?page=${page}&page_size=${pageSize}`, { method: 'GET' }),
            get: (id) => request(`/projects/${id}`, { method: 'GET' }),
            update: (id, name, description) => request(`/projects/${id}`, { method: 'PUT', body: { name, description } }),
            delete: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
        },
        crawl: {
            create: ({ url, maxDepth = 2, maxPages = 50, renderJs = false, projectId = null }) =>
                request('/crawl', { method: 'POST', body: { url, max_depth: maxDepth, max_pages: maxPages, render_js: renderJs, project_id: projectId } }),
            list: ({ page = 1, pageSize = 20, status = null, crawlMode = null, search = null, sortBy = 'created_at', sortOrder = 'desc' } = {}) => {
                const params = new URLSearchParams({ page, page_size: pageSize, sort_by: sortBy, sort_order: sortOrder });
                if (status && status !== 'ALL') params.append('status', status);
                if (crawlMode && crawlMode !== 'ALL') params.append('crawl_mode', crawlMode);
                if (search) params.append('search', search);
                return request(`/crawl/jobs?${params.toString()}`, { method: 'GET' });
            },
            get: (jobId) => request(`/crawl/${jobId}`, { method: 'GET' }),
            results: (jobId, page = 1, limit = 20) => request(`/crawl/${jobId}/results?page=${page}&limit=${limit}`, { method: 'GET' }),
            statistics: (jobId) => request(`/crawl/${jobId}/statistics`, { method: 'GET' }),
            dataset: (jobId) => request(`/crawl/${jobId}/dataset`, { method: 'GET' }),
            export: (jobId, format = 'json') => request(`/crawl/${jobId}/export`, { method: 'POST', body: { format }, responseType: 'blob' }),
        },
        batch: {
            create: ({ urls, maxDepth = 2, maxPages = 50, renderJs = false, projectId = null }) =>
                request('/batch', { method: 'POST', body: { urls, max_depth: maxDepth, max_pages: maxPages, render_js: renderJs, project_id: projectId } }),
            list: ({ page = 1, pageSize = 20, status = null, sortBy = 'created_at', sortOrder = 'desc' } = {}) => {
                const params = new URLSearchParams({ page, page_size: pageSize, sort_by: sortBy, sort_order: sortOrder });
                if (status && status !== 'ALL') params.append('status', status);
                return request(`/batch/list?${params.toString()}`, { method: 'GET' });
            },
            get: (batchId) => request(`/batch/${batchId}`, { method: 'GET' }),
            statistics: (batchId) => request(`/batch/${batchId}/statistics`, { method: 'GET' }),
            retry: (batchId) => request(`/batch/${batchId}/retry`, { method: 'POST' }),
            dataset: (batchId) => request(`/batch/${batchId}/dataset`, { method: 'GET' }),
            export: (batchId, format = 'json') => request(`/batch/${batchId}/export`, { method: 'POST', body: { format }, responseType: 'blob' }),
        },
        ai: {
            analyzeCrawl: (jobId) => request(`/ai/crawl/${jobId}/analyze`, { method: 'POST' }),
            queryCrawl: (jobId, question, history = []) => request(`/ai/crawl/${jobId}/query`, { method: 'POST', body: { question, history } }),
            prepareRag: (jobId) => request(`/ai/crawl/${jobId}/prepare-rag`, { method: 'POST' }),
            analyzeBatch: (batchId) => request(`/ai/batch/${batchId}/analyze`, { method: 'POST' }),
            queryBatch: (batchId, question, history = []) => request(`/ai/batch/${batchId}/query`, { method: 'POST', body: { question, history } }),
        },
    };
})();
