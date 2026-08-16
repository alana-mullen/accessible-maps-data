from accessible_maps.config import REGIONS, get_region


def test_regions_are_unique():
    names = [region.name for region in REGIONS]
    assert len(names) == len(set(names))
    assert len(REGIONS) == 52
    assert "england" not in names


def test_uk_nations_urls():
    scotland = get_region("scotland")
    assert (
        scotland.source_url
        == "https://download.geofabrik.de/europe/united-kingdom/scotland-latest-free.gpkg.zip"
    )

    wales = get_region("wales")
    assert (
        wales.source_url
        == "https://download.geofabrik.de/europe/united-kingdom/wales-latest-free.gpkg.zip"
    )

    london = get_region("greater-london")
    assert (
        london.source_url
        == "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest-free.gpkg.zip"
    )


def test_crown_dependencies():
    iom = get_region("isle-of-man")
    assert iom.source_url == "https://download.geofabrik.de/europe/isle-of-man-latest-free.gpkg.zip"

    ci = get_region("guernsey-jersey")
    assert (
        ci.source_url == "https://download.geofabrik.de/europe/guernsey-jersey-latest-free.gpkg.zip"
    )


def test_all_regions_are_https():
    assert all(region.source_url.startswith("https://") for region in REGIONS)
