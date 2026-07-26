#!/usr/bin/env python3
"""Triage submitter-deposited SDRF files for the Q0 fast lane.

`bulk_screen.py` flags a project for Q0 when any deposited filename contains
`sdrf`, which is a filename heuristic and not a guarantee. This script downloads
each candidate and classifies it by the work required before it can be promoted:

    full              usable SDRF; validate, then repair with sdrf-improve
    legacy-case       MAGE-TAB style Title Case headers; normalise then validate
    partial-technical only comment[] columns; the sample section must be authored
    not-sdrf          filename matched but the content is not an SDRF; demote

Downloads are cached, so reruns only fetch new candidates.

Example
-------
    python3 scripts/q0_triage.py --queue docs/bulk-lfq-dia-small/queues/Q0-deposited-sdrf.tsv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "sandbox" / "bulk-lfq-dia-small" / "cache"
DOWNLOAD_DIR = REPO_ROOT / "sandbox" / "bulk-lfq-dia-small" / "deposited"

ANCHOR_COLUMNS = ("source name", "assay name")
DATA_FILE_COLUMNS = ("comment[data file]", "comment[raw file]")

COLUMNS = [
    "id",
    "deposited_file",
    "classification",
    "n_rows",
    "n_columns",
    "n_raw_expected",
    "row_match",
    "has_source_name",
    "has_assay_name",
    "has_data_file",
    "has_template_declaration",
    "missing_core_columns",
    "action",
]

CORE_COLUMNS = (
    "source name",
    "characteristics[organism]",
    "assay name",
    "technology type",
    "comment[data file]",
    "comment[fraction identifier]",
    "comment[technical replicate]",
    "comment[instrument]",
    "comment[label]",
    "comment[sdrf version]",
)

ACTIONS = {
    "full": "validate with parse_sdrf, then sdrf-improve for required columns",
    "legacy-case": "lowercase headers, map Comment[Raw File] to comment[data file], then validate",
    "partial-technical": "author the sample section from PRIDE and the publication, then validate",
    "not-sdrf": "demote to Q1 or Q2; the deposited file is not an SDRF",
    "unavailable": "download failed; retry or demote",
}


def strip_proxies() -> None:
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(key, None)


def download_url(entry: dict) -> str | None:
    for location in entry.get("publicFileLocations") or []:
        value = location.get("value") if isinstance(location, dict) else None
        if not value:
            continue
        if value.startswith("http"):
            return value
        if value.startswith("ftp"):
            return "https://" + value.split("://", 1)[1]
    return None


def fetch(accession: str) -> tuple[str, Path | None]:
    """Return the deposited SDRF-like filename and its local path."""
    cache_file = CACHE_DIR / f"{accession}.files.json"
    if not cache_file.exists():
        return "", None
    try:
        entries = json.loads(cache_file.read_text())
    except json.JSONDecodeError:
        return "", None
    if not isinstance(entries, list):
        return "", None

    candidates = [
        entry
        for entry in entries
        if isinstance(entry, dict) and "sdrf" in (entry.get("fileName") or "").lower()
    ]
    # Prefer a real table over a README-style text file.
    candidates.sort(key=lambda entry: (not entry.get("fileName", "").lower().endswith((".tsv", ".txt", ".csv")),))
    if not candidates:
        return "", None

    entry = candidates[0]
    name = entry["fileName"]
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = DOWNLOAD_DIR / f"{accession}__{name}"
    if destination.exists():
        return name, destination

    url = download_url(entry)
    if not url:
        return name, None
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "sdrf-q0-triage/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            destination.write_bytes(response.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return name, None
    return name, destination


def classify(path: Path) -> tuple[str, list[str], int, int]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unavailable", [], 0, 0

    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return "not-sdrf", [], 0, 0

    header = lines[0].split("\t")
    lowered = [column.strip().lower() for column in header]
    n_rows = len(lines) - 1

    has_anchor = any(column in lowered for column in ANCHOR_COLUMNS)
    has_data_file = any(column in lowered for column in DATA_FILE_COLUMNS)
    has_bracketed = any("[" in column for column in lowered)

    if len(header) < 3 or not has_bracketed:
        return "not-sdrf", lowered, n_rows, len(header)

    original_has_upper = any(column[:1].isupper() for column in header if column.strip())
    if original_has_upper and (has_anchor or has_data_file):
        return "legacy-case", lowered, n_rows, len(header)
    if has_anchor and has_data_file:
        return "full", lowered, n_rows, len(header)
    if has_data_file and not has_anchor:
        return "partial-technical", lowered, n_rows, len(header)
    return "not-sdrf", lowered, n_rows, len(header)


def triage(row: dict) -> dict:
    accession = row["id"]
    result = {column: "" for column in COLUMNS}
    result["id"] = accession
    result["n_raw_expected"] = row.get("n_raw", "")

    name, path = fetch(accession)
    result["deposited_file"] = name
    if not path:
        result.update(classification="unavailable", action=ACTIONS["unavailable"])
        return result

    classification, lowered, n_rows, n_columns = classify(path)
    missing = [column for column in CORE_COLUMNS if column not in lowered]

    expected = row.get("n_raw") or "0"
    result.update(
        classification=classification,
        n_rows=str(n_rows),
        n_columns=str(n_columns),
        row_match="yes" if expected.isdigit() and n_rows == int(expected) else "no",
        has_source_name="yes" if "source name" in lowered else "no",
        has_assay_name="yes" if "assay name" in lowered else "no",
        has_data_file="yes" if any(column in lowered for column in DATA_FILE_COLUMNS) else "no",
        has_template_declaration="yes" if "comment[sdrf template]" in lowered else "no",
        missing_core_columns=";".join(missing) if classification != "not-sdrf" else "",
        action=ACTIONS.get(classification, ""),
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--queue",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "queues" / "Q0-deposited-sdrf.tsv",
        help="Q0 queue TSV produced by bulk_screen.py",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-triage.tsv",
        help="Output TSV path",
    )
    parser.add_argument("--workers", type=int, default=4, help="Parallel downloads (default: 4)")
    args = parser.parse_args()

    strip_proxies()
    rows = list(csv.DictReader(args.queue.open(), delimiter="\t"))
    if not rows:
        print(f"no rows in {args.queue}", file=sys.stderr)
        return 1

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(triage, rows))

    order = {"full": 0, "legacy-case": 1, "partial-technical": 2, "not-sdrf": 3, "unavailable": 4}
    results.sort(key=lambda item: (order.get(item["classification"], 9), item["id"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)

    counts: dict[str, int] = {}
    for item in results:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1
    summary = ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    print(f"triaged {len(results)} Q0 candidates -> {args.out} ({summary})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
