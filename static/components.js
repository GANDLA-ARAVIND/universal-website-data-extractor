/**
 * Essential UI Component Library (Step 1B)
 * Modular, reusable component builders adhering to the SaaS design system.
 */

window.UI = (function () {
    // Helper to render Lucide icons in dynamically created elements
    function renderIcons(element) {
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons({ props: {}, nameAttr: 'data-lucide', attrs: {}, element });
        }
    }

    return {
        /** 1. Button Component */
        button({ variant = 'primary', size = 'md', label = '', iconLeft = null, iconRight = null, loading = false, disabled = false, onClick = null, className = '' }) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `btn btn-${variant} btn-${size} ${loading ? 'loading' : ''} ${className}`.trim();
            btn.disabled = disabled || loading;

            let contentHTML = '';
            if (loading) {
                contentHTML += `<span class="btn-spinner"></span>`;
            } else if (iconLeft) {
                contentHTML += `<i data-lucide="${iconLeft}" style="width:14px; height:14px;"></i>`;
            }
            if (label) contentHTML += `<span>${label}</span>`;
            if (iconRight && !loading) {
                contentHTML += `<i data-lucide="${iconRight}" style="width:14px; height:14px;"></i>`;
            }

            btn.innerHTML = contentHTML;
            renderIcons(btn);

            if (onClick && !btn.disabled) {
                btn.addEventListener('click', onClick);
            }
            return btn;
        },

        /** 2. Card Component */
        card({ variant = 'default', title = null, description = null, body = null, footer = null, onClick = null, className = '' }) {
            const card = document.createElement('div');
            card.className = `card ${variant === 'interactive' ? 'card-interactive' : ''} ${className}`.trim();

            let innerHTML = '';
            if (title || description) {
                innerHTML += `<div class="card-header">
                    <div>
                        ${title ? `<div class="card-title">${title}</div>` : ''}
                        ${description ? `<div class="card-desc">${description}</div>` : ''}
                    </div>
                </div>`;
            }
            if (body) {
                innerHTML += `<div class="card-body">${typeof body === 'string' ? body : ''}</div>`;
            }
            if (footer) {
                innerHTML += `<div class="card-footer">${typeof footer === 'string' ? footer : ''}</div>`;
            }

            card.innerHTML = innerHTML;

            if (body && typeof body !== 'string') {
                const bodyContainer = card.querySelector('.card-body');
                if (bodyContainer) bodyContainer.appendChild(body);
            }
            if (footer && typeof footer !== 'string') {
                const footerContainer = card.querySelector('.card-footer');
                if (footerContainer) footerContainer.appendChild(footer);
            }

            renderIcons(card);

            if (onClick) {
                card.addEventListener('click', onClick);
            }
            return card;
        },

        /** 3. Badge Component */
        badge({ variant = 'neutral', label = '', dot = true }) {
            const span = document.createElement('span');
            span.className = `badge badge-${variant}`;
            span.innerHTML = `${dot ? '<span class="badge-dot"></span>' : ''}<span>${label}</span>`;
            return span;
        },

        /** 4. Input Component */
        input({ type = 'text', label = null, placeholder = '', value = '', helperText = null, error = null, disabled = false, onChange = null }) {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-field';

            wrapper.innerHTML = `
                ${label ? `<label class="form-label">${label}</label>` : ''}
                <input type="${type}" class="input-text ${error ? 'error' : ''}" placeholder="${placeholder}" value="${value}" ${disabled ? 'disabled' : ''}>
                ${error ? `<span class="form-error-msg">${error}</span>` : (helperText ? `<span class="form-helper">${helperText}</span>` : '')}
            `;

            const inputEl = wrapper.querySelector('input');
            if (onChange && inputEl) {
                inputEl.addEventListener('input', (e) => onChange(e.target.value));
            }
            return wrapper;
        },

        /** 5. Textarea Component */
        textarea({ label = null, placeholder = '', value = '', rows = 3, charLimit = null, onChange = null }) {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-field';

            wrapper.innerHTML = `
                ${label ? `<label class="form-label">${label}</label>` : ''}
                <textarea class="textarea-control" rows="${rows}" placeholder="${placeholder}">${value}</textarea>
                ${charLimit ? `<div class="char-counter"><span class="char-count">0</span> / ${charLimit}</div>` : ''}
            `;

            const txtEl = wrapper.querySelector('textarea');
            const counterEl = wrapper.querySelector('.char-count');

            if (txtEl) {
                txtEl.addEventListener('input', (e) => {
                    if (counterEl) counterEl.textContent = e.target.value.length;
                    if (onChange) onChange(e.target.value);
                });
            }
            return wrapper;
        },

        /** 6. Select & Toggle Switch Components */
        select({ label = null, options = [], value = '', onChange = null }) {
            const wrapper = document.createElement('div');
            wrapper.className = 'form-field';

            const optsHTML = options.map(opt => `<option value="${opt.value}" ${opt.value === value ? 'selected' : ''}>${opt.label}</option>`).join('');

            wrapper.innerHTML = `
                ${label ? `<label class="form-label">${label}</label>` : ''}
                <select class="select-control">${optsHTML}</select>
            `;

            const selectEl = wrapper.querySelector('select');
            if (onChange && selectEl) {
                selectEl.addEventListener('change', (e) => onChange(e.target.value));
            }
            return wrapper;
        },

        toggle({ label = '', checked = false, onChange = null }) {
            const labelEl = document.createElement('label');
            labelEl.style.display = 'inline-flex';
            labelEl.style.alignItems = 'center';
            labelEl.style.gap = '10px';
            labelEl.style.cursor = 'pointer';

            labelEl.innerHTML = `
                <span class="toggle-switch">
                    <input type="checkbox" ${checked ? 'checked' : ''}>
                    <span class="toggle-slider"></span>
                </span>
                <span style="font-size: 13px; font-weight: 500; color: var(--text-primary);">${label}</span>
            `;

            const inputEl = labelEl.querySelector('input');
            if (onChange && inputEl) {
                inputEl.addEventListener('change', (e) => onChange(e.target.checked));
            }
            return labelEl;
        },

        /** 7. Tabs Component */
        tabs({ items = [], activeId = '', onSelect = null }) {
            const container = document.createElement('div');
            container.className = 'tabs-container';

            items.forEach(item => {
                const tab = document.createElement('div');
                tab.className = `tab-item ${item.id === activeId ? 'active' : ''}`;
                tab.innerHTML = `${item.icon ? `<i data-lucide="${item.icon}" style="width:14px; height:14px;"></i>` : ''}<span>${item.label}</span>`;

                tab.addEventListener('click', () => {
                    container.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    if (onSelect) onSelect(item.id);
                });

                container.appendChild(tab);
            });

            renderIcons(container);
            return container;
        },

        /** 8. Progress Components */
        progressBar({ value = 0, max = 100 }) {
            const track = document.createElement('div');
            track.className = 'progress-bar-track';
            const pct = Math.min(100, Math.max(0, (value / max) * 100));
            track.innerHTML = `<div class="progress-bar-fill" style="width: ${pct}%;"></div>`;
            return track;
        },

        circularProgress({ value = 0, max = 100, size = 48 }) {
            const wrap = document.createElement('div');
            wrap.className = 'circular-progress-wrap';
            wrap.style.width = `${size}px`;
            wrap.style.height = `${size}px`;

            const radius = (size - 8) / 2;
            const circumference = 2 * Math.PI * radius;
            const pct = Math.min(100, Math.max(0, (value / max) * 100));
            const strokeDashoffset = circumference - (pct / 100) * circumference;

            wrap.innerHTML = `
                <svg width="${size}" height="${size}" class="circular-progress">
                    <circle class="circular-bg" stroke-width="4" fill="transparent" r="${radius}" cx="${size/2}" cy="${size/2}"/>
                    <circle class="circular-fill" stroke-width="4" stroke-dasharray="${circumference}" stroke-dashoffset="${strokeDashoffset}" fill="transparent" r="${radius}" cx="${size/2}" cy="${size/2}"/>
                </svg>
                <span class="circular-val">${Math.round(pct)}%</span>
            `;
            return wrap;
        },

        steps({ steps = [], currentStep = 1 }) {
            const bar = document.createElement('div');
            bar.className = 'steps-bar';

            steps.forEach((st, idx) => {
                const stepNum = idx + 1;
                const item = document.createElement('div');
                let stateClass = '';
                if (stepNum === currentStep) stateClass = 'active';
                else if (stepNum < currentStep) stateClass = 'completed';

                item.className = `step-item ${stateClass}`;
                item.innerHTML = `
                    <div class="step-circle">${stepNum < currentStep ? '✓' : stepNum}</div>
                    <span style="font-size: 11px; font-weight: 500; color: var(--text-secondary);">${st.label}</span>
                `;
                bar.appendChild(item);
            });
            return bar;
        },

        /** 9. Skeleton Loader Component */
        skeleton({ type = 'text', width = '100%', height = '16px' }) {
            const sk = document.createElement('div');
            sk.className = `skeleton ${type === 'card' ? 'skeleton-card' : 'skeleton-text'}`;
            sk.style.width = width;
            if (height) sk.style.height = height;
            return sk;
        },

        /** 10. Modal Dialog Component */
        modal({ title = '', content = '', actions = [], onClose = null }) {
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop';

            backdrop.innerHTML = `
                <div class="modal-box" role="dialog" aria-modal="true">
                    <div class="modal-header">
                        <div style="font-size: 15px; font-weight: 600; color: var(--text-primary);">${title}</div>
                        <button type="button" class="modal-close-btn" style="color: var(--text-muted);"><i data-lucide="x" style="width:16px; height:16px;"></i></button>
                    </div>
                    <div class="modal-body">${typeof content === 'string' ? content : ''}</div>
                    <div class="modal-footer"></div>
                </div>
            `;

            if (content && typeof content !== 'string') {
                backdrop.querySelector('.modal-body').appendChild(content);
            }

            const footer = backdrop.querySelector('.modal-footer');
            actions.forEach(act => {
                const btn = UI.button({ label: act.label, variant: act.variant || 'secondary', onClick: () => { act.onClick(); backdrop.classList.remove('open'); } });
                footer.appendChild(btn);
            });

            renderIcons(backdrop);

            const closeBtn = backdrop.querySelector('.modal-close-btn');
            function closeModal() {
                backdrop.classList.remove('open');
                setTimeout(() => { if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop); if (onClose) onClose(); }, 150);
            }
            if (closeBtn) closeBtn.addEventListener('click', closeModal);
            backdrop.addEventListener('click', (e) => { if (e.target === backdrop) closeModal(); });

            document.body.appendChild(backdrop);
            requestAnimationFrame(() => backdrop.classList.add('open'));
            return backdrop;
        },

        /** 11. Dropdown Menu Component */
        dropdown({ label = 'Actions', items = [] }) {
            const wrap = document.createElement('div');
            wrap.className = 'dropdown';

            const btn = UI.button({ label, variant: 'secondary', size: 'sm', iconRight: 'chevron-down' });
            const menu = document.createElement('div');
            menu.className = 'dropdown-menu';

            items.forEach(it => {
                const itemEl = document.createElement('div');
                itemEl.className = 'dropdown-item';
                itemEl.innerHTML = `${it.icon ? `<i data-lucide="${it.icon}" style="width:14px; height:14px;"></i>` : ''}<span>${it.label}</span>`;
                itemEl.addEventListener('click', (e) => {
                    e.stopPropagation();
                    menu.classList.remove('open');
                    if (it.onClick) it.onClick();
                });
                menu.appendChild(itemEl);
            });

            wrap.appendChild(btn);
            wrap.appendChild(menu);
            renderIcons(wrap);

            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('open');
            });

            document.addEventListener('click', () => menu.classList.remove('open'));
            return wrap;
        }
    };
})();
