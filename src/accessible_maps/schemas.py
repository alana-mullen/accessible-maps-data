from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PydanticAssetInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    filename: str
    sha256: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    download_url: str | None = None


class PydanticTableManifestEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    table_name: str
    geometry_type: str | None
    delta_file: str
    delta_sha256: str
    delta_size_bytes: int
    insert_count: int
    update_count: int
    delete_count: int
    target_row_count: int


class PydanticDeltaManifest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    format_version: str = "1.0"
    dataset_name: str
    base_version: str
    target_version: str
    created_at: str
    base_dataset: dict[str, Any] = Field(default_factory=dict)
    target_dataset: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, int] = Field(default_factory=dict)
    tables: dict[str, PydanticTableManifestEntry] = Field(default_factory=dict)
    signing: dict[str, Any] = Field(default_factory=dict)


class PydanticDeltaCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    from_version: str
    to_version: str
    release_tag: str
    updated_at: str
    delta_asset: str
    download_url: str | None = None
    manifest_url: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    manifest_signature: str | None = None
    public_key: str | None = None
    delta_stats: dict[str, int] = Field(default_factory=dict)


class PydanticRegionCatalogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    region_name: str
    latest_version: str
    latest_release_tag: str
    latest_updated_at: str
    full_dataset: dict[str, Any] = Field(default_factory=dict)
    release_html_url: str | None = None
    available_deltas: list[PydanticDeltaCatalogEntry] = Field(default_factory=list)


class PydanticDatasetCatalog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    catalog_version: str = "1.0"
    updated_at: str
    regions: dict[str, PydanticRegionCatalogEntry] = Field(default_factory=dict)


class PydanticReleaseMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    release_tag: str
    dataset_name: str
    version: str
    base_version: str | None = None
    created_at: str
    table_stats: dict[str, int] = Field(default_factory=dict)
    delta_stats: dict[str, int] | None = None
    attribution: str
    license: str
    signing: dict[str, Any] = Field(default_factory=dict)
    assets: list[PydanticAssetInfo] = Field(default_factory=list)


def export_json_schemas(output_dir: Path) -> dict[str, Path]:
    """Export standard JSON Schema definitions for client validation (e.g. Kotlin)."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schemas = {
        "delta_manifest.schema.json": PydanticDeltaManifest.model_json_schema(),
        "dataset_catalog.schema.json": PydanticDatasetCatalog.model_json_schema(),
        "release_metadata.schema.json": PydanticReleaseMetadata.model_json_schema(),
    }

    results: dict[str, Path] = {}
    for filename, schema in schemas.items():
        file_path = output_dir / filename
        file_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        results[filename] = file_path

    return results
