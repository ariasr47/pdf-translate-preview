# Onboarding maintenance (runtime version 55 unchanged)

Adds a feature table, a complete source-generated Spanish form tutorial, and
Codex/Claude Code installation paths. Public tests execute the documented tutorial,
exercise field save/reopen and overwrite refusal, and check local Markdown link
targets. No PDFs or fonts are distributed. Automated results do not complete
linguistic, accessibility or native-viewer qualification.

# 55.0.0 — authored-text diagnostics and font comparison

Version 55 reports unsupported authored C0/C1 controls with exact Unicode code
points and available channel, page, segment and occurrence context. QA reports
them before source-comparison skips, and rebuild refuses them before font/PDF
work or output creation. TAB, LF and CR remain allowed. U+00AD SOFT HYPHEN is
retained and reported separately for discretionary-break review; it is not
removed or normalized.

`audit-fonts` now accepts repeatable `--candidate FONT` options. Each candidate
is compared against all effective authored text, including retained Latin
identifiers in Arabic or Devanagari jobs. This is an advisory comparison: it
does not select, replace or rewrite configured fonts, and candidate coverage
does not change the configured-font exit status.

With the updated instrument on the version-54 runtime, the controlled four-case
replay recorded 102 changed diagnostic occurrences: 96 GSA, 5 IRS, 1 NASA and
0 OPM. All four strict outcomes remained unchanged in that instrument-only
comparison. With the version-55 runtime and the same instrument, IRS, GSA and
OPM retained their strict failures and their 21 output pages were
pixel-identical; NASA instead refuses earlier at rebuild on six U+0003 controls.
QA also reports two soft-hyphen warnings and the existing URL warning. Explicit
Arabic Arial and Hindi Nirmala candidate checks covered all effective targets
while the configured script fonts still had gaps; audit exit 1 remained
unchanged.

These are controlled mechanical results using pseudo-localized or authored test
inputs. They are not natural-language translation-quality evidence. The 3/13
version-51 benchmark and version-54 frozen subset remain historical records,
and no new qualified human linguistic, native-viewer or accessibility result is
claimed. For published validation, inspect the Actions run whose head SHA
matches the exact source commit. The
[preceding version-54 run](https://github.com/ariasr47/pdf-translate-preview/actions/runs/34056891624)
is evidence only for that earlier commit. No formal GitHub Release is claimed.

# 54.0.0 — conservative preservation and input refusals

Version 54 corrects graphics-state preservation for demonstrated cases during
text removal and refuses text clipping that cannot be safely stripped. The frozen synthetic 12×12 black
square retained 144 dark pixels through stripped, output and final stages; the
WHO source retained all 766 vector paths and paint settings. The earlier silent
synthetic graphics defect did not occur on WHO.

Sources that require a password refuse. The CLI does not accept, bypass or
recover passwords; ask the user for an authorized accessible copy and process
that copy as a new input. Pages with inherited or direct nonzero `/Rotate`
values refuse at initialization. Capability inventory work and depth are bounded, including an
explicit CLI work budget; all seven frozen negative cases produced clean
expected refusals.

The exact qualified floor is PyMuPDF 1.27.1, pikepdf 10.5.0 and fonttools
4.40.0. This explicitly supersedes the version-53 note below that named
PyMuPDF 1.24.10. Tested PyMuPDF 1.25.0, 1.25.5, 1.26.0 and 1.26.7 fail the
strengthened ActualText semantics; intermediate releases are not claimed.

Validation: 363 development tests and 38 exported public tests passed. The
unchanged frozen replay mechanically finalized 3/7 available public documents
and 14/24 actual-translation synthetic cases; 6 synthetic cases refused during
rebuild and 4 rotated cases refused during initialization. Render comparison of
all 28 passing final pages was pixel-identical to the frozen originals.

Fonts for mixed-script output must cover retained source tokens and the target
script. A retained identifier such as `ZX-2048` needs Latin letters, digits and
punctuation even in Arabic or Devanagari output. Meaningful source control
characters, including soft hyphens, and occurrence-specific benchmark
preservation remain open measured limitations.

This remained an experimental, supervised, document-specific source preview.
No qualified human linguistic, native-viewer or accessibility review was added.
Its subsequent public CI record is linked from the current release section. No
formal GitHub Release was claimed.

# 53.0.0 — dependency qualification and earlier diagnostics

Corrected unsupported dependency floors to the measured working baseline:
PyMuPDF 1.24.10, pikepdf 10.5.0 and fonttools 4.40.0. Exact constraints and a
Python 3.10 CI job exercise public regressions and copied-folder smoke, retaining
resolved versions. Intermediate patches and every possible mixture are not
claimed as tested.

Malformed AcroForm entries now produce a concise preflight refusal. Inventory
reserves a bounded amount of graph work before expanding children and limits
depth, including primitive leaves and repeated references. These limits do not
sandbox native parsing or decompression.

The optional `audit-fonts` command reports codepoint gaps by font role and
available page/segment context before layout. It checks all effective authored
text against each face, without inferring actual role usage. Coverage remains
advisory; shaping, overflow and final delivery checks are still required.
Ten new public regressions cover these behaviors on both the current and
minimum local environments.

The benchmark follow-up reproduced nine deliberate retained-source findings
and identified document-global fragment protection in benchmark authoring.
No leak gate, allowlist, archived result or translation success count changed.
Human, native-viewer and accessibility qualifications remain unestablished.

# 52.0.0 — failure reporting and maintenance

Python tracebacks now appear in diagnostic reports, including chained and
truncated traces. Expected caption refusals emit a concise field-specific
failure instead of an uncaught traceback. Refusal gates and PDF rendering are
unchanged. The archived FDA failure now produces useful diagnostics and the
same input still refuses without writing an output or altering its source.

Validation: 326 runtime, 15 grader and 17 tooling tests passed.
Eight diagnostic regressions are now included in the public suite (18 tests
total). The artifact-upload action was reviewed against its official v7.0.1
release, updated by immutable commit and tested across the CI matrix. The
reviewed dependency PR passed after refreshing its exact source inventory.
No checksum checks or PDF gates were disabled.

The version-51 translation/benchmark qualifications below remain their measured
scope; this update does not establish new viewer or human qualifications.

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
