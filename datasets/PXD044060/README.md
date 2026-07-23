# PXD044060 — Ribosomal protein signature in adult mouse organs

[PXD044060](https://www.ebi.ac.uk/pride/archive/projects/PXD044060): Brunchault et al., label-free proteomics of **sucrose-cushion purified ribosomal fractions** from 14 adult C57BL/6J mouse tissues (Q Exactive HF, DDA top20 HCD).

## Status: MAPPED

| Item | Value |
|---|---|
| Organism | *Mus musculus* C57BL/6J |
| Material analyzed | Ribosomal fraction (not whole-tissue lysate) |
| Tissues | 14 × 3 biological replicates = **42** RAW files |
| Factor | `factor value[organism part]` |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## RAW → tissue mapping

Instrument sample names were recovered from Thermo RAW UTF-16 metadata (pattern `190628_<FrenchTissue>_<rep>_333ng`):

| Xcalibur code | Organism part |
|---|---|
| Rein | kidney |
| Retine | retina |
| Poumon | lung |
| Hippo | hippocampus |
| Rate | spleen |
| Coeur | heart |
| muscle | skeletal muscle tissue |
| testis | testis |
| Cortex | cerebral cortex |
| Intestin | small intestine |
| Cervelet | cerebellum |
| Glandes | adrenal gland |
| Foie | liver |
| BO | olfactory bulb |

Full table: `sandbox/PXD044060/raw_tissue_map.tsv`.

Muscle and testis use Xcalibur replicate labels **1, 2, 4** (not 1–3); SDRF `characteristics[biological replicate]` keeps those labels.

## Annotation notes

- **Enrichment:** `characteristics[material type]=tissue` (allowed SDRF vocabulary) while source/assay names and this README state the assayed material is the ribosomal pellet after subcellular fractionation.
- **Sex:** testis → `male`; all other tissues → `not available` (paper: mixed male/female, not per-file).
- **Age / stage:** methods report 4–6 week-old adult mice; SDRF uses `6W` (standard age unit) plus developmental stage `adult` (EFO:0001272).
- **Mods / search:** carbamidomethyl (C, fixed); acetyl (protein N-term, variable); oxidation (M, variable); Trypsin; 10 ppm / 25 mmu.

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD044060/PXD044060.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

## Enrichment

Assays are sucrose-cushion **ribosomal fractions** (`characteristics[cell part]=ribosome GO:0005840`; `characteristics[enrichment process]=density-gradient centrifugation CHMO:0002017`), not whole-tissue lysates.
