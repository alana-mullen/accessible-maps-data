from pathlib import Path

from accessible_maps.delta.checksums import sha256_file
from accessible_maps.publish.metadata import AssetInfo, ReleaseMetadata
from accessible_maps.publish.validator import (
    parse_checksums_file,
    validate_checksums_file,
    validate_geopackage,
    validate_release_package,
)


def test_validate_geopackage_missing(tmp_path: Path):
    valid, errors = validate_geopackage(tmp_path / "missing.gpkg")
    assert not valid
    assert any("does not exist" in e for e in errors)


def test_validate_geopackage_empty(tmp_path: Path):
    empty_file = tmp_path / "empty.gpkg"
    empty_file.write_bytes(b"")
    valid, errors = validate_geopackage(empty_file)
    assert not valid
    assert any("empty" in e for e in errors)


def test_parse_and_validate_checksums_file(tmp_path: Path):
    f1 = tmp_path / "file1.bin"
    f1.write_bytes(b"content-1")
    f2 = tmp_path / "file2.bin"
    f2.write_bytes(b"content-2")

    checksums_file = tmp_path / "checksums.txt"
    checksums_file.write_text(
        f"{sha256_file(f1)}  file1.bin\n{sha256_file(f2)} *file2.bin\n",
        encoding="utf-8",
    )

    parsed = parse_checksums_file(checksums_file)
    assert parsed["file1.bin"] == sha256_file(f1)
    assert parsed["file2.bin"] == sha256_file(f2)

    valid, errors = validate_checksums_file(tmp_path, checksums_file)
    assert valid
    assert len(errors) == 0


def test_validate_release_package(tmp_path: Path):
    rel_dir = tmp_path / "release"
    rel_dir.mkdir()

    data_file = rel_dir / "dataset.zip"
    data_file.write_bytes(b"mock-dataset-zip")

    # Checksums
    checksums = rel_dir / "checksums.txt"
    checksums.write_text(f"{sha256_file(data_file)}  dataset.zip\n", encoding="utf-8")

    # Metadata
    metadata = ReleaseMetadata(
        release_tag="v1.0-test",
        dataset_name="test",
        version="1.0",
        assets=[
            AssetInfo(
                filename="dataset.zip",
                sha256=sha256_file(data_file),
                size_bytes=data_file.stat().st_size,
            )
        ],
    )
    (rel_dir / "metadata.json").write_text(metadata.to_json(), encoding="utf-8")

    valid, errors = validate_release_package(rel_dir)
    assert valid
    assert len(errors) == 0

    # Tampering with file causes failure
    data_file.write_bytes(b"tampered-content")
    valid, errors = validate_release_package(rel_dir)
    assert not valid
    assert any("Checksum mismatch" in e for e in errors)
