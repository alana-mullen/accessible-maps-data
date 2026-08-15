from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    """Compute hex SHA-256 hash of a bytes object."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute hex SHA-256 hash of a file using streaming chunks."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for checksum: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sha256_canonical_json(data: dict[str, Any] | list[Any]) -> str:
    """Compute hex SHA-256 hash of a JSON-serializable structure deterministically."""
    canonical_bytes = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256_bytes(canonical_bytes)


def verify_file_checksum(path: Path, expected_sha256: str) -> bool:
    """Verify that a file's SHA-256 hash matches the expected value using constant-time comparison."""
    actual_sha256 = sha256_file(path)
    return hmac.compare_digest(actual_sha256.lower(), expected_sha256.lower())
