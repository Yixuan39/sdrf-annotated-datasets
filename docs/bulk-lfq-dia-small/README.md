# Bulk LFQ / DIA small-dataset campaign

Branch: `datasets/bulk-lfq-dia-small`

Grow the annotated corpus by importing small label-free projects, preferring
those that already ship an SDRF or a design sheet in PRIDE.

## Layout

| path | role |
| --- | --- |
| `criteria.md` | admission rules and review tiers |
| `extract.md` | metascreen column definitions |
| `metascreen.tsv` | screened candidates |
| `queues/` | Q0–Q3 work queues |
| `q0-triage.tsv` | deposited-SDRF content classification |
| `q0-normalize-report.tsv` | last normaliser run |
| `q0-wave1-promoted.txt` | accessions promoted in wave 1 |

## Scripts

```bash
# Screen a candidate pool (resumable; caches under sandbox/)
python3 scripts/bulk_screen.py --search "data-independent acquisition" --pages 3
python3 scripts/bulk_screen.py --accession-file /tmp/candidates.txt

# Triage Q0 deposited SDRFs
python3 scripts/q0_triage.py

# Deterministic repairs, then validate with parse_sdrf before promoting
python3 scripts/q0_normalize.py --limit 20
```

## Queues

| queue | meaning |
| --- | --- |
| Q0 | submitter deposited an SDRF — import, normalise, validate |
| Q1 | small LFQ/DIA with a public design or sample sheet |
| Q2 | small LFQ/DIA; mapping from filenames |
| Q3 | hold |

## Wave 1 result

First Q0 wave promoted validation-clean SDRFs into `datasets/`. See
`q0-wave1-promoted.txt`. Failures that need curator attention stay in
`q0-wave1-failed.txt` or are skipped when the deposited file is incomplete.
