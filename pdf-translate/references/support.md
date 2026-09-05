# Support and measured limits

The engine is intended for born-digital PDFs with extractable visible text and
supported fonts/layouts. It preserves page geometry and AcroForm structure with
strict gates, but success is document-specific. It refuses image-only scans and
OCR overlays; it does not implement OCR masking or a general reflow fallback.
RTL/shaped scripts require licensed glyph coverage, logical text validation and
visual review. Mirroring is opt-in. PDF/UA/tagged accessibility is not promised.

The 2026-09-05 public-document instrument attempted 17 URLs: 13 were available,
covering 415 pages; four USCIS URLs returned HTTP 403. With the documented
pseudo-localization map, expansion factor 1.0 and four actual Arial role files:
6 stopped at retypesetting, 1 at stripping, 5 at final verification, and 1
completed final verification. No findings were suppressed. This is a pipeline
stress measurement, not evidence of linguistic translation quality or a
17-document success claim. Availability and source bytes can change.

Failures included missing glyphs, overflow and final field/placement findings.
Use this evidence to prioritize layout coverage; do not promise universal
pixel fidelity. Corpus extraction/strip verdicts are narrower tests than an
end-to-end translated delivery. Full measurement logs live with the repository
implementation evidence, outside the portable runtime.

Windows/Python 3.14 was exercised locally during hardening. CI defines other
OS/Python checks; their configuration is not evidence they have run. Proprietary
viewer interaction, fresh external host installation and qualified human review
must be recorded separately when performed. A copied-folder smoke test proves
local runtime independence, not universal host compatibility.


Final choice appearance caching supports tested combo/list fields, inherited
fields and quarter-turn rotation. Scrolling lists with nonzero `/TI`, ambiguous
multi-valued combos or labels the renderer cannot faithfully cache are refused.
This path uses the tested PyMuPDF native wrapper API and requires regression
checks on dependency upgrades. Future viewer interaction remains a separate
qualification from the cached initial appearance.
