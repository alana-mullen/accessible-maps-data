import sqlite3
from pathlib import Path

import pytest

from accessible_maps.gpkg import has_layer, list_layers, optimize_geopackage


def test_list_layers_requires_existing_file(tmp_path: Path):
    with pytest.raises(Exception):
        list_layers(tmp_path / "missing.gpkg")


def test_has_layer_uses_layer_names(monkeypatch, tmp_path: Path):
    class FakePath:
        pass

    monkeypatch.setattr(
        "accessible_maps.gpkg.list_layers",
        lambda _: (
            type("Layer", (), {"name": "points"})(),
            type("Layer", (), {"name": "lines"})(),
        ),
    )

    assert has_layer(FakePath(), "points")
    assert not has_layer(FakePath(), "polygons")


def test_optimize_geopackage(tmp_path: Path):
    db_path = tmp_path / "test.gpkg"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_layer (fid INTEGER PRIMARY KEY, name TEXT);")
    for i in range(1000):
        cur.execute("INSERT INTO test_layer (name) VALUES (?);", (f"feature_{i}",))
    conn.commit()
    conn.close()

    result = optimize_geopackage(db_path)
    assert result["size_before"] > 0
    assert result["size_after"] > 0
    assert "reduction_pct" in result


def test_optimize_geopackage_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        optimize_geopackage(tmp_path / "nonexistent.gpkg")
