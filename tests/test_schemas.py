import json
from pathlib import Path

from accessible_maps.schemas import export_json_schemas


def test_export_json_schemas(tmp_path: Path):
    schemas_dir = tmp_path / "schemas"
    exported = export_json_schemas(schemas_dir)

    assert "delta_manifest.schema.json" in exported
    assert "dataset_catalog.schema.json" in exported
    assert "release_metadata.schema.json" in exported

    for name, path in exported.items():
        assert path.is_file()
        content = json.loads(path.read_text(encoding="utf-8"))
        assert "$defs" in content or "properties" in content or "title" in content
