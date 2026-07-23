# PXD061609 — TMTpro 10-tissue mouse atlas (SAX + BPRP)

[PXD061609](https://www.ebi.ac.uk/pride/archive/projects/PXD061609): Liu & Paulo, proteomic profiling of ten C57BL/6J mouse tissues with TMTpro multiplexing, SAX peptide partitioning, and BPRP super-fractions on Orbitrap Eclipse + FAIMS (RTS-MS3).

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus* C57BL/6J (Jackson) |
| Tissues | brain, brown fat, heart, kidney, liver, lung, skeletal muscle, spleen, ovaries, testes |
| Labels | Figure 1A: 18 channels (126–135), female then male for paired tissues; ovaries=134C (female); testes=135 (male) |
| Factor | `factor value[organism part]` only (sex is a characteristic) |
| Fractionation | BPRP → 24 super-fractions; SAX partitions encoded as `comment[sample preparation batch]` (`NoSAX` / `HighSalt` / `LowSalt`), not a factor |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

Paper methods text says “16 channels”; **Figure 1A** maps **18** reporter channels (includes 134C and 135). This SDRF follows Figure 1A.

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | 75 |
| KEY.xlsx mapped | 72 |
| SDRF rows | **1296** (= 72 × 18) |
| Held out | `ea12594b.raw`, `ea12620b.raw`, `ea12621b.raw` (re-runs not in KEY; primary `ea12594`, `ea12620`, `ea12621` are included) |

## Age / developmental stage

Mouse age is **not reported** in the manuscript methods used here → `characteristics[age]` and `characteristics[developmental stage]` = `not available`.

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD061609/PXD061609.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

Result (OLS cache only): **PASS with warning** — `C57BL/6J` in `characteristics[strain or breed]` is free text (not an NCBITaxon class). Same pattern as other vertebrate atlas SDRFs.
