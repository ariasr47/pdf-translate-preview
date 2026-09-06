# Experimental PDF translation skill — 53.0.0

This folder is a self-contained Agent Skill for translating supported
born-digital PDFs with strict layout and AcroForm checks. Read [SKILL.md](SKILL.md)
and [the workflow](references/workflow.md). Use Python 3.10+ and install
`requirements.txt` in a virtual environment.

Finalization embeds a full field font, verifies the exact delivered PDF and
writes hash-bound evidence. Contextual mappings can distinguish repeated labels.
Automated verification, model review, human revision and viewer testing are
recorded separately. Inspect every final page and test target-script field entry.

See [support limits](references/support.md), [security](references/security.md),
[delivery evidence](references/delivery.md), and [third-party notices](THIRD_PARTY_NOTICES.md).
This is not a universal PDF converter: scans/OCR overlays and unsupported cases
are refused. No certification, official status, PDF/UA conformance or universal
viewer behavior is implied.

Development tests, benchmarks and package-building tools live in the separate
development repository outside this portable folder and are not needed to run an installed skill.

## Distribution

Experimental source-only preview. The MIT license covers this project's original
code and documentation. The PyMuPDF integration uses the GNU AGPLv3 distribution
route described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), unless you
obtain a suitable commercial license from Artifex. No commercial license is
included. Dependencies are installed separately under their upstream terms.
No Python runtime, dependency wheels, fonts or test PDFs are bundled.
