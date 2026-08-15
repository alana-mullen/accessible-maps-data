# Accessible Maps Data

Data pipeline for generating UK accessibility datasets, high-efficiency Zstandard delta updates, and automated global distribution for the Accessible Maps app.

## Features

- **Geofabrik Downloader**: Streaming GeoPackage downloads with ETag/304 conditional checking, retry logic, integrity checks, and rich terminal progress bars.
- **Workflow Caching & Isolation**: Weekly Geofabrik dataset caching and isolated parallel matrix runners in GitHub Actions.
- **SQLite Database Optimization**: Pre-release SQLite `VACUUM`, `ANALYZE`, and 4096-byte page alignment tailored for mobile flash storage.
- **High-Performance Compression**: Dual distribution in standard `.zip` and ultra-fast **Zstandard** (`.gpkg.zst` and `.tar.zst`) for 30–50% smaller downloads and 3–5x faster mobile decompression.
- **Delta Engine**:
  - **Comparison**: Deep record-level diffing detecting inserts, updates, and deletes across tables.
  - **Per-table Deltas**: Compact, structured table-level delta files with row counts and schema information.
  - **Streaming Checksums**: Deterministic SHA-256 calculation for GeoPackage files, table deltas, and canonical JSON metadata.
  - **Manifests**: Machine-readable `manifest.json` describing datasets, table statistics, versions, file hashes, and cryptographic signatures.
  - **Cryptographic Signing**: Asymmetric Ed25519 signing and verification with automated GitHub Actions secret injection and memory shredding.
- **Publishing & Distribution**:
  - **JSON Schema Export**: Automated generation of `manifest.schema.json` and `catalog.schema.json` to formally validate Kotlin client `kotlinx.serialization` models.
  - **GitHub Pages Global CDN**: Automated deployment of `catalog.json` and schemas to GitHub Pages for rate-limit-free mobile client discovery.
  - **GitHub Releases**: Automated release notes, checksums, and multi-format asset uploads.
- **Rich CLI**: Beautiful terminal tables and progress bars with `rich`.

## Local setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest
```

## CLI Usage

### 1. List regions & inspect Geofabrik datasets

```bash
# List configured regions in a formatted table
accessible-maps-build list-regions

# Download and inspect layers for a region with rich progress bar
accessible-maps-build inspect north-west
```

### 2. Generate Ed25519 signing keypair

```bash
accessible-maps-build generate-keys --output-dir keys/ --prefix delta_key
```

### 3. Generate a Delta Package

Compute differences between two GeoPackage datasets, generate per-table deltas, checksums, and sign the manifest:

```bash
accessible-maps-build generate-delta \
  --base data/north-west-2026.01.gpkg \
  --target data/north-west-2026.02.gpkg \
  --output-dir delta-north-west/ \
  --dataset-name north-west \
  --base-version 2026.01 \
  --target-version 2026.02 \
  --signing-key keys/delta_key.pem
```

### 4. Verify a Delta Package

Verify manifest cryptographic signature and checksum integrity of all delta files:

```bash
accessible-maps-build verify-delta \
  --delta-dir delta-north-west/ \
  --public-key keys/delta_key.pub
```

### 5. Apply a Delta Package

Reconstruct the target dataset by applying per-table deltas to a base dataset:

```bash
accessible-maps-build apply-delta \
  --base data/north-west-2026.01.gpkg \
  --delta-dir delta-north-west/ \
  --output data/north-west-reconstructed.gpkg \
  --public-key keys/delta_key.pub
```

### 6. Package a Release Bundle

Optimizes SQLite layout and packages full dataset (`.gpkg.zip` & `.gpkg.zst`), delta files (`.zip` & `.tar.zst`), checksums, and metadata:

```bash
accessible-maps-build package-release \
  --target data/north-west.gpkg \
  --output-dir releases/north-west/ \
  --dataset-name north-west \
  --version 2026.08.1 \
  --base data/north-west-prev.gpkg \
  --base-version 2026.07.1 \
  --signing-key keys/delta_key.pem
```

### 7. Export Client JSON Schemas

Export formal JSON Schemas for Kotlin `kotlinx.serialization` validation:

```bash
accessible-maps-build export-schemas --output-dir schemas/
```

### 8. Build Global Dataset Catalog (`catalog.json`)

Build `catalog.json` with timestamps, file hashes, and direct download URLs:

```bash
accessible-maps-build build-catalog \
  --metadata-files releases/*/metadata.json \
  --repo "alana-mullen/accessible-maps-data" \
  --export-schemas-dir schemas/ \
  --output catalog.json
```

### 9. Publish to GitHub Releases

Upload assets, checksums, and generated release notes to GitHub Releases:

```bash
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_REPOSITORY="alana-mullen/accessible-maps-data"

accessible-maps-build publish-release \
  --release-dir releases/north-west/
```

## Data policy

Source data is downloaded from Geofabrik. Generated datasets should be distributed with
appropriate OpenStreetMap attribution and under the applicable ODbL terms.
