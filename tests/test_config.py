from accessible_maps.config import REGIONS, get_region


def test_regions_are_unique():
    names = [region.name for region in REGIONS]
    assert len(names) == len(set(names))
    assert len(REGIONS) == 14


def test_north_west_url():
    region = get_region("north-west")
    assert region.source_url.endswith("/england/north-west-latest-free.gpkg.zip")


def test_crown_dependencies():
    iom = get_region("isle-of-man")
    assert iom.source_url == "https://download.geofabrik.de/europe/isle-of-man-latest-free.gpkg.zip"

    ci = get_region("guernsey-jersey")
    assert (
        ci.source_url == "https://download.geofabrik.de/europe/guernsey-jersey-latest-free.gpkg.zip"
    )


def test_all_regions_are_https():
    assert all(region.source_url.startswith("https://") for region in REGIONS)
