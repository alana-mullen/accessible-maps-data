/**
 * Accessible Maps Data Catalog - Client-Side App
 * Fetches catalog.json and renders an accessible, responsive, dual-mode table.
 */

(function () {
    'use strict';

    let catalogData = null;
    let regionsList = [];
    let currentSort = { column: 'name', ascending: true };

    const elements = {
        totalRegions: document.getElementById('stat-total-regions'),
        catalogVersion: document.getElementById('stat-catalog-version'),
        updatedAt: document.getElementById('stat-updated-at'),
        searchInput: document.getElementById('search'),
        sortSelect: document.getElementById('sort-select'),
        tableBody: document.getElementById('table-body'),
        statusContainer: document.getElementById('status-container'),
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
     * Format bytes into human-readable size (MB / KB).
     */
    function formatBytes(bytes) {
        if (!bytes || isNaN(bytes)) return '';
        if (bytes >= 1024 * 1024) {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        return (bytes / 1024).toFixed(1) + ' KB';
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
     * Hide status container by emptying it (CSS :empty handles visibility).
     */
    function showTable() {
        if (elements.statusContainer) {
            elements.statusContainer.innerHTML = '';
        }
    }

    /**
     * Populate header statistics.
     */
    function renderStats(catalog) {
        if (elements.totalRegions) {
            elements.totalRegions.textContent = Object.keys(catalog.regions || {}).length;
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
     * Build row HTML for a single region.
     */
    function buildRegionRow(region) {
        const escapedName = escapeHtml(region.region_name);
        const escapedVersion = escapeHtml(region.latest_version || '1.0');
        const rawDate = region.latest_updated_at || '';
        const dateFormatted = escapeHtml(rawDate.length >= 10 ? rawDate.substring(0, 10) : rawDate);

        // 1. Download buttons (.zip & .zst)
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

        // 2. Checksum (Full hash rendered into DOM; CSS handles visual ellipsis truncation)
        const fullSha = escapeHtml(region.full_dataset_sha256 || region.zst_dataset_sha256 || '');

        // 3. Deltas display
        let deltasHtml = '<span class="text-muted">None</span>';
        if (region.available_deltas && region.available_deltas.length > 0) {
            const deltaBadges = region.available_deltas.map(d => {
                const dUrl = escapeHtml(d.download_url || '#');
                const dFrom = escapeHtml(d.from_version);
                const dTo = escapeHtml(d.to_version);
                const dSize = formatBytes(d.size_bytes);
                return `
                    <a class="delta-badge" href="${dUrl}" title="Delta ${dFrom} -> ${dTo} (${dSize})" aria-label="Download delta from ${dFrom} to ${dTo}">
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
                <td data-label="Downloads">
                    ${downloadsHtml}
                </td>
                <td data-label="SHA-256">
                    <code class="checksum-badge" title="${fullSha}" onclick="navigator.clipboard && navigator.clipboard.writeText('${fullSha}')">${fullSha || 'N/A'}</code>
                </td>
                <td data-label="Deltas">
                    ${deltasHtml}
                </td>
            </tr>
        `;
    }

    /**
     * Render rows into the table body based on search filter and sort order.
     */
    function renderTable() {
        if (!elements.tableBody) return;

        const query = (elements.searchInput ? elements.searchInput.value : '').toLowerCase().trim();

        // 1. Filter
        const filtered = regionsList.filter(r => {
            if (!query) return true;
            return r.region_name.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            elements.tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="status-message">
                        No regions match <strong>"${escapeHtml(query)}"</strong>.
                    </td>
                </tr>
            `;
            return;
        }

        // 2. Sort
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

        // 3. Render
        elements.tableBody.innerHTML = filtered.map(buildRegionRow).join('');
    }

    /**
     * Initialize event listeners.
     */
    function initEvents() {
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', renderTable);
        }

        if (elements.sortSelect) {
            elements.sortSelect.addEventListener('change', function (e) {
                const parts = e.target.value.split('-');
                currentSort.column = parts[0];
                currentSort.ascending = parts[1] === 'asc';
                renderTable();
            });
        }

        // Column header sorting
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
                    available_deltas: entry.available_deltas || [],
                };
            });

            renderStats(catalogData);
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
