# PXD019394 — mouse 9-tissue protein expression atlas (Huttlin 2010, expression subset)

[PXD019394](https://www.ebi.ac.uk/pride/archive/projects/PXD019394): *A Tissue-Specific
Atlas of Mouse Protein Phosphorylation and Expression*, Huttlin et al.,
[*Cell* 2010, DOI 10.1016/j.cell.2010.12.001](https://doi.org/10.1016/j.cell.2010.12.001).
Label-free **GeLC-MS** (SDS-PAGE + in-gel trypsin) on an **LTQ Orbitrap Velos** across
nine adult mouse tissues.

This folder annotates the dataset as two SDRFs, mirroring the `-proteome`/`-phosphoproteome`
split used for PXD030983:
- **`PXD019394-expression.sdrf.tsv`** — protein-expression subset (107 raw files).
- **`PXD019394-phosphorylation.sdrf.tsv`** — phosphopeptide-enriched subset (240 raw files),
  with `characteristics[enrichment process] = enrichment of phosphorylated protein`
  (EFO:0010806) and a `Phospho` (UNIMOD:21, S/T/Y) variable modification.

## Design (expression subset)

| Item | Value |
|---|---|
| Organism | *Mus musculus* (strain **not reported** in archive metadata) |
| Developmental stage | **adult** (EFO:0001272) |
| Tissues (9) | brain, brown adipose tissue, heart, kidney, pancreas, spleen, liver, lung, testis |
| Sample structure | one sample per tissue, separated into ~11–12 SDS-PAGE gel fractions (GeLC-MS) |
| Quant | Label-free (spectrum/peptide counting) |
| Digestion | In-gel **trypsin** after SDS-PAGE |
| Instrument | LTQ Orbitrap Velos (MS:1001742) — "LTQ-Velos-Orbitrap" per the processing protocol |
| Acquisition | DDA (shotgun); CID fragmentation |
| Factor | `factor value[organism part]` |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW (total) | 347 |
| Expression RAW | **107** (this SDRF) |
| Phosphorylation RAW | 240 (→ `PXD019394-phosphorylation.sdrf.tsv`) |
| SDRF rows (expression) | **107** (1 row per expression RAW) |
| SDRF rows (phosphorylation) | **240** (1 row per phospho RAW) |

RAW → sample mapping from file names
`{Tissue}_Protein_Expression_{batch}_{tissue}_f{N}_v{id}.RAW`
(e.g. `Heart_Protein_Expression_protein4_heart_f5_v02904.RAW`). All fractions of a
tissue share one `source name`; the `f{N}` token becomes `comment[fraction identifier]`.
Edge cases handled: `liver_..._f1_02858.RAW` (missing `v` prefix) → liver fraction 1;
`Spleen_..._spleenv2_f11_v02999.RAW` → spleen fraction 11, technical replicate 2.

## Fields left as `not available`

- `characteristics[strain or breed]`, `characteristics[age]`, `characteristics[sex]`
  — not reported in archive metadata. (Testis is present, implying male mice for at
  least that tissue; the *Cell* 2010 paper can confirm the cohort — refine if needed.)
- `comment[precursor/fragment mass tolerance]` — not in archive metadata.

`comment[dissociation method]` = CID and mods (Carbamidomethyl fixed / Oxidation
variable) reflect the standard in-gel-digest + LTQ-Velos ion-trap workflow of this era.

## Phosphorylation subset notes

`PXD019394-phosphorylation.sdrf.tsv` covers 240 phosphopeptide-enriched runs across the
same 9 tissues. Fraction handling differs by tissue because the file names are
inconsistent:
- liver / pancreas / testis encode the fraction and replicate
  (`{tissue}_f{N}_{rr}_w#####`, plus one `scx1` variant) → used directly as
  `comment[fraction identifier]` / `comment[technical replicate]`.
- brain, brown fat, heart, kidney, lung, spleen carry only an opaque run id
  (`o#####`), so `comment[fraction identifier]` is assigned by **acquisition order**
  (1…28) and flagged here — the true SCX fraction number is not encoded in the file
  names and should be refined from the paper's supplementary run table if needed.

## Validation

```bash
parse_sdrf validate-sdrf -s datasets/PXD019394/PXD019394-expression.sdrf.tsv \
  -t ms-proteomics -t vertebrates --use_ols_cache_only
parse_sdrf validate-sdrf -s datasets/PXD019394/PXD019394-phosphorylation.sdrf.tsv \
  -t ms-proteomics -t vertebrates --use_ols_cache_only
```

Result (OLS cache only): both **PASS** — "Everything seems to be fine."
