from __future__ import annotations

import logging
from pathlib import Path

from ..delta.checksums import sha256_file
from ..delta.manifest import load_manifest, validate_manifest
from ..gpkg import list_layers
from .metadata import ReleaseMetadata

LOGGER = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Raised when release validation fails."""


def validate_geopackage(path: Path) -> tuple[bool, list[str]]:
    """Validate that a file is a valid, readable GeoPackage with layers."""
    errors: list[str] = []
    path = Path(path)

    if not path.is_file():
        return False, [f"GeoPackage file does not exist: {path}"]

    if path.stat().st_size == 0:
        return False, [f"GeoPackage file is empty: {path}"]

    try:
        layers = list_layers(path)
        if not layers:
            errors.append(f"GeoPackage has no layers: {path}")
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        errors.append(f"Failed to read GeoPackage layers from {path}: {exc}")

    return len(errors) == 0, errors


def parse_checksums_file(path: Path) -> dict[str, str]:
    """Parse standard sha256sum formatted file into filename -> hash mapping."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Checksums file not found: {path}")

    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            checksum = parts[0].strip()
            # Handle binary mode marker '*' if present
            filename = parts[1].lstrip("*").strip()
            mapping[filename] = checksum

    return mapping


def validate_checksums_file(directory: Path, checksums_path: Path | None = None) -> tuple[bool, list[str]]:
    """Verify all files listed in checksums.txt match their hashes in directory."""
    errors: list[str] = []
    directory = Path(directory)
    checksums_path = checksums_path or (directory / "checksums.txt")

    if not checksums_path.is_file():
        return False, [f"Checksums file missing: {checksums_path}"]

    try:
        expected_hashes = parse_checksums_file(checksums_path)
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        return False, [f"Failed to parse checksums file: {exc}"]

    for filename, expected_hash in expected_hashes.items():
        file_path = directory / filename
        if not file_path.is_file():
            errors.append(f"Referenced file missing: {filename}")
            continue

        actual_hash = sha256_file(file_path)
        if actual_hash.lower() != expected_hash.lower():
            errors.append(
                f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
            )

    return len(errors) == 0, errors


def validate_release_package(
    release_dir: Path,
    public_key: str | Path | None = None,
) -> tuple[bool, list[str]]:
    """Comprehensive validation of a packaged release directory."""
    errors: list[str] = []
    release_dir = Path(release_dir)

    if not release_dir.is_dir():
        return False, [f"Release directory does not exist: {release_dir}"]

    # 1. Metadata check
    metadata_path = release_dir / "metadata.json"
    if not metadata_path.is_file():
        errors.append("Missing metadata.json in release directory")
    else:
        try:
            metadata = ReleaseMetadata.from_json(metadata_path.read_text(encoding="utf-8"))
            if not metadata.dataset_name or not metadata.version or not metadata.release_tag:
                errors.append("metadata.json missing required identifiers")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(f"Invalid metadata.json format: {exc}")

    # 2. Checksums.txt check
    checksums_path = release_dir / "checksums.txt"
    valid_sums, sum_errors = validate_checksums_file(release_dir, checksums_path)
    if not valid_sums:
        errors.extend(sum_errors)

    # 3. Manifest and delta check (if manifest exists)
    manifest_path = release_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = load_manifest(manifest_path)
            valid_man, man_errors = validate_manifest(
                manifest=manifest,
                delta_dir=release_dir,
                public_key=public_key,
            )
            if not valid_man:
                errors.extend(man_errors)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(f"Invalid manifest.json: {exc}")

    return len(errors) == 0, errors
