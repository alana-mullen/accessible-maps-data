from __future__ import annotations

import logging
from pathlib import Path

from .download import download_region
from .gpkg import list_layers

LOGGER = logging.getLogger(__name__)


def prepare_region(
    region_name: str,
    data_dir: Path = Path("data"),
) -> Path:
    """Download, extract and inspect a regional source GeoPackage."""
    gpkg = download_region(region_name, data_dir=data_dir)

    layers = list_layers(gpkg)
    LOGGER.info(
        "Source GeoPackage %s contains %d layers",
        gpkg,
        len(layers),
    )

    for layer in layers:
        LOGGER.info(
            "Layer: %s (%s)",
            layer.name,
            layer.geometry_type or "non-spatial",
        )

    return gpkg
