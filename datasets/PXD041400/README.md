# PXD041400 — mouse multi-organ proteome, infancy to adulthood (10 organs, DIA)

[PXD041400](https://www.ebi.ac.uk/pride/archive/projects/PXD041400): *The mouse
multi-organ proteome from infancy to adulthood*
([DOI 10.1038/s41467-024-50183-6](https://doi.org/10.1038/s41467-024-50183-6),
*Nat Commun* 2024). Label-free **DIA** on a **Q Exactive HF** of ten organs across
three postnatal ages and both sexes.

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus* (strain **not reported** in archive metadata) |
| Organs (10) | brain, heart, lung, liver, kidney, spleen, stomach, skin, gastrocnemius (muscle), intestine |
| Age | **1 week, 4 week, 8 week** (per sample) |
| Developmental stage | 1w → infant (EFO:0001355); 4w → juvenile stage (UBERON:0034919); 8w → adult (EFO:0001272) |
| Sex | **female and male** (per sample) |
| Replicates | 5 biological replicates (animals) per organ × age × sex |
| Quant | Label-free DIA; Proteome Discoverer + DIA-NN 1.8 |
| Digestion | FASP; trypsin (Biognosys); DTT reduction + iodoacetamide alkylation |
| Instrument | Q Exactive HF (MS:1002523) |
| Factors | `factor value[organism part]` and `factor value[age]` |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | **300** |
| SDRF rows | **300** (1 row per RAW; label-free DIA) |
| Layout | 10 organs × 3 ages × 2 sexes × 5 replicates |

RAW → sample mapping is deterministic from the file names
`{Organ}{age}w_{Sex}_{animal}.raw` (e.g. `Muscle8w_M_3.raw`, `brain_1w_F_5.raw`;
brain/heart/lung use an underscore before the age token, the other organs do not).
The trailing animal number is remapped to a 1–5 biological replicate within each
organ × age × sex group.

## Notes

- This is a genuine **multi-tissue expression atlas** with per-sample age and sex —
  for an adult-only tissue map, filter to the **8-week** rows (100 rows, 10 organs
  × 2 sexes × 5 reps).
- `characteristics[strain or breed]` is `not available` in archive metadata; the
  *Nat Commun* paper can confirm the strain (likely C57BL/6) — refine if needed.
- `comment[precursor/fragment mass tolerance]` left `not available`; recover from
  the raw files with `/sdrf:techrefine`. `comment[dissociation method]` = beam-type
  CID (HCD), standard for Q Exactive HF. PRIDE lists no identified PTMs; the DIA-NN
  default variable Oxidation (M) + fixed Carbamidomethyl (C) from the iodoacetamide
  protocol are annotated.

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD041400/PXD041400.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

Result (OLS cache only): **PASS** — "Everything seems to be fine."
