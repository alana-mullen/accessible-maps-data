from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests

from .metadata import AssetInfo, ReleaseMetadata
from .validator import validate_release_package

LOGGER = logging.getLogger(__name__)


class GitHubPublishError(RuntimeError):
    """Raised when publishing to GitHub Releases fails."""


def publish_github_release(
    release_dir: Path,
    repo: str | None = None,
    token: str | None = None,
    draft: bool = False,
    prerelease: bool = False,
    dry_run: bool = False,
    public_key: str | Path | None = None,
) -> dict[str, Any]:
    """Publish a packaged dataset release directory to GitHub Releases."""
    release_dir = Path(release_dir)
    metadata_path = release_dir / "metadata.json"

    if not metadata_path.is_file():
        raise GitHubPublishError(f"metadata.json missing in {release_dir}")

    # Validate before publishing
    valid, errors = validate_release_package(release_dir, public_key=public_key)
    if not valid:
        raise GitHubPublishError(f"Release validation failed: {'; '.join(errors)}")

    metadata = ReleaseMetadata.from_json(metadata_path.read_text(encoding="utf-8"))

    repo = repo or os.getenv("GITHUB_REPOSITORY")
    token = token or os.getenv("GITHUB_TOKEN")

    if not dry_run:
        if not repo:
            raise GitHubPublishError(
                "Missing repository identifier (e.g., owner/repo or GITHUB_REPOSITORY)"
            )
        if not token:
            raise GitHubPublishError(
                "Missing authentication token (token arg or GITHUB_TOKEN env var)"
            )

    release_notes_path = release_dir / "release_notes.md"
    release_notes = (
        release_notes_path.read_text(encoding="utf-8")
        if release_notes_path.is_file()
        else metadata.generate_release_notes()
    )

    if dry_run:
        LOGGER.info(
            "[DRY-RUN] Would publish release %s to %s with %d assets",
            metadata.release_tag,
            repo or "<local>",
            len(metadata.assets),
        )
        return {
            "dry_run": True,
            "release_tag": metadata.release_tag,
            "assets": [a.filename for a in metadata.assets],
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "accessible-maps-publisher/1.0",
    }

    # 1. Create Release on GitHub
    api_url = f"https://api.github.com/repos/{repo}/releases"
    payload = {
        "tag_name": metadata.release_tag,
        "name": f"Accessible Maps {metadata.dataset_name} ({metadata.version})",
        "body": release_notes,
        "draft": draft,
        "prerelease": prerelease,
    }

    LOGGER.info("Creating release %s in %s...", metadata.release_tag, repo)
    resp = requests.post(api_url, json=payload, headers=headers, timeout=30.0)

    if resp.status_code == 422:
        # Release tag might already exist; query it
        LOGGER.info("Release tag %s exists, fetching existing release...", metadata.release_tag)
        get_resp = requests.get(
            f"{api_url}/tags/{metadata.release_tag}", headers=headers, timeout=30.0
        )
        get_resp.raise_for_status()
        release_data = get_resp.json()
    else:
        resp.raise_for_status()
        release_data = resp.json()

    release_id = release_data["id"]
    upload_url_template = release_data[
        "upload_url"
    ]  # Format: https://uploads.github.com/.../assets{?name,label}
    base_upload_url = upload_url_template.split("{")[0]

    # 2. Upload assets
    uploaded_assets: list[str] = []
    for asset in metadata.assets:
        asset_path = release_dir / asset.filename
        if not asset_path.is_file():
            LOGGER.warning("Asset file %s not found on disk, skipping upload", asset.filename)
            continue

        LOGGER.info("Uploading asset %s (%d bytes)...", asset.filename, asset.size_bytes)
        upload_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": asset.content_type,
            "Accept": "application/vnd.github+json",
            "User-Agent": "accessible-maps-publisher/1.0",
        }

        with open(asset_path, "rb") as f:
            upload_resp = requests.post(
                f"{base_upload_url}?name={asset.filename}",
                headers=upload_headers,
                data=f,
                timeout=120.0,
            )

        if upload_resp.status_code == 422:
            LOGGER.warning("Asset %s already uploaded to release %d", asset.filename, release_id)
        else:
            upload_resp.raise_for_status()
            uploaded_assets.append(asset.filename)

    LOGGER.info("Successfully published release %s (ID: %d)", metadata.release_tag, release_id)
    return {
        "release_id": release_id,
        "release_tag": metadata.release_tag,
        "html_url": release_data.get("html_url"),
        "uploaded_assets": uploaded_assets,
    }


