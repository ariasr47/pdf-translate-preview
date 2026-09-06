# Dependency inventory

`pdf-translate/requirements.txt` declares supported direct dependency ranges.
`pdf-translate/constraints-reference.txt` records the direct versions from one
Windows Python 3.14 reference run. It is not a portable lock file and does not
claim that one Windows wheel hash selects or verifies artifacts for Linux,
macOS, other Python versions, or other architectures.

`pdf-translate/constraints-minimum.txt` pins the exact direct dependency floors
used by the Python 3.10 minimum-dependency CI job. PyMuPDF 1.24.10 and 1.24.11
lack `TEXT_IGNORE_ACTUALTEXT`, while tested 1.25.0, 1.25.5, 1.26.0 and 1.26.7
still return replacement ActualText when that flag is requested. The Arabic
shaping gate requires the displayed glyphs instead. PyMuPDF 1.27.1 is the
conservatively qualified floor; intermediate releases were not exhaustively
tested. Pikepdf 8.0.0, 9.0.0, and 10.0.0 lack the dictionary `values()`
surface exercised by the public caption regressions, so pikepdf 10.5.0 remains
the qualified floor. The local minimum-dependency qualification job proves this
exact direct set can complete init, rebuild, finish, copied-folder smoke, and
all public synthetic regressions on its qualification host. It does not claim
every version mixture inside the declared ranges has been tested. Qualification
on a public CI host remains pending for the published version-54 source commit.

Version 54 locally qualified both exact direct sets: the minimum set above and
the Windows Python 3.14 reference set recorded in
`pdf-translate/constraints-reference.txt` (PyMuPDF 1.28.2, pikepdf 10.13.0.post1
and fonttools 4.64.0). Public CI for the published source commit remains pending;
these local results do not claim every intermediate dependency combination.

The public CI matrix installs from the ranges on each OS and Python version and
uploads `pip freeze --all` output as a resolved-version inventory. Download the
inventory from the exact workflow run used for a qualification record. Retain
the run URL, commit, OS, architecture, Python version, and preview manifest hash.
An inventory reports the resolver result; it does not replace artifact hashes,
runtime tests, viewer checks, or human review.

Dependabot opens weekly pull requests for Python dependencies and GitHub
Actions. Maintainers review and test those pull requests; no automatic merge is
configured.

Dependency PRs intentionally require maintainer review of the source inventory.
Tests run before the checksum gate so the bot's unchanged manifest does not
prevent regression results. After reviewing the dependency diff, check out its
branch, run `python tools/refresh_inventory.py`, inspect the SHA256SUMS.json
diff, and commit it with the update. Then require the complete CI run to pass.
Do not auto-refresh hashes as proof that unreviewed code is safe. The helper
only refreshes existing inventory entries; added/removed public files require
an explicitly reviewed export. No privileged bot-write workflow is installed.
