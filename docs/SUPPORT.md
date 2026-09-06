# Qualification matrix

Prepared 2026-09-06. Experimental supervised source preview; success remains
document-specific. Version 55 adds authored-control diagnostics/refusal and
advisory candidate-font comparisons. Translation and human/viewer scope remain
unqualified.

| Area | Demonstrated evidence and limits |
|---|---|
| Starting scope | Proposed simple-form trials: 1–5 pages, at most 50 widgets, visible born-digital text; all further input and delivery gates apply |
| AcroForm | Automated field/export/geometry and fill round-trip checks; supported cached choices and normal/pressed/rollover captions; no universal interactive-viewer guarantee |
| Windows | Actual Python 3.14 fresh-environment Spanish and Arabic synthetic lifecycle checks passed for version 51 |
| Automated tests | Version 55 development tests passed locally; inspect exact-commit public CI for the exported suite |
| Frozen replay | 3/7 public documents and 14/24 actual-translation synthetic cases mechanically finalized; 6 synthetic rebuild refusals and 4 rotation init refusals; all 28 passing final pages pixel-identical |
| CI | Inspect the Actions run whose head SHA matches the exact source commit. CI does not exercise native viewers |
| Agent host | Prior bounded Windows Claude CLI negative/positive/injection cases passed their recorded scopes; these do not qualify every task or agent host |
| Human linguistic review | Not performed; a paired local canary packet and MQM-based public protocol are prepared |
| Acrobat / Preview / browser | Not performed. Adobe failed at startup before opening the PDF, no macOS viewer is available here, and the attempted local browser PDF route was blocked by tool policy. These are not PDF compatibility results |
| Accessibility | Automated inventory completed; canary lacks five alternate control labels, tags and declared tab order. Keyboard/screen-reader review and conformance remain unestablished |

The same-source two-page canary retains 13 fields, all four checked identifiers
and source text size. Exact-byte final verification passed, with zero QA errors
and one deliberate school-name warning. Both source/final pages were visually
inspected by the model. The recorded version-51 run independently reverified
the sealed PDF without modifying it; version 54 only hash-checked retained
sealed jobs. Human and viewer review categories remain pending.

The preceding version-54 public CI run is
[available here](https://github.com/ariasr47/pdf-translate-preview/actions/runs/34056891624).
It is evidence for that earlier commit; use the exact-commit Actions run for
version 55.
Installation on macOS is not a Preview interaction test. CI archives are build
artifacts, separate from a GitHub Release and from product qualification.

The [controlled benchmark](BENCHMARK.md) now completes 3 of 13 available PDFs;
ten still fail or refuse and four unavailable PDFs are not passes. One change
comes from corrected benchmark authoring, one additional pass from engine
metadata verification. The findings support controlled trials, not general
production readiness or a linguistic quality score.

The frozen version-54 subset replay does not replace that 13-document baseline.
Graphics checks preserved a synthetic 12×12 black square (144 dark pixels) and
the WHO document's 766 vector paths and paint settings. WHO never exhibited the
earlier silent synthetic graphics defect. Text clipping, password-requiring
sources and nonzero page rotation refuse before stripping. The CLI does not
accept, bypass or recover passwords; ask the user for an authorized accessible
copy and process that copy as a new input.

For mixed-script output, configured fonts must cover retained tokens such as
`ZX-2048` as well as the target script. Version 55 can compare repeatable
candidate fonts against the full effective authored text, but it does not select
or replace configured fonts and candidate coverage does not change the audit
exit status. Unsupported authored C0/C1 controls produce contextual QA findings
and an early rebuild refusal; TAB, LF and CR remain allowed. Soft hyphens are
retained and receive a separate discretionary-break warning rather than being
removed or normalized. Occurrence-specific benchmark preservation remains an
open measured limitation. Do not weaken font, ink or leak gates around it.

Record every new result with input/output hashes, exact runtime/environment,
locale, font set, checks, reviewer/app versions and limitations. The
[human](review/human.md), [macOS](review/macos.md) and [viewer](review/viewers.md)
protocols are not signatures or completed reviews. Never weaken a gate, remove
meaning or flatten a required form field to manufacture a successful delivery.
