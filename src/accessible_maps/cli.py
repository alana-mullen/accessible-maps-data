from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .config import REGIONS
from .delta import (
    apply_delta_package,
    create_delta_package,
    load_manifest,
    save_keypair,
    validate_manifest,
)
from .etl import prepare_region
from .logging import configure_logging
from .publish import (
    DatasetCatalog,
    ReleaseMetadata,
    fetch_github_releases_metadata,
    package_release,
    publish_github_release,
    validate_release_package,
    write_catalog_html,
)
from .schemas import export_json_schemas
from .version import __version__

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="accessible-maps-build",
        description="Build Accessible Maps regional datasets, deltas, and releases.",
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command")

    # list-regions
    list_regions = subparsers.add_parser(
        "list-regions",
        help="List configured UK regions and source URLs.",
    )
    list_regions.add_argument("--plain", action="store_true", help="Print plain list of names only")
    list_regions.set_defaults(handler=_list_regions)

    # inspect
    inspect = subparsers.add_parser(
        "inspect",
        help="Download/extract a region and list its GeoPackage layers.",
    )
    inspect.add_argument("region", choices=[r.name for r in REGIONS])
    inspect.add_argument("--data-dir", type=Path, default=Path("data"))
    inspect.set_defaults(handler=_inspect)

    # generate-delta
    gen_delta = subparsers.add_parser(
        "generate-delta",
        help="Generate per-table deltas, checksums, and signed manifest between datasets.",
    )
    gen_delta.add_argument("--target", type=Path, required=True, help="Target (newer) GeoPackage")
    gen_delta.add_argument("--base", type=Path, default=None, help="Base (older) GeoPackage")
    gen_delta.add_argument(
        "--output-dir", type=Path, required=True, help="Output directory for delta package"
    )
    gen_delta.add_argument(
        "--dataset-name", default="accessible-maps", help="Dataset name identifier"
    )
    gen_delta.add_argument("--base-version", default="v1", help="Base version tag")
    gen_delta.add_argument("--target-version", default="v2", help="Target version tag")
    gen_delta.add_argument(
        "--signing-key", type=Path, default=None, help="Path to Ed25519 private key"
    )
    gen_delta.set_defaults(handler=_generate_delta)

    # apply-delta
    apply_delta = subparsers.add_parser(
        "apply-delta",
        help="Validate and apply delta package to reconstruct target dataset.",
    )
    apply_delta.add_argument(
        "--delta-dir", type=Path, required=True, help="Directory containing delta package"
    )
    apply_delta.add_argument("--output", type=Path, required=True, help="Output GeoPackage path")
    apply_delta.add_argument("--base", type=Path, default=None, help="Base GeoPackage path")
    apply_delta.add_argument(
        "--public-key", type=Path, default=None, help="Path to Ed25519 public key"
    )
    apply_delta.set_defaults(handler=_apply_delta)

    # verify-delta
    verify_delta = subparsers.add_parser(
        "verify-delta",
        help="Verify manifest signature and delta file checksums.",
    )
    verify_delta.add_argument(
        "--delta-dir", type=Path, required=True, help="Directory containing delta package"
    )
    verify_delta.add_argument(
        "--public-key", type=Path, default=None, help="Optional Ed25519 public key"
    )
    verify_delta.set_defaults(handler=_verify_delta)

    # generate-keys
    gen_keys = subparsers.add_parser(
        "generate-keys",
        help="Generate a new Ed25519 keypair for signing deltas.",
    )
    gen_keys.add_argument(
        "--output-dir", type=Path, default=Path("keys"), help="Directory to save keys"
    )
    gen_keys.add_argument("--prefix", default="delta_key", help="Key file prefix")
    gen_keys.set_defaults(handler=_generate_keys)

    # package-release
    pkg_release = subparsers.add_parser(
        "package-release",
        help="Bundle dataset, delta updates, checksums, and metadata into a release folder.",
    )
    pkg_release.add_argument("--target", type=Path, required=True, help="Target GeoPackage")
    pkg_release.add_argument(
        "--output-dir", type=Path, required=True, help="Release bundle directory"
    )
    pkg_release.add_argument("--dataset-name", required=True, help="Dataset name / region")
    pkg_release.add_argument("--version", required=True, help="Release version string")
    pkg_release.add_argument("--base", type=Path, default=None, help="Base GeoPackage for delta")
    pkg_release.add_argument("--base-version", default=None, help="Base version for delta")
    pkg_release.add_argument("--signing-key", type=Path, default=None, help="Ed25519 private key")
    pkg_release.add_argument(
        "--no-optimize", action="store_true", help="Skip SQLite database optimization"
    )
    pkg_release.set_defaults(handler=_package_release)

    # validate-release
    val_release = subparsers.add_parser(
        "validate-release",
        help="Validate consistency, checksums, and signatures of a release bundle.",
    )
    val_release.add_argument(
        "--release-dir", type=Path, required=True, help="Release bundle directory"
    )
    val_release.add_argument(
        "--public-key", type=Path, default=None, help="Optional Ed25519 public key"
    )
    val_release.set_defaults(handler=_validate_release)

    # publish-release
    pub_release = subparsers.add_parser(
        "publish-release",
        help="Validate and publish a release bundle to GitHub Releases.",
    )
    pub_release.add_argument(
        "--release-dir", type=Path, required=True, help="Release bundle directory"
    )
    pub_release.add_argument("--repo", default=None, help="GitHub repository (owner/repo)")
    pub_release.add_argument("--token", default=None, help="GitHub authentication token")
    pub_release.add_argument("--draft", action="store_true", help="Publish as draft release")
    pub_release.add_argument("--prerelease", action="store_true", help="Publish as pre-release")
    pub_release.add_argument(
        "--dry-run", action="store_true", help="Simulate publishing without network calls"
    )
    pub_release.add_argument(
        "--public-key", type=Path, default=None, help="Optional Ed25519 public key"
    )
    pub_release.set_defaults(handler=_publish_release)

    # build-catalog
    cat_cmd = subparsers.add_parser(
        "build-catalog",
        help="Build global catalog.json from release metadata files.",
    )
    cat_cmd.add_argument(
        "--metadata-files",
        type=Path,
        nargs="*",
        default=None,
        help="List of local metadata.json files",
    )
    cat_cmd.add_argument(
        "--from-catalog",
        type=Path,
        default=None,
        help="Path to an existing catalog.json to regenerate HTML/CSS/Schemas without rebuilding",
    )
    cat_cmd.add_argument(
        "--fetch-from-github",
        default=None,
        help="GitHub repo (e.g. owner/repo) to fetch published release metadata from directly via API",
    )
    cat_cmd.add_argument(
        "--output", type=Path, default=Path("catalog/catalog.json"), help="Output catalog path"
    )
    cat_cmd.add_argument(
        "--repo", default=None, help="GitHub repo (e.g. owner/repo) to generate download URLs"
    )
    cat_cmd.add_argument("--base-url", default=None, help="Base URL for asset downloads")
    cat_cmd.add_argument(
        "--export-schemas-dir",
        type=Path,
        default=None,
        help="Optional directory to export JSON schemas",
    )
    cat_cmd.set_defaults(handler=_build_catalog)

    # export-schemas
    schema_cmd = subparsers.add_parser(
        "export-schemas",
        help="Export JSON Schema definitions for client Kotlin validation.",
    )
    schema_cmd.add_argument(
        "--output-dir", type=Path, default=Path("schemas"), help="Output directory for schemas"
    )
    schema_cmd.set_defaults(handler=_export_schemas)

    # fetch-boundaries
    fetch_cmd = subparsers.add_parser(
        "fetch-boundaries",
        help="Fetch and update region boundary polygons from Nominatim.",
    )
    fetch_cmd.set_defaults(handler=_fetch_boundaries)

    return parser


