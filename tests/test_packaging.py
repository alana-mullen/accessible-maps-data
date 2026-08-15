from pathlib import Path
import zipfile

from accessible_maps.delta.checksums import sha256_file
from accessible_maps.publish.packaging import (
    compress_dir_to_zip,
    compress_file_to_zip,
    generate_checksums_file,
)
from accessible_maps.publish.validator import parse_checksums_file


def test_compress_file_to_zip(tmp_path: Path):
    source = tmp_path / "sample.txt"
    source.write_text("accessible maps test data", encoding="utf-8")

    zip_out = tmp_path / "sample.zip"
    compress_file_to_zip(source, zip_out)

    assert zip_out.is_file()
    with zipfile.ZipFile(zip_out, "r") as zf:
        assert zf.namelist() == ["sample.txt"]
        assert zf.read("sample.txt").decode("utf-8") == "accessible maps test data"


def test_compress_dir_to_zip(tmp_path: Path):
    source_dir = tmp_path / "src_dir"
    source_dir.mkdir()
    (source_dir / "f1.txt").write_text("1")
    sub = source_dir / "sub"
    sub.mkdir()
    (sub / "f2.txt").write_text("2")

    zip_out = tmp_path / "dir.zip"
    compress_dir_to_zip(source_dir, zip_out)

    assert zip_out.is_file()
    with zipfile.ZipFile(zip_out, "r") as zf:
        names = sorted(zf.namelist())
        assert names == ["f1.txt", "sub/f2.txt"]


def test_generate_checksums_file(tmp_path: Path):
    f1 = tmp_path / "a.bin"
    f1.write_bytes(b"aaa")
    f2 = tmp_path / "b.bin"
    f2.write_bytes(b"bbb")

    out_sums = tmp_path / "checksums.txt"
    generate_checksums_file([f1, f2], out_sums)

    assert out_sums.is_file()
    parsed = parse_checksums_file(out_sums)
    assert parsed["a.bin"] == sha256_file(f1)
    assert parsed["b.bin"] == sha256_file(f2)
