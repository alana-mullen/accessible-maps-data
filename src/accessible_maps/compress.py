from __future__ import annotations

import io
import tarfile
from pathlib import Path

import zstandard as zstd


def compress_file_zstd(
    source_file: Path,
    output_file: Path | None = None,
    level: int = 10,
) -> Path:
    """Compress a single file with Zstandard."""
    source_file = Path(source_file)
    output_file = (
        Path(output_file) if output_file else source_file.with_suffix(source_file.suffix + ".zst")
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cctx = zstd.ZstdCompressor(level=level)
    with open(source_file, "rb") as ifh, open(output_file, "wb") as ofh:
        cctx.copy_stream(ifh, ofh)

    return output_file


def decompress_file_zstd(
    source_file: Path,
    output_file: Path,
) -> Path:
    """Decompress a .zst file."""
    source_file = Path(source_file)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    dctx = zstd.ZstdDecompressor()
    with open(source_file, "rb") as ifh, open(output_file, "wb") as ofh:
        dctx.copy_stream(ifh, ofh)

    return output_file


def compress_dir_tar_zstd(
    source_dir: Path,
    output_file: Path,
    level: int = 10,
) -> Path:
    """Pack and compress a directory into a .tar.zst archive."""
    source_dir = Path(source_dir)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    tar_buf = io.BytesIO()
    with tarfile.open(fileobj=tar_buf, mode="w") as tar:
        for file_path in sorted(source_dir.rglob("*")):
            if file_path.is_file() and not file_path.name.startswith("."):
                arcname = str(file_path.relative_to(source_dir))
                tar.add(file_path, arcname=arcname)

    cctx = zstd.ZstdCompressor(level=level)
    compressed_bytes = cctx.compress(tar_buf.getvalue())
    output_file.write_bytes(compressed_bytes)

    return output_file


def decompress_dir_tar_zstd(
    source_file: Path,
    output_dir: Path,
) -> Path:
    """Extract a .tar.zst archive into output_dir."""
    source_file = Path(source_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dctx = zstd.ZstdDecompressor()
    decompressed_bytes = dctx.decompress(source_file.read_bytes())
    tar_buf = io.BytesIO(decompressed_bytes)
    with tarfile.open(fileobj=tar_buf, mode="r") as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=output_dir, filter="data")
        else:
            tar.extractall(path=output_dir)

    return output_dir
