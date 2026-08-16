from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metadata import DatasetCatalog

WEB_ASSETS_DIR = Path(__file__).parent / "web"

CATALOG_CSS = (WEB_ASSETS_DIR / "style.css").read_text(encoding="utf-8")
CATALOG_JS = (WEB_ASSETS_DIR / "app.js").read_text(encoding="utf-8")


def generate_catalog_html(catalog: DatasetCatalog, repo: str | None = None) -> str:
    """Generate accessible, responsive HTML landing page for the catalog."""
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
            <td data-label="Region">
                <span class="region-name">{escaped_name}</span>
            </td>
            <td data-label="Version">
                <span class="badge badge-version">v{escaped_version}</span>
            </td>
            <td data-label="Updated">{escaped_updated[:10]}</td>
            <td data-label="Downloads">{downloads_html}</td>
            <td data-label="SHA-256">
                <code class="checksum-badge" title="{full_sha256}">{full_sha256 if full_sha256 else "N/A"}</code>
            </td>
            <td data-label="Deltas">{deltas_html}</td>
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
    <script src="app.js" defer></script>
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
                    <a class="btn btn-secondary" id="repo-link" href="https://github.com/{repo_name}" target="_blank" rel="noopener">
                        GitHub Repository
                    </a>
                </div>
            </div>

            <div class="meta-stats">
                <div class="stat-card">
                    <div class="stat-label">Total Regions</div>
                    <div class="stat-value" id="stat-total-regions">{total_regions}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Catalog Version</div>
                    <div class="stat-value" id="stat-catalog-version">v{catalog.catalog_version}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Data Attribution</div>
                    <div class="stat-value stat-value-sub">
                        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener" class="stat-link">&copy; OpenStreetMap (ODbL)</a>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Last Updated (UTC)</div>
                    <div class="stat-value stat-value-sub" id="stat-updated-at">{updated_at[:19]}</div>
                </div>
            </div>
        </header>

        <main>
            <div class="controls-row">
                <input
                    type="search"
                    id="search"
                    class="search-input"
                    placeholder="Search regions (e.g. London, Manchester, Scotland, Wales)..."
                    aria-label="Search regions"
                >
                <select id="sort-select" class="sort-select" aria-label="Sort datasets by">
                    <option value="name-asc">Sort: Region Name (A-Z)</option>
                    <option value="name-desc">Sort: Region Name (Z-A)</option>
                    <option value="version-desc">Sort: Version (Newest First)</option>
                    <option value="updated-desc">Sort: Updated Date (Recent First)</option>
                    <option value="size-desc">Sort: Size (Largest First)</option>
                    <option value="size-asc">Sort: Size (Smallest First)</option>
                </select>
            </div>

            <div id="status-container" class="status-message"></div>

            <div id="table-container" class="table-responsive">
                <table id="regions-table">
                    <thead>
                        <tr>
                            <th scope="col" class="sortable" data-sort="name">Region &#x21C5;</th>
                            <th scope="col" class="sortable" data-sort="version">Version &#x21C5;</th>
                            <th scope="col" class="sortable" data-sort="updated">Updated &#x21C5;</th>
                            <th scope="col">Downloads</th>
                            <th scope="col">SHA-256</th>
                            <th scope="col">Available Deltas</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
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
</body>
</html>
"""


def write_catalog_html(
    catalog: DatasetCatalog,
    output_path: Path,
    repo: str | None = None,
) -> tuple[Path, Path, Path]:
    """Write generated catalog HTML landing page, external stylesheet, and client app JS to directory."""
    output_path = Path(output_path)
    output_dir = output_path.parent if output_path.suffix else output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    html_file = output_dir / (output_path.name if output_path.suffix else "index.html")
    css_file = output_dir / "style.css"
    js_file = output_dir / "app.js"

    html_content = generate_catalog_html(catalog, repo=repo)
    html_file.write_text(html_content, encoding="utf-8")
    css_file.write_text(CATALOG_CSS, encoding="utf-8")
    js_file.write_text(CATALOG_JS, encoding="utf-8")

    return html_file, css_file, js_file
