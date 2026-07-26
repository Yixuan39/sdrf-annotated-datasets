#!/usr/bin/env python3
"""Normalise submitter-deposited SDRFs for the Q0 fast lane.

Applies only deterministic repairs that do not invent biology:

- strip trailing whitespace from headers and cells
- lowercase Title-Case MAGE-TAB headers and map Comment[Raw File]
- fill missing technology type / sdrf version / acquisition method / templates
- capitalise Fixed/Variable in modification MT= fields
- expand common dissociation shorthand (HCD, CID) to PSI-MS preferred labels
- put factor columns last and enforce a safe column order
- replace empty required cells and illegal reserved words with safe defaults

Does not invent organism parts, diseases, factors, or file-to-sample maps.

Example
-------
    python3 scripts/q0_normalize.py \\
        --triage docs/bulk-lfq-dia-small/q0-triage.tsv \\
        --metascreen docs/bulk-lfq-dia-small/metascreen.tsv \\
        --limit 20
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPOSITED = REPO_ROOT / "sandbox" / "bulk-lfq-dia-small" / "deposited"
NORMALIZED = REPO_ROOT / "sandbox" / "bulk-lfq-dia-small" / "normalized"

# Bare labels: the dia-acquisition template rejects the NT=/AC= form.
ACQUISITION = {
    "DIA": "Data-independent acquisition",
    "DDA": "Data-dependent acquisition",
}
TECHNOLOGY = "proteomic profiling by mass spectrometry"
SDRF_VERSION = "v1.1.0"
# Must match base.yaml: NT=name;VV=vX.Y.Z | name vX.Y.Z | manual curation
ANNOTATION_TOOL = "manual curation"

HEADER_ALIASES = {
    "comment[raw file]": "comment[data file]",
    "comment[rawfile]": "comment[data file]",
    "characteristics[strain]": "characteristics[strain or breed]",
}

DISSOCIATION = {
    "hcd": "NT=beam-type collision-induced dissociation;AC=MS:1000422",
    "cid": "NT=collision-induced dissociation;AC=MS:1000133",
    "etd": "NT=electron transfer dissociation;AC=MS:1000598",
    "ecd": "NT=electron capture dissociation;AC=MS:1000250",
}

# Columns that reject not applicable and need a numeric default.
NUMERIC_REQUIRED = {
    "comment[fraction identifier]": "1",
    "comment[technical replicate]": "1",
    "characteristics[biological replicate]": "1",
}

EMPTY_TO_NOT_APPLICABLE = {
    "characteristics[organism part]",
    "characteristics[cell type]",
    "characteristics[disease]",
}

EMPTY_TO_NOT_AVAILABLE = {
    "characteristics[developmental stage]",
    "characteristics[age]",
}

ORGANISM_SYNONYMS = {
    "human": "Homo sapiens",
    "homo sapiens": "Homo sapiens",
    "mouse": "Mus musculus",
    "mus musculus": "Mus musculus",
    "rat": "Rattus norvegicus",
    "yeast": "Saccharomyces cerevisiae",
    "baker's yeast": "Saccharomyces cerevisiae",
    "honeybee": "Apis mellifera",
    "honey bee": "Apis mellifera",
}

SEX_SYNONYMS = {
    "m": "male",
    "f": "female",
    "male": "male",
    "female": "female",
}

LABEL_FREE = "NT=label free sample;AC=MS:1002038"

NA_TOKENS = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
    "not applicable",
    "not available",
    "not_applicable",
    "not_available",
}


def is_missing(value: str) -> bool:
    return value.strip().lower() in NA_TOKENS


def canonical_reserved(value: str) -> str | None:
    token = value.strip().lower()
    if token in {"not applicable", "not_applicable"}:
        return "not applicable"
    if token in {"not available", "not_available", "n/a", "na", "none", "null", "unknown", ""}:
        return "not available"
    return None

ANCHOR_ORDER_PREFIX = [
    "source name",
]
CHARACTERISTIC_PRIORITY = [
    "characteristics[organism]",
    "characteristics[organism part]",
    "characteristics[cell type]",
    "characteristics[disease]",
    "characteristics[cell line]",
    "characteristics[cellosaurus accession]",
    "characteristics[developmental stage]",
    "characteristics[age]",
    "characteristics[sex]",
    "characteristics[strain or breed]",
    "characteristics[material type]",
    "characteristics[biological replicate]",
]
MID_ORDER = [
    "assay name",
    "technology type",
]
COMMENT_PRIORITY = [
    "comment[proteomics data acquisition method]",
    "comment[instrument]",
    "comment[label]",
    "comment[cleavage agent details]",
    "comment[modification parameters]",
    "comment[dissociation method]",
    "comment[fractionation method]",
    "comment[precursor mass tolerance]",
    "comment[fragment mass tolerance]",
    "comment[fraction identifier]",
    "comment[technical replicate]",
    "comment[data file]",
    "comment[sdrf version]",
    "comment[sdrf annotation tool]",
    "comment[sdrf template]",
]


def read_tsv(path: Path) -> tuple[list[str], list[list[str]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    rows = list(csv.reader(text.splitlines(), delimiter="\t"))
    if not rows:
        raise ValueError(f"{path}: empty file")
    return rows[0], rows[1:]


def normalise_header(name: str) -> str:
    cleaned = name.strip().lower()
    return HEADER_ALIASES.get(cleaned, cleaned)


def clean_cell(value: str) -> str:
    return value.strip()


def fix_modification(value: str) -> str:
    return re.sub(r"(?i)MT=(fixed|variable)", lambda m: f"MT={m.group(1).capitalize()}", value)


def fix_dissociation(value: str) -> str:
    compact = re.sub(r"\s+", "", value).lower()
    if compact in DISSOCIATION:
        return DISSOCIATION[compact]
    match = re.fullmatch(r"nt=(hcd|cid|etd|ecd)", compact)
    if match and "ac=" not in compact:
        return DISSOCIATION[match.group(1)]
    return value


ORGANISM_STRUCTURED = {
    "Homo sapiens": "NT=Homo sapiens;AC=NCBITaxon:9606",
    "Mus musculus": "NT=Mus musculus;AC=NCBITaxon:10090",
    "Rattus norvegicus": "NT=Rattus norvegicus;AC=NCBITaxon:10116",
    "Saccharomyces cerevisiae": "NT=Saccharomyces cerevisiae;AC=NCBITaxon:4932",
    "Arabidopsis thaliana": "NT=Arabidopsis thaliana;AC=NCBITaxon:3702",
    "Danio rerio": "NT=Danio rerio;AC=NCBITaxon:7955",
}


def fix_organism(value: str) -> str:
    """Canonicalise common depositor organism synonyms and casing."""
    if not value or value.startswith("NT="):
        return value
    reserved = canonical_reserved(value)
    if reserved:
        return reserved
    synonym = ORGANISM_SYNONYMS.get(value.strip().lower())
    if synonym:
        return ORGANISM_STRUCTURED.get(synonym, synonym)
    tokens = value.split()
    if len(tokens) >= 2 and tokens[0][0].islower():
        tokens[0] = tokens[0].capitalize()
        tokens[1] = tokens[1].lower()
        value = " ".join(tokens)
    return ORGANISM_STRUCTURED.get(value, value)


def fix_label(value: str) -> str:
    if is_missing(value) or value.strip().lower() in {"label free", "label-free", "lfq", "label free sample"}:
        return LABEL_FREE
    if value.strip().lower() == "label free sample":
        return LABEL_FREE
    return value


def fix_sex(value: str) -> str:
    if is_missing(value):
        return "not available"
    return SEX_SYNONYMS.get(value.strip().lower(), value)


def ensure_column(header: list[str], rows: list[list[str]], name: str, value: str) -> None:
    if name in header:
        index = header.index(name)
        for row in rows:
            if not row[index].strip():
                row[index] = value
        return
    header.append(name)
    for row in rows:
        row.append(value)


def set_column(header: list[str], rows: list[list[str]], name: str, value: str) -> None:
    if name in header:
        index = header.index(name)
        for row in rows:
            row[index] = value
        return
    header.append(name)
    for row in rows:
        row.append(value)


def declare_templates(header: list[str], rows: list[list[str]], acquisition_mode: str) -> list[str]:
    """Declare only templates the existing columns can support."""
    present = set(header)
    templates = ["ms-proteomics"]

    organism_values = []
    if "characteristics[organism]" in present:
        index = header.index("characteristics[organism]")
        organism_values = [row[index] for row in rows if row[index]]

    organism_blob = " ".join(organism_values).lower()
    if "homo sapiens" in organism_blob or "ncbitaxon:9606" in organism_blob or organism_blob.strip() in {"human"}:
        templates.append("human")
    elif any(
        token in organism_blob
        for token in (
            "mus musculus",
            "ncbitaxon:10090",
            "rattus",
            "danio",
            "gallus",
            "sus scrofa",
            "bos taurus",
            "oryctolagus",
            "canis",
            "felis",
            "equus",
            "macaca",
        )
    ):
        templates.append("vertebrates")
    elif any(token in organism_blob for token in ("drosophila", "caenorhabditis", "apis ", "ncbitaxon:7460")):
        templates.append("invertebrates")
    elif any(token in organism_blob for token in ("arabidopsis", "oryza", "zea mays", "nicotiana", "ncbitaxon:3702")):
        templates.append("plants")

    if acquisition_mode == "DIA":
        templates.append("dia-acquisition")

    # cell-lines requires Cellosaurus accession; do not declare without it.
    if "characteristics[cell line]" in present and "characteristics[cellosaurus accession]" in present:
        templates.append("cell-lines")

    # Drop any prior template declarations and rewrite cleanly.
    keep = [i for i, name in enumerate(header) if name != "comment[sdrf template]"]
    header[:] = [header[i] for i in keep]
    for row in rows:
        row[:] = [row[i] for i in keep]

    for template in templates:
        header.append("comment[sdrf template]")
        value = f"NT={template};VV={SDRF_VERSION}"
        for row in rows:
            row.append(value)
    return templates


def reorder(header: list[str], rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    factors = [name for name in header if name.startswith("factor value[")]
    characteristics = [name for name in header if name.startswith("characteristics[")]
    comments = [name for name in header if name.startswith("comment[")]
    others = [
        name
        for name in header
        if name not in ANCHOR_ORDER_PREFIX
        and name not in MID_ORDER
        and not name.startswith(("characteristics[", "comment[", "factor value["))
    ]

    ordered: list[str] = []
    for name in ANCHOR_ORDER_PREFIX:
        if name in header:
            ordered.append(name)
    for name in CHARACTERISTIC_PRIORITY:
        if name in characteristics and name not in ordered:
            ordered.append(name)
    for name in characteristics:
        if name not in ordered:
            ordered.append(name)
    for name in MID_ORDER:
        if name in header and name not in ordered:
            ordered.append(name)
    for name in others:
        if name not in ordered:
            ordered.append(name)
    for name in COMMENT_PRIORITY:
        if name == "comment[modification parameters]":
            ordered.extend(n for n in comments if n == name)
        elif name == "comment[sdrf template]":
            ordered.extend(n for n in comments if n == name)
        elif name in comments and name not in ordered:
            ordered.append(name)
    for name in comments:
        if name not in ordered:
            ordered.append(name)
    ordered.extend(name for name in factors if name not in ordered)

    index = {name: i for i, name in enumerate(header)}
    # For repeated names (mods / templates), walk in original order.
    used = {name: 0 for name in header}
    positions: list[int] = []
    for name in ordered:
        occurrences = [i for i, item in enumerate(header) if item == name]
        positions.append(occurrences[used[name]])
        used[name] += 1

    return [header[i] for i in positions], [[row[i] for i in positions] for row in rows]


def fill_required_defaults(header: list[str], rows: list[list[str]]) -> None:
    for index, name in enumerate(header):
        if name in NUMERIC_REQUIRED:
            default = NUMERIC_REQUIRED[name]
            for row in rows:
                if is_missing(row[index]):
                    row[index] = default
        elif name in EMPTY_TO_NOT_APPLICABLE:
            for row in rows:
                if is_missing(row[index]):
                    row[index] = "not applicable"
        elif name in EMPTY_TO_NOT_AVAILABLE:
            for row in rows:
                if is_missing(row[index]):
                    row[index] = "not available"
        elif name == "assay name":
            data_file = header.index("comment[data file]") if "comment[data file]" in header else None
            for row in rows:
                if not row[index]:
                    if data_file is not None and row[data_file]:
                        row[index] = Path(row[data_file]).stem
                    else:
                        row[index] = "not available"
        elif name == "technology type":
            for row in rows:
                if is_missing(row[index]):
                    row[index] = TECHNOLOGY
        elif name == "characteristics[organism]":
            for row in rows:
                row[index] = fix_organism(row[index])
        elif name == "characteristics[sex]":
            for row in rows:
                row[index] = fix_sex(row[index])
        elif name == "comment[label]":
            for row in rows:
                row[index] = fix_label(row[index])
        elif name == "characteristics[age]":
            # Age usually forbids not applicable.
            for row in rows:
                if is_missing(row[index]) or row[index].strip().lower() == "not applicable":
                    row[index] = "not available"


def detect_acquisition(header: list[str], rows: list[list[str]], screen_mode: str) -> str:
    if "comment[proteomics data acquisition method]" in header:
        index = header.index("comment[proteomics data acquisition method]")
        values = {row[index].strip().lower() for row in rows if row[index].strip()}
        if any("independent" in value for value in values):
            return "DIA"
        if any("dependent" in value for value in values):
            return "DDA"
    return screen_mode if screen_mode in {"DIA", "DDA"} else "DDA"


def normalise_file(path: Path, acquisition_mode: str) -> tuple[Path, list[str]]:
    header, rows = read_tsv(path)
    header = [normalise_header(name) for name in header]
    rows = [[clean_cell(cell) for cell in row] for row in rows]

    width = len(header)
    for row in rows:
        if len(row) < width:
            row.extend([""] * (width - len(row)))
        elif len(row) > width:
            del row[width:]

    for index, name in enumerate(header):
        if name == "comment[modification parameters]":
            for row in rows:
                row[index] = fix_modification(row[index])
        elif name == "comment[dissociation method]":
            for row in rows:
                row[index] = fix_dissociation(row[index])

    mode = detect_acquisition(header, rows, acquisition_mode)
    ensure_column(header, rows, "technology type", TECHNOLOGY)
    ensure_column(header, rows, "comment[label]", LABEL_FREE)
    ensure_column(header, rows, "comment[fraction identifier]", "1")
    ensure_column(header, rows, "comment[technical replicate]", "1")
    set_column(header, rows, "comment[sdrf version]", SDRF_VERSION)
    set_column(header, rows, "comment[sdrf annotation tool]", ANNOTATION_TOOL)
    set_column(header, rows, "comment[proteomics data acquisition method]", ACQUISITION[mode])

    templates = declare_templates(header, rows, mode)
    fill_required_defaults(header, rows)
    header, rows = reorder(header, rows)

    NORMALIZED.mkdir(parents=True, exist_ok=True)
    accession = path.name.split("__", 1)[0]
    destination = NORMALIZED / f"{accession}.sdrf.tsv"
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    return destination, templates


def load_metascreen(path: Path) -> dict[str, dict]:
    with path.open() as handle:
        return {row["id"]: row for row in csv.DictReader(handle, delimiter="\t")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--triage",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-triage.tsv",
    )
    parser.add_argument(
        "--metascreen",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "metascreen.tsv",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--classifications", default="full")
    parser.add_argument("--allow-row-mismatch", action="store_true")
    args = parser.parse_args()

    metascreen = load_metascreen(args.metascreen)
    allowed = {item.strip() for item in args.classifications.split(",") if item.strip()}
    with args.triage.open() as handle:
        candidates = list(csv.DictReader(handle, delimiter="\t"))

    selected = []
    for row in candidates:
        if row["classification"] not in allowed:
            continue
        if not args.allow_row_mismatch and row.get("row_match") != "yes":
            continue
        selected.append(row)
    selected.sort(key=lambda row: (int(row["n_rows"] or 0), row["id"]))
    if args.limit:
        selected = selected[: args.limit]

    if not selected:
        print("no candidates matched the selection filters", file=sys.stderr)
        return 1

    report_path = REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-normalize-report.tsv"
    report_rows = []
    for row in selected:
        deposited = DEPOSITED / f"{row['id']}__{row['deposited_file']}"
        if not deposited.exists():
            print(f"missing deposited file for {row['id']}: {deposited}", file=sys.stderr)
            continue
        meta = metascreen.get(row["id"], {})
        path, templates = normalise_file(deposited, acquisition_mode=meta.get("acquisition_mode") or "DDA")
        report_rows.append(
            {
                "id": row["id"],
                "normalized": str(path.relative_to(REPO_ROOT)),
                "templates": ";".join(templates),
                "n_rows": row["n_rows"],
            }
        )
        print(f"normalised {row['id']} templates={';'.join(templates)}", file=sys.stderr)

    with report_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "normalized", "templates", "n_rows"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"wrote {len(report_rows)} normalised SDRFs; report -> {report_path.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
