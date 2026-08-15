from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class TableDelta:
    """Represents changes to a single dataset table/layer."""

    table_name: str
    primary_key: str = "fid"
    geometry_column: str | None = "geometry"
    crs: str | None = "EPSG:4326"
    inserts: list[dict[str, Any]] = field(default_factory=list)
    updates: list[dict[str, Any]] = field(default_factory=list)
    deletes: list[Any] = field(default_factory=list)
    total_target_rows: int = 0

    @property
    def insert_count(self) -> int:
        return len(self.inserts)

    @property
    def update_count(self) -> int:
        return len(self.updates)

    @property
    def delete_count(self) -> int:
        return len(self.deletes)

    @property
    def has_changes(self) -> bool:
        return bool(self.inserts or self.updates or self.deletes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_name": self.table_name,
            "primary_key": self.primary_key,
            "geometry_column": self.geometry_column,
            "crs": self.crs,
            "counts": {
                "inserts": self.insert_count,
                "updates": self.update_count,
                "deletes": self.delete_count,
                "total_target_rows": self.total_target_rows,
            },
            "inserts": self.inserts,
            "updates": self.updates,
            "deletes": self.deletes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableDelta:
        counts = data.get("counts", {})
        return cls(
            table_name=data["table_name"],
            primary_key=data.get("primary_key", "fid"),
            geometry_column=data.get("geometry_column", "geometry"),
            crs=data.get("crs", "EPSG:4326"),
            inserts=list(data.get("inserts", [])),
            updates=list(data.get("updates", [])),
            deletes=list(data.get("deletes", [])),
            total_target_rows=counts.get("total_target_rows", 0),
        )

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> TableDelta:
        return cls.from_dict(json.loads(json_str))


@dataclass(slots=True)
class TableManifestEntry:
    """Manifest entry describing delta properties of a single table."""

    table_name: str
    geometry_type: str | None
    delta_file: str
    delta_sha256: str
    delta_size_bytes: int
    insert_count: int
    update_count: int
    delete_count: int
    target_row_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableManifestEntry:
        return cls(**data)


@dataclass(slots=True)
class DeltaManifest:
    """Top-level signed manifest describing the complete dataset delta bundle."""

    dataset_name: str
    base_version: str
    target_version: str
    format_version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    base_sha256: str | None = None
    base_size_bytes: int | None = None
    target_sha256: str | None = None
    target_size_bytes: int | None = None
    tables: dict[str, TableManifestEntry] = field(default_factory=dict)
    signature: str | None = None
    public_key: str | None = None

    @property
    def total_inserts(self) -> int:
        return sum(t.insert_count for t in self.tables.values())

    @property
    def total_updates(self) -> int:
        return sum(t.update_count for t in self.tables.values())

    @property
    def total_deletes(self) -> int:
        return sum(t.delete_count for t in self.tables.values())

    def to_dict(self, include_signature: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "format_version": self.format_version,
            "dataset_name": self.dataset_name,
            "base_version": self.base_version,
            "target_version": self.target_version,
            "created_at": self.created_at,
            "base_dataset": {
                "sha256": self.base_sha256,
                "size_bytes": self.base_size_bytes,
            },
            "target_dataset": {
                "sha256": self.target_sha256,
                "size_bytes": self.target_size_bytes,
            },
            "summary": {
                "total_inserts": self.total_inserts,
                "total_updates": self.total_updates,
                "total_deletes": self.total_deletes,
                "table_count": len(self.tables),
            },
            "tables": {k: v.to_dict() for k, v in sorted(self.tables.items())},
        }

        if include_signature:
            data["signing"] = {
                "algorithm": "Ed25519" if self.signature else None,
                "signature": self.signature,
                "public_key": self.public_key,
            }

        return data

    def canonical_bytes(self) -> bytes:
        """Returns deterministic UTF-8 JSON bytes of unsigned content for signing/verification."""
        unsigned_data = self.to_dict(include_signature=False)
        return json.dumps(
            unsigned_data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaManifest:
        base_info = data.get("base_dataset", {})
        target_info = data.get("target_dataset", {})
        tables_dict = {
            k: TableManifestEntry.from_dict(v) for k, v in data.get("tables", {}).items()
        }
        signing_info = data.get("signing", {})

        return cls(
            format_version=data.get("format_version", "1.0"),
            dataset_name=data["dataset_name"],
            base_version=data["base_version"],
            target_version=data["target_version"],
            created_at=data.get("created_at", ""),
            base_sha256=base_info.get("sha256"),
            base_size_bytes=base_info.get("size_bytes"),
            target_sha256=target_info.get("sha256"),
            target_size_bytes=target_info.get("size_bytes"),
            tables=tables_dict,
            signature=signing_info.get("signature"),
            public_key=signing_info.get("public_key"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DeltaManifest:
        return cls.from_dict(json.loads(json_str))
