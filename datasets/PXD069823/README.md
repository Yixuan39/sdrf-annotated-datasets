# PXD069823 — E17 mouse embryo circadian proteome (brain / heart / lung / liver, DIA)

[PXD069823](https://www.ebi.ac.uk/pride/archive/projects/PXD069823): *Mouse Circadian
Proteome Atlas by next-generation deep proteome analysis* (Yoshitane lab; published
2025-11-27). Deep label-free **DIA** on an **Orbitrap Astral** of four **embryonic day 17
(E17)** mouse organs sampled around the circadian cycle.

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus* (strain **not reported** in archive metadata) |
| Developmental stage | **Embryonic day 17 (E17)** — annotated as `embryo stage` (EFO:0007725) |
| Tissues | brain, heart, lung, liver (embryonic organs) |
| Circadian time | CT2, CT6, CT10, CT14, CT18, CT22 (6 timepoints, 4 h spacing) |
| Replicates | 3 biological replicates per tissue × timepoint (file suffix A/B/C) |
| Quant | Label-free DIA; Proteome Discoverer + DIA-NN |
| Digestion | Phase-transfer-surfactant (PTS) protocol, trypsin (Sigma); reduced (DTT) + alkylated (iodoacetamide) |
| Instrument | Orbitrap Astral (MS:1003378) |
| Factors | `factor value[organism part]` and `factor value[sampling time]` (circadian time) |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | **72** |
| SDRF rows | **72** (1 row per RAW; label-free DIA) |
| Layout | 4 tissues × 6 circadian timepoints × 3 replicates |

RAW → sample mapping is deterministic from the file names:
`{acq date}_E17_{Tissue}_{CT##}{replicate}.raw`
(e.g. `250904_E17_Brain_CT10A.raw`). The leading date is the acquisition date
(brain 250904, heart 250905, lung 250906, liver 250907), not a sample property.
One heart file carries an extra Xcalibur timestamp suffix
(`250905_E17_Heart_CT22C_20250909160329.raw`) and is mapped as heart / CT22 / rep C.

## Why "E17" = embryonic day 17

PRIDE lists no resolvable DOI/PMID for this accession, so the developmental stage
is inferred from the archive file-naming convention across the same lab's sibling
submissions (same PI, same title, same 2025-11-27 release):

- Sibling **PXD061981** uses `E9`, `E13`, `E17` tokens for an explicit embryonic-day
  series (its organism parts include `Embryo`).
- The **adult** whole-body siblings (PXD064583 kidney/muscle, PXD064539
  esophagus/stomach, PXD064534 hypothalamus/olfactory bulb) carry **no** `E##`
  token.

So `E17` here denotes embryonic day 17. EFO offers only E16.5 / E17.5 (no exact
E17.0), so the SDRF uses the general `embryo stage` (EFO:0007725) rather than
asserting a specific half-day. **Refine to `embryonic day 17`/`17.5` once the
manuscript is available.**

## Fields left as `not available` (need manuscript confirmation)

- `characteristics[strain or breed]` — strain not reported in archive metadata.
- `characteristics[age]`, `characteristics[sex]` — not resolvable per sample.
- `comment[precursor mass tolerance]`, `comment[fragment mass tolerance]` — DIA
  search tolerances not in archive metadata; recover with `/sdrf:techrefine` from
  the raw files.

`comment[dissociation method]` is set to beam-type CID (HCD), the standard
Orbitrap Astral DIA fragmentation; confirm via techrefine if needed.

## Sibling accessions (same atlas)

PXD064534 (brain: HYP/OB), PXD069794 & PXD064461 (liver), PXD064583 & PXD064539
(adult whole-body organ pairs), PXD061981 (E9/E13/E17 embryo + adult liver WT/PER2).

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD069823/PXD069823.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

Result (OLS cache only): **PASS with warnings** — the `characteristics[sampling time]`
values use circadian-time notation (`CT2`…`CT22`), which does not match the
`number + hour/day` unit hint. The CT notation is retained deliberately; the check
is warning-level only.
