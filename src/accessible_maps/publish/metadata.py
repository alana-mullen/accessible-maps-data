from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AssetInfo:
    """Information about a release asset file."""

    filename: str
    sha256: str
    size_bytes: int
    content_type: str = "application/octet-stream"
    download_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssetInfo:
        return cls(**data)


@dataclass(slots=True)
class ReleaseMetadata:
    """Structured metadata for a published dataset release."""

    release_tag: str
    dataset_name: str
    version: str
    base_version: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    assets: list[AssetInfo] = field(default_factory=list)
    table_stats: dict[str, int] = field(default_factory=dict)
    delta_stats: dict[str, int] | None = None
    attribution: str = "© OpenStreetMap contributors, licensed under ODbL"
    license: str = "ODbL-1.0"
    manifest_signature: str | None = None
    public_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_tag": self.release_tag,
            "dataset_name": self.dataset_name,
            "version": self.version,
            "base_version": self.base_version,
            "created_at": self.created_at,
            "table_stats": self.table_stats,
            "delta_stats": self.delta_stats,
            "attribution": self.attribution,
            "license": self.license,
            "signing": {
                "manifest_signature": self.manifest_signature,
                "public_key": self.public_key,
            },
            "assets": [a.to_dict() for a in self.assets],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReleaseMetadata:
        signing = data.get("signing", {})
        assets = [AssetInfo.from_dict(a) for a in data.get("assets", [])]
        return cls(
            release_tag=data["release_tag"],
            dataset_name=data["dataset_name"],
            version=data["version"],
            base_version=data.get("base_version"),
            created_at=data.get("created_at", ""),
            assets=assets,
            table_stats=dict(data.get("table_stats", {})),
            delta_stats=data.get("delta_stats"),
            attribution=data.get("attribution", "© OpenStreetMap contributors, licensed under ODbL"),
            license=data.get("license", "ODbL-1.0"),
            manifest_signature=signing.get("manifest_signature"),
            public_key=signing.get("public_key"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> ReleaseMetadata:
        return cls.from_dict(json.loads(json_str))

    def generate_release_notes(self) -> str:
        """Generate formatted Markdown release notes for GitHub Releases."""
        lines = [
            f"# Accessible Maps Dataset Release: `{self.dataset_name}` ({self.version})",
            "",
            f"- **Dataset:** `{self.dataset_name}`",
            f"- **Version:** `{self.version}`",
        ]

        if self.base_version:
            lines.append(f"- **Delta Base Version:** `{self.base_version}`")

        lines.extend([
            f"- **Release Tag:** `{self.release_tag}`",
            f"- **Published:** `{self.created_at}`",
            f"- **License:** [{self.license}](https://opendatacommons.org/licenses/odbl/)",
            f"- **Attribution:** {self.attribution}",
            "",
            "## Table Summary",
            "",
            "| Layer / Table | Feature Count |",
            "| :--- | :--- |",
        ])

        for table, count in sorted(self.table_stats.items()):
            lines.append(f"| `{table}` | {count:,} |")

        if self.delta_stats:
            lines.extend([
                "",
                "## Delta Changes (vs Base)",
                "",
                f"- **New Features (Inserts):** {self.delta_stats.get('inserts', 0):,}",
                f"- **Modified Features (Updates):** {self.delta_stats.get('updates', 0):,}",
                f"- **Removed Features (Deletes):** {self.delta_stats.get('deletes', 0):,}",
            ])

        lines.extend([
            "",
            "## Assets & Checksums",
            "",
            "| Asset File | Size (Bytes) | SHA-256 Checksum |",
            "| :--- | :--- | :--- |",
        ])

        for asset in self.assets:
            lines.append(f"| `{asset.filename}` | {asset.size_bytes:,} | `{asset.sha256}` |")

        if self.manifest_signature:
            lines.extend([
                "",
                "## Cryptographic Verification",
                "",
                "The release manifest is cryptographically signed using Ed25519.",
                f"- **Public Key:** `{self.public_key}`",
                f"- **Manifest Signature:** `{self.manifest_signature}`",
            ])

        lines.append("")
        return "\n".join(lines)


@dataclass(slots=True)
class DeltaCatalogEntry:
    """Catalog entry for an incremental delta update."""

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
    delta_stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaCatalogEntry:
        return cls(**data)


@dataclass(slots=True)
class RegionCatalogEntry:
    """Catalog entry tracking available full datasets and deltas for a region."""

    region_name: str
    latest_version: str
    latest_release_tag: str
    latest_updated_at: str
    full_dataset_asset: str | None = None
    full_dataset_download_url: str | None = None
    full_dataset_sha256: str | None = None
    full_dataset_size_bytes: int | None = None
    release_html_url: str | None = None
    table_stats: dict[str, int] = field(default_factory=dict)
    available_deltas: list[DeltaCatalogEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_name": self.region_name,
            "latest_version": self.latest_version,
            "latest_release_tag": self.latest_release_tag,
            "latest_updated_at": self.latest_updated_at,
            "full_dataset": {
                "asset": self.full_dataset_asset,
                "download_url": self.full_dataset_download_url,
                "sha256": self.full_dataset_sha256,
                "size_bytes": self.full_dataset_size_bytes,
                "table_stats": self.table_stats,
            },
            "release_html_url": self.release_html_url,
            "available_deltas": [d.to_dict() for d in self.available_deltas],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RegionCatalogEntry:
        full_info = data.get("full_dataset", {})
        deltas = [DeltaCatalogEntry.from_dict(d) for d in data.get("available_deltas", [])]
        return cls(
            region_name=data["region_name"],
            latest_version=data["latest_version"],
            latest_release_tag=data["latest_release_tag"],
            latest_updated_at=data.get("latest_updated_at", ""),
            full_dataset_asset=full_info.get("asset"),
            full_dataset_download_url=full_info.get("download_url"),
            full_dataset_sha256=full_info.get("sha256"),
            full_dataset_size_bytes=full_info.get("size_bytes"),
            release_html_url=data.get("release_html_url"),
            table_stats=dict(full_info.get("table_stats", {})),
            available_deltas=deltas,
        )


@dataclass(slots=True)
class DatasetCatalog:
    """Global catalog index of all regional datasets, timestamped updates, and delta paths."""

    catalog_version: str = "1.0"
    updated_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    regions: dict[str, RegionCatalogEntry] = field(default_factory=dict)

    def add_release(
        self,
        metadata: ReleaseMetadata,
        release_html_url: str | None = None,
        repo: str | None = None,
        base_download_url: str | None = None,
    ) -> None:
        """Register or update a release in the catalog with timestamps and location URLs."""
        self.updated_at = datetime.now(UTC).isoformat()

        def _resolve_url(filename: str | None) -> str | None:
            if not filename:
                return None
            if base_download_url:
                return f"{base_download_url.rstrip('/')}/{metadata.release_tag}/{filename}"
            if repo:
                return f"https://github.com/{repo}/releases/download/{metadata.release_tag}/{filename}"
            return None

        full_asset = next(
            (a for a in metadata.assets if a.filename.endswith((".gpkg.zip", ".gpkg"))),
            None,
        )
        full_download_url = full_asset.download_url if full_asset and full_asset.download_url else (
            _resolve_url(full_asset.filename) if full_asset else None
        )

        entry = self.regions.get(metadata.dataset_name)
        if entry is None:
            entry = RegionCatalogEntry(
                region_name=metadata.dataset_name,
                latest_version=metadata.version,
                latest_release_tag=metadata.release_tag,
                latest_updated_at=metadata.created_at,
                full_dataset_asset=full_asset.filename if full_asset else None,
                full_dataset_download_url=full_download_url,
                full_dataset_sha256=full_asset.sha256 if full_asset else None,
                full_dataset_size_bytes=full_asset.size_bytes if full_asset else None,
                release_html_url=release_html_url,
                table_stats=metadata.table_stats,
            )
            self.regions[metadata.dataset_name] = entry
        else:
            entry.latest_version = metadata.version
            entry.latest_release_tag = metadata.release_tag
            entry.latest_updated_at = metadata.created_at
            entry.release_html_url = release_html_url or entry.release_html_url
            if full_asset:
                entry.full_dataset_asset = full_asset.filename
                entry.full_dataset_download_url = full_download_url
                entry.full_dataset_sha256 = full_asset.sha256
                entry.full_dataset_size_bytes = full_asset.size_bytes
            entry.table_stats = metadata.table_stats

        if metadata.base_version:
            delta_asset = next(
                (a for a in metadata.assets if "delta" in a.filename),
                None,
            )
            manifest_asset = next(
                (a for a in metadata.assets if a.filename == "manifest.json"),
                None,
            )
            delta_download_url = delta_asset.download_url if delta_asset and delta_asset.download_url else (
                _resolve_url(delta_asset.filename) if delta_asset else None
            )
            manifest_url = manifest_asset.download_url if manifest_asset and manifest_asset.download_url else (
                _resolve_url("manifest.json") if manifest_asset else None
            )

            # Avoid duplicates for same from/to version
            entry.available_deltas = [
                d for d in entry.available_deltas
                if not (d.from_version == metadata.base_version and d.to_version == metadata.version)
            ]

            entry.available_deltas.append(
                DeltaCatalogEntry(
                    from_version=metadata.base_version,
                    to_version=metadata.version,
                    release_tag=metadata.release_tag,
                    updated_at=metadata.created_at,
                    delta_asset=delta_asset.filename if delta_asset else "",
                    download_url=delta_download_url,
                    manifest_url=manifest_url,
                    sha256=delta_asset.sha256 if delta_asset else None,
                    size_bytes=delta_asset.size_bytes if delta_asset else None,
                    manifest_signature=metadata.manifest_signature,
                    public_key=metadata.public_key,
                    delta_stats=metadata.delta_stats or {},
                )
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_version": self.catalog_version,
            "updated_at": self.updated_at,
            "regions": {k: v.to_dict() for k, v in sorted(self.regions.items())},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetCatalog:
        regions = {
            k: RegionCatalogEntry.from_dict(v)
            for k, v in data.get("regions", {}).items()
        }
        return cls(
            catalog_version=data.get("catalog_version", "1.0"),
            updated_at=data.get("updated_at", ""),
            regions=regions,
        )

    @classmethod
    def from_json(cls, json_str: str) -> DatasetCatalog:
        return cls.from_dict(json.loads(json_str))
