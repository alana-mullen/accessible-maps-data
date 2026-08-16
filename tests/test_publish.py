from pathlib import Path

import pytest

from accessible_maps.delta.checksums import sha256_file
from accessible_maps.publish.github import (
    GitHubPublishError,
    fetch_github_releases_metadata,
    publish_github_release,
)
from accessible_maps.publish.metadata import AssetInfo, ReleaseMetadata


def test_publish_github_release_dry_run(tmp_path: Path):
    rel_dir = tmp_path / "release"
    rel_dir.mkdir()

    asset_file = rel_dir / "london-1.0.gpkg.zip"
    asset_file.write_bytes(b"sample-zip-data")

    checksums = rel_dir / "checksums.txt"
    checksums.write_text(f"{sha256_file(asset_file)}  london-1.0.gpkg.zip\n", encoding="utf-8")

    metadata = ReleaseMetadata(
        release_tag="v1.0-london",
        dataset_name="london",
        version="1.0",
        assets=[
            AssetInfo(
                filename="london-1.0.gpkg.zip",
                sha256=sha256_file(asset_file),
                size_bytes=asset_file.stat().st_size,
            )
        ],
    )
    (rel_dir / "metadata.json").write_text(metadata.to_json(), encoding="utf-8")

    result = publish_github_release(
        release_dir=rel_dir,
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["release_tag"] == "v1.0-london"
    assert "london-1.0.gpkg.zip" in result["assets"]


def test_publish_github_release_missing_auth_raises(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    rel_dir = tmp_path / "release"
    rel_dir.mkdir()
    asset = rel_dir / "test.zip"
    asset.write_bytes(b"data")
    (rel_dir / "checksums.txt").write_text(f"{sha256_file(asset)}  test.zip\n")

    metadata = ReleaseMetadata(
        release_tag="v1.0-test",
        dataset_name="test",
        version="1.0",
        assets=[AssetInfo(filename="test.zip", sha256=sha256_file(asset), size_bytes=4)],
    )
    (rel_dir / "metadata.json").write_text(metadata.to_json(), encoding="utf-8")

    with pytest.raises(GitHubPublishError):
        publish_github_release(release_dir=rel_dir, dry_run=False)


def test_fetch_github_releases_metadata(monkeypatch):
    sample_meta = ReleaseMetadata(
        release_tag="v2026.08.16.01-greater-london",
        dataset_name="greater-london",
        version="2026.08.16.01",
    )

    class MockReleasesResponse:
        status_code = 200

        def json(self):
            return [
                {
                    "tag_name": "v2026.08.16.01-greater-london",
                    "assets": [
                        {
                            "name": "metadata.json",
                            "browser_download_url": "https://example.com/metadata.json",
                        }
                    ],
                }
            ]

        def raise_for_status(self):
            pass

    class MockMetadataResponse:
        status_code = 200
        text = sample_meta.to_json()

    def mock_get(url, **kwargs):
        if "releases" in url:
            return MockReleasesResponse()
        return MockMetadataResponse()

    monkeypatch.setattr("requests.get", mock_get)

    results = fetch_github_releases_metadata("test-owner/test-repo", token="mock-token")
    assert len(results) == 1
    assert results[0].dataset_name == "greater-london"
    assert results[0].version == "2026.08.16.01"
