from pathlib import Path

import pytest

from accessible_maps.delta.checksums import (
    sha256_bytes,
    sha256_canonical_json,
    sha256_file,
    verify_file_checksum,
)


def test_sha256_bytes():
    # sha256 of "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert sha256_bytes(b"hello world") == expected


def test_sha256_file(tmp_path: Path):
    test_file = tmp_path / "data.bin"
    test_file.write_bytes(b"hello world")

    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert sha256_file(test_file) == expected


def test_sha256_file_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        sha256_file(tmp_path / "nonexistent.bin")


def test_sha256_canonical_json_order_independent():
    obj1 = {"b": 2, "a": 1, "nested": {"y": [1, 2], "x": True}}
    obj2 = {"nested": {"x": True, "y": [1, 2]}, "a": 1, "b": 2}

    assert sha256_canonical_json(obj1) == sha256_canonical_json(obj2)


def test_verify_file_checksum(tmp_path: Path):
    test_file = tmp_path / "sample.txt"
    test_file.write_text("accessible maps test payload", encoding="utf-8")

    correct_hash = sha256_file(test_file)
    assert verify_file_checksum(test_file, correct_hash)
    assert verify_file_checksum(test_file, correct_hash.upper())
    assert not verify_file_checksum(test_file, "0" * 64)
