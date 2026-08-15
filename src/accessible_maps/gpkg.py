from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pyogrio

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LayerInfo:
    name: str
    geometry_type: str | None


def list_layers(path: Path) -> tuple[LayerInfo, ...]:
    """Return the layers available in a GeoPackage."""
    rows = pyogrio.list_layers(path)

    return tuple(
        LayerInfo(
            name=str(row[0]),
            geometry_type=None if row[1] is None else str(row[1]),
        )
        for row in rows
    )


def layer_names(path: Path) -> tuple[str, ...]:
    return tuple(layer.name for layer in list_layers(path))


def has_layer(path: Path, name: str) -> bool:
    return name in layer_names(path)


def optimize_geopackage(path: Path) -> dict[str, int | float]:
    """Optimize GeoPackage SQLite database layout for mobile distribution.

    Sets page size to 4096 bytes (ideal for mobile flash blocks), cleans journal,
    runs VACUUM and ANALYZE to optimize internal B-trees.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"GeoPackage not found: {path}")

    size_before = path.stat().st_size

    conn = sqlite3.connect(str(path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA page_size = 4096;")
        cur.execute("PRAGMA journal_mode = DELETE;")
        cur.execute("PRAGMA synchronous = NORMAL;")
        cur.execute("VACUUM;")
        cur.execute("ANALYZE;")
        conn.commit()
    finally:
        conn.close()

    size_after = path.stat().st_size
    saved_bytes = max(0, size_before - size_after)
    reduction_pct = (saved_bytes / size_before * 100) if size_before > 0 else 0.0

    LOGGER.info(
        "Optimized GeoPackage %s: %d -> %d bytes (saved %.1f%%)",
        path.name,
        size_before,
        size_after,
        reduction_pct,
    )

    return {
        "size_before": size_before,
        "size_after": size_after,
        "saved_bytes": saved_bytes,
        "reduction_pct": round(reduction_pct, 2),
    }
