from __future__ import annotations

from pathlib import Path

from .checksums import sha256_file, verify_file_checksum
from .models import DeltaManifest, TableDelta, TableManifestEntry
from .signing import sign_manifest, verify_manifest


def build_manifest(
    dataset_name: str,
    base_version: str,
    target_version: str,
    base_gpkg: Path | None = None,
    target_gpkg: Path | None = None,
    table_deltas: dict[str, tuple[TableDelta, Path, str | None]] | None = None,
    private_key: str | Path | None = None,
) -> DeltaManifest:
    """Build a complete DeltaManifest with checksums and optional signature.

    table_deltas mapping: table_name -> (TableDelta, delta_file_path, geometry_type)
    """
    base_sha256 = sha256_file(base_gpkg) if base_gpkg and base_gpkg.is_file() else None
    base_size = base_gpkg.stat().st_size if base_gpkg and base_gpkg.is_file() else None

    target_sha256 = sha256_file(target_gpkg) if target_gpkg and target_gpkg.is_file() else None
    target_size = target_gpkg.stat().st_size if target_gpkg and target_gpkg.is_file() else None

    entries: dict[str, TableManifestEntry] = {}

    if table_deltas:
        for name, (td, delta_path, geom_type) in table_deltas.items():
            delta_sha = sha256_file(delta_path) if delta_path.is_file() else ""
            delta_size = delta_path.stat().st_size if delta_path.is_file() else 0

            entries[name] = TableManifestEntry(
                table_name=name,
                geometry_type=geom_type,
                delta_file=delta_path.name,
                delta_sha256=delta_sha,
                delta_size_bytes=delta_size,
                insert_count=td.insert_count,
                update_count=td.update_count,
                delete_count=td.delete_count,
                target_row_count=td.total_target_rows,
            )

    manifest = DeltaManifest(
        dataset_name=dataset_name,
        base_version=base_version,
        target_version=target_version,
        base_sha256=base_sha256,
        base_size_bytes=base_size,
        target_sha256=target_sha256,
        target_size_bytes=target_size,
        tables=entries,
    )

    if private_key is not None:
        sign_manifest(manifest, private_key)

    return manifest


def save_manifest(manifest: DeltaManifest, output_path: Path) -> Path:
    """Save DeltaManifest to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manifest.to_json(indent=2), encoding="utf-8")
    return output_path


def load_manifest(path: Path) -> DeltaManifest:
    """Load DeltaManifest from a JSON file."""
    path = Path(path)
    return DeltaManifest.from_json(path.read_text(encoding="utf-8"))


def validate_manifest(
    manifest: DeltaManifest,
    delta_dir: Path,
    public_key: str | Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate manifest integrity, signature, and referenced delta file checksums."""
    errors: list[str] = []
    delta_dir = Path(delta_dir)

    # 1. Signature check if signature exists or public_key is provided
    if (manifest.signature or public_key) and not verify_manifest(manifest, public_key):
        errors.append("Manifest cryptographic signature verification failed")

    # 2. Check each table delta file
    for table_name, entry in manifest.tables.items():
        file_path = delta_dir / entry.delta_file
        if not file_path.is_file():
            errors.append(f"Missing delta file for table '{table_name}': {entry.delta_file}")
            continue

        if not verify_file_checksum(file_path, entry.delta_sha256):
            errors.append(f"Checksum mismatch for table '{table_name}' file '{entry.delta_file}'")

        if file_path.stat().st_size != entry.delta_size_bytes:
            errors.append(f"Size mismatch for table '{table_name}' file '{entry.delta_file}'")

    return len(errors) == 0, errors
