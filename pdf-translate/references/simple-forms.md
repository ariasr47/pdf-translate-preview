# Experimental simple-form trials

This is a narrow evaluation scope, not a new compatibility guarantee. Start
with 1–5 pages, at most 50 widget occurrences, visible born-digital text,
ordinary horizontal layout, and text/check/radio/choice controls. Require
licensed font coverage and room for the authored translation. Exclude signed
documents, scans/OCR overlays, unsupported button states or icons, dynamic XFA,
and workflows dependent on scripts or attachments. Ordinary normal-state
captions still need their appearance checks; field count alone predicts no fit.

Run `scripts/pipeline.py audit-form SOURCE.pdf --output JOB/source-audit.json`.
This read-only report inventories language, field names/types/flags, candidate
accessible names, appearances and declared tab order. It omits current values.
Its basic size/text screen does not establish all the limits above. Use `init`
with `--content-policy refuse-active` and inspect the source visually as well.

Qualification is per source version, target locale, font set and final PDF
hash. Require complete mapping and automated gates, inspection of every page,
then entry, selection, checkbox/radio changes, save and reopen in each claimed
viewer. Record application/version and results separately. A macOS CI install
does not qualify Preview; a MuPDF round trip does not qualify Acrobat.

Human bilingual review checks meaning, omissions/additions, terminology,
numbers, protected data, register and instructions in context. Record severity,
location, correction and resolution, and leave reviewer identity/qualification
unfilled until a person actually reviews it. Automated pseudo-localization
measures mechanics and cannot establish translation accuracy.

Accessibility needs a separate review. Tab through every control; confirm
visible focus, logical order and no traps. Use a screen reader to check the
label, role, required/read-only state and changed value. Inspect reading order
and relationships for page content as well as fields. Candidate dictionary
entries are evidence for inspection, not proof of their exposed semantics.
Current retypesetting does not preserve a usable tagged structure tree and
must not be described as PDF/UA compliant or generally accessible.

W3C's [PDF12 technique](https://www.w3.org/WAI/WCAG22/Techniques/pdf/PDF12)
describes form names, roles and values; its
[PDF3 technique](https://www.w3.org/WAI/WCAG22/Techniques/pdf/PDF3) addresses
tab and reading order. These are testing guidance, not a conformance certificate.
