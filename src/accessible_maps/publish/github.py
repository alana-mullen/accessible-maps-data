from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests

from .metadata import ReleaseMetadata
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
            raise GitHubPublishError("Missing repository identifier (e.g., owner/repo or GITHUB_REPOSITORY)")
        if not token:
            raise GitHubPublishError("Missing authentication token (token arg or GITHUB_TOKEN env var)")

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
        get_resp = requests.get(f"{api_url}/tags/{metadata.release_tag}", headers=headers, timeout=30.0)
        get_resp.raise_for_status()
        release_data = get_resp.json()
    else:
        resp.raise_for_status()
        release_data = resp.json()

    release_id = release_data["id"]
    upload_url_template = release_data["upload_url"]  # Format: https://uploads.github.com/.../assets{?name,label}
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
