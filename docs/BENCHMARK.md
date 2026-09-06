# Public-document stress measurement — version 51

On 2026-09-05, 13 available documents covered 415 pages. Four USCIS inputs
remained unavailable (the preceding fetch returned HTTP 403); this run did not
refetch them. No source PDF or font binaries are distributed here.

The instrument uses deterministic pseudo-localization at expansion factor 1.0,
full pages and four explicit local Arial role files. It tests mechanical
behavior, not natural translation or human review. No gates were weakened.

| Instrument and runtime | Final verified / available |
|---|---:|
| Previous instrument, version 50 | 1 / 13 |
| Corrected instrument, unchanged version 50 | 2 / 13 |
| Same corrected instrument, version 51 | 3 / 13 |

The corrected instrument preserves hyphenated form codes, source spacing and
quoted operational spans across extracted lines. W-9 passes on the unchanged
engine with that correction; it is not counted as an engine improvement. W-4
additionally passes on version 51 after metadata identity verification is fixed.
The control and final run used identical PDF and font hashes.

Instrument SHA256: `b452947f5276f3f15fad5a10481bb84f721cb282d3dbb7dcbf8bccb5812d8def`.

| Source identifier | Pages | Observed result |
|---|---:|---|
| irs-w9.pdf | 6 | Final verification passed |
| irs-w4.pdf | 5 | Final verification passed |
| irs-1040es.pdf | 16 | Final verification failed |
| irs-i1040gi.pdf | 126 | Retypeset refused |
| uscis-i9.pdf | — | Unavailable; not refetched |
| uscis-i864.pdf | — | Unavailable; not refetched |
| uscis-n400.pdf | — | Unavailable; not refetched |
| uscis-g28.pdf | — | Unavailable; not refetched |
| cajc-fl100.pdf | 3 | Retypeset refused |
| cajc-fl300.pdf | 4 | Retypeset refused |
| opm-sf15.pdf | 2 | Final verification failed |
| state-ds11.pdf | 6 | Retypeset refused |
| fda-3500.pdf | 8 | Strip refused |
| eu-gdpr.pdf | 88 | Retypeset refused |
| arxiv-babeldoc.pdf | 10 | Retypeset refused |
| medicare-handbook.pdf | 128 | Retypeset refused |
| rpi4-datasheet.pdf | 13 | Final verification passed |

**Result: 3 passed, 10 refused/failed, 4 unavailable.**

Failure stages: seven retypeset, one strip, and two final-verification stops.
Caption expansion and unsupported source style/transform cases now stop before
an unchecked output is delivered. Other findings include missing glyphs,
page-text overflow and retained source phrases needing contextual disposition.
A gate failure is not automatically a proven translation defect: quoted
operational wording can conflict with source-language leak checks and needs
explicit review. No such findings were suppressed in this measurement.

This small convenience corpus does not establish a population success rate,
accessibility, native viewer compatibility or human-reviewed translation quality.

## Follow-up investigation

Reverification reproduced the seven IRS 1040-ES and two OPM SF15 leak findings.
The authored mappings deliberately retain these strings. The Treasury payee
and SF15 document title/status have operational context; the quoted USPS rule
label is explanatory wording. Quotation alone does not settle whether words
should stay in the source language.

The instrument also has a confirmed authoring defect: it promotes split quoted
fragments into a document-wide protection list. A wrapped payee contributes
`United`, which then survives in unrelated privacy-notice prose. Future
instrument authoring should bind preservation to the actual page and segment
occurrences. Do not add blanket candidate exemptions or global token allowlists
to improve the score. Any new measurement must record a changed instrument
hash separately from runtime changes.

The existing 3/13 result and archived outputs remain unchanged. This
investigation is not a new translation qualification.

## Version 54 frozen subset replay

On 2026-09-06, the unchanged frozen seven-document subset again produced three
mechanically finalized outputs. The separate 24-case actual-translation
synthetic set produced 14 finals, 6 rebuild refusals and 4 early rotation
refusals. All 28 pages from passing finals were pixel-identical to the frozen
originals. The WHO case retained 766 vector paths and matching paint settings.

This replay used unchanged sources and thresholds. It is regression evidence
for this subset and does not change the historical 3/13 measurement, establish
a population success rate, or add human, native-viewer or accessibility review.
Document-global fragment protection remains an authoring limitation; future
work should preserve source content by exact occurrence where appropriate.
