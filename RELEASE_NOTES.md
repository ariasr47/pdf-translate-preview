# 51.0.0 — experimental source preview

Prepared 2026-09-05. This source update does not imply a GitHub Release exists.

Translated pushbuttons now receive checked embedded-font appearances while
preserving supported normal, pressed and rollover states, source font size,
chrome, field identity and actions. Actual cached text, advances and unclipped
ink replace the old approximate width gate. Unsupported whitespace, transforms,
shaping, complex resources and expansion refuse explicitly. Independent review
found and verified fixes for whitespace normalization, horizontal-scale size
loss and repeated resource traversal.

Metadata verification accepts deliberate identity mappings while rejecting
incorrect titles and deleted/reordered outline entries. Source-word checks
retain accented words. URL punctuation differences require review without
silently allowing changed query values or addresses.

New diagnose and audit-form commands provide bounded failure guidance and a
read-only form inventory. Documentation describes recovery, the proposed
simple-form scope and separate accessibility/viewer/human qualifications.
The public source now includes synthetic regressions, source fixture/font
generators, dependency-update configuration, resolved-version artifacts and a
reproducible runtime ZIP workflow. Maintainers still review dependency changes
and refresh the source inventory before merging; no automatic merge is enabled.

Validation: 322 runtime, 15 grader and 17 tooling tests passed; the 10 distributed
public regressions passed locally. Fresh Windows Spanish and Arabic lifecycles
passed. The same-source 13-field canary passed final verification with no
scaling. Its cached Print caption is translated and its originally inert action
remains inert. Human review, actual viewer interaction and accessible structure
remain unqualified. See the [support matrix](docs/SUPPORT.md).

The [controlled public-document run](docs/BENCHMARK.md) completed 3/13 available
PDFs, versus 2/13 on the unchanged old engine with the corrected instrument and
1/13 with the original instrument. Ten available PDFs still fail/refuse; four
sources remain unavailable. No result is a human translation-quality score.

Source only: no private Git history, PDF fixtures, fonts, wheels or raw agent
traces are included. MIT and complete AGPL notices are retained unchanged.
Install the complete pdf-translate directory and use a fresh job and new final
artifact destinations; old sealed delivery evidence must never be edited.
