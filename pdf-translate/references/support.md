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
