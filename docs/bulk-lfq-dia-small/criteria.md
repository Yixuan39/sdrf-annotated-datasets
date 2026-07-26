# Bulk LFQ/DIA small-dataset campaign — screening criteria

Goal: grow the annotated corpus by admitting datasets that can be annotated
correctly and quickly. Optimise for annotations per curator-hour, not for
completeness of any single resource.

A candidate is admitted only when the sample-to-file mapping is recoverable from
public evidence without guessing.

## Decision values

| decision | meaning |
| --- | --- |
| `include` | Ready to annotate now (queue Q1 or Q2) |
| `hold` | Plausible but the run map is not recoverable yet |
| `exclude` | Out of scope for this campaign |

## Fast lane: submitter-deposited SDRF (queue Q0)

When the PRIDE project already contains a file whose name includes `sdrf`, the
submitter has solved the sample-to-file mapping. The work becomes import,
validation, and spec repair rather than annotation from scratch, so the
size ceiling and the multiplexing exclusion below **do not apply** to Q0.

Q0 still requires acquisition files to be present, and the deposited SDRF must
be checked rather than trusted: verify row count against the acquisition files,
resolve every ontology term, and confirm the declared templates. A deposited
SDRF that fails validation is repaired with `sdrf-improve`, not discarded.

## Inclusion rules

Admit when **all** of the following hold.

1. **Size.** At most 48 vendor acquisition files. Prefer 24 or fewer.
   Bruker `.d` acquisitions are directories and are deposited as `run.d.zip`;
   each such archive counts as one acquisition, not as a bundled project.
2. **Label-free quantitation.** Acquisition is LFQ or DIA/SWATH, so one SDRF row
   maps to one acquisition file.
3. **Single organism**, or a host/pathogen pair where each file is unambiguously
   assigned to one organism.
4. **Simple design.** At most three experimental factors and identifiable
   biological replicates.
5. **Recoverable mapping.** Either
   - a design or sample-annotation file is public in the PRIDE project
     (queue **Q1**), or
   - acquisition filenames carry unambiguous condition and replicate tokens
     (queue **Q2**).
6. **Raw files retrievable.** The archive exposes acquisition filenames through
   `https://www.ebi.ac.uk/pride/ws/archive/v3/projects/{ACC}/files/all` or a
   documented repository fallback.
7. **Not already annotated** in `datasets/`.

## Exclusion rules

Exclude when **any** of the following hold.

- Isobaric or metabolic multiplexing (TMT, iTRAQ, SILAC, dimethyl) unless the
  project is at most 6 files **and** a channel-to-sample key is public.
- 100 or more acquisition files, or deep fractionation producing hundreds of runs.
- No vendor acquisition files (search results such as `pep.xml`, `mzid`, `mgf`
  only).
- Benchmark or entrapment mixtures whose "samples" are dilution series of
  standards, unless the user asks for them.
- The number of biological samples in the publication cannot be reconciled with
  the number of acquisitions and no run map exists. Record as `run_map_unresolved`.
- Already present in `datasets/`.

## Hold rules

Use `hold` rather than `exclude` when the science fits but the evidence does not
yet support annotation:

- Condition codes appear in filenames but no dictionary resolves them
  (the honeybee `experimentalDesignTemplate` failure mode).
- A design file exists but is unreadable or paywalled.
- Mixed acquisition modes in one project without a per-file split.

## Metadata companion files that raise priority

Filenames matched case-insensitively in the PRIDE project file list:

```
*sdrf*            *sample*          *design*          *annotation*
*metadata*        experimentalDesignTemplate*         mqpar*
*spectronaut*     *dia-nn*  *diann*  *report*         *.xlsx  *.csv  *.tsv
```

A deposited SDRF or a MaxQuant `experimentalDesignTemplate.txt` is the strongest
signal; a generic `*.csv` under OTHER is weak until inspected.

## Priority score

```
priority_score = size_score + acquisition_score + metadata_score + design_score
```

| component | value |
| --- | --- |
| `size_score` | 3 if ≤ 12 files, 2 if ≤ 24, 1 if ≤ 48, else 0 |
| `acquisition_score` | 2 for DIA or LFQ explicitly declared, 1 if inferred, 0 if unclear |
| `metadata_score` | 3 for deposited SDRF, 2 for design/sample sheet, 1 for weak companion, 0 for none |
| `design_score` | 2 if simple, 1 if moderate, 0 if hard |

Queue assignment:

- **Q0** — `include` with a submitter-deposited SDRF (import and verify)
- **Q1** — `include` with `metadata_score >= 2`
- **Q2** — `include` with `metadata_score < 2` and filename-derived mapping
- **Q3** — `hold`

## Review policy for this campaign

Full adversarial review does not scale to this volume and is reserved for risk.

| tier | applies to | gate |
| --- | --- | --- |
| A | default Q1/Q2 artifacts | `parse_sdrf validate-sdrf` clean plus evidence manifest |
| B | random 5–10 % sample of each wave | full adversarial review |
| C | partial annotations with deferred files, disease claims, or per-sample demographics | full adversarial review, always |

Warnings-only validation may be promoted when the warning is recorded in the
evidence manifest, for example study-specific developmental stage codes that
have no EFO term.
