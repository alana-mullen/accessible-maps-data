from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..gpkg import list_layers
from .comparator import compare_gpkg_table
from .manifest import build_manifest, load_manifest, save_manifest, validate_manifest
from .models import DeltaManifest, TableDelta

LOGGER = logging.getLogger(__name__)


def create_delta_package(
    target_gpkg: Path,
    output_dir: Path,
    base_gpkg: Path | None = None,
    dataset_name: str = "accessible-maps",
    base_version: str = "v1",
    target_version: str = "v2",
    private_key: str | Path | None = None,
    primary_key: str = "fid",
) -> DeltaManifest:
    """Generate per-table deltas, checksums, manifest, and optional cryptographic signature."""
    target_gpkg = Path(target_gpkg)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if base_gpkg is not None:
        base_gpkg = Path(base_gpkg)

    target_layers = {layer.name: layer.geometry_type for layer in list_layers(target_gpkg)}
    base_layers = (
        {layer.name: layer.geometry_type for layer in list_layers(base_gpkg)}
        if base_gpkg and base_gpkg.is_file()
        else {}
    )

    all_table_names = sorted(set(target_layers.keys()) | set(base_layers.keys()))
    LOGGER.info("Computing deltas for %d tables...", len(all_table_names))

    table_deltas: dict[str, tuple[TableDelta, Path, str | None]] = {}

    for table_name in all_table_names:
        geom_type = target_layers.get(table_name) or base_layers.get(table_name)
        td = compare_gpkg_table(
            table_name=table_name,
            base_gpkg=base_gpkg,
            target_gpkg=target_gpkg,
            primary_key=primary_key,
        )

        delta_file = output_dir / f"{table_name}.delta.json"
        delta_file.write_text(td.to_json(indent=2), encoding="utf-8")
        table_deltas[table_name] = (td, delta_file, geom_type)

        LOGGER.info(
            "Table '%s': +%d, ~%d, -%d (target total: %d)",
            table_name,
            td.insert_count,
            td.update_count,
            td.delete_count,
            td.total_target_rows,
        )

    manifest = build_manifest(
        dataset_name=dataset_name,
        base_version=base_version,
        target_version=target_version,
        base_gpkg=base_gpkg,
        target_gpkg=target_gpkg,
        table_deltas=table_deltas,
        private_key=private_key,
    )

    manifest_path = output_dir / "manifest.json"
    save_manifest(manifest, manifest_path)
    LOGGER.info("Generated delta package in %s (manifest: %s)", output_dir, manifest_path)

    return manifest


def apply_table_delta(
    base_records: list[dict[str, Any]],
    table_delta: TableDelta,
) -> list[dict[str, Any]]:
    """Apply insertions, updates, and deletions from TableDelta to base records."""
    pk = table_delta.primary_key
    record_map: dict[Any, dict[str, Any]] = {
        row[pk]: dict(row) for row in base_records if pk in row
    }

    # 1. Apply deletes
    for del_id in table_delta.deletes:
        record_map.pop(del_id, None)

    # 2. Apply updates
    for update_row in table_delta.updates:
        row_id = update_row.get(pk)
        if row_id is not None:
            record_map[row_id] = dict(update_row)

    # 3. Apply inserts
    for insert_row in table_delta.inserts:
        row_id = insert_row.get(pk)
        if row_id is not None:
            record_map[row_id] = dict(insert_row)

    return list(record_map.values())


def apply_delta_package(
    delta_dir: Path,
    output_gpkg: Path,
    base_gpkg: Path | None = None,
    public_key: str | Path | None = None,
) -> Path:
    """Validate delta package and apply table deltas to construct the target GeoPackage."""
    import geopandas as gpd
    import pandas as pd
    import pyogrio
    from shapely import from_wkt

    delta_dir = Path(delta_dir)
    output_gpkg = Path(output_gpkg)
    output_gpkg.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = delta_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found in {delta_dir}")

    manifest = load_manifest(manifest_path)
    valid, errors = validate_manifest(manifest, delta_dir, public_key=public_key)
    if not valid:
        raise ValueError(f"Delta package validation failed: {'; '.join(errors)}")

    if output_gpkg.exists():
        output_gpkg.unlink()

    for table_name, entry in manifest.tables.items():
        delta_file = delta_dir / entry.delta_file
        td = TableDelta.from_json(delta_file.read_text(encoding="utf-8"))

        base_records: list[dict[str, Any]] = []
        if base_gpkg and base_gpkg.is_file():
            try:
                base_df = pyogrio.read_dataframe(base_gpkg, layer=table_name)
                if hasattr(base_df, "geometry") and base_df.geometry is not None:
                    base_df_copy = base_df.copy()
                    base_df_copy[base_df.geometry.name] = base_df_copy[base_df.geometry.name].apply(
                        lambda g: g.wkt if g is not None else None
                    )
                    base_records = base_df_copy.reset_index(
                        names=[td.primary_key] if td.primary_key not in base_df_copy.columns else []
                    ).to_dict(orient="records")
                else:
                    base_records = base_df.reset_index(
                        names=[td.primary_key] if td.primary_key not in base_df.columns else []
                    ).to_dict(orient="records")
            except (KeyError, ValueError, OSError, AttributeError):
                base_records = []

        result_records = apply_table_delta(base_records, td)

        if not result_records:
            continue

        df = pd.DataFrame(result_records)
        geom_col = td.geometry_column or "geometry"

        if geom_col in df.columns and any(df[geom_col].notna()):
            df[geom_col] = df[geom_col].apply(
                lambda x: from_wkt(x) if isinstance(x, str) and x else None
            )
            gdf = gpd.GeoDataFrame(df, geometry=geom_col, crs=td.crs or "EPSG:4326")
            pyogrio.write_dataframe(gdf, output_gpkg, layer=table_name, driver="GPKG")
        else:
            pyogrio.write_dataframe(df, output_gpkg, layer=table_name, driver="GPKG")

    LOGGER.info("Successfully reconstructed dataset at %s", output_gpkg)
    return output_gpkg
