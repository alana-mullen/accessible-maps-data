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
  - **JSON Schema Export**: Automated generation of `delta_manifest.schema.json`, `dataset_catalog.schema.json`, and `release_metadata.schema.json` to formally validate Kotlin client `kotlinx.serialization` models.
  - **GitHub Pages Global CDN & Landing Page**: Responsive web landing page (`index.html` + `style.css`), live filtering, and `catalog.json` distribution for rate-limit-free mobile client discovery.
  - **GitHub Releases**: Automated CalVer versioning (`YYYY.MM.DD.01`), release notes, checksums, and multi-format asset uploads.
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
accessible-maps-build inspect greater-london
```

### 2. Generate Ed25519 signing keypair

```bash
accessible-maps-build generate-keys --output-dir keys/ --prefix delta_key
```

### 3. Generate a Delta Package

Compute differences between two GeoPackage datasets, generate per-table deltas, checksums, and sign the manifest:

```bash
accessible-maps-build generate-delta \
  --base data/greater-london-2026.08.15.01.gpkg \
  --target data/greater-london-2026.08.16.01.gpkg \
  --output-dir delta-london/ \
  --dataset-name greater-london \
  --base-version 2026.08.15.01 \
  --target-version 2026.08.16.01 \
  --signing-key keys/delta_key.pem
```

### 4. Verify a Delta Package

Verify manifest cryptographic signature and checksum integrity of all delta files:

```bash
accessible-maps-build verify-delta \
  --delta-dir delta-london/ \
  --public-key keys/delta_key.pub
```

### 5. Apply a Delta Package

Reconstruct the target dataset by applying per-table deltas to a base dataset:

```bash
accessible-maps-build apply-delta \
  --base data/greater-london-2026.08.15.01.gpkg \
  --delta-dir delta-london/ \
  --output data/greater-london-reconstructed.gpkg \
  --public-key keys/delta_key.pub
```

### 6. Package a Release Bundle

Optimizes SQLite layout and packages full dataset (`.gpkg.zip` & `.gpkg.zst`), delta files (`.zip` & `.tar.zst`), checksums, and metadata:

```bash
accessible-maps-build package-release \
  --target data/greater-london.gpkg \
  --output-dir releases/greater-london/ \
  --dataset-name greater-london \
  --version 2026.08.16.01 \
  --base data/greater-london-prev.gpkg \
  --base-version 2026.08.15.01 \
  --signing-key keys/delta_key.pem
```

### 7. Export Client JSON Schemas

Export formal JSON Schemas for Kotlin `kotlinx.serialization` validation:

```bash
accessible-maps-build export-schemas --output-dir schemas/
```

### 8. Build & Regenerate Global Catalog (`catalog.json`, `index.html`, `style.css`)

Build the catalog and responsive landing page using any of the following methods:

#### Method A: From local release metadata files
```bash
accessible-maps-build build-catalog \
  --metadata-files releases/*/metadata.json \
  --repo "alana-mullen/accessible-maps-data" \
  --output catalog/catalog.json \
  --export-schemas-dir catalog/schemas/
```

#### Method B: Re-render HTML/CSS from an existing `catalog.json` (instant local re-render)
```bash
accessible-maps-build build-catalog \
  --from-catalog catalog/catalog.json \
  --output catalog/catalog.json \
  --export-schemas-dir catalog/schemas/
```

#### Method C: Fetch metadata directly from GitHub Releases via API (no dataset download)
```bash
accessible-maps-build build-catalog \
  --fetch-from-github "alana-mullen/accessible-maps-data" \
  --output catalog/catalog.json \
  --export-schemas-dir catalog/schemas/
```

### 9. Publish to GitHub Releases

Upload assets, checksums, and generated release notes to GitHub Releases:

```bash
export GITHUB_TOKEN="ghp_your_token"
export GITHUB_REPOSITORY="alana-mullen/accessible-maps-data"

accessible-maps-build publish-release \
  --release-dir releases/greater-london/
```

## GitHub Actions Workflows

1. **`ci.yml`**: Runs code quality checks (`ruff check .`, `ruff format --check .`) and full pytest test suite across matrix targets.
2. **`build.yml`**: Scheduled weekly Geofabrik download and layer inspection with runner caching.
3. **`publish.yml`**: End-to-end pipeline to package, optimize, cryptographically sign, publish releases to GitHub, and deploy GitHub Pages. Automatically generates CalVer versions (`YYYY.MM.DD.01`) with same-day increment support.
4. **`deploy-pages.yml`**: Lightweight 1-click workflow to fetch release metadata via GitHub API and re-deploy `index.html`, `style.css`, `catalog.json`, and schemas to GitHub Pages in ~15 seconds without re-downloading heavy datasets.

## Data policy

Source data is downloaded from Geofabrik. Generated datasets should be distributed with
appropriate OpenStreetMap attribution and under the applicable ODbL terms.
