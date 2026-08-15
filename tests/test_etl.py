from pathlib import Path

from accessible_maps.etl import prepare_region


def test_prepare_region_delegates(monkeypatch, tmp_path: Path):
    source = tmp_path / "source.gpkg"

    monkeypatch.setattr(
        "accessible_maps.etl.download_region",
        lambda region_name, data_dir: source,
    )
    monkeypatch.setattr(
        "accessible_maps.etl.list_layers",
        lambda _: (),
    )

    assert prepare_region("north-west", tmp_path) == source
