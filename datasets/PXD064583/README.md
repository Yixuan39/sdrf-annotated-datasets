# PXD064583 — adult mouse 10-organ circadian proteome (DIA)

[PXD064583](https://www.ebi.ac.uk/pride/archive/projects/PXD064583): part of *Mouse Circadian
Proteome Atlas by next-generation deep proteome analysis* (Yoshitane lab; released
2025-11-27). Deep label-free **DIA** on an **Orbitrap Astral** of ten organs in
**adult** mice sampled around the circadian cycle.

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus* (strain **not reported** in archive metadata) |
| Developmental stage | **adult** (EFO:0001272) — mature-organ dissection; no embryonic (`E##`) token, unlike sibling PXD069823/PXD061981 |
| Tissues (10) | kidney, skeletal muscle, pancreas, lung, thymus, thyroid gland, eye, salivary gland, heart, spleen |
| Circadian time | CT2, CT6, CT10, CT14, CT18, CT22 (6 timepoints, 4 h spacing) |
| Replicates | 2 biological replicates per tissue × timepoint (file suffix `_1`/`_2`) |
| Quant | Label-free DIA; Proteome Discoverer + DIA-NN |
| Digestion | Phase-transfer-surfactant (PTS), trypsin (Sigma); DTT reduction + iodoacetamide alkylation |
| Instrument | Orbitrap Astral (MS:1003378) |
| Factors | `factor value[organism part]` and `factor value[sampling time]` (circadian time) |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | **120** |
| SDRF rows | **120** (1 row per RAW; label-free DIA) |
| Layout | 10 tissues × 6 circadian timepoints × 2 replicates |

RAW → sample mapping is deterministic from the file names
`{acq date}_{NN}_DIA_{Tissue}_CT{##}_{rep}.raw`
(e.g. `241016_01_DIA_Kidney_CT2_1.raw`). The leading date/index are acquisition
batch order, not sample properties.

## Fields left as `not available` (need manuscript confirmation)

- `characteristics[strain or breed]`, `characteristics[age]`, `characteristics[sex]`
  — not reported in archive metadata; no resolvable DOI/PMID in the PRIDE record.
- `comment[precursor mass tolerance]`, `comment[fragment mass tolerance]` — DIA
  search tolerances not in archive metadata; recover with `/sdrf:techrefine`.

`comment[dissociation method]` = beam-type CID (HCD), the standard Orbitrap Astral
DIA fragmentation.

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD064583/PXD064583.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

Result (OLS cache only): **PASS with warnings** — only the
`characteristics[sampling time]` circadian values (`CT2`…`CT22`) trip the
`number + hour/day` unit hint; CT notation is retained deliberately.
