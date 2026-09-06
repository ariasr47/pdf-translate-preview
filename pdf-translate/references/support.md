# Support and measured limits

Use this engine for visible born-digital text with supported fonts/layouts.
Success is document-specific. Scans and OCR overlays refuse; no general OCR
masking or reflow fallback is implemented. RTL page text requires suitable
fonts, logical text validation and visual inspection. Caption shaping has a
narrower supported route. PDF/UA and tagged accessibility are not promised.
See [simple-form trials](simple-forms.md) for the proposed 1–5 page, at most
50-widget starting scope and its separate qualification requirements.

The 2026-09-05 controlled version-51 stress measurement used 13 available PDFs
(415 pages); four previously blocked USCIS sources remained unavailable. With
deterministic E=1.0 pseudo-localization and four actual Arial font-role files,
three documents reached final verification. Seven stopped during retypesetting,
one during strip and two during final verification. No findings were suppressed.
This is mechanics testing, not human-reviewed translation or a success-rate
estimate for all PDFs. One newly passing case is attributable to corrected
benchmark authoring: the unchanged version-50 runtime passed two cases with the
same corrected instrument, source bytes and fonts. Version 51 additionally
passed W-4 after metadata checks were corrected.

Actual Windows/Python 3.14 fresh-environment Spanish and Arabic synthetic
lifecycles passed. The source-preview CI separately exercises installation and
synthetic checks on its reported OS/Python matrix; those results do not qualify
native viewers or all scripts/layouts. Model-agent traces, mechanical PDF
checks, visual inspection and qualified human review are separate evidence.
Unavailable reviews remain not_performed.

The 2026-09-06 version-54 replay used a smaller frozen subset without changing
its sources or thresholds. It mechanically finalized 3 of 7 available public
documents and 14 of 24 actual-translation synthetic cases. Six synthetic cases
refused during rebuild and four rotated cases refused during initialization.
All 28 passing final pages were pixel-identical to their frozen originals. This
replay is regression evidence, not a replacement for the older 13-document
measurement or a human translation-quality, native-viewer or accessibility
qualification.

The exact Python 3.10 dependency-floor job uses PyMuPDF 1.27.1, pikepdf 10.5.0
and fonttools 4.40.0 and runs a generated-font init/rebuild/finish lifecycle.
Earlier tested PyMuPDF releases either lack or do not honor the ActualText
extraction behavior needed by the Arabic shaping check. Password-protected inputs and pages with
nonzero inherited or direct `/Rotate` values are refused before text stripping.
Version 54 locally qualified this exact minimum set and the Windows Python 3.14
reference set (PyMuPDF 1.28.2, pikepdf 10.13.0.post1 and fonttools 4.64.0).
For version 55, inspect the public Actions run whose head SHA is the exact source
commit being used. The preceding version-54 public CI run is
[34056891624](https://github.com/ariasr47/pdf-translate-preview/actions/runs/34056891624);
it is historical evidence for that earlier commit.
Text used as a clipping path is also refused because removing it would change
page graphics. A source that requires a password refuses; the CLI does not
accept, bypass or recover passwords. Ask the user for an authorized accessible
copy and process that copy as a new input.

The graphics-state fix retained the frozen synthetic 12×12 black square
(144 dark pixels at source, stripped, output and final stages) and the WHO
document's 766 vector paths and paint settings. The earlier silent synthetic
graphics defect did not occur on WHO and should not be attributed to it.

Mixed-script fonts must cover retained source tokens as well as the target
script; `ZX-2048`, for example, requires Latin letters, digits and punctuation.
Version 55 adds repeatable advisory candidate-font comparisons over that full
effective authored text. Candidates are not selected or substituted, and their
coverage does not change the configured-font audit exit status. Unsupported
authored C0/C1 controls now produce contextual QA diagnostics and an early
rebuild refusal. TAB, LF and CR remain allowed. U+00AD SOFT HYPHEN remains in
the authored text and receives a separate discretionary-break warning; it is
not removed or normalized. Occurrence-specific benchmark preservation remains
an open measured limitation; do not weaken font, ink or source-leak gates to
work around it.

Final choice appearance caching supports tested combo/list fields, inherited
fields and quarter-turn rotation. Scrolling lists with nonzero /TI, ambiguous
multi-valued combos and unreproducible labels refuse. Caption reconstruction
supports bounded simple vector normal/pressed/rollover streams at source font
size. Missing source style, unsupported transforms/shaping/whitespace, icons,
complex resource graphs or expansion refuse. Read [widget text](widget-text.md).
Future interactive behavior still requires save/reopen in each claimed viewer.

The two-page, 13-field canary retains all fields and checked identifiers with
zero verification failures and no scaling. Its automated accessibility inventory
still finds five controls without alternate labels, no usable tagged structure
tree and unspecified tab order. No screen-reader, native-viewer or qualified
human review was completed. Mechanical preservation is not accessibility.