def _list_regions(args: argparse.Namespace) -> int:
    if getattr(args, "plain", False):
        for region in REGIONS:
            print(region.name)
        return 0

    table = Table(
        title="Configured Accessible Maps UK Sub-Regions",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Region Identifier", style="bold green")
    table.add_column("Geofabrik Source URL", style="dim")

    for region in REGIONS:
        table.add_row(region.name, region.source_url)

    console.print(table)
    return 0


def _inspect(args: argparse.Namespace) -> int:
    console.print(
        f"[bold blue]Downloading and inspecting region:[/bold blue] [green]{args.region}[/green]"
    )
    prepare_region(args.region, data_dir=args.data_dir)
    return 0


def _generate_delta(args: argparse.Namespace) -> int:
    manifest = create_delta_package(
        target_gpkg=args.target,
        output_dir=args.output_dir,
        base_gpkg=args.base,
        dataset_name=args.dataset_name,
        base_version=args.base_version,
        target_version=args.target_version,
        private_key=args.signing_key,
    )
    table = Table(title="Delta Package Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="green")

    table.add_row("Output Directory", str(args.output_dir))
    table.add_row("Tables Count", str(len(manifest.tables)))
    table.add_row("Total Inserts", f"{manifest.total_inserts:,}")
    table.add_row("Total Updates", f"{manifest.total_updates:,}")
    table.add_row("Total Deletes", f"{manifest.total_deletes:,}")
    table.add_row("Cryptographically Signed", "Yes" if manifest.signature else "No")

    console.print(table)
    return 0


def _apply_delta(args: argparse.Namespace) -> int:
    out = apply_delta_package(
        delta_dir=args.delta_dir,
        output_gpkg=args.output,
        base_gpkg=args.base,
        public_key=args.public_key,
    )
    console.print(f"[bold green]Successfully applied delta to[/bold green] [cyan]{out}[/cyan]")
    return 0


def _verify_delta(args: argparse.Namespace) -> int:
    manifest_path = args.delta_dir / "manifest.json"
    manifest = load_manifest(manifest_path)
    valid, errors = validate_manifest(
        manifest=manifest,
        delta_dir=args.delta_dir,
        public_key=args.public_key,
    )
    if valid:
        console.print(
            "[bold green]Delta package validation successful: all checksums and signatures verified.[/bold green]"
        )
        return 0
    else:
        console.print("[bold red]Delta package validation FAILED:[/bold red]")
        for err in errors:
            console.print(f"  [red]- {err}[/red]")
        return 1


def _generate_keys(args: argparse.Namespace) -> int:
    priv_path, pub_path = save_keypair(args.output_dir, prefix=args.prefix)
    console.print("[bold green]Generated Ed25519 keypair:[/bold green]")
    console.print(f"  [bold]Private Key:[/bold] {priv_path}")
    console.print(f"  [bold]Public Key:[/bold]  {pub_path}")
    return 0


def _package_release(args: argparse.Namespace) -> int:
    metadata, out_dir = package_release(
        target_gpkg=args.target,
        output_dir=args.output_dir,
        dataset_name=args.dataset_name,
        version=args.version,
        base_gpkg=args.base,
        base_version=args.base_version,
        signing_key=args.signing_key,
        optimize_db=not getattr(args, "no_optimize", False),
    )
    console.print(
        f"[bold green]Packaged release bundle[/bold green] [cyan]'{metadata.release_tag}'[/cyan] into {out_dir}:"
    )
    console.print(f"  Assets: {len(metadata.assets)}")
    console.print(f"  Layers: {len(metadata.table_stats)}")
    return 0


def _validate_release(args: argparse.Namespace) -> int:
    valid, errors = validate_release_package(args.release_dir, public_key=args.public_key)
    if valid:
        console.print(
            "[bold green]Release validation successful: metadata, checksums, and signatures verified.[/bold green]"
        )
        return 0
    else:
        console.print("[bold red]Release validation FAILED:[/bold red]")
        for err in errors:
            console.print(f"  [red]- {err}[/red]")
        return 1


def _publish_release(args: argparse.Namespace) -> int:
    res = publish_github_release(
        release_dir=args.release_dir,
        repo=args.repo,
        token=args.token,
        draft=args.draft,
        prerelease=args.prerelease,
        dry_run=args.dry_run,
        public_key=args.public_key,
    )
    if args.dry_run:
        console.print(
            f"[bold yellow]Dry run successful for release {res['release_tag']}.[/bold yellow]"
        )
    else:
        console.print(
            f"[bold green]Published release {res['release_tag']} (URL: {res.get('html_url')}).[/bold green]"
        )
    return 0


def _build_catalog(args: argparse.Namespace) -> int:
    if args.from_catalog:
        if not args.from_catalog.is_file():
            console.print(f"[bold red]Catalog file not found:[/bold red] {args.from_catalog}")
            return 1
        catalog = DatasetCatalog.from_json(args.from_catalog.read_text(encoding="utf-8"))
        console.print(
            f"[bold blue]Loaded existing catalog with {len(catalog.regions)} regions from[/bold blue] [cyan]{args.from_catalog}[/cyan]"
        )
    elif args.fetch_from_github:
        repo = args.fetch_from_github
        console.print(
            f"[bold blue]Fetching release metadata from GitHub repository:[/bold blue] [cyan]{repo}[/cyan]..."
        )
        metadata_list = fetch_github_releases_metadata(repo)
        catalog = DatasetCatalog()
        for meta in metadata_list:
            catalog.add_release(meta, repo=repo, base_download_url=args.base_url)
        console.print(
            f"[bold green]Fetched and aggregated {len(metadata_list)} releases across {len(catalog.regions)} regions.[/bold green]"
        )
    elif args.metadata_files:
        catalog = DatasetCatalog()
        for meta_file in args.metadata_files:
            meta = ReleaseMetadata.from_json(meta_file.read_text(encoding="utf-8"))
            catalog.add_release(meta, repo=args.repo, base_download_url=args.base_url)
    else:
        console.print(
            "[bold red]Must provide either --metadata-files, --from-catalog, or --fetch-from-github.[/bold red]"
        )
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(catalog.to_json(indent=2), encoding="utf-8")
    console.print(
        f"[bold green]Built catalog with {len(catalog.regions)} regions at[/bold green] [cyan]{args.output}[/cyan]"
    )

    html_path = args.output.parent / "index.html"
    write_catalog_html(
        catalog, html_path, repo=args.repo or getattr(args, "fetch_from_github", None)
    )
    console.print(
        f"[bold green]Generated catalog HTML landing page & style.css at[/bold green] [cyan]{html_path}[/cyan]"
    )

    if args.export_schemas_dir:
        exported = export_json_schemas(args.export_schemas_dir)
        console.print(
            f"[bold green]Exported {len(exported)} JSON Schemas to[/bold green] [cyan]{args.export_schemas_dir}[/cyan]"
        )

    return 0


def _export_schemas(args: argparse.Namespace) -> int:
    exported = export_json_schemas(args.output_dir)
    console.print(
        f"[bold green]Exported JSON schemas to[/bold green] [cyan]{args.output_dir}[/cyan]:"
    )
    for name, path in exported.items():
        console.print(f"  - {name} ({path})")
    return 0


def _fetch_boundaries(args: argparse.Namespace) -> int:
    import inspect
    import json
    import time
    import urllib.parse
    import urllib.request

    from . import config

    config_path = Path(inspect.getfile(config))
    console.print(f"[bold blue]Loading regions from[/bold blue] [cyan]{config_path}[/cyan]...")

    boundary_map = {}

    for r in REGIONS:
        name = r.name
        # Build query
        query_name = name.replace("-", " ")
        if name == "scotland":
            query = "Scotland, UK"
        elif name == "wales":
            query = "Wales, UK"
        elif name == "northern-ireland":
            query = "Northern Ireland, UK"
        elif name == "isle-of-man":
            query = "Isle of Man"
        elif name == "guernsey-jersey":
            query = "Channel Islands"
        elif "hull" in name:
            query = "East Riding of Yorkshire, UK"
        else:
            query = f"{query_name}, England, UK"

        url_encoded = urllib.parse.quote(query)
        nominatim_url = f"https://nominatim.openstreetmap.org/search?q={url_encoded}&format=json&limit=1"

        console.print(f"Fetching boundary for [bold cyan]{name}[/bold cyan]...")

        req = urllib.request.Request(
            nominatim_url,
            headers={
                "User-Agent": "AccessibleMaps/1.0 (uk.me.alanamullen.accessiblemaps)"
            }
        )

        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if data:
                    bbox = data[0].get("boundingbox")
                    if bbox and len(bbox) == 4:
                        south, north, west, east = map(float, bbox)
                        poly = [
                            [round(west, 4), round(south, 4)],
                            [round(east, 4), round(south, 4)],
                            [round(east, 4), round(north, 4)],
                            [round(west, 4), round(north, 4)],
                            [round(west, 4), round(south, 4)]
                        ]
                        boundary_map[name] = poly
                        console.print(f"  -> Found: {bbox}")
                    else:
                        console.print(f"[yellow]  -> No bbox for {name}[/yellow]")
                else:
                    console.print(f"[yellow]  -> No results for {name}[/yellow]")
        except Exception as e:
            console.print(f"[red]  -> Error: {e}[/red]")

        time.sleep(1.2)

    new_regions_code = []
    for r in REGIONS:
        name = r.name
        url = r.source_url
        poly = boundary_map.get(name) or [list(pt) for pt in r.boundary]
        if poly:
            poly_str = ", ".join([f"({pt[0]}, {pt[1]})" for pt in poly])
            boundary_code = f"        boundary=({poly_str}),\n"
        else:
            boundary_code = "        boundary=(),\n"

        # Simplify URL using base variables
        if url.startswith("https://download.geofabrik.de/europe/united-kingdom/england/"):
            url_val = 'f"{GEOFABRIK_ENGLAND}/' + url.split("england/")[-1] + '"'
        elif url.startswith("https://download.geofabrik.de/europe/united-kingdom/"):
            url_val = 'f"{GEOFABRIK_UK}/' + url.split("united-kingdom/")[-1] + '"'
        elif url.startswith("https://download.geofabrik.de/europe/"):
            url_val = 'f"{GEOFABRIK_EUROPE}/' + url.split("europe/")[-1] + '"'
        else:
            url_val = f'"{url}"'

        new_regions_code.append(
            f'    Region(\n        "{name}",\n        {url_val},\n{boundary_code}    )'
        )

    regions_joined = ",\n".join(new_regions_code)

    output_content = f"""from __future__ import annotations

from dataclasses import dataclass

from .constants import GEOFABRIK_ENGLAND, GEOFABRIK_EUROPE, GEOFABRIK_UK


@dataclass(frozen=True, slots=True)
class Region:
    name: str
    source_url: str
    boundary: tuple[tuple[float, float], ...] = ()


REGIONS: tuple[Region, ...] = (
{regions_joined},
)


def get_region(name: str) -> Region:
    for region in REGIONS:
        if region.name == name:
            return region
    raise ValueError(f"Unknown region: {{name}}")
"""

    config_path.write_text(output_content, encoding="utf-8")
    console.print(f"[bold green]Updated boundaries for {len(REGIONS)} regions in config.py.[/bold green]")
    return 0


def main() -> int:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
