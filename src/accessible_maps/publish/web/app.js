/**
 * Accessible Maps Data Catalog - Client-Side App
 * Fetches catalog.json and renders an accessible, responsive, dual-mode table
 * with real-time filtering, categorization, sorting, and stats breakdowns.
 */

(function () {
    'use strict';

    let catalogData = null;
    let regionsList = [];
    let currentCategory = 'all';
    let currentSort = { column: 'name', ascending: true };

    const elements = {
        totalRegions: document.getElementById('stat-total-regions'),
        totalSize: document.getElementById('stat-total-size'),
        catalogVersion: document.getElementById('stat-catalog-version'),
        updatedAt: document.getElementById('stat-updated-at'),
        searchInput: document.getElementById('search'),
        searchClear: document.getElementById('search-clear'),
        resultsCount: document.getElementById('results-count'),
        sortSelect: document.getElementById('sort-select'),
        tableBody: document.getElementById('table-body'),
        statusContainer: document.getElementById('status-container'),
        pillsContainer: document.getElementById('filter-pills'),
    };

    /**
     * Escape HTML special characters to prevent XSS.
     */
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * Format bytes into human-readable size (MB / GB / KB).
     */
    function formatBytes(bytes) {
        if (!bytes || isNaN(bytes)) return '';
        if (bytes >= 1024 * 1024 * 1024) {
            return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
        }
        if (bytes >= 1024 * 1024) {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        return (bytes / 1024).toFixed(1) + ' KB';
    }

    /**
     * Format large numbers compactly (e.g. 154200 -> 154.2k).
     */
    function formatCompactNumber(num) {
        if (!num || isNaN(num)) return '0';
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'k';
        }
        return num.toLocaleString();
    }

    /**
     * Determine category for a given region identifier.
     */
    function getRegionCategory(name) {
        const lower = (name || '').toLowerCase();
        if (lower === 'scotland') return 'scotland';
        if (lower === 'wales') return 'wales';
        if (lower === 'northern-ireland') return 'northern-ireland';
        if (lower === 'isle-of-man' || lower === 'guernsey-jersey' || lower.includes('island')) {
            return 'islands';
        }
        return 'england';
    }

    /**
     * Show loading spinner.
     */
    function showLoading() {
        if (elements.statusContainer) {
            elements.statusContainer.innerHTML = `
                <div class="spinner" role="status" aria-label="Loading catalog"></div>
                <p>Loading Accessible Maps dataset catalog...</p>
            `;
        }
    }

    /**
     * Show error state.
     */
    function showError(message) {
        if (elements.statusContainer) {
            elements.statusContainer.innerHTML = `
                <p class="error-title">Unable to load dataset catalog</p>
                <p class="text-muted error-detail">${escapeHtml(message)}</p>
            `;
        }
    }

    /**
     * Hide status container by clearing contents (CSS :empty handles visibility).
     */
    function showTable() {
        if (elements.statusContainer) {
            elements.statusContainer.innerHTML = '';
        }
    }

    /**
     * Calculate and populate header statistics.
     */
    function renderStats(catalog) {
        const total = Object.keys(catalog.regions || {}).length;
        if (elements.totalRegions) {
            elements.totalRegions.textContent = total;
        }

        // Calculate total aggregate size of all Zstandard / ZIP datasets
        let aggregateBytes = 0;
        Object.values(catalog.regions || {}).forEach(entry => {
            const zstSize = (entry.zst_dataset && entry.zst_dataset.size_bytes) || 0;
            const zipSize = (entry.full_dataset && entry.full_dataset.size_bytes) || 0;
            aggregateBytes += zstSize || zipSize;
        });

        if (elements.totalSize) {
            elements.totalSize.textContent = formatBytes(aggregateBytes);
        }

        if (elements.catalogVersion) {
            elements.catalogVersion.textContent = 'v' + (catalog.catalog_version || '1.0');
        }

        if (elements.updatedAt) {
            const rawDate = catalog.updated_at || '';
            elements.updatedAt.textContent = rawDate.length >= 19 ? rawDate.substring(0, 19).replace('T', ' ') : rawDate;
        }
    }

    /**
     * Populate counts inside filter pills.
     */
    function updatePillCounts() {
        const counts = { all: regionsList.length, england: 0, scotland: 0, wales: 0, 'northern-ireland': 0, islands: 0 };
        regionsList.forEach(r => {
            const cat = getRegionCategory(r.region_name);
            if (counts[cat] !== undefined) {
                counts[cat]++;
            }
        });

        document.querySelectorAll('.pill-btn').forEach(btn => {
            const cat = btn.getAttribute('data-category');
            const countSpan = btn.querySelector('.pill-count');
            if (countSpan && counts[cat] !== undefined) {
                countSpan.textContent = counts[cat];
            }
        });
    }

    /**
     * Build row HTML for a single region.
     */
    function buildRegionRow(region) {
        const escapedName = escapeHtml(region.region_name);
        const escapedVersion = escapeHtml(region.latest_version || '1.0');
        const rawDate = region.latest_updated_at || '';
        const dateFormatted = escapeHtml(rawDate.length >= 10 ? rawDate.substring(0, 10) : rawDate);

        // 1. Layer feature stats breakdown
        let featuresHtml = '<span class="text-muted">&mdash;</span>';
        if (region.table_stats && Object.keys(region.table_stats).length > 0) {
            const statChips = Object.entries(region.table_stats).map(([table, count]) => {
                const tableName = escapeHtml(table.replace(/_/g, ' '));
                const countFormatted = formatCompactNumber(count);
                return `<span class="stats-chip" title="${tableName}: ${count.toLocaleString()} features">${countFormatted} ${tableName}</span>`;
            });
            featuresHtml = `<div class="feature-stats-pill">${statChips.join('')}</div>`;
        }

        // 2. Download buttons (.zip & .zst)
        const downloadButtons = [];
        if (region.full_dataset_download_url) {
            const zipUrl = escapeHtml(region.full_dataset_download_url);
            const zipSize = formatBytes(region.full_dataset_size_bytes);
            downloadButtons.push(`
                <a class="btn-download btn-zip" href="${zipUrl}" title="Download ZIP archive (${zipSize})" aria-label="Download ZIP dataset for ${escapedName}">
                    .gpkg.zip ${zipSize ? `(${zipSize})` : ''}
                </a>
            `);
        }

        if (region.zst_dataset_download_url) {
            const zstUrl = escapeHtml(region.zst_dataset_download_url);
            const zstSize = formatBytes(region.zst_dataset_size_bytes);
            downloadButtons.push(`
                <a class="btn-download btn-zst" href="${zstUrl}" title="Download Zstandard archive (${zstSize})" aria-label="Download Zstandard dataset for ${escapedName}">
                    .gpkg.zst ${zstSize ? `(${zstSize})` : ''}
                </a>
            `);
        }

        const downloadsHtml = downloadButtons.length > 0
            ? `<div class="download-group">${downloadButtons.join('')}</div>`
            : `<span class="text-muted">N/A</span>`;

        // 3. Checksum (Full hash rendered into DOM; CSS handles visual truncation)
        const fullSha = escapeHtml(region.full_dataset_sha256 || region.zst_dataset_sha256 || '');

        // 4. Deltas display
        let deltasHtml = '<span class="text-muted">None</span>';
        if (region.available_deltas && region.available_deltas.length > 0) {
            const deltaBadges = region.available_deltas.map(d => {
                const dUrl = escapeHtml(d.download_url || '#');
                const dFrom = escapeHtml(d.from_version);
                const dTo = escapeHtml(d.to_version);
                const dSize = formatBytes(d.size_bytes);
                let statSummary = '';
                if (d.delta_stats) {
                    const ins = d.delta_stats.inserts || 0;
                    const upd = d.delta_stats.updates || 0;
                    statSummary = ` (+${ins}/~${upd})`;
                }
                return `
                    <a class="delta-badge" href="${dUrl}" title="Delta ${dFrom} -> ${dTo}${statSummary} (${dSize})" aria-label="Download delta from ${dFrom} to ${dTo}">
                        v${dFrom} &rarr; v${dTo} ${dSize ? `(${dSize})` : ''}
                    </a>
                `;
            });
            deltasHtml = `<div class="deltas-container">${deltaBadges.join('')}</div>`;
        }

        return `
            <tr data-region="${escapedName}">
                <td data-label="Region">
                    <span class="region-name">${escapedName}</span>
                </td>
                <td data-label="Version">
                    <span class="badge badge-version">v${escapedVersion}</span>
                </td>
                <td data-label="Updated">
                    <span>${dateFormatted}</span>
                </td>
                <td data-label="Features">
                    ${featuresHtml}
                </td>
                <td data-label="Downloads">
                    ${downloadsHtml}
                </td>
                <td data-label="SHA-256">
                    <code class="checksum-badge" title="Click to copy full SHA-256 hash" onclick="navigator.clipboard && navigator.clipboard.writeText('${fullSha}')">${fullSha || 'N/A'}</code>
                </td>
                <td data-label="Deltas">
                    ${deltasHtml}
                </td>
            </tr>
        `;
    }

    /**
     * Render rows into the table body based on search filter, category, and sort order.
     */
    function renderTable() {
        if (!elements.tableBody) return;

        const query = (elements.searchInput ? elements.searchInput.value : '').toLowerCase().trim();

        // 1. Filter by category and search text
        const filtered = regionsList.filter(r => {
            const matchesCat = currentCategory === 'all' || getRegionCategory(r.region_name) === currentCategory;
            if (!matchesCat) return false;

            if (!query) return true;
            return r.region_name.toLowerCase().includes(query);
        });

        // 2. Update results count indicator
        if (elements.resultsCount) {
            elements.resultsCount.textContent = `Showing ${filtered.length} of ${regionsList.length} regions`;
        }

        if (filtered.length === 0) {
            elements.tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="status-message">
                        No regions found matching your criteria.
                    </td>
                </tr>
            `;
            return;
        }

        // 3. Sort
        filtered.sort((a, b) => {
            let valA, valB;
            switch (currentSort.column) {
                case 'size':
                    valA = a.full_dataset_size_bytes || a.zst_dataset_size_bytes || 0;
                    valB = b.full_dataset_size_bytes || b.zst_dataset_size_bytes || 0;
                    break;
                case 'updated':
                    valA = a.latest_updated_at || '';
                    valB = b.latest_updated_at || '';
                    break;
                case 'version':
                    valA = a.latest_version || '';
                    valB = b.latest_version || '';
                    break;
                case 'name':
                default:
                    valA = a.region_name.toLowerCase();
                    valB = b.region_name.toLowerCase();
                    break;
            }

            if (valA < valB) return currentSort.ascending ? -1 : 1;
            if (valA > valB) return currentSort.ascending ? 1 : -1;
            return 0;
        });

        // 4. Render rows
        elements.tableBody.innerHTML = filtered.map(buildRegionRow).join('');
    }

    /**
     * Initialize event listeners.
     */
    function initEvents() {
        // Search Input
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', renderTable);
        }

        // Search Clear Button
        if (elements.searchClear) {
            elements.searchClear.addEventListener('click', function () {
                if (elements.searchInput) {
                    elements.searchInput.value = '';
                    elements.searchInput.focus();
                }
                renderTable();
            });
        }

        // Keyboard Shortcut: Press '/' or 'Cmd+K' to focus search
        document.addEventListener('keydown', function (e) {
            if ((e.key === '/' || (e.key === 'k' && (e.metaKey || e.ctrlKey))) && document.activeElement !== elements.searchInput) {
                e.preventDefault();
                if (elements.searchInput) {
                    elements.searchInput.focus();
                    elements.searchInput.select();
                }
            }
        });

        // Category Filter Pills
        document.querySelectorAll('.pill-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentCategory = this.getAttribute('data-category') || 'all';
                renderTable();
            });
        });

        // Sort Select Dropdown
        if (elements.sortSelect) {
            elements.sortSelect.addEventListener('change', function (e) {
                const parts = e.target.value.split('-');
                currentSort.column = parts[0];
                currentSort.ascending = parts[1] === 'asc';
                renderTable();
            });
        }

        // Column Header Sorting
        document.querySelectorAll('th.sortable').forEach(th => {
            th.addEventListener('click', function () {
                const col = this.getAttribute('data-sort');
                if (currentSort.column === col) {
                    currentSort.ascending = !currentSort.ascending;
                } else {
                    currentSort.column = col;
                    currentSort.ascending = true;
                }

                // Update select dropdown to match
                if (elements.sortSelect) {
                    elements.sortSelect.value = `${currentSort.column}-${currentSort.ascending ? 'asc' : 'desc'}`;
                }

                renderTable();
            });
        });
    }

    /**
     * Fetch catalog.json and start the application.
     */
    async function init() {
        showLoading();
        initEvents();

        try {
            const response = await fetch('catalog.json?t=' + Date.now(), {
                headers: { 'Accept': 'application/json' },
                cache: 'no-cache'
            });

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status} (${response.statusText})`);
            }

            catalogData = await response.json();

            // Transform regions dict into array
            regionsList = Object.entries(catalogData.regions || {}).map(([name, entry]) => {
                const fullInfo = entry.full_dataset || {};
                const zstInfo = entry.zst_dataset || {};
                return {
                    region_name: entry.region_name || name,
                    latest_version: entry.latest_version || '1.0',
                    latest_release_tag: entry.latest_release_tag || '',
                    latest_updated_at: entry.latest_updated_at || '',
                    full_dataset_download_url: fullInfo.download_url || entry.full_dataset_download_url,
                    full_dataset_size_bytes: fullInfo.size_bytes || entry.full_dataset_size_bytes,
                    full_dataset_sha256: fullInfo.sha256 || entry.full_dataset_sha256,
                    zst_dataset_download_url: zstInfo.download_url || entry.zst_dataset_download_url,
                    zst_dataset_size_bytes: zstInfo.size_bytes || entry.zst_dataset_size_bytes,
                    zst_dataset_sha256: zstInfo.sha256 || entry.zst_dataset_sha256,
                    table_stats: fullInfo.table_stats || entry.table_stats || {},
                    available_deltas: entry.available_deltas || [],
                };
            });

            renderStats(catalogData);
            updatePillCounts();
            renderTable();
            showTable();
        } catch (err) {
            console.error('Failed to load dataset catalog:', err);
            showError(`Could not fetch catalog.json: ${err.message}`);
        }
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
