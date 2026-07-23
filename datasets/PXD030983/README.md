# PXD030983 — Mass spectrometry-based draft of the mouse proteome

Split SDRFs for [PXD030983](https://www.ebi.ac.uk/pride/archive/projects/PXD030983) (Giansanti et al., *Nat Methods*, PMID 35710609).

## Why not one file / why not 2207 rows?

PRIDE has **2207 RAW** files. They are **not one experiment**:

| Subset | File | Rows | Factor |
|---|---|---|---|
| Healthy tissue proteome (41 tissues, 32 HpH/mixed-mode fractions + bio-reps) | `PXD030983-tissues-proteome.sdrf.tsv` | **1536** | organism part |
| Healthy tissue phosphoproteome (Fe³⁺-IMAC, U01–U04) | `PXD030983-tissues-phosphoproteome.sdrf.tsv` | **328** | organism part |
| Murine PDAC cell-line proteome (66 lines × 4 hpH fractions) | `PXD030983-pdac-proteome.sdrf.tsv` | **264** | cell line |
| Murine PDAC cell-line phosphoproteome | `PXD030983-pdac-phosphoproteome.sdrf.tsv` | **66** | cell line |
| **Annotated total** | | **2194** | |
| Held out | sORF/JPT standards (7) + 6 misc `05070_*` runs | **13** | not atlas samples |

Earlier **1184** was only the first 30 tissues whose `mqpar.xml` we could decompress from a corrupt ProteomicsDB zip. The remaining 11 tissue proteome maps were recovered from `MQ_1percent_FDR_PTR_phosphoPACiFIC.zip` (`Tissues/mqpar.xml` filePaths).

## Drug exposure

There are **no drug-treated MS raw files** in this dataset. Drug/radiation sensitivity assays are **phenotypic** (CellTiter-Glo / proliferation) on the same PDAC panel; responses live in ESM MOESM10 and are correlated with the untreated PDAC proteomes in the paper. Do not invent a `factor value[treatment]` / drug-channel SDRF from those tables.

## Instruments (per PRIDE protocol)

- Tissue proteome + tissue phospho → Q Exactive HF  
- PDAC proteome → Q Exactive HF-X  
- PDAC phospho → Orbitrap Exploris 480  

## Validation

```bash
parse_sdrf validate-sdrf -s datasets/PXD030983/PXD030983-tissues-proteome.sdrf.tsv -t ms-proteomics --use_ols_cache_only
parse_sdrf validate-sdrf -s datasets/PXD030983/PXD030983-tissues-phosphoproteome.sdrf.tsv -t ms-proteomics --use_ols_cache_only
parse_sdrf validate-sdrf -s datasets/PXD030983/PXD030983-pdac-proteome.sdrf.tsv -t ms-proteomics --use_ols_cache_only
parse_sdrf validate-sdrf -s datasets/PXD030983/PXD030983-pdac-phosphoproteome.sdrf.tsv -t ms-proteomics --use_ols_cache_only
```
