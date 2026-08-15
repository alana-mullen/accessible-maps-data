from pathlib import Path
import zipfile

import pytest

from accessible_maps.download import (
    DownloadError,
    _download_with_retries,
    _find_gpkg,
    _safe_extract,
    _valid_zip,
)


def test_valid_zip(tmp_path: Path):
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("example.gpkg", b"placeholder")

    assert _valid_zip(archive)


def test_invalid_zip(tmp_path: Path):
    archive = tmp_path / "test.zip"
    archive.write_text("not a zip")

    assert not _valid_zip(archive)


def test_find_gpkg(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    gpkg = nested / "source.gpkg"
    gpkg.write_bytes(b"placeholder")

    assert _find_gpkg(tmp_path) == gpkg


def test_find_gpkg_rejects_multiple(tmp_path: Path):
    (tmp_path / "one.gpkg").write_bytes(b"1")
    (tmp_path / "two.gpkg").write_bytes(b"2")

    with pytest.raises(DownloadError):
        _find_gpkg(tmp_path)


def test_safe_extract_rejects_path_traversal(tmp_path: Path):
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../../evil.txt", "bad")

    destination = tmp_path / "extract"
    destination.mkdir()

    with zipfile.ZipFile(archive) as zf:
        with pytest.raises(DownloadError):
            _safe_extract(zf, destination)


def test_download_with_retries_304_reuses_archive(tmp_path: Path, monkeypatch):
    archive = tmp_path / "test.gpkg.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("test.gpkg", b"data")

    etag_file = archive.with_suffix(".etag")
    etag_file.write_text('"12345"', encoding="utf-8")

    class MockResponse:
        status_code = 304

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("requests.get", lambda url, **kwargs: MockResponse())

    # Should exit cleanly without error when 304 received
    _download_with_retries("https://example.com/test.zip", archive, attempts=1, timeout=(5.0, 5.0))
    assert archive.is_file()
