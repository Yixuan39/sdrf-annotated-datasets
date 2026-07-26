#!/usr/bin/env python3
"""Validate normalised Q0 SDRFs and promote clean ones into datasets/.

Example
-------
    python3 scripts/q0_promote.py --from-report docs/bulk-lfq-dia-small/q0-normalize-report.tsv
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def strip_proxies() -> None:
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        os.environ.pop(key, None)


def templates_from_file(path: Path) -> list[str]:
    with path.open() as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows:
        return ["ms-proteomics"]
    header, first = rows[0], rows[1]
    values = []
    for index, name in enumerate(header):
        if name != "comment[sdrf template]":
            continue
        value = first[index]
        if value.startswith("NT="):
            values.append(value.split(";", 1)[0][3:])
        elif value:
            values.append(value.split()[0])
    return values or ["ms-proteomics"]


def validate(path: Path, templates: list[str]) -> list[str]:
    command = ["parse_sdrf", "validate-sdrf", "-s", str(path)]
    for template in templates:
        command.extend(["-t", template])
    process = subprocess.run(command, capture_output=True, text=True)
    output = f"{process.stdout}\n{process.stderr}"
    return [line for line in output.splitlines() if line.startswith("ERROR:")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-report",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-normalize-report.tsv",
    )
    parser.add_argument(
        "--promoted-list",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-wave2-promoted.txt",
    )
    parser.add_argument(
        "--failed-list",
        type=Path,
        default=REPO_ROOT / "docs" / "bulk-lfq-dia-small" / "q0-wave2-failed.txt",
    )
    parser.add_argument("--skip-existing", action="store_true", default=True)
    args = parser.parse_args()

    strip_proxies()
    rows = list(csv.DictReader(args.from_report.open(), delimiter="\t"))
    promoted: list[str] = []
    failed: list[tuple[str, str]] = []

    for row in rows:
        accession = row["id"]
        destination = REPO_ROOT / "datasets" / accession / f"{accession}.sdrf.tsv"
        if args.skip_existing and destination.exists():
            print(f"SKIP {accession} (already in datasets/)", file=sys.stderr)
            continue
        path = REPO_ROOT / row["normalized"]
        if not path.exists():
            failed.append((accession, "normalized file missing"))
            print(f"FAIL {accession}: normalized file missing", file=sys.stderr)
            continue
        templates = templates_from_file(path)
        # Incomplete deposited SDRFs often lack instrument/cleavage; skip inventing them.
        with path.open() as handle:
            header = next(csv.reader(handle, delimiter="\t"))
        required = {"comment[instrument]", "comment[label]", "comment[data file]", "source name", "assay name"}
        missing = sorted(required - set(header))
        if missing:
            failed.append((accession, f"missing columns: {', '.join(missing)}"))
            print(f"SKIP {accession}: missing {missing}", file=sys.stderr)
            continue

        errors = validate(path, templates)
        if errors:
            failed.append((accession, errors[0]))
            print(f"FAIL {accession} ({len(errors)} errors)", file=sys.stderr)
            for error in errors[:4]:
                print(f"  {error}", file=sys.stderr)
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        promoted.append(accession)
        print(f"PROMOTE {accession} -> {destination.relative_to(REPO_ROOT)}", file=sys.stderr)

    args.promoted_list.write_text("\n".join(promoted) + ("\n" if promoted else ""))
    args.failed_list.write_text("\n".join(f"{acc}\t{reason}" for acc, reason in failed) + ("\n" if failed else ""))
    print(f"promoted={len(promoted)} failed={len(failed)}", file=sys.stderr)
    return 0 if not failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
