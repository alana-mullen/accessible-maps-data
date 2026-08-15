from pathlib import Path

from accessible_maps.delta.manifest import (
    build_manifest,
    load_manifest,
    save_manifest,
    validate_manifest,
)
from accessible_maps.delta.models import TableDelta
from accessible_maps.delta.signing import generate_keypair


def test_manifest_roundtrip_and_validation(tmp_path: Path):
    delta_dir = tmp_path / "delta"
    delta_dir.mkdir()

    # Create dummy base and target files
    base_file = tmp_path / "base.gpkg"
    base_file.write_bytes(b"base-gpkg-content")

    target_file = tmp_path / "target.gpkg"
    target_file.write_bytes(b"target-gpkg-content")

    # Create dummy table delta
    td = TableDelta(
        table_name="kerbs",
        primary_key="fid",
        inserts=[{"fid": 10}],
        updates=[{"fid": 2}],
        deletes=[1],
        total_target_rows=5,
    )
    delta_file = delta_dir / "kerbs.delta.json"
    delta_file.write_text(td.to_json(), encoding="utf-8")

    priv_key, pub_key = generate_keypair()

    manifest = build_manifest(
        dataset_name="london",
        base_version="1.0.0",
        target_version="1.1.0",
        base_gpkg=base_file,
        target_gpkg=target_file,
        table_deltas={"kerbs": (td, delta_file, "Point")},
        private_key=priv_key,
    )

    manifest_path = delta_dir / "manifest.json"
    save_manifest(manifest, manifest_path)
    reloaded = load_manifest(manifest_path)

    assert reloaded.dataset_name == "london"
    assert reloaded.base_version == "1.0.0"
    assert reloaded.target_version == "1.1.0"
    assert "kerbs" in reloaded.tables
    assert reloaded.tables["kerbs"].insert_count == 1
    assert reloaded.tables["kerbs"].update_count == 1
    assert reloaded.tables["kerbs"].delete_count == 1

    # Validate
    valid, errors = validate_manifest(reloaded, delta_dir, public_key=pub_key)
    assert valid
    assert len(errors) == 0


def test_manifest_validation_detects_tampering(tmp_path: Path):
    delta_dir = tmp_path / "delta"
    delta_dir.mkdir()

    td = TableDelta(table_name="lines")
    delta_file = delta_dir / "lines.delta.json"
    delta_file.write_text(td.to_json(), encoding="utf-8")

    priv_key, pub_key = generate_keypair()
    manifest = build_manifest(
        dataset_name="scotland",
        base_version="1.0",
        target_version="2.0",
        table_deltas={"lines": (td, delta_file, "LineString")},
        private_key=priv_key,
    )

    # Tamper with delta file content after manifest creation
    delta_file.write_text("{\"corrupted\": true}", encoding="utf-8")

    valid, errors = validate_manifest(manifest, delta_dir, public_key=pub_key)
    assert not valid
    assert any("Checksum mismatch" in err for err in errors)
