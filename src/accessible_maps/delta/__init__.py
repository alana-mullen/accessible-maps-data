from __future__ import annotations

from .checksums import sha256_bytes, sha256_file, verify_file_checksum
from .comparator import compare_gpkg_table, compare_records
from .engine import apply_delta_package, apply_table_delta, create_delta_package
from .manifest import build_manifest, load_manifest, save_manifest, validate_manifest
from .models import DeltaManifest, TableDelta, TableManifestEntry
from .signing import (
    generate_keypair,
    load_private_key,
    load_public_key,
    save_keypair,
    sign_bytes,
    sign_manifest,
    verify_manifest,
    verify_signature,
)

__all__ = [
    "DeltaManifest",
    "TableDelta",
    "TableManifestEntry",
    "apply_delta_package",
    "apply_table_delta",
    "build_manifest",
    "compare_gpkg_table",
    "compare_records",
    "create_delta_package",
    "generate_keypair",
    "load_manifest",
    "load_private_key",
    "load_public_key",
    "save_keypair",
    "save_manifest",
    "sha256_bytes",
    "sha256_file",
    "sign_bytes",
    "sign_manifest",
    "validate_manifest",
    "verify_file_checksum",
    "verify_manifest",
    "verify_signature",
]
