# PXD060109 — adult mouse integral membrane proteome (11 organs/regions)

[PXD060109](https://www.ebi.ac.uk/pride/archive/projects/PXD060109): *Integral membrane
proteome of adult mouse brain and other organs*
([DOI 10.1038/s41467-025-62735-5](https://doi.org/10.1038/s41467-025-62735-5),
*Nat Commun* 2025). Label-free **GeLC-MS** of Na₂CO₃-extracted integral membrane
fractions from adult mouse organs.

## Design

| Item | Value |
|---|---|
| Organism | *Mus musculus*, wild-type (strain **not reported**) |
| Developmental stage | **adult** (EFO:0001272) — stated in the processing protocol |
| Organs / regions (11) | whole brain, forebrain, cerebellum, heart, lung, liver, kidney, spleen, intestine, skeletal muscle, urinary bladder |
| Preparation | Na₂CO₃ (pH 11) extraction of integral membrane proteins → SDS-PAGE → in-gel trypsin (GeLC-MS) |
| Quant | Label-free (MS1 intensity) |
| Acquisition | DDA (bottom-up); Mascot |
| Factor | `factor value[organism part]` |
| Templates | `ms-proteomics` + `vertebrates` (v1.1.0) |

## File coverage

| Set | Count |
|---|---|
| PRIDE RAW | **16** |
| SDRF rows | **16** (1 row per RAW) |

RAW → sample mapping from file names:
- `wt-mouse-{organ}-membrane.raw` → 10 single-run organs (one biological replicate, one fraction each).
- `wt-mouse-whole-brain-membrane-{1,2}_{m,o,u}.raw` → whole brain, **2 biological replicates × 3 gel fractions** (the `m`/`o`/`u` suffix → `comment[fraction identifier]` 1/2/3). The file `intenstine` (sic) is intestine.

## Caveats / fields to confirm

- **Instrument is ambiguous.** PRIDE lists two instruments for this project —
  **Q Exactive HF-X** and **LTQ Orbitrap XL** — and the archive metadata does not
  map runs to instruments. All rows are annotated as **Q Exactive HF-X** (the primary
  instrument); the fractionated whole-brain runs may have used the LTQ Orbitrap XL.
  **Confirm per-run instrument from the *Nat Commun* paper / raw files** (`/sdrf:techrefine`).
- This is a **membrane subproteome** (Na₂CO₃-extracted integral membrane fraction), not
  a whole-tissue lysate — relevant when combining with other tissue-map datasets.
- `characteristics[strain or breed]`, `age`, `sex` are `not available`; `comment[precursor/
  fragment mass tolerance]` `not available`. `comment[dissociation method]` = beam-type
  CID (HCD), standard for Q Exactive HF-X.

## Validation

```bash
parse_sdrf validate-sdrf \
  -s datasets/PXD060109/PXD060109.sdrf.tsv \
  -t ms-proteomics -t vertebrates \
  --use_ols_cache_only
```

Result (OLS cache only): **PASS** — "Everything seems to be fine."
