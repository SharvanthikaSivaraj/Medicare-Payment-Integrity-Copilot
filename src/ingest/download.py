"""
Download raw public datasets for the Medicare Payment Integrity Copilot.

Sources
- CMS data.cms.gov catalog (data.json): finds the CSV link for each year of a dataset series
- OIG LEIE exclusion list: providers excluded from federal health programs

Usage (from the repo root, with .venv active):
    python src/ingest/download.py --list                 # show available years
    python src/ingest/download.py --years 2021 2022 2023  # download those years
"""

import argparse
import sys
from pathlib import Path

import requests

RAW_DIR = Path("data/raw")
CATALOG_URL = "https://data.cms.gov/data.json"
LEIE_URL = "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv"

# CMS dataset series we need (exact series titles on data.cms.gov)
CMS_SERIES = {
    "partb_provider": "Medicare Physician & Other Practitioners - by Provider",
    "partd_provider": "Medicare Part D Prescribers - by Provider",
}

# CMS's firewall blocks unusual user agents, so identify as a normal browser.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept": "application/json,text/csv,*/*",
}

# If the catalog can't be fetched automatically, save it here from your browser.
LOCAL_CATALOG = RAW_DIR / "data.json"


def load_catalog() -> list[dict]:
    import json

    if LOCAL_CATALOG.exists():
        print(f"Using saved catalog: {LOCAL_CATALOG}")
        with open(LOCAL_CATALOG) as f:
            return json.load(f)["dataset"]

    print("Fetching CMS catalog (a large JSON file, may take a minute)...")
    resp = requests.get(CATALOG_URL, headers=HEADERS, timeout=300)
    if resp.status_code == 403:
        print(
            "\nCMS blocked the automatic download (403).\n"
            f"Fix: open {CATALOG_URL} in your browser, save the page as\n"
            f"     {LOCAL_CATALOG}  (File > Save As, format 'Page Source'),\n"
            "     then run this script again."
        )
        sys.exit(1)
    resp.raise_for_status()
    LOCAL_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_CATALOG.write_bytes(resp.content)  # cache it for next runs
    return resp.json()["dataset"]


def series_title(dataset: dict) -> str:
    """Series name: from inSeries if present, else the part of the title before ' : '."""
    for s in dataset.get("inSeries", []) or []:
        if s.get("title"):
            return s["title"].strip()
    return dataset.get("title", "").split(" : ")[0].strip()


def csv_links_for_series(catalog: list[dict], name: str) -> dict[int, str]:
    """Return {year: csv_download_url} for one dataset series."""
    links = {}
    for ds in catalog:
        if series_title(ds) != name:
            continue
        temporal = ds.get("temporal") or [{}]
        end = temporal[0].get("endDate", "")
        if not end[:4].isdigit():
            continue
        year = int(end[:4])
        for dist in ds.get("distribution", []):
            url = dist.get("downloadURL", "")
            if dist.get("format") == "CSV" and url.lower().endswith(".csv"):
                links[year] = url
    return dict(sorted(links.items()))


def suggest_names(catalog: list[dict], name: str) -> list[str]:
    words = [w.lower() for w in name.split() if len(w) > 3]
    names = {series_title(d) for d in catalog}
    return sorted(n for n in names if sum(w in n.lower() for w in words) >= 2)[:10]


def download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists): {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"  downloading {url}")
    with requests.get(url, headers=HEADERS, stream=True, timeout=600) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / 1e6:,.0f} / {total / 1e6:,.0f} MB", end="")
    print()
    tmp.rename(dest)
    print(f"  saved {dest} ({dest.stat().st_size / 1e6:,.0f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, nargs="*", help="years to download, e.g. 2021 2022 2023")
    parser.add_argument("--list", action="store_true", help="only list available years")
    args = parser.parse_args()

    catalog = load_catalog()

    available = {}
    for key, name in CMS_SERIES.items():
        links = csv_links_for_series(catalog, name)
        if not links:
            print(f"\nNo CSV files found for series: {name!r}")
            print("Similar series names in the catalog:")
            for s in suggest_names(catalog, name):
                print(f"  - {s}")
            sys.exit(1)
        available[key] = links
        print(f"{key}: years available {list(links)}")

    common = sorted(set.intersection(*(set(v) for v in available.values())))
    print(f"\nYears available in all CMS datasets: {common}")
    if args.list:
        return

    years = args.years or common[-3:]
    print(f"Downloading years: {years}\n")

    for key, links in available.items():
        for year in years:
            if year not in links:
                print(f"  {key} {year}: not available, skipping")
                continue
            download(links[year], RAW_DIR / key / f"{key}_{year}.csv")

    print("\nOIG LEIE exclusion list")
    download(LEIE_URL, RAW_DIR / "leie" / "leie_updated.csv")

    print("\nDone. Next: python src/ingest/to_parquet.py")


if __name__ == "__main__":
    main()
