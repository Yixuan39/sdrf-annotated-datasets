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
| `q0-promoted-all.txt` | all Q0 accessions promoted so far |
| `q0-waveN-*.txt` | per-wave candidates / promoted / failed |
| `pre-pr-validation.tsv` | last pre-PR validation of new promotions |

## Scripts

```bash
# Screen a candidate pool (resumable; caches under sandbox/)
python3 scripts/bulk_screen.py --search "data-independent acquisition" --pages 3
python3 scripts/bulk_screen.py --accession-file /tmp/candidates.txt

# Triage Q0 deposited SDRFs
python3 scripts/q0_triage.py --queue docs/bulk-lfq-dia-small/queues/Q0-waveN.tsv

# Deterministic repairs, then validate with parse_sdrf before promoting
python3 scripts/q0_normalize.py --triage docs/bulk-lfq-dia-small/q0-waveN-triage.tsv
python3 scripts/q0_promote.py --from-report docs/bulk-lfq-dia-small/q0-waveN-normalize-report.tsv
```

## Queues

| queue | meaning |
| --- | --- |
| Q0 | submitter deposited an SDRF — import, normalise, validate |
| Q1 | small LFQ/DIA with a public design or sample sheet |
| Q2 | small LFQ/DIA; mapping from filenames |
| Q3 | hold |

## Q0 promotion status

`q0-promoted-all.txt` lists **90** accessions promoted via waves 1–7
(including 6b/7b salvage waves). Each promotion was normalised with
deterministic repairs only (no invented biology) and validated with
`parse_sdrf` before copy into `datasets/`.

Incomplete deposits, not-sdrf files, xlsx-only submissions, and row-map
mismatches are held in the corresponding `q0-wave*-failed.txt` logs.
