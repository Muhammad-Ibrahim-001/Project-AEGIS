#!/usr/bin/env python3
"""
==============================================================================
DL3004 DWBI Final Project: Federal Data Sources Downloader
Platform: Databricks Volume / Local Staging Parity
Sources:  EIA-860, EIA-923, EIA-930, EPA CAMPD, EPA-EIA Crosswalk, NOAA ISD
==============================================================================

CLI Tool for downloading federal bulk datasets across 2021-2024:
  - Supports --year (2021..2024), --source (eia860|eia923|eia930|campd|noaa|crosswalk|all)
  - Built-in resume capability (skips existing files unless --force is specified)
  - Computes and logs SHA-256 checksums
  - --test-connection flag probes all endpoints without large payload downloads
  - Gracefully notes authentication requirements (e.g. EPA CAMPD API key)
"""

import os
import sys
import time
import argparse
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root and 03_ETL to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ETL_DIR = PROJECT_ROOT / "03_ETL"
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

import config

DEFAULT_DEST_DIR = PROJECT_ROOT / "02_Data" / "raw_data"

# Federal Bulk Endpoints Catalog
ENDPOINT_CATALOG: Dict[str, Dict[str, Any]] = {
    "crosswalk": {
        "name": "EPA-EIA Power Sector Crosswalk Bridge",
        "url_template": "https://raw.githubusercontent.com/USEPA/camd-eia-crosswalk/master/epa_eia_crosswalk.csv",
        "filename_template": "epa_eia_crosswalk.csv",
        "requires_auth": False,
        "is_annual": False,
        "notes": "Direct CSV linking EPA CAMPD units with EIA generators."
    },
    "noaa_history": {
        "name": "NOAA ISD Weather Station History Master",
        "url_template": "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv",
        "filename_template": "isd-history.csv",
        "requires_auth": False,
        "is_annual": False,
        "notes": "Master list of global ISD weather stations with coordinates."
    },
    "eia860": {
        "name": "EIA-860 Annual Electric Generator Report",
        "url_template": "https://www.eia.gov/electricity/data/eia860/archive/xls/eia860{year}.zip",
        "filename_template": "eia860_{year}.zip",
        "requires_auth": False,
        "is_annual": True,
        "notes": "Annual generator and plant schedules (.zip containing Excel workbooks)."
    },
    "eia923": {
        "name": "EIA-923 Monthly Generation and Fuel Consumption",
        "url_template": "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{year}.zip",
        "filename_template": "f923_{year}.zip",
        "requires_auth": False,
        "is_annual": True,
        "notes": "Monthly generation, fuel consumption, and stocks (.zip containing Excel workbooks)."
    },
    "eia930": {
        "name": "EIA-930 Real-Time Hourly Grid Telemetry",
        "url_template": "https://www.eia.gov/electricity/gridmonitor/knownissues/xls/EIA930_BALANCE_{year}_Jan_Jun.csv",
        "filename_template": "eia930_balance_{year}_jan_jun.csv",
        "requires_auth": False,
        "is_annual": True,
        "notes": "Hourly grid balancing authority demand, generation, and interchange CSV."
    },
    "campd": {
        "name": "EPA CAMPD Hourly Flue-Gas Emissions (CEMS)",
        "url_template": "https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly?year={year}",
        "filename_template": "campd_emissions_{year}.csv",
        "requires_auth": True,
        "is_annual": True,
        "notes": "Hourly smokestack emissions. Bulk portal: https://campd.epa.gov/data/bulk-data-files. API requires 'x-api-key'."
    },
    "noaa": {
        "name": "NOAA ISD Synoptic Hourly Surface Weather",
        "url_template": "https://www.ncei.noaa.gov/pub/data/noaa/{year}/",
        "filename_template": "noaa_isd_{year}/",
        "requires_auth": False,
        "is_annual": True,
        "notes": "Tarball / station-by-station hourly surface observations directory."
    }
}


