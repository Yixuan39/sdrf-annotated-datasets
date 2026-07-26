#!/usr/bin/env python3
"""Screen PRIDE projects for the bulk LFQ/DIA small-dataset campaign.

Reads accessions (or discovers them through PRIDE search), fetches project
metadata and the full file list, then scores each candidate against
`docs/bulk-lfq-dia-small/criteria.md` and writes one TSV row per accession.

Responses are cached under the sandbox directory so reruns are cheap and the
screen can be resumed after an interruption.

Examples
--------
    python3 scripts/bulk_screen.py --search "label free" --pages 4 --out docs/bulk-lfq-dia-small/metascreen.tsv
    python3 scripts/bulk_screen.py --accessions PXD012345,PXD023456
    python3 scripts/bulk_screen.py --accession-file candidates.txt --workers 6
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PRIDE_API = "https://www.ebi.ac.uk/pride/ws/archive/v3"
REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "sandbox" / "bulk-lfq-dia-small" / "cache"

RAW_EXTENSIONS = (".raw", ".wiff", ".d", ".raw.gz", ".wiff.gz")
SEARCH_ONLY_EXTENSIONS = (".pep.xml", ".mzid", ".mgf", ".mzml", ".msf", ".dat")

# Bruker `.d` acquisitions are directories, so archives deposit them as
# `run.d.zip`. These are one acquisition per archive, not a bundled project.
PACKED_RAW_PATTERN = re.compile(r"\.(d|raw|wiff)\.(zip|tar|tar\.gz|7z)$", re.IGNORECASE)

METADATA_GLOBS = (
    "*sdrf*",
    "*sample*",
    "*design*",
    "*annotation*",
    "*metadata*",
    "experimentaldesigntemplate*",
    "mqpar*",
    "*spectronaut*",
    "*dia-nn*",
    "*diann*",
)
METADATA_SUFFIXES = (".xlsx", ".xls", ".csv", ".tsv", ".txt")

MULTIPLEX_PATTERNS = (
    r"\btmt\s?pro\b",
    r"\btmt\b",
    r"\bitraq\b",
    r"\bsilac\b",
    r"\bdimethyl\s+label",
    r"\btandem mass tag\b",
)
DIA_PATTERNS = (r"\bdia\b", r"\bswath\b", r"diapasef", r"data[- ]independent")
DDA_PATTERNS = (r"\bdda\b", r"data[- ]dependent", r"\bshotgun\b")
LFQ_PATTERNS = (r"label[- ]free", r"\blfq\b", r"\bibaq\b", r"\bmaxlfq\b")

ORGANISM_TEMPLATE = {
    "homo sapiens": "human",
    "mus musculus": "vertebrates",
    "rattus norvegicus": "vertebrates",
    "danio rerio": "vertebrates",
    "gallus gallus": "vertebrates",
    "sus scrofa": "vertebrates",
    "bos taurus": "vertebrates",
    "drosophila melanogaster": "invertebrates",
    "caenorhabditis elegans": "invertebrates",
    "apis mellifera": "invertebrates",
    "arabidopsis thaliana": "plants",
    "oryza sativa": "plants",
    "zea mays": "plants",
}

COLUMNS = [
    "id",
    "label",
    "reason",
    "evidence",
    "queue",
    "priority_score",
    "organism",
    "n_files_total",
    "n_raw",
    "raw_extensions",
    "acquisition_mode",
    "quant_mode",
    "instruments",
    "has_pride_metadata_file",
    "has_deposited_sdrf",
    "metadata_filenames",
    "design_complexity",
    "estimated_sdrf_rows",
    "templates",
    "publication",
    "already_annotated",
    "notes",
]


def strip_proxies() -> None:
    """EBI blocks the local corporate proxy; screening always goes direct."""
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "http_proxy",
        "https_proxy",
        "ALL_PROXY",
        "all_proxy",
    ):
        os.environ.pop(key, None)


def fetch_json(url: str, timeout: int = 120) -> object | None:
    request = urllib.request.Request(
        url, headers={"User-Agent": "sdrf-bulk-screen/1.0", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def cached_json(name: str, url: str) -> object | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{name}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink()
    payload = fetch_json(url)
    if payload is not None:
        path.write_text(json.dumps(payload))
    return payload


def discover(keyword: str, pages: int, page_size: int) -> list[str]:
    accessions: list[str] = []
    for page in range(pages):
        query = urllib.parse.urlencode(
            {"keyword": keyword, "pageSize": page_size, "page": page, "sortDirection": "DESC"}
        )
        payload = fetch_json(f"{PRIDE_API}/search/projects?{query}")
        records = _search_records(payload)
        if not records:
            break
        for record in records:
            accession = record.get("accession")
            if accession and accession not in accessions:
                accessions.append(accession)
    return accessions


def _search_records(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("_embedded", "content", "list"):
            value = payload.get(key)
            if isinstance(value, dict):
                for nested in value.values():
                    if isinstance(nested, list):
                        return [item for item in nested if isinstance(item, dict)]
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def cv_names(value: object) -> list[str]:
    """PRIDE v3 returns plain strings or CvParam objects depending on the field."""
    names: list[str] = []
    for item in value or []:
        if isinstance(item, dict):
            item = item.get("name") or item.get("value") or item.get("accession") or ""
        text = str(item).strip()
        if text:
            names.append(text)
    return names


def match_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def is_raw(name: str) -> bool:
    lower = name.lower()
    if PACKED_RAW_PATTERN.search(lower):
        return True
    return lower.endswith(RAW_EXTENSIONS) and not lower.endswith(SEARCH_ONLY_EXTENSIONS)


def raw_extension(name: str) -> str:
    packed = PACKED_RAW_PATTERN.search(name.lower())
    if packed:
        return f"{packed.group(1)}.{packed.group(2)}"
    return re.sub(r"\.gz$", "", name.lower()).rsplit(".", 1)[-1]


def is_metadata_companion(name: str) -> bool:
    lower = name.lower()
    if lower.endswith(RAW_EXTENSIONS) or lower.endswith(SEARCH_ONLY_EXTENSIONS):
        return False
    if any(fnmatch.fnmatch(lower, pattern) for pattern in METADATA_GLOBS):
        return True
    return lower.endswith(METADATA_SUFFIXES) and "sdrf" in lower


def metadata_strength(names: list[str]) -> tuple[int, list[str]]:
    """Score companion files: deposited SDRF > design sheet > weak table."""
    matches = [name for name in names if is_metadata_companion(name)]
    if not matches:
        weak = [
            name
            for name in names
            if name.lower().endswith(METADATA_SUFFIXES)
            and not name.lower().endswith(SEARCH_ONLY_EXTENSIONS)
        ]
        return (1, weak[:3]) if weak else (0, [])
    lowered = " ".join(matches).lower()
    if "sdrf" in lowered:
        return 3, matches[:3]
    if any(token in lowered for token in ("design", "sample", "annotation", "metadata", "mqpar")):
        return 2, matches[:3]
    return 1, matches[:3]


def classify_modes(details: dict) -> tuple[str, str]:
    experiment_types = " ".join(cv_names(details.get("experimentTypes"))).lower()
    quant_methods = " ".join(cv_names(details.get("quantificationMethods"))).lower()
    prose = " ".join(
        str(details.get(field) or "")
        for field in ("projectDescription", "sampleProcessingProtocol", "dataProcessingProtocol")
    ).lower()
    keywords = " ".join(cv_names(details.get("keywords"))).lower()
    haystack = f"{experiment_types} {quant_methods} {prose} {keywords}"

    if "data-independent" in experiment_types or match_any(haystack, DIA_PATTERNS):
        acquisition = "DIA"
    elif "data-dependent" in experiment_types or match_any(haystack, DDA_PATTERNS):
        acquisition = "DDA"
    else:
        acquisition = "unknown"

    if match_any(f"{quant_methods} {haystack}", MULTIPLEX_PATTERNS):
        quant = "TMT/iTRAQ/SILAC"
    elif match_any(f"{quant_methods} {haystack}", LFQ_PATTERNS) or acquisition == "DIA":
        quant = "LFQ"
    else:
        quant = "unknown"
    return acquisition, quant


def normalise_organism(name: str) -> str:
    """PRIDE reports names such as 'Arabidopsis thaliana (mouse-ear cress)'."""
    stripped = re.sub(r"\(.*?\)", " ", name).strip().lower()
    tokens = stripped.split()
    return " ".join(tokens[:2]) if len(tokens) >= 2 else stripped


def plan_templates(organisms: list[str], acquisition: str, prose: str) -> str:
    templates = ["ms-proteomics"]
    if len(organisms) == 1:
        layer = ORGANISM_TEMPLATE.get(normalise_organism(organisms[0]))
        if layer:
            templates.append(layer)
    if acquisition == "DIA":
        templates.append("dia-acquisition")
    if "cell line" in prose.lower():
        templates.append("cell-lines")
    return ";".join(templates)


def size_score(n_raw: int) -> int:
    if n_raw == 0:
        return 0
    if n_raw <= 12:
        return 3
    if n_raw <= 24:
        return 2
    return 1 if n_raw <= 48 else 0


def screen(accession: str, max_raw: int) -> dict:
    row = {column: "" for column in COLUMNS}
    row["id"] = accession
    row["already_annotated"] = "yes" if (REPO_ROOT / "datasets" / accession).is_dir() else "no"

    details = cached_json(f"{accession}.details", f"{PRIDE_API}/projects/{accession}")
    if not isinstance(details, dict):
        row.update(label="hold", reason="PRIDE project metadata unavailable", evidence=f"{PRIDE_API}/projects/{accession}")
        return row

    files = cached_json(f"{accession}.files", f"{PRIDE_API}/projects/{accession}/files/all")
    names = [entry.get("fileName", "") for entry in files] if isinstance(files, list) else []

    raws = [name for name in names if is_raw(name)]
    extensions = sorted({raw_extension(name) for name in raws})
    deposited_sdrf = [name for name in names if "sdrf" in name.lower()]
    meta_score, meta_files = metadata_strength(names)
    acquisition, quant = classify_modes(details)
    organisms = cv_names(details.get("organisms"))
    prose = " ".join(
        str(details.get(field) or "")
        for field in ("projectDescription", "sampleProcessingProtocol", "dataProcessingProtocol")
    )
    references = cv_names(details.get("references"))
    pmid = ""
    if references:
        found = re.search(r"pubMed:(\d+)", " ".join(references))
        pmid = f"PMID:{found.group(1)}" if found else "in_pride"

    row.update(
        organism=";".join(organisms) if organisms else "unknown",
        n_files_total=str(len(names)),
        n_raw=str(len(raws)),
        raw_extensions=";".join(extensions),
        acquisition_mode=acquisition,
        quant_mode=quant,
        instruments=";".join(cv_names(details.get("instruments"))),
        has_pride_metadata_file="yes" if meta_score >= 2 else "no",
        has_deposited_sdrf="yes" if deposited_sdrf else "no",
        metadata_filenames=";".join(deposited_sdrf[:3] or meta_files),
        estimated_sdrf_rows=str(len(raws)),
        templates=plan_templates(organisms, acquisition, prose),
        publication=pmid or "none_in_pride",
        evidence=f"PRIDE {PRIDE_API}/projects/{accession}; files/all n={len(names)}",
    )

    complexity = "simple" if len(raws) <= 12 else ("moderate" if len(raws) <= 48 else "hard")
    row["design_complexity"] = complexity
    row["priority_score"] = str(
        size_score(len(raws))
        + (2 if acquisition in {"DIA", "DDA"} and quant == "LFQ" else 1 if quant == "LFQ" else 0)
        + meta_score
        + (2 if complexity == "simple" else 1 if complexity == "moderate" else 0)
    )

    archives = [name for name in names if name.lower().endswith((".zip", ".tar", ".tar.gz", ".7z"))]

    if row["already_annotated"] == "yes":
        row.update(label="exclude", reason="Already annotated in datasets/")
    elif deposited_sdrf and raws:
        # The submitter already solved the sample-to-file mapping; this becomes an
        # import-and-verify job rather than annotation from scratch, so the size
        # ceiling and the multiplexing rule do not apply.
        row.update(
            label="include",
            queue="Q0",
            reason="Submitter deposited an SDRF in PRIDE; import, validate, and improve",
            notes=f"deposited: {';'.join(deposited_sdrf[:3])}",
        )
    elif not raws and archives:
        row.update(
            label="hold",
            reason="Acquisition files are bundled inside archives and are not listed individually",
            notes=f"{len(archives)} archive(s); inspect the FTP listing before annotating",
        )
    elif not raws:
        row.update(label="exclude", reason="No vendor acquisition files in the archive")
    elif quant == "TMT/iTRAQ/SILAC" and len(raws) > 6:
        row.update(label="exclude", reason="Isobaric or metabolic multiplexing above the 6-file exception")
    elif len(raws) > max_raw:
        row.update(label="exclude", reason=f"{len(raws)} acquisition files exceeds the {max_raw}-file ceiling")
    elif quant == "unknown" and acquisition == "unknown":
        row.update(label="hold", reason="Neither acquisition nor quantitation mode could be determined")
    elif meta_score >= 2:
        row.update(label="include", queue="Q1", reason="Small label-free project with a public design or sample sheet")
    else:
        row.update(
            label="include",
            queue="Q2",
            reason="Small label-free project; mapping must come from acquisition filenames",
            notes="Verify filename tokens resolve condition and replicate before annotating",
        )
    if row["label"] == "hold" and not row["queue"]:
        row["queue"] = "Q3"
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--accessions", help="Comma-separated accession list")
    source.add_argument("--accession-file", type=Path, help="File with one accession per line")
    source.add_argument("--search", help="PRIDE keyword search used to discover candidates")
    parser.add_argument("--pages", type=int, default=2, help="Search pages to pull (default: 2)")
    parser.add_argument("--page-size", type=int, default=100, help="Results per search page (default: 100)")
    parser.add_argument("--max-raw", type=int, default=48, help="Acquisition-file ceiling (default: 48)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel screens (default: 4)")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "metascreen.tsv",
        help="Output TSV path",
    )
    parser.add_argument(
        "--queues-dir",
        type=Path,
        default=None,
        help="Directory for per-queue TSVs (default: <out parent>/queues)",
    )
    args = parser.parse_args()

    strip_proxies()

    if args.accessions:
        accessions = [item.strip() for item in args.accessions.split(",") if item.strip()]
    elif args.accession_file:
        accessions = [line.strip() for line in args.accession_file.read_text().splitlines() if line.strip()]
    else:
        accessions = discover(args.search, args.pages, args.page_size)
        print(f"discovered {len(accessions)} accessions for {args.search!r}", file=sys.stderr)

    if not accessions:
        print("no accessions to screen", file=sys.stderr)
        return 1

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda acc: screen(acc, args.max_raw), accessions))

    rows.sort(key=lambda row: (row["label"] != "include", -int(row["priority_score"] or 0), row["id"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    queues_dir = args.queues_dir or args.out.parent / "queues"
    queues_dir.mkdir(parents=True, exist_ok=True)
    queue_names = {
        "Q0": "Q0-deposited-sdrf.tsv",
        "Q1": "Q1-ready.tsv",
        "Q2": "Q2-filename-map.tsv",
        "Q3": "Q3-hold.tsv",
    }
    for queue, filename in queue_names.items():
        members = [row for row in rows if row["queue"] == queue]
        with (queues_dir / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(members)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["label"]] = counts.get(row["label"], 0) + 1
    summary = ", ".join(f"{label}={count}" for label, count in sorted(counts.items()))
    queue_summary = ", ".join(
        f"{queue}={sum(1 for row in rows if row['queue'] == queue)}" for queue in queue_names
    )
    print(f"screened {len(rows)} accessions -> {args.out} ({summary})", file=sys.stderr)
    print(f"queues -> {queues_dir} ({queue_summary})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
