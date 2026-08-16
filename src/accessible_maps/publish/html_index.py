from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metadata import DatasetCatalog

CATALOG_CSS = """\
:root {
    --bg-color: #0f172a;
    --card-bg: #1e293b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --accent: #38bdf8;
    --accent-hover: #0ea5e9;
    --accent-dim: rgba(56, 189, 248, 0.15);
    --border-color: #334155;
    --badge-bg: #334155;
    --success-color: #34d399;
    --zst-color: #818cf8;
    --zst-hover: #6366f1;
    --radius-md: 8px;
    --radius-lg: 12px;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: var(--bg-color);
    color: var(--text-main);
    font-family: var(--font-sans);
    line-height: 1.6;
    padding: 2rem 1rem;
    min-height: 100vh;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
}

header {
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 1.5rem;
}

.header-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1rem;
}

h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.header-links {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease-in-out;
    cursor: pointer;
}

.btn-primary {
    background-color: var(--accent);
    color: #0f172a;
}

.btn-primary:hover {
    background-color: var(--accent-hover);
}

.btn-secondary {
    background-color: var(--card-bg);
    color: var(--text-main);
    border: 1px solid var(--border-color);
}

.btn-secondary:hover {
    background-color: #273549;
    border-color: var(--accent);
}

.subtitle {
    color: var(--text-muted);
    margin-top: 0.5rem;
    font-size: 1rem;
}

.meta-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}

.stat-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
}

.stat-label {
    font-size: 0.8125rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent);
    margin-top: 0.25rem;
}

.stat-value-sub {
    font-size: 1.05rem;
    padding-top: 0.35rem;
}

.stat-link {
    color: var(--accent);
    text-decoration: none;
}

.stat-link:hover {
    text-decoration: underline;
}

.search-bar-row {
    margin: 1.5rem 0;
    display: flex;
    gap: 1rem;
    align-items: center;
}

.search-input {
    flex: 1;
    padding: 0.75rem 1rem;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-main);
    font-size: 1rem;
    outline: none;
    transition: border-color 0.15s ease;
}

.search-input:focus {
    border-color: var(--accent);
}

.table-responsive {
    overflow-x: auto;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.9375rem;
}

th {
    background-color: #162032;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.8125rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--border-color);
}

td {
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--border-color);
    vertical-align: middle;
}

tr:last-child td {
    border-bottom: none;
}

tr:hover td {
    background-color: rgba(56, 189, 248, 0.03);
}

.region-name {
    font-weight: 600;
    color: var(--text-main);
    text-transform: capitalize;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: var(--font-mono);
}

.badge-version {
    background-color: var(--accent-dim);
    color: var(--accent);
    border: 1px solid rgba(56, 189, 248, 0.3);
}

.checksum-badge {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    background-color: var(--badge-bg);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    color: var(--text-muted);
}

.download-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    align-items: center;
}

.btn-download {
    display: inline-block;
    padding: 0.35rem 0.65rem;
    border-radius: var(--radius-md);
    font-size: 0.8125rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.15s ease;
    white-space: nowrap;
}

.btn-zip {
    background-color: var(--accent);
    color: #0f172a;
}

.btn-zip:hover {
    background-color: var(--accent-hover);
}

.btn-zst {
    background-color: var(--zst-color);
    color: #ffffff;
}

.btn-zst:hover {
    background-color: var(--zst-hover);
}

.deltas-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
}

.delta-badge {
    display: inline-block;
    background-color: rgba(52, 211, 153, 0.15);
    color: var(--success-color);
    border: 1px solid rgba(52, 211, 153, 0.3);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    text-decoration: none;
    transition: all 0.15s ease;
    white-space: nowrap;
}

.delta-badge:hover {
    background-color: rgba(52, 211, 153, 0.3);
}

.text-muted {
    color: var(--text-muted);
    font-size: 0.8125rem;
}

footer {
    margin-top: 3rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-color);
    text-align: center;
    color: var(--text-muted);
    font-size: 0.875rem;
}

.footer-sub {
    margin-top: 0.4rem;
}

footer a {
    color: var(--accent);
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

.hidden {
    display: none !important;
}
"""


