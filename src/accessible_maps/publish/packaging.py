from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path

from ..compress import compress_dir_tar_zstd, compress_file_zstd
from ..delta.checksums import sha256_file
from ..delta.engine import create_delta_package
from ..gpkg import list_layers, optimize_geopackage
from .metadata import AssetInfo, ReleaseMetadata
from .validator import validate_geopackage

LOGGER = logging.getLogger(__name__)


def compress_file_to_zip(source_file: Path, zip_path: Path) -> Path:
    """Compress a single file into a ZIP archive with maximum compression."""
    source_file = Path(source_file)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(source_file, arcname=source_file.name)

    return zip_path


def compress_dir_to_zip(source_dir: Path, zip_path: Path) -> Path:
    """Compress a directory into a ZIP archive."""
    source_dir = Path(source_dir)
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for file in sorted(source_dir.rglob("*")):
            if file.is_file() and not file.name.startswith("."):
                rel_path = file.relative_to(source_dir)
                zf.write(file, arcname=str(rel_path))

    return zip_path


def generate_checksums_file(files: list[Path], output_path: Path) -> Path:
    """Generate GNU sha256sum compatible checksums.txt file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for file in sorted(files, key=lambda p: p.name):
        if file.is_file():
            file_hash = sha256_file(file)
            lines.append(f"{file_hash}  {file.name}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def count_layer_rows(gpkg_path: Path) -> dict[str, int]:
    """Count rows per layer in GeoPackage."""
    import pyogrio

    counts: dict[str, int] = {}
    try:
        layers = list_layers(gpkg_path)
        for layer in layers:
            df = pyogrio.read_dataframe(gpkg_path, layer=layer.name)
            counts[layer.name] = len(df)
    except (OSError, ValueError, KeyError, AttributeError) as exc:
        LOGGER.warning("Could not count layer rows: %s", exc)

    return counts


def package_release(
    target_gpkg: Path,
    output_dir: Path,
    dataset_name: str,
    version: str,
    base_gpkg: Path | None = None,
    base_version: str | None = None,
    signing_key: str | Path | None = None,
    release_tag_prefix: str = "v",
    optimize_db: bool = True,
) -> tuple[ReleaseMetadata, Path]:
    """Package dataset GeoPackage, delta updates, checksums, and metadata into release bundle."""
    target_gpkg = Path(target_gpkg)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    valid, errors = validate_geopackage(target_gpkg)
    if not valid:
        raise ValueError(f"Target GeoPackage validation failed: {'; '.join(errors)}")

    if optimize_db:
        LOGGER.info("Optimizing SQLite database layout for %s...", target_gpkg.name)
        optimize_geopackage(target_gpkg)

    release_tag = f"{release_tag_prefix}{version}-{dataset_name}"
    LOGGER.info("Packaging release %s into %s", release_tag, output_dir)

    # 1. Compress target GeoPackage (ZIP and Zstandard formats)
    full_zip_name = f"{dataset_name}-{version}.gpkg.zip"
    full_zip_path = output_dir / full_zip_name
    compress_file_to_zip(target_gpkg, full_zip_path)

    full_zst_name = f"{dataset_name}-{version}.gpkg.zst"
    full_zst_path = output_dir / full_zst_name
    compress_file_zstd(target_gpkg, full_zst_path)

    # 2. Count table rows
    table_stats = count_layer_rows(target_gpkg)

    # 3. Create delta if base_gpkg provided
    delta_stats: dict[str, int] | None = None
    manifest_signature: str | None = None
    public_key: str | None = None
    delta_zip_path: Path | None = None
    delta_zst_path: Path | None = None

    if base_gpkg and base_gpkg.is_file():
        delta_staging = output_dir / ".delta_staging"
        delta_staging.mkdir(parents=True, exist_ok=True)

        manifest = create_delta_package(
            target_gpkg=target_gpkg,
            output_dir=delta_staging,
            base_gpkg=base_gpkg,
            dataset_name=dataset_name,
            base_version=base_version or "base",
            target_version=version,
            private_key=signing_key,
        )

        manifest_signature = manifest.signature
        public_key = manifest.public_key
        delta_stats = {
            "inserts": manifest.total_inserts,
            "updates": manifest.total_updates,
            "deletes": manifest.total_deletes,
        }

        # ZIP archive
        delta_zip_name = f"{dataset_name}-delta-{base_version or 'base'}-to-{version}.zip"
        delta_zip_path = output_dir / delta_zip_name
        compress_dir_to_zip(delta_staging, delta_zip_path)

        # Zstandard tar archive
        delta_zst_name = f"{dataset_name}-delta-{base_version or 'base'}-to-{version}.tar.zst"
        delta_zst_path = output_dir / delta_zst_name
        compress_dir_tar_zstd(delta_staging, delta_zst_path)

        # Copy manifest into release root for direct inspection
        shutil.copy2(delta_staging / "manifest.json", output_dir / "manifest.json")
        shutil.rmtree(delta_staging, ignore_errors=True)

    # 4. Gather release assets
    asset_files: list[Path] = [full_zip_path, full_zst_path]
    if delta_zip_path and delta_zip_path.is_file():
        asset_files.append(delta_zip_path)
    if delta_zst_path and delta_zst_path.is_file():
        asset_files.append(delta_zst_path)
    if (output_dir / "manifest.json").is_file():
        asset_files.append(output_dir / "manifest.json")

    # 5. Generate checksums.txt
    checksums_path = output_dir / "checksums.txt"
    generate_checksums_file(asset_files, checksums_path)
    asset_files.append(checksums_path)

    # 6. Build AssetInfo list
    assets: list[AssetInfo] = []
    for f in asset_files:
        content_type = "application/octet-stream"
        if f.name.endswith(".zip"):
            content_type = "application/zip"
        elif f.name.endswith(".zst"):
            content_type = "application/zstd"
        elif f.name.endswith(".json"):
            content_type = "application/json"
        elif f.name.endswith(".txt"):
            content_type = "text/plain"

        assets.append(
            AssetInfo(
                filename=f.name,
                sha256=sha256_file(f),
                size_bytes=f.stat().st_size,
                content_type=content_type,
            )
        )

    # 7. Write metadata.json
    metadata = ReleaseMetadata(
        release_tag=release_tag,
        dataset_name=dataset_name,
        version=version,
        base_version=base_version,
        assets=assets,
        table_stats=table_stats,
        delta_stats=delta_stats,
        manifest_signature=manifest_signature,
        public_key=public_key,
    )

    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(metadata.to_json(indent=2), encoding="utf-8")

    # 8. Write release_notes.md
    notes_path = output_dir / "release_notes.md"
    notes_path.write_text(metadata.generate_release_notes(), encoding="utf-8")

    LOGGER.info("Release bundle packaged successfully with %d assets", len(assets))
    return metadata, output_dir
