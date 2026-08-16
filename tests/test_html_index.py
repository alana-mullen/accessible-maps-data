from pathlib import Path

from accessible_maps.publish.html_index import (
    CATALOG_CSS,
    generate_catalog_html,
    write_catalog_html,
)
from accessible_maps.publish.metadata import AssetInfo, DatasetCatalog, ReleaseMetadata


def test_generate_and_write_catalog_html(tmp_path: Path):
    catalog = DatasetCatalog()
    meta = ReleaseMetadata(
        release_tag="v2026.08.16.01-greater-london",
        dataset_name="greater-london",
        version="2026.08.16.01",
        assets=[
            AssetInfo(
                filename="greater-london.gpkg.zip",
                sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                size_bytes=10 * 1024 * 1024,
                download_url="https://github.com/example/repo/releases/download/tag/file.zip",
            )
        ],
    )
    catalog.add_release(meta)

    html_content = generate_catalog_html(catalog, repo="test-org/test-repo")
    assert "<!DOCTYPE html>" in html_content
    assert '<link rel="stylesheet" href="style.css">' in html_content
    assert "<style>" not in html_content
    assert "Accessible Maps Data Catalog" in html_content
    assert "greater-london" in html_content
    assert "v2026.08.16.01" in html_content
    assert "10.0 MB" in html_content

    out_file = tmp_path / "index.html"
    html_res, css_res = write_catalog_html(catalog, out_file, repo="test-org/test-repo")
    assert html_res.is_file()
    assert css_res.is_file()
    assert css_res.name == "style.css"
    assert css_res.read_text(encoding="utf-8") == CATALOG_CSS
    assert html_res.read_text(encoding="utf-8") == html_content
