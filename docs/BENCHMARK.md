# Public-document stress result — 2026-09-05

This sanitized summary records the final local rerun across 17 source entries.
Thirteen documents were available, covering 415 pages. Four USCIS downloads
returned HTTP 403 and remain missing, not passed. No PDFs, font files or private
execution logs are distributed with this summary.

The instrument uses deterministic pseudo-localization at expansion factor 1.0,
full pages and actual local font-role files. It performs final verification
after field-font finalization. It does not assess natural translation, and
human/model translation review was not performed. No thresholds were relaxed
or findings suppressed to obtain these results.

| Document identifier | Pages | Final observed result |
|---|---:|---|
| IRS W-9 | 6 | Final verification failed |
| IRS W-4 | 5 | Final verification failed |
| IRS 1040-ES | 16 | Final verification failed |
| IRS 1040 general instructions | 126 | Retypeset failed |
| USCIS I-9 | — | Missing, HTTP 403 |
| USCIS I-864 | — | Missing, HTTP 403 |
| USCIS N-400 | — | Missing, HTTP 403 |
| USCIS G-28 | — | Missing, HTTP 403 |
| California FL-100 | 3 | Final verification failed |
| California FL-300 | 4 | Final verification failed |
| OPM SF-15 | 2 | Final verification failed |
| State DS-11 | 6 | Retypeset failed |
| FDA 3500 | 8 | Final verification failed |
| EU GDPR | 88 | Retypeset failed |
| BabelDOC paper | 10 | Retypeset failed |
| Medicare handbook | 128 | Retypeset failed |
| Raspberry Pi 4 datasheet | 13 | Final verification passed |

**Result: 1 passed, 12 failed, 4 unavailable.** The denominator for available
documents is 13; the passing case is not a human-reviewed translation.
Source editions and availability can change, so these identifiers are not a
universal claim about every edition of each document.

Fixes allowed W-4 and FDA 3500 to reach final verification. Remaining failures
include caption clipping, metadata and identifier mismatches, untranslated text,
overflow and missing glyph coverage. Progress to a later stage is not completion.
This evidence supports continued development and controlled trials only.
