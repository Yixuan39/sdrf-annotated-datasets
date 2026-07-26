# Bulk LFQ/DIA campaign — extraction columns

One row per screened accession in `metascreen.tsv`. Required columns come first,
then campaign columns. Leave a field as `unknown` only when the source genuinely
does not state it; never guess.

| column | source | notes |
| --- | --- | --- |
| `id` | accession | PXD / MSV / PDC identifier |
| `label` | screening | `include`, `hold`, or `exclude` |
| `reason` | screening | one sentence, states the deciding rule |
| `evidence` | PRIDE, publication | field names or URLs backing the decision |
| `queue` | screening | `Q1`, `Q2`, `Q3`, or empty when excluded |
| `priority_score` | computed | see `criteria.md` |
| `organism` | PRIDE `organisms` | scientific name; `multiple` when more than one |
| `n_files_total` | PRIDE files API | all files in the project |
| `n_raw` | PRIDE files API | vendor acquisition files only |
| `raw_extensions` | PRIDE files API | e.g. `raw`, `wiff`, `d` |
| `acquisition_mode` | PRIDE `experimentTypes`, methods | `DIA`, `DDA`, `mixed`, `unknown` |
| `quant_mode` | PRIDE `quantificationMethods`, methods | `LFQ`, `TMT`, `SILAC`, `unknown` |
| `instruments` | PRIDE `instruments` | semicolon separated |
| `has_pride_metadata_file` | PRIDE files API | `yes` or `no` |
| `has_deposited_sdrf` | PRIDE files API | `yes` when any filename contains `sdrf`; drives queue Q0 |
| `metadata_filenames` | PRIDE files API | deposited SDRF names when present, otherwise up to three companion files |
| `design_complexity` | screening | `simple`, `moderate`, `hard` |
| `estimated_sdrf_rows` | computed | equals `n_raw` for label-free designs |
| `templates` | screening | planned template set, e.g. `ms-proteomics;human;dia-acquisition` |
| `publication` | PRIDE `references` | PMID or DOI, `none_in_pride` if absent |
| `already_annotated` | local repo | `yes` when `datasets/{id}/` exists |
| `notes` | screening | blockers, deferred-file risk, follow-up needed |

## Field rules

- `acquisition_mode` — take `Data-independent acquisition` or
  `Data-dependent acquisition` from `experimentTypes` when present. Otherwise
  search `sampleProcessingProtocol` and `dataProcessingProtocol` for
  `DIA`, `SWATH`, `diaPASEF`, `DDA`, `Spectronaut`, `DIA-NN`, `MaxQuant`.
  Record `unknown` rather than assuming DDA.
- `quant_mode` — treat explicit `TMT`, `iTRAQ`, `SILAC`, or `dimethyl` wording as
  disqualifying under `criteria.md`. `LFQ` requires either the
  `label-free quantification` method or clear label-free wording.
- `design_complexity` —
  - `simple`: one factor with replicates, or a straightforward case/control split;
  - `moderate`: two or three factors, or a time course with a public map;
  - `hard`: condition codes without a dictionary, pooled QC of unclear role, or
    an unreconciled sample-to-run count.
- `templates` — `ms-proteomics` always, plus the organism layer
  (`human`, `vertebrates`, `invertebrates`, `plants`), plus `dia-acquisition`
  when `acquisition_mode` is `DIA`, plus `cell-lines` when the metadata names a
  cell line.
- `already_annotated` — check `datasets/{id}/` in this repository before
  screening, and skip re-screening accessions already promoted.
