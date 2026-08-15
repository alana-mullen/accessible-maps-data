from accessible_maps.publish.metadata import (
    AssetInfo,
    DatasetCatalog,
    ReleaseMetadata,
)


def test_asset_info_roundtrip():
    asset = AssetInfo(
        filename="north-west.gpkg.zip",
        sha256="abc123sha",
        size_bytes=1024,
        content_type="application/zip",
        download_url="https://example.com/north-west.gpkg.zip",
    )
    d = asset.to_dict()
    reloaded = AssetInfo.from_dict(d)
    assert reloaded.filename == asset.filename
    assert reloaded.sha256 == asset.sha256
    assert reloaded.size_bytes == asset.size_bytes
    assert reloaded.download_url == asset.download_url


def test_release_metadata_json_and_notes():
    metadata = ReleaseMetadata(
        release_tag="v2026.08.1-north-west",
        dataset_name="north-west",
        version="2026.08.1",
        base_version="2026.07.1",
        table_stats={"kerbs": 5000, "footways": 12000},
        delta_stats={"inserts": 100, "updates": 50, "deletes": 10},
        assets=[
            AssetInfo(filename="north-west.gpkg.zip", sha256="111", size_bytes=2048),
            AssetInfo(filename="delta.zip", sha256="222", size_bytes=512),
        ],
        manifest_signature="sig-base64",
        public_key="pub-base64",
    )

    json_str = metadata.to_json()
    reloaded = ReleaseMetadata.from_json(json_str)

    assert reloaded.release_tag == metadata.release_tag
    assert reloaded.dataset_name == "north-west"
    assert reloaded.table_stats["kerbs"] == 5000
    assert reloaded.delta_stats["inserts"] == 100
    assert len(reloaded.assets) == 2

    # Verify release notes contain essential sections
    notes = metadata.generate_release_notes()
    assert "# Accessible Maps Dataset Release: `north-west`" in notes
    assert "| `kerbs` | 5,000 |" in notes
    assert "New Features (Inserts):** 100" in notes
    assert "public_key" in notes or "pub-base64" in notes


def test_dataset_catalog_add_release_and_urls():
    catalog = DatasetCatalog()

    meta1 = ReleaseMetadata(
        release_tag="v1.0-london",
        dataset_name="london",
        version="1.0",
        created_at="2026-08-01T12:00:00+00:00",
        assets=[AssetInfo(filename="london.gpkg.zip", sha256="aaa", size_bytes=1000)],
        table_stats={"kerbs": 1000},
    )

    catalog.add_release(
        meta1,
        release_html_url="https://github.com/alana-mullen/accessible-maps-data/releases/tag/v1.0-london",
        repo="alana-mullen/accessible-maps-data",
    )
    assert "london" in catalog.regions
    london_entry = catalog.regions["london"]
    assert london_entry.latest_version == "1.0"
    assert london_entry.latest_updated_at == "2026-08-01T12:00:00+00:00"
    assert london_entry.full_dataset_sha256 == "aaa"
    assert (
        london_entry.full_dataset_download_url
        == "https://github.com/alana-mullen/accessible-maps-data/releases/download/v1.0-london/london.gpkg.zip"
    )

    # Add delta release
    meta2 = ReleaseMetadata(
        release_tag="v1.1-london",
        dataset_name="london",
        version="1.1",
        base_version="1.0",
        created_at="2026-08-15T12:00:00+00:00",
        assets=[
            AssetInfo(filename="london.gpkg.zip", sha256="bbb", size_bytes=1100),
            AssetInfo(filename="london-delta-1.0-to-1.1.zip", sha256="ccc", size_bytes=150),
            AssetInfo(filename="manifest.json", sha256="ddd", size_bytes=50),
        ],
        table_stats={"kerbs": 1100},
        delta_stats={"inserts": 100, "updates": 10, "deletes": 0},
    )

    catalog.add_release(
        meta2,
        release_html_url="https://github.com/alana-mullen/accessible-maps-data/releases/tag/v1.1-london",
        repo="alana-mullen/accessible-maps-data",
    )
    assert london_entry.latest_version == "1.1"
    assert london_entry.latest_updated_at == "2026-08-15T12:00:00+00:00"
    assert london_entry.full_dataset_sha256 == "bbb"
    assert len(london_entry.available_deltas) == 1

    delta = london_entry.available_deltas[0]
    assert delta.from_version == "1.0"
    assert delta.to_version == "1.1"
    assert delta.updated_at == "2026-08-15T12:00:00+00:00"
    assert (
        delta.download_url
        == "https://github.com/alana-mullen/accessible-maps-data/releases/download/v1.1-london/london-delta-1.0-to-1.1.zip"
    )
    assert (
        delta.manifest_url
        == "https://github.com/alana-mullen/accessible-maps-data/releases/download/v1.1-london/manifest.json"
    )

    # Test catalog json roundtrip
    cat_json = catalog.to_json()
    cat_reloaded = DatasetCatalog.from_json(cat_json)
    assert "london" in cat_reloaded.regions
    assert cat_reloaded.regions["london"].latest_version == "1.1"
    assert (
        cat_reloaded.regions["london"].available_deltas[0].updated_at == "2026-08-15T12:00:00+00:00"
    )
