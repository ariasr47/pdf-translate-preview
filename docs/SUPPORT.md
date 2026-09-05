# Qualification matrix

Status as prepared on 2026-09-05. This is an experimental source preview.
The table distinguishes demonstrated local behavior from planned qualification.

| Area | Evidence and boundary |
|---|---|
| Intended starting scope | Simple born-digital pages with extractable visible text, modest text expansion and fonts with target glyph coverage; document-specific gates must pass |
| AcroForm fields | Automated structure and fill round-trip checks; combo/list appearance support has explicit refusal boundaries; actual viewer editing must be tested separately |
| Spanish (es-US) and Arabic | Controlled synthetic Windows engine examples completed after an Arabic target-length adjustment; this is not human linguistic qualification or support for every document in either language |
| General public-document stress run | Final rerun: 17 source URLs, 13 available documents covering 415 pages, four unavailable; pseudo-localization at expansion factor 1.0 completed final verification for 1/13. See the [result table](BENCHMARK.md) |
| Windows Python | Python 3.14 local runs and fresh-environment Spanish/Arabic lifecycle checks passed for version 50; this does not qualify other OS, document classes or all locales |
| macOS | Pending; installation and review protocol supplied, no actual Mac run asserted |
| Linux and other Python versions | No platform-wide qualification asserted by this preview |
| Agent host | Three bounded Windows Claude CLI cases: a negative activation case completed with zero tools; version-50 positive and injection PDF repeats completed and independently passed artifact verification and QA. The injected instruction was observed and its requested sentinel was not created. This is not the complete evaluation matrix or a host-wide compatibility guarantee |
| Qualified bilingual human review | Pending; model output and mechanical checks are not a human sign-off |
| Acrobat, Preview, browser PDF viewers | Pending. Adobe failed during startup before a PDF opened; browser policy blocked the attempted local-PDF route. Neither attempt establishes PDF compatibility or failure |
| Accessibility, PDF/UA, official/certified translation | Not established; preserve source and follow the applicable issuing body's requirements |

A final synthetic canary exercised two pages and 13 fields: verification passed,
all four checked identifiers survived, no scaling was needed, and QA retained one
deliberate issuer warning with zero errors. Model visual inspection passed both
pages; this is explicitly separate from human, native-viewer and accessibility review.

The final positive and injection host repeats used 25 and 28 tool calls
respectively, and their exact final manifests validated. Earlier 240-second
timeouts remain recorded failures; later successful repeats do not erase them.
The injection result supports only the tested instruction-handling case, not a
general security guarantee. No human review was performed by these model runs.

The included CI workflow proposes Windows, macOS and Linux clean installation,
imports, source verification and synthetic init smoke checks on Python 3.10/3.14.
Configuration alone is not evidence of an executed check. A future passing job
would qualify those limited checks, not full translation or native PDF viewers.

The benchmark uses deterministic pseudo-localization, not professional translation.
Its final failures are retained: five retypeset and seven final-verification
stops. It does not support a claim of general production readiness.
The proposed scope is a place to begin a controlled trial, not a success guarantee.

Image-only scans, OCR overlays, unsupported scripts/fonts/layouts and failed
gates require refusal or a separately planned workflow. No OCR masking or
general reflow fallback is implemented. Do not shorten away meaning to fit a box,
suppress findings, or equate an exit-zero result with a reviewed translation.

Record each new qualification with source/output SHA256, preview version,
environment, viewer versions, exact checks and limitations. The
[human](review/human.md), [macOS](review/macos.md) and [viewer](review/viewers.md)
packets are unfilled protocols, not claims that anyone completed them.
