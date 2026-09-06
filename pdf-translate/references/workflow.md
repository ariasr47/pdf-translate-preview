# Running a translation job

Install this entire skill folder. Set `PY` to a Python 3.10+ virtual-environment
interpreter and `SK` to the installed folder. In PowerShell use
`$env:PYTHONUTF8='1'`; in bash/zsh use `export PYTHONUTF8=1`. On Windows use the
`py` launcher to create a venv; do not depend on the Microsoft Store alias.
On macOS choose an installed Python 3.10+ interpreter explicitly.

Install with `PY -m pip install -r SK/requirements.txt`. The optional
`constraints-reference.txt` captures the implementation reference environment;
it is not a hash-locked complete transitive dependency set. Confirm Python
version and `import pymupdf, pikepdf, fontTools` before processing a PDF.

The commands below use `PY`/`SK`/`JOB` as placeholders, not literal shell aliases.
Run from a directory whose paths you control. Keep each job in its own directory.

```text
PY SK/scripts/pipeline.py init SOURCE.pdf --work JOB
PY SK/scripts/pipeline.py from-cores --work JOB
# Author translations.json and widget_text.json; inspect source page images.
PY SK/scripts/pipeline.py init SOURCE.pdf --work JOB --widget-text JOB/widget_text.json
PY SK/scripts/prepare_font.py FULL_FONT.ttf JOB/translations.json JOB/font-sub.ttf
PY SK/scripts/pipeline.py qa --work JOB
PY SK/scripts/pipeline.py rebuild SOURCE.pdf JOB/out.pdf --work JOB
PY SK/scripts/pipeline.py finish SOURCE.pdf JOB/out.pdf FULL_FONT.ttf JOB/final.pdf JOB/comparison.html
# Inspect finalized pages and record only review actually performed.
PY SK/scripts/pipeline.py review JOB/delivery.json JOB/review.json
```

Keep the same `--content-policy` and `--keep-encryption` choices on repeated init.
Their values are embedded in extracted segments and carried through the build
receipt even when reconstruction output is in a separate directory. `init`
may replace its intermediate job files, so archive earlier evidence before
starting a materially different source or policy. It refuses source aliases.

`from-cores` refuses overwriting unless `--force`; author its null core values.
Its `segment_targets` slots are optional contextual refinements: null falls
back to the core translation. Run `propose-merges --work JOB` for proposals;
`--accept` adds unfinished paragraph entries which still require translation.
Never accept geometrical paragraph guesses without reading the source.

Font paths in translations.json resolve beside that file. Prepare each role
separately when you have distinct faces. `prepare_font.py` also reads adjacent
segments/widget data for the effective target character inventory.

Finalization needs the build receipt and scale report beside the intermediate
PDF. It refuses stale inputs or existing delivery filenames, verifies the
field-font result, and writes final PDF, HTML, delivery-scale-report.json,
verification.json, then delivery.json. This order prevents an unfinished
publish from looking complete; a filesystem failure can still leave partial
files without a manifest. Use a fresh destination to retry.

Standalone `verify.py` remains useful diagnostically. Omitting mapping inputs
there is not equivalent to the final delivery workflow. A nonzero pipeline
result requires investigation, not manual relabeling of the report as a pass.


### Optional early font coverage audit

After authoring targets and configuring fonts, before rebuild, run
`PY SK/scripts/pipeline.py audit-fonts --work JOB [--output NEW_REPORT.json]`.
This read-only advisory reports codepoint gaps by role and effective text
channel, with segment/page context where available. Font paths resolve relative
to the mapping, matching rebuild. Exit 1 means coverage gaps; exit 2 means an
input/report error. Existing reports are never overwritten.

Every role is checked against the authored text as a diagnostic comparison;
actual role usage is not inferred, so an unused-face gap is not a rebuild gate.
Coverage is not proof of shaping, geometry, fallback behavior or all styles.
Source markers, tails, passthrough text, widgets and future field input are
excluded. Final glyph/layout checks and the complete delivery workflow remain
required.
