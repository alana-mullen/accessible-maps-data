from __future__ import annotations

import logging
import shutil
import sys
import time
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .config import get_region

LOGGER = logging.getLogger(__name__)


class DownloadError(RuntimeError):
    """Raised when a source dataset cannot be downloaded or validated."""


def download_region(
    region_name: str,
    data_dir: Path = Path("data"),
    *,
    attempts: int = 4,
    timeout: tuple[float, float] = (30.0, 300.0),
    force: bool = False,
    show_progress: bool | None = None,
) -> Path:
    """Download and extract a Geofabrik GeoPackage archive.

    Uses conditional HTTP requests (ETag/If-Modified-Since) to avoid re-downloading
    unchanged datasets. The archive is downloaded to a temporary file, verified
    with ZIP validation, and atomically replaced. Existing valid extractions are reused.
    """
    region = get_region(region_name)
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    archive = data_dir / f"{region.name}.gpkg.zip"
    extract_dir = data_dir / region.name

    if archive.exists() and _valid_zip(archive) and not force:
        LOGGER.info("Checking for remote updates to: %s", region.source_url)
    _download_with_retries(
        region.source_url,
        archive,
        attempts=attempts,
        timeout=timeout,
        force=force,
        show_progress=show_progress,
    )

    gpkg = _find_existing_gpkg(extract_dir)
    if (
        gpkg is not None
        and archive.exists()
        and extract_dir.stat().st_mtime >= archive.stat().st_mtime
    ):
        LOGGER.info("Using existing extraction: %s", gpkg)
        return gpkg

    _extract_archive(archive, extract_dir)
    gpkg = _find_gpkg(extract_dir)

    LOGGER.info("Extracted GeoPackage: %s", gpkg)
    return gpkg


def _download_with_retries(
    url: str,
    destination: Path,
    *,
    attempts: int,
    timeout: tuple[float, float],
    force: bool = False,
    show_progress: bool | None = None,
) -> None:
    last_error: Exception | None = None
    etag_file = destination.with_suffix(".etag")

    if show_progress is None:
        show_progress = sys.stdout.isatty()

    for attempt in range(1, attempts + 1):
        temp_path: Path | None = None
        try:
            LOGGER.info(
                "Requesting %s (attempt %d/%d)",
                url,
                attempt,
                attempts,
            )

            headers = {"User-Agent": "accessible-maps-data/0.1"}
            if (
                not force
                and destination.is_file()
                and _valid_zip(destination)
                and etag_file.is_file()
            ):
                headers["If-None-Match"] = etag_file.read_text(encoding="utf-8").strip()

            with requests.get(
                url,
                stream=True,
                timeout=timeout,
                headers=headers,
            ) as response:
                if response.status_code == 304:
                    LOGGER.info("Dataset unchanged on server (304 Not Modified): %s", destination)
                    return

                response.raise_for_status()

                etag = response.headers.get("ETag")
                total_size = int(response.headers.get("Content-Length", 0))

                with NamedTemporaryFile(
                    mode="wb",
                    prefix=f".{destination.name}.",
                    suffix=".partial",
                    dir=destination.parent,
                    delete=False,
                ) as tmp:
                    temp_path = Path(tmp.name)

                    if show_progress and total_size > 0:
                        with Progress(
                            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                            BarColumn(),
                            "[progress.percentage]{task.percentage:>3.1f}%",
                            "•",
                            DownloadColumn(),
                            "•",
                            TransferSpeedColumn(),
                            "•",
                            TimeRemainingColumn(),
                        ) as progress:
                            task = progress.add_task(
                                "download", filename=destination.name, total=total_size
                            )
                            for chunk in response.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    tmp.write(chunk)
                                    progress.update(task, advance=len(chunk))
                    else:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                tmp.write(chunk)

            if not temp_path.exists() or temp_path.stat().st_size == 0:
                raise DownloadError("Downloaded archive is empty")

            if not _valid_zip(temp_path):
                raise DownloadError("Downloaded file is not a valid ZIP archive")

            temp_path.replace(destination)

            if etag:
                etag_file.write_text(etag.strip(), encoding="utf-8")

            return

        except (requests.RequestException, OSError, DownloadError) as exc:
            last_error = exc
            LOGGER.warning("Download attempt failed: %s", exc)

            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))

    # If destination exists and is valid, keep using it on network error
    if destination.is_file() and _valid_zip(destination):
        LOGGER.warning("Network update check failed, using existing local archive %s", destination)
        return

    raise DownloadError(f"Unable to download {url} after {attempts} attempts") from last_error


def _valid_zip(path: Path) -> bool:
    try:
        return zipfile.is_zipfile(path)
    except OSError:
        return False


def _extract_archive(archive: Path, extract_dir: Path) -> None:
    temporary_dir = extract_dir.with_name(f".{extract_dir.name}.partial")
    if temporary_dir.exists():
        shutil.rmtree(temporary_dir)

    temporary_dir.mkdir(parents=True)

    try:
        with zipfile.ZipFile(archive) as zf:
            _safe_extract(zf, temporary_dir)

        gpkg = _find_gpkg(temporary_dir)
        if gpkg is None:
            raise DownloadError("ZIP archive contains no GeoPackage")

        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        temporary_dir.replace(extract_dir)

    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise


def _safe_extract(zf: zipfile.ZipFile, destination: Path) -> None:
    destination = destination.resolve()

    for member in zf.infolist():
        target = (destination / member.filename).resolve()

        if destination != target and destination not in target.parents:
            raise DownloadError(f"Unsafe ZIP member path: {member.filename}")

    zf.extractall(destination)


def _find_existing_gpkg(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    return _find_gpkg(directory)


def _find_gpkg(directory: Path) -> Path | None:
    matches = list(directory.rglob("*.gpkg"))

    if not matches:
        return None

    if len(matches) > 1:
        raise DownloadError(f"Expected one GeoPackage, found {len(matches)} in {directory}")

    return matches[0]
