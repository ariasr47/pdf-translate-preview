# Local installation

Use a separate Python virtual environment and the complete source tree. Commands
below run from the directory containing this README's parent folder and
`pdf-translate/`. Python 3.10+ is the declared requirement; the actual local
reference checks used Windows and Python 3.14. macOS commands are a qualification
protocol and have not been executed by the maintainer for this preview.

## Windows PowerShell

Install Python from its official distribution if the `py` launcher is unavailable.
Then open PowerShell in the downloaded preview directory:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
py -3.14 -m venv .venv
$PY = Join-Path $PWD '.venv/Scripts/python.exe'
& $PY -m pip install -r pdf-translate/requirements.txt
& $PY -c "import sys, pymupdf, pikepdf, fontTools; print(sys.version); print(pymupdf.__version__, pikepdf.__version__, fontTools.__version__)"
& $PY tools/verify_preview.py
& $PY examples/make_example.py --output sample-input.pdf
```

Using the venv executable directly avoids changing PowerShell execution policy.
If using another supported Python version, select it explicitly in the venv
creation command and record that version with your results.

## macOS Terminal (zsh or bash; qualification pending)

Choose an explicitly named installed Python 3.10+ interpreter. The following
uses `python3.14`; replace it consistently with your installed `python3.X`
version if needed. Do not rely on Apple's system Python or an ambiguous
`python3` command. The version check must pass before creating the environment:

```bash
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
python3.14 -c 'import sys; sys.exit("Python 3.10+ is required") if sys.version_info < (3, 10) else print(sys.version)'
python3.14 -m venv .venv
PY="$PWD/.venv/bin/python"
"$PY" -m pip install -r pdf-translate/requirements.txt
"$PY" -c 'import sys, pymupdf, pikepdf, fontTools; print(sys.version); print(pymupdf.__version__, pikepdf.__version__, fontTools.__version__)'
"$PY" tools/verify_preview.py
"$PY" examples/make_example.py --output sample-input.pdf
```

Use the [macOS packet](review/macos.md) to record actual results. No Apple Silicon,
Intel Mac, Preview.app or macOS agent-host compatibility is claimed yet.

## Dependencies and first translation

`requirements.txt` declares dependency ranges. Optional
`constraints-reference.txt` records the direct versions used locally; it is not
a complete transitive or cross-platform lock. See the
[resolved-version inventory protocol](DEPENDENCIES.md). To use those direct versions, append
`-c pdf-translate/constraints-reference.txt` to the pip command. Retain the
resolved dependency versions in private local evidence. Dependency installation
accesses upstream package servers and their software has its own license terms.

For a reproducible check of the declared direct dependency floors, use Python
3.10 and append `-c pdf-translate/constraints-minimum.txt` instead. This matches
the dedicated minimum-dependency CI job, including its generated-font
init/rebuild/finish lifecycle and ActualText shaping-gate regression. Transitive
dependencies still resolve for the current platform and must be recorded from
the actual run.

Point your agent at the installed skill and ask:

> Translate the synthetic sample-input.pdf into Spanish (es-US). Keep the form
> fillable. Use the skill's complete finalize-and-review workflow. Report any
> failed checks and mark reviews that have not been performed honestly.

Supply fonts you have permission to use and embed, with glyph coverage for the
target text. The preview includes no fonts and does not silently download them.
The [workflow](../pdf-translate/references/workflow.md) is available from the
repository root under `pdf-translate/references/workflow.md`.

For manual use, follow that workflow with the venv Python executable and a fresh
job directory. Its `PY`, `SK` and `JOB` names are placeholders, not literal shell
commands. A scaffold with null translations is unfinished; extraction alone
does not translate a document. Never label an intermediate PDF a final delivery.


Before an expensive rebuild, optionally run `pipeline.py audit-fonts --work JOB`
using your venv Python and the installed `pdf-translate/scripts/pipeline.py`.
Add repeatable `--candidate FONT` options to compare possible faces.
Add `--output NEW_REPORT.json` to retain a new report; existing files and input
aliases are refused. Font paths resolve beside `translations.json`, with the
same legacy caller-relative fallback as rebuild. The job also needs
`segments.json`. Exit 0 means the checked codepoints are covered; 1 reports
coverage gaps; 2 reports invalid inputs or report paths.

This read-only advisory checks effective authored text (including occurrence
replacements, merges, overrides and notices) against each configured role face.
A candidate path resolves from the caller and is checked against all effective
authored text, including retained identifiers. Candidate results do not select,
replace or rewrite configured fonts and do not change the configured-font exit
status.
A gap in an unused face does not necessarily affect the build: actual style use
is not inferred. Reports include role, page/segment when available, channel and
missing Unicode codepoints. Coverage does not prove shaping, geometry or all
styles work. Source markers, tails, passthrough text, widgets and future field
input are excluded. Final glyph, layout and delivery gates remain authoritative.

QA diagnoses unsupported authored C0/C1 controls with exact code points and
available mapping context. Rebuild refuses the same controls before creating an
output. TAB, LF and CR are allowed. U+00AD SOFT HYPHEN is retained and produces
a separate warning for review of the discretionary break; it is not normalized
away.

Input capability inventory rejects a non-dictionary AcroForm and bounds Python
graph traversal to 100,000 work items (including primitive leaves) and 128
levels. These are traversal limits, not parser, decompression, file-size or
process-memory guarantees. Actions are inventoried without execution.
