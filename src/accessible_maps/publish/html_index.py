from __future__ import annotations

import html
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metadata import DatasetCatalog

WEB_ASSETS_DIR = Path(__file__).parent / "web"

CATALOG_HTML = (WEB_ASSETS_DIR / "index.html").read_text(encoding="utf-8")
CATALOG_CSS = (WEB_ASSETS_DIR / "style.css").read_text(encoding="utf-8")
CATALOG_JS = (WEB_ASSETS_DIR / "app.js").read_text(encoding="utf-8")


def render_catalog_html(repo: str | None = None) -> str:
    """Return the client-side catalog HTML shell configured with the repository name."""
    repo_name = html.escape(repo or "alana-mullen/accessible-maps-data")
    return CATALOG_HTML.replace("alana-mullen/accessible-maps-data", repo_name)


def write_catalog_html(
    catalog: DatasetCatalog | None = None,
    output_path: Path | str = "index.html",
    repo: str | None = None,
) -> tuple[Path, Path, Path]:
    """Write static client-side web application assets (index.html, style.css, app.js) to directory."""
    output_path = Path(output_path)
    output_dir = output_path.parent if output_path.suffix else output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    html_file = output_dir / (output_path.name if output_path.suffix else "index.html")
    css_file = output_dir / "style.css"
    js_file = output_dir / "app.js"

    html_content = render_catalog_html(repo=repo)
    html_file.write_text(html_content, encoding="utf-8")
    css_file.write_text(CATALOG_CSS, encoding="utf-8")
    js_file.write_text(CATALOG_JS, encoding="utf-8")

    return html_file, css_file, js_file
