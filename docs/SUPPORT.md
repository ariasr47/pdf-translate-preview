# Qualification matrix

Prepared 2026-09-05. Experimental source preview; success remains document-specific.
Version 52 adds diagnostic robustness; translation and human/viewer scope remain
the version-51 measurements. Public diagnostics tests run in the CI matrix.

| Area | Demonstrated evidence and limits |
|---|---|
| Starting scope | Proposed simple-form trials: 1–5 pages, at most 50 widgets, visible born-digital text; all further input and delivery gates apply |
| AcroForm | Automated field/export/geometry and fill round-trip checks; supported cached choices and normal/pressed/rollover captions; no universal interactive-viewer guarantee |
| Windows | Actual Python 3.14 fresh-environment Spanish and Arabic synthetic lifecycle checks passed for version 51 |
| Automated tests | 326 development runtime tests, 15 canary-grader tests, 17 tooling tests; 18 public synthetic tests are distributed and pass locally |
| CI | The preceding public version-50 commit passed six OS/Python installation/init jobs. The updated workflow adds public regressions and reproducible runtime archives; see the actual commit's Actions results before claiming it passed |
| Agent host | Prior bounded Windows Claude CLI negative/positive/injection cases passed their recorded scopes; these do not qualify every task or agent host |
| Human linguistic review | Not performed; a paired local canary packet and MQM-based public protocol are prepared |
| Acrobat / Preview / browser | Not performed. Adobe failed at startup before opening the PDF, no macOS viewer is available here, and the attempted local browser PDF route was blocked by tool policy. These are not PDF compatibility results |
| Accessibility | Automated inventory completed; canary lacks five alternate control labels, tags and declared tab order. Keyboard/screen-reader review and conformance remain unestablished |

The same-source two-page canary retains 13 fields, all four checked identifiers
and source text size. Exact-byte final verification passed, with zero QA errors
and one deliberate school-name warning. Both source/final pages were visually
inspected by the model. The final runtime independently reverified the sealed
PDF without modifying it. Its human and viewer review categories remain pending.

The preceding public CI run is
[available here](https://github.com/ariasr47/pdf-translate-preview/actions/runs/33983017600).
Installation on macOS is not a Preview interaction test. CI archives are build
artifacts, separate from a GitHub Release and from product qualification.

The [controlled benchmark](BENCHMARK.md) now completes 3 of 13 available PDFs;
ten still fail or refuse and four unavailable PDFs are not passes. One change
comes from corrected benchmark authoring, one additional pass from engine
metadata verification. The findings support controlled trials, not general
production readiness or a linguistic quality score.

Record every new result with input/output hashes, exact runtime/environment,
locale, font set, checks, reviewer/app versions and limitations. The
[human](review/human.md), [macOS](review/macos.md) and [viewer](review/viewers.md)
protocols are not signatures or completed reviews. Never weaken a gate, remove
meaning or flatten a required form field to manufacture a successful delivery.
