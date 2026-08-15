from pathlib import Path
import pytest

from accessible_maps.delta.checksums import sha256_file
from accessible_maps.publish.github import GitHubPublishError, publish_github_release
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
