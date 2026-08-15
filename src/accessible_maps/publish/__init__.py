from __future__ import annotations

from .github import GitHubPublishError, publish_github_release
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
    "AssetInfo",
    "DatasetCatalog",
    "GitHubPublishError",
    "RegionCatalogEntry",
    "ReleaseMetadata",
    "ValidationError",
    "compress_dir_to_zip",
    "compress_file_to_zip",
    "generate_checksums_file",
    "package_release",
    "parse_checksums_file",
    "publish_github_release",
    "validate_checksums_file",
    "validate_geopackage",
    "validate_release_package",
]