def generate_catalog_html(catalog: DatasetCatalog, repo: str | None = None) -> str:
    """Generate accessible, standalone, responsive HTML landing page for the catalog."""
    repo_name = html.escape(repo or "alana-mullen/accessible-maps-data")
    updated_at = html.escape(catalog.updated_at or "Unknown")
    total_regions = len(catalog.regions)

    region_rows: list[str] = []
    for region_name, entry in sorted(catalog.regions.items()):
        escaped_name = html.escape(region_name)
        escaped_version = html.escape(entry.latest_version)
        escaped_updated = html.escape(entry.latest_updated_at or "")

        # Download buttons
        download_buttons: list[str] = []
        if entry.full_dataset_download_url:
            zip_url = html.escape(entry.full_dataset_download_url)
            zip_size = (
                f"{entry.full_dataset_size_bytes / (1024 * 1024):.1f} MB"
                if entry.full_dataset_size_bytes
                else ""
            )
            download_buttons.append(
                f'<a class="btn-download btn-zip" href="{zip_url}" title="Download ZIP GeoPackage dataset ({zip_size})" aria-label="Download ZIP dataset for {escaped_name}">'
                f".gpkg.zip {f'({zip_size})' if zip_size else ''}</a>"
            )

        if entry.zst_dataset_download_url:
            zst_url = html.escape(entry.zst_dataset_download_url)
            zst_size = (
                f"{entry.zst_dataset_size_bytes / (1024 * 1024):.1f} MB"
                if entry.zst_dataset_size_bytes
                else ""
            )
            download_buttons.append(
                f'<a class="btn-download btn-zst" href="{zst_url}" title="Download Zstandard GeoPackage dataset ({zst_size})" aria-label="Download Zstandard dataset for {escaped_name}">'
                f".gpkg.zst {f'({zst_size})' if zst_size else ''}</a>"
            )

        downloads_html = (
            f'<div class="download-group">{" ".join(download_buttons)}</div>'
            if download_buttons
            else '<span class="text-muted">N/A</span>'
        )

        raw_sha256 = entry.full_dataset_sha256 or entry.zst_dataset_sha256 or ""
        sha256_short = html.escape(raw_sha256[:12] + "..." if raw_sha256 else "N/A")
        full_sha256 = html.escape(raw_sha256)

        deltas_html = ""
        if entry.available_deltas:
            delta_links = []
            for d in entry.available_deltas:
                d_url = html.escape(d.download_url or "#")
                d_from = html.escape(d.from_version)
                d_to = html.escape(d.to_version)
                d_size = f"{d.size_bytes / 1024:.1f} KB" if d.size_bytes else ""
                delta_links.append(
                    f'<a class="delta-badge" href="{d_url}" title="Delta {d_from} -> {d_to} ({d_size})" aria-label="Download delta from version {d_from} to {d_to}">'
                    f"v{d_from} &rarr; v{d_to} ({d_size})</a>"
                )
            deltas_html = f'<div class="deltas-container">{" ".join(delta_links)}</div>'
        else:
            deltas_html = '<span class="text-muted">None</span>'

        region_rows.append(
            f"""
        <tr data-region="{escaped_name}">
            <td class="col-region">
                <span class="region-name">{escaped_name}</span>
            </td>
            <td class="col-version">
                <span class="badge badge-version">v{escaped_version}</span>
            </td>
            <td class="col-updated">{escaped_updated[:10]}</td>
            <td class="col-downloads">{downloads_html}</td>
            <td class="col-checksum">
                <code class="checksum-badge" title="{full_sha256}">{sha256_short}</code>
            </td>
            <td class="col-deltas">{deltas_html}</td>
        </tr>"""
        )

    regions_table_body = "\n".join(region_rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Accessible Maps UK Geospatial Accessibility Dataset Distribution & Delta Catalog">
    <title>Accessible Maps Data Catalog</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title-row">
                <div>
                    <h1>Accessible Maps Data Catalog</h1>
                    <p class="subtitle">
                        Geospatial accessibility dataset distribution &amp; cryptographic delta packages derived from
                        <strong>&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a></strong> (<a href="https://opendatacommons.org/licenses/odbl/" target="_blank" rel="noopener">ODbL</a>)
                    </p>
                </div>
                <div class="header-links">
                    <a class="btn btn-primary" href="catalog.json" target="_blank" rel="noopener">
                        View catalog.json
                    </a>
                    <a class="btn btn-secondary" href="https://github.com/{repo_name}" target="_blank" rel="noopener">
                        GitHub Repository
                    </a>
                </div>
            </div>

            <div class="meta-stats">
                <div class="stat-card">
                    <div class="stat-label">Total Regions</div>
                    <div class="stat-value">{total_regions}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Catalog Version</div>
                    <div class="stat-value">v{catalog.catalog_version}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Data Attribution</div>
                    <div class="stat-value stat-value-sub">
                        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener" class="stat-link">&copy; OpenStreetMap (ODbL)</a>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Last Updated (UTC)</div>
                    <div class="stat-value stat-value-sub">{updated_at[:19]}</div>
                </div>
            </div>
        </header>

        <main>
            <div class="search-bar-row">
                <input
                    type="search"
                    id="search"
                    class="search-input"
                    placeholder="Filter regions (e.g. London, Manchester, Scotland, Wales)..."
                    aria-label="Filter regions"
                >
            </div>

            <div class="table-responsive">
                <table id="regions-table">
                    <thead>
                        <tr>
                            <th scope="col">Region</th>
                            <th scope="col">Version</th>
                            <th scope="col">Updated</th>
                            <th scope="col">Downloads</th>
                            <th scope="col">SHA-256</th>
                            <th scope="col">Available Deltas</th>
                        </tr>
                    </thead>
                    <tbody>
{regions_table_body}
                    </tbody>
                </table>
            </div>
        </main>

        <footer>
            <p>Data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap contributors</a>, licensed under the <a href="https://opendatacommons.org/licenses/odbl/" target="_blank" rel="noopener">Open Database License (ODbL)</a>. Regional extracts sourced via <a href="https://download.geofabrik.de/" target="_blank" rel="noopener">Geofabrik</a>.</p>
            <p class="footer-sub">Automated pipeline built with <a href="https://github.com/{repo_name}" target="_blank" rel="noopener">{repo_name}</a>.</p>
        </footer>
    </div>

    <script>
        document.getElementById('search').addEventListener('input', function(e) {{
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('#regions-table tbody tr');
            rows.forEach(row => {{
                const region = row.getAttribute('data-region') || '';
                row.classList.toggle('hidden', !region.toLowerCase().includes(query));
            }});
        }});
    </script>
</body>
</html>
"""


def write_catalog_html(
    catalog: DatasetCatalog,
    output_path: Path,
    repo: str | None = None,
) -> tuple[Path, Path]:
    """Write generated catalog HTML landing page and external stylesheet to directory."""
    output_path = Path(output_path)
    output_dir = output_path.parent if output_path.suffix else output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    html_file = output_dir / (output_path.name if output_path.suffix else "index.html")
    css_file = output_dir / "style.css"

    html_content = generate_catalog_html(catalog, repo=repo)
    html_file.write_text(html_content, encoding="utf-8")
    css_file.write_text(CATALOG_CSS, encoding="utf-8")

    return html_file, css_file
