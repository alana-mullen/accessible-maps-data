from __future__ import annotations

from .github import (
    GitHubPublishError,
    fetch_github_releases_metadata,
    publish_github_release,
)
from .html_index import CATALOG_CSS, generate_catalog_html, write_catalog_html
from .metadata import AssetInfo, DatasetCatalog, RegionCatalogEntry, ReleaseMetadata
from .packaging import (
    compress_dir_to_zip,
    compress_file_to_zip,
    generate_checksums_file,
    package_release,
)
from .validator import (
    ValidationError,
    parse_checksums_file,
    validate_checksums_file,
    validate_geopackage,
    validate_release_package,
)

__all__ = [
    "CATALOG_CSS",
    "AssetInfo",
    "DatasetCatalog",
    "GitHubPublishError",
    "RegionCatalogEntry",
    "ReleaseMetadata",
    "ValidationError",
    "compress_dir_to_zip",
    "compress_file_to_zip",
    "fetch_github_releases_metadata",
    "generate_catalog_html",
    "generate_checksums_file",
    "package_release",
    "parse_checksums_file",
    "publish_github_release",
    "validate_checksums_file",
    "validate_geopackage",
    "validate_release_package",
    "write_catalog_html",
]
