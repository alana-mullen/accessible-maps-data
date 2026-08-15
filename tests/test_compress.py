from pathlib import Path

from accessible_maps.compress import (
    compress_dir_tar_zstd,
    compress_file_zstd,
    decompress_dir_tar_zstd,
    decompress_file_zstd,
)


def test_compress_and_decompress_file_zstd(tmp_path: Path):
    source_file = tmp_path / "data.txt"
    source_file.write_text("Hello from Accessible Maps Zstandard test payload!", encoding="utf-8")

    zst_file = tmp_path / "data.txt.zst"
    compress_file_zstd(source_file, zst_file)

    assert zst_file.is_file()
    assert zst_file.stat().st_size > 0

    decompressed_file = tmp_path / "data.decompressed.txt"
    decompress_file_zstd(zst_file, decompressed_file)

    assert decompressed_file.is_file()
    assert decompressed_file.read_text(encoding="utf-8") == "Hello from Accessible Maps Zstandard test payload!"


def test_compress_and_decompress_dir_tar_zstd(tmp_path: Path):
    source_dir = tmp_path / "source_data"
    source_dir.mkdir()
    (source_dir / "layer1.json").write_text('{"name": "kerbs"}', encoding="utf-8")
    (source_dir / "layer2.json").write_text('{"name": "footways"}', encoding="utf-8")

    tar_zst = tmp_path / "bundle.tar.zst"
    compress_dir_tar_zstd(source_dir, tar_zst)

    assert tar_zst.is_file()
    assert tar_zst.stat().st_size > 0

    extract_dir = tmp_path / "extracted_data"
    decompress_dir_tar_zstd(tar_zst, extract_dir)

    assert (extract_dir / "layer1.json").is_file()
    assert (extract_dir / "layer2.json").is_file()
    assert (extract_dir / "layer1.json").read_text(encoding="utf-8") == '{"name": "kerbs"}'
