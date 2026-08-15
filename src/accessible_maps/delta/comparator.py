from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .models import TableDelta


def _normalize_value(val: Any) -> Any:
    """Normalize values for robust equality checking (handles NaN, floats, None)."""
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, (bytes, bytearray)):
        return val.hex()
    return val


def _records_differ(
    base_row: dict[str, Any],
    target_row: dict[str, Any],
    geometry_col: str | None = "geometry",
) -> bool:
    """Check if two row records differ in non-geometry attributes or geometry."""
    all_keys = set(base_row.keys()) | set(target_row.keys())

    for key in all_keys:
        val_base = _normalize_value(base_row.get(key))
        val_target = _normalize_value(target_row.get(key))

        if key == geometry_col:
            # If geometries are WKT strings, hex WKB, or dict/geojson
            if val_base != val_target:
                return True
        else:
            if val_base != val_target:
                return True

    return False


def compare_records(
    table_name: str,
    base_records: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
    primary_key: str = "fid",
    geometry_column: str | None = "geometry",
    crs: str | None = "EPSG:4326",
) -> TableDelta:
    """Compare in-memory base and target record collections to produce a TableDelta."""
    base_map = {row[primary_key]: row for row in base_records if primary_key in row}
    target_map = {row[primary_key]: row for row in target_records if primary_key in row}

    base_ids = set(base_map.keys())
    target_ids = set(target_map.keys())

    inserted_ids = sorted(target_ids - base_ids, key=str)
    deleted_ids = sorted(base_ids - target_ids, key=str)
    common_ids = sorted(base_ids & target_ids, key=str)

    inserts: list[dict[str, Any]] = [target_map[i] for i in inserted_ids]
    updates: list[dict[str, Any]] = []

    for item_id in common_ids:
        base_row = base_map[item_id]
        target_row = target_map[item_id]
        if _records_differ(base_row, target_row, geometry_col=geometry_column):
            updates.append(target_row)

    return TableDelta(
        table_name=table_name,
        primary_key=primary_key,
        geometry_column=geometry_column,
        crs=crs,
        inserts=inserts,
        updates=updates,
        deletes=deleted_ids,
        total_target_rows=len(target_records),
    )


def compare_gpkg_table(
    table_name: str,
    base_gpkg: Path | None,
    target_gpkg: Path | None,
    primary_key: str = "fid",
) -> TableDelta:
    """Compare a table across two GeoPackage files using pyogrio / geopandas."""
    import pyogrio

    base_records: list[dict[str, Any]] = []
    target_records: list[dict[str, Any]] = []
    crs: str | None = "EPSG:4326"
    geometry_column: str | None = "geometry"

    if base_gpkg is not None and base_gpkg.is_file():
        try:
            base_df = pyogrio.read_dataframe(base_gpkg, layer=table_name)
            if hasattr(base_df, "geometry") and base_df.geometry is not None:
                geometry_column = base_df.geometry.name
                crs = str(base_df.crs) if base_df.crs else None
                # Convert geometry to WKT for deterministic comparison
                base_df_copy = base_df.copy()
                base_df_copy[geometry_column] = base_df_copy[geometry_column].apply(
                    lambda g: g.wkt if g is not None else None
                )
                base_records = base_df_copy.reset_index(names=[primary_key] if primary_key not in base_df_copy.columns else []).to_dict(orient="records")
            else:
                base_records = base_df.reset_index(names=[primary_key] if primary_key not in base_df.columns else []).to_dict(orient="records")
        except (KeyError, ValueError, OSError, AttributeError):
            base_records = []

    if target_gpkg is not None and target_gpkg.is_file():
        target_df = pyogrio.read_dataframe(target_gpkg, layer=table_name)
        if hasattr(target_df, "geometry") and target_df.geometry is not None:
            geometry_column = target_df.geometry.name
            crs = str(target_df.crs) if target_df.crs else None
            target_df_copy = target_df.copy()
            target_df_copy[geometry_column] = target_df_copy[geometry_column].apply(
                lambda g: g.wkt if g is not None else None
            )
            target_records = target_df_copy.reset_index(names=[primary_key] if primary_key not in target_df_copy.columns else []).to_dict(orient="records")
        else:
            target_records = target_df.reset_index(names=[primary_key] if primary_key not in target_df.columns else []).to_dict(orient="records")

    return compare_records(
        table_name=table_name,
        base_records=base_records,
        target_records=target_records,
        primary_key=primary_key,
        geometry_column=geometry_column,
        crs=crs,
    )