def compute_sha256(file_path: Path) -> str:
    """Calculates SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def test_endpoint_connection(source_key: str, year: int = 2023) -> Dict[str, Any]:
    """Tests connectivity to an endpoint via an HTTP HEAD / GET probe."""
    spec = ENDPOINT_CATALOG.get(source_key)
    if not spec:
        return {"source": source_key, "status": "UNKNOWN_SOURCE", "code": 0, "auth_required": False}

    url = spec["url_template"].format(year=year)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Project-AEGIS-Downloader/1.0"}

    # Special handling for authenticated endpoints
    if spec["requires_auth"]:
        api_key = os.environ.get("CAMPD_API_KEY") or os.environ.get("EPA_API_KEY")
        if not api_key:
            return {
                "source": source_key,
                "name": spec["name"],
                "url": url,
                "status": "AUTH_REQUIRED",
                "code": 401,
                "auth_required": True,
                "message": "EPA CAMPD API requires CAMPD_API_KEY environment variable (or manual download from https://campd.epa.gov/data/bulk-data-files)."
            }
        headers["x-api-key"] = api_key

    req = urllib.request.Request(url, headers=headers)
    try:
        with fetch_with_retry(req, max_retries=3) as resp:
            code = resp.getcode()
            return {
                "source": source_key,
                "name": spec["name"],
                "url": url,
                "status": "AVAILABLE" if code in [200, 301, 302] else "UNEXPECTED_STATUS",
                "code": code,
                "auth_required": spec["requires_auth"],
                "message": f"HTTP {code} OK"
            }
    except urllib.error.HTTPError as e:
        return {
            "source": source_key,
            "name": spec["name"],
            "url": url,
            "status": "HTTP_ERROR",
            "code": e.code,
            "auth_required": spec["requires_auth"],
            "message": f"HTTP Error {e.code}: {e.reason}"
        }
    except Exception as e:
        return {
            "source": source_key,
            "name": spec["name"],
            "url": url,
            "status": "CONNECTION_FAILED",
            "code": 0,
            "auth_required": spec["requires_auth"],
            "message": str(e)
        }


def fetch_with_retry(req: urllib.request.Request, max_retries: int = 3, initial_backoff: float = 1.0):
    """Executes urllib.request with exponential backoff on HTTP 429/5xx errors."""
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            if e.code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2.0
                continue
            raise


def download_file(
    url: str,
    dest_path: Path,
    limit_bytes: Optional[int] = None,
    force: bool = False
) -> Tuple[bool, str, int]:
    """
    Downloads a remote file with resume capability and optional byte limit.
    Returns: (success: bool, checksum: str, bytes_written: int)
    """
    if dest_path.exists() and not force:
        size = dest_path.stat().st_size
        if size > 0:
            print(f"   [RESUME] Skipping existing file: {dest_path.name} ({size} bytes). Use --force to re-download.")
            return True, compute_sha256(dest_path), size

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Project-AEGIS-Downloader/1.0"}
    req = urllib.request.Request(url, headers=headers)

    temp_path = dest_path.with_name(dest_path.name + ".part")
    bytes_downloaded = 0
    sha = hashlib.sha256()

    try:
        with fetch_with_retry(req, max_retries=3) as resp, open(temp_path, "wb") as out_f:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                if limit_bytes and (bytes_downloaded + len(chunk) > limit_bytes):
                    remaining = limit_bytes - bytes_downloaded
                    out_f.write(chunk[:remaining])
                    sha.update(chunk[:remaining])
                    bytes_downloaded += remaining
                    break
                out_f.write(chunk)
                sha.update(chunk)
                bytes_downloaded += len(chunk)

        if temp_path.exists():
            if dest_path.exists():
                dest_path.unlink()
            temp_path.rename(dest_path)

        checksum = sha.hexdigest()
        return True, checksum, bytes_downloaded
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"   ✗ Download error for {url}: {e}")
        return False, "", 0


def probe_all_endpoints(year: int = 2023) -> List[Dict[str, Any]]:
    """Probes all federal data endpoints and prints a status table."""
    print("====================================================================")
    print(f"PROBING FEDERAL DATA SOURCE ENDPOINTS (Year: {year})")
    print("====================================================================")
    results = []
    for key in ENDPOINT_CATALOG.keys():
        res = test_endpoint_connection(key, year=year)
        results.append(res)
        status_flag = "✓" if res["status"] == "AVAILABLE" else ("!" if res["status"] == "AUTH_REQUIRED" else "✗")
        print(f" {status_flag} [{res['source']:<12}] {res['name']:<45} | Status: {res['status']:<18} | Code: {res['code']}")
        if res.get("message") and res["status"] != "AVAILABLE":
            print(f"    -> Note: {res['message']}")
    print("====================================================================")
    return results


def main():
    parser = argparse.ArgumentParser(description="Download bulk federal power and emissions datasets for 2021-2024.")
    parser.add_argument("--year", type=int, default=2023, choices=[2021, 2022, 2023, 2024], help="Target year")
    parser.add_argument("--source", type=str, default="crosswalk", choices=list(ENDPOINT_CATALOG.keys()) + ["all"], help="Federal source")
    parser.add_argument("--limit", type=int, default=None, help="Maximum bytes to download (for testing)")
    parser.add_argument("--dest-dir", type=str, default=str(DEFAULT_DEST_DIR), help="Target local download directory")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing files")
    parser.add_argument("--test-connection", action="store_true", help="Test endpoint connectivity without downloading")

    args = parser.parse_args()
    dest_dir = Path(args.dest_dir)

    if args.test_connection:
        probe_all_endpoints(year=args.year)
        return

    sources_to_download = list(ENDPOINT_CATALOG.keys()) if args.source == "all" else [args.source]

    print("====================================================================")
    print(f"STARTING BULK DATA DOWNLOAD SUITE (Year: {args.year}, Sources: {sources_to_download})")
    print(f"Destination: {dest_dir}")
    print("====================================================================")

    for src_key in sources_to_download:
        spec = ENDPOINT_CATALOG[src_key]
        if spec["requires_auth"]:
            print(f"\n-> Skipping '{src_key}': {spec['notes']}")
            continue

        url = spec["url_template"].format(year=args.year)
        fname = spec["filename_template"].format(year=args.year)
        target_path = dest_dir / fname

        print(f"\n-> Downloading {spec['name']}...")
        print(f"   URL:  {url}")
        print(f"   Dest: {target_path}")

        success, sha, size = download_file(url, target_path, limit_bytes=args.limit, force=args.force)
        if success:
            print(f"   ✓ Downloaded: {target_path.name} ({size:,} bytes | SHA-256: {sha[:16]}...)")
        else:
            print(f"   ✗ Failed to download {src_key}.")

    print("\n====================================================================")
    print("DOWNLOAD TASK COMPLETE")
    print("====================================================================")


if __name__ == "__main__":
    main()
