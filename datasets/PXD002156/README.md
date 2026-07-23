# PXD002156 — Mouse brain / liver / skeletal muscle glycolysis proteomes (LFQ)

[PXD002156](https://www.ebi.ac.uk/pride/archive/projects/PXD002156): Wiśniewski, Gizak & Rakus, *J Proteome Res* 2015 ([PMID 26080680](https://pubmed.ncbi.nlm.nih.gov/26080680/), [DOI 10.1021/acs.jproteome.5b00276](https://doi.org/10.1021/acs.jproteome.5b00276)). Label-free MED-FASP proteomics of adult Swiss white mouse **brain**, **liver**, and **skeletal muscle** for glycolytic/gluconeogenic enzyme titers (Q Exactive, DDA).

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus* (Swiss white), adult |
| Tissues | brain (sample 94), liver (95), skeletal muscle (97) |
| Quant | Label-free; MaxQuant 1.2.6.20 + Total Protein Approach |
| Digestion | MED-FASP: Lys-C then trypsin (separate LC–MS fractions) |
| Factor | `factor value[organism part]` only |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

RAW→tissue mapping is from the deposited MaxQuant `experimentalDesignTemplate.txt` (`B*`/`L*`/`M*` experiment codes). Filename `_L_` / `_T_` match Lys-C / Trypsin (confirmed in `summary.txt` Protease column).

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | **18** |
| SDRF rows | **18** (1 row per RAW; LFQ) |
| Tech reps × tissues | 3 tissues × 3 tech reps × 2 enzyme fractions |
| Not in SDRF | `Glycolysisupload.zip` (SEARCH only) |

Muscle Lys-C tech-rep 3 is absent from the archive; June `97_L_1`/`97_L_2` supply Lys-C for muscle tech reps 2 and 3.

## Demographics

- Developmental stage: **adult** (cohort-level; paper Methods)
- Age / sex: **not available** (not reported per sample)
- Strain: free text **Swiss white** (paper); no NCBITaxon strain class used

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD002156/PXD002156.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```
