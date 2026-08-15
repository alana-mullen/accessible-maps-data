from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Region:
    name: str
    source_url: str


REGIONS: tuple[Region, ...] = (
    Region(
        "north-west",
        "https://download.geofabrik.de/europe/united-kingdom/england/north-west-latest-free.gpkg.zip",
    ),
    Region(
        "north-east",
        "https://download.geofabrik.de/europe/united-kingdom/england/north-east-latest-free.gpkg.zip",
    ),
    Region(
        "yorkshire-and-the-humber",
        "https://download.geofabrik.de/europe/united-kingdom/england/yorkshire-and-the-humber-latest-free.gpkg.zip",
    ),
    Region(
        "east-midlands",
        "https://download.geofabrik.de/europe/united-kingdom/england/east-midlands-latest-free.gpkg.zip",
    ),
    Region(
        "west-midlands",
        "https://download.geofabrik.de/europe/united-kingdom/england/west-midlands-latest-free.gpkg.zip",
    ),
    Region(
        "east-of-england",
        "https://download.geofabrik.de/europe/united-kingdom/england/east-of-england-latest-free.gpkg.zip",
    ),
    Region(
        "south-east",
        "https://download.geofabrik.de/europe/united-kingdom/england/south-east-latest-free.gpkg.zip",
    ),
    Region(
        "south-west",
        "https://download.geofabrik.de/europe/united-kingdom/england/south-west-latest-free.gpkg.zip",
    ),
    Region(
        "greater-london",
        "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest-free.gpkg.zip",
    ),
    Region(
        "scotland",
        "https://download.geofabrik.de/europe/united-kingdom/scotland-latest-free.gpkg.zip",
    ),
    Region(
        "wales",
        "https://download.geofabrik.de/europe/united-kingdom/wales-latest-free.gpkg.zip",
    ),
    Region(
        "northern-ireland",
        "https://download.geofabrik.de/europe/united-kingdom/northern-ireland-latest-free.gpkg.zip",
    ),
    Region(
        "isle-of-man",
        "https://download.geofabrik.de/europe/isle-of-man-latest-free.gpkg.zip",
    ),
    Region(
        "guernsey-jersey",
        "https://download.geofabrik.de/europe/guernsey-jersey-latest-free.gpkg.zip",
    ),
)


def get_region(name: str) -> Region:
    for region in REGIONS:
        if region.name == name:
            return region
    raise ValueError(f"Unknown region: {name}")
