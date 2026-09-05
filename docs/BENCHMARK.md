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
