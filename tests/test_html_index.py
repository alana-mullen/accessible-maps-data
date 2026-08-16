from pathlib import Path

from accessible_maps.publish.html_index import (
    CATALOG_CSS,
    CATALOG_HTML,
    CATALOG_JS,
    render_catalog_html,
    write_catalog_html,
)
from accessible_maps.publish.metadata import DatasetCatalog


def test_render_and_write_catalog_html(tmp_path: Path):
    catalog = DatasetCatalog()

    html_content = render_catalog_html(repo="test-org/test-repo")
    assert "<!DOCTYPE html>" in html_content
    assert '<link rel="stylesheet" href="style.css">' in html_content
    assert '<script src="app.js" defer></script>' in html_content
    assert "<style>" not in html_content
    assert "Accessible Maps Data Catalog" in html_content
    assert "test-org/test-repo" in html_content
    assert "OpenStreetMap" in html_content

    out_file = tmp_path / "index.html"
    html_res, css_res, js_res = write_catalog_html(catalog, out_file, repo="test-org/test-repo")
    assert html_res.is_file()
    assert css_res.is_file()
    assert js_res.is_file()
    assert html_res.name == "index.html"
    assert css_res.name == "style.css"
    assert js_res.name == "app.js"
    assert css_res.read_text(encoding="utf-8") == CATALOG_CSS
    assert js_res.read_text(encoding="utf-8") == CATALOG_JS
    assert html_res.read_text(encoding="utf-8") == html_content
    assert CATALOG_HTML != ""