def fetch_github_releases_metadata(
    repo: str,
    token: str | None = None,
) -> list[ReleaseMetadata]:
    """Fetch all ReleaseMetadata objects across published releases in a GitHub repo."""
    token = token or os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "accessible-maps-publisher/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results: list[ReleaseMetadata] = []
    page = 1

    while True:
        api_url = f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}"
        resp = requests.get(api_url, headers=headers, timeout=30.0)
        if resp.status_code != 200:
            LOGGER.warning("Failed to fetch releases (HTTP %d): %s", resp.status_code, resp.text)
            break
        releases = resp.json()
        if not releases or not isinstance(releases, list):
            break

        for rel in releases:
            tag_name = rel.get("tag_name", "")
            assets = rel.get("assets", [])

            # Check if metadata.json asset is directly attached
            meta_asset = next((a for a in assets if a.get("name") == "metadata.json"), None)
            parsed_meta: ReleaseMetadata | None = None

            if meta_asset and meta_asset.get("browser_download_url"):
                try:
                    meta_resp = requests.get(
                        meta_asset["browser_download_url"],
                        headers={"User-Agent": "accessible-maps-publisher/1.0"},
                        timeout=15.0,
                    )
                    if meta_resp.status_code == 200:
                        parsed_meta = ReleaseMetadata.from_json(meta_resp.text)
                except Exception as exc:
                    LOGGER.debug("Could not fetch direct metadata.json: %s", exc)

            if parsed_meta is not None:
                results.append(parsed_meta)
                continue

            # Fallback: Reconstruct metadata from GitHub release assets & checksums.txt
            raw_tag = tag_name.lstrip("v")
            parts = raw_tag.split("-", 1)
            if len(parts) >= 2:
                version = parts[0]
                dataset_name = parts[1]
            else:
                version = raw_tag
                dataset_name = rel.get("name", raw_tag)

            checksum_map: dict[str, str] = {}
            chk_asset = next((a for a in assets if a.get("name") == "checksums.txt"), None)
            if chk_asset and chk_asset.get("browser_download_url"):
                try:
                    chk_resp = requests.get(
                        chk_asset["browser_download_url"],
                        headers={"User-Agent": "accessible-maps-publisher/1.0"},
                        timeout=15.0,
                    )
                    if chk_resp.status_code == 200:
                        for line in chk_resp.text.splitlines():
                            line_parts = line.strip().split()
                            if len(line_parts) >= 2:
                                checksum_map[line_parts[1]] = line_parts[0]
                except Exception as exc:
                    LOGGER.debug("Could not fetch checksums.txt: %s", exc)

            asset_infos: list[AssetInfo] = []
            for a in assets:
                filename = a.get("name", "")
                content_type = "application/octet-stream"
                if filename.endswith(".zip"):
                    content_type = "application/zip"
                elif filename.endswith(".zst"):
                    content_type = "application/zstd"
                elif filename.endswith(".json"):
                    content_type = "application/json"
                elif filename.endswith(".txt"):
                    content_type = "text/plain"

                asset_infos.append(
                    AssetInfo(
                        filename=filename,
                        sha256=checksum_map.get(filename, ""),
                        size_bytes=a.get("size", 0),
                        content_type=content_type,
                        download_url=a.get("browser_download_url"),
                    )
                )

            reconstructed = ReleaseMetadata(
                release_tag=tag_name,
                dataset_name=dataset_name,
                version=version,
                assets=asset_infos,
            )
            results.append(reconstructed)

        if len(releases) < 100:
            break
        page += 1

    return results
