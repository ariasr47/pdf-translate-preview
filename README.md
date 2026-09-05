# PDF Translate — experimental preview

An editable Agent Skill and local Python pipeline for translating simple
born-digital PDFs while checking page geometry, text placement and AcroForm
fields. This is an experimental source preview, not a generally qualified PDF
translation product. Begin with low-risk, non-confidential sample documents.

The pipeline can extract text, apply an authored translation, rebuild the page,
prepare field fonts and verify the finalized PDF. A language-capable agent or
translator must author the mapping; no model or translation service is included.
Failures are document-specific and must be resolved before delivery. An automated
pass does not establish correct meaning or working form entry in every viewer.

## Install and try

Follow the [Windows or macOS installation instructions](docs/INSTALL.md).
Install the complete `pdf-translate/` directory in your agent host's documented
skill location. Read [SKILL.md](pdf-translate/SKILL.md) and the
[job workflow](pdf-translate/references/workflow.md). Host setup is separate from
installing Python dependencies; this preview does not assume a particular plugin
marketplace or host-specific installer.

The [sample generator](examples/make_example.py) creates a local, synthetic form
from source. No PDFs or fonts are distributed here. Use the generated form for
a first experiment and retain `delivery.json`, which records exact output hashes
and distinguishes automated checks from reviews actually performed.

Use [failure recovery](pdf-translate/references/recovery.md) and the
[experimental simple-form trial checklist](pdf-translate/references/simple-forms.md).
Public tests include source generators and an invented test font; no binary
fixtures are shipped. Dependency PRs and CI runtime archives support maintenance.

Read the [support matrix](docs/SUPPORT.md), [release notes](RELEASE_NOTES.md),
[security guidance](SECURITY.md) and [review packets](docs/review/human.md).
Qualified bilingual review and macOS/viewer qualification remain pending unless
a later dated record explicitly establishes them. The public-document stress
baseline completed 1 of 13 available documents; it is not a translation-quality
score. The [controlled version-51 rerun](docs/BENCHMARK.md) completed 3/13;
one additional pass is attributable to the engine and one to corrected benchmark
authoring. Ten available documents still fail or refuse.

## Source and licensing

This preview contains source, instructions and documentation. Dependencies are
installed separately; no Python interpreter, wheels, native libraries, fonts,
corpus PDFs or development Git history are included.

The [MIT license](LICENSE) covers this project's original code and documentation.
When distributed as a combined application with the AGPL edition of
PyMuPDF/MuPDF, the combined work is provided under [GNU AGPLv3](COPYING.AGPL-3.0).
The separate MIT grant remains available and does not replace third-party terms.
No Artifex commercial license is included. Read the unchanged
[license scope and third-party notices](THIRD_PARTY_NOTICES.md) before redistribution
or offering an integrated application as a service.

Run `python tools/verify_preview.py` from this directory to verify its checksum
inventory. Checksums detect changes relative to the included manifest; they are
not a publisher signature, a licensing clearance or a product qualification.

Report reproducible problems using the issue templates. Share only a minimal
synthetic reproduction; **do not attach confidential PDFs, real personal data,
credentials, raw agent traces or unsanitized screenshots**.
