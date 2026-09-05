# 50.0.0 — experimental source preview

Prepared 2026-09-05; publication is not implied by this file.

This preview includes finalized-output verification and hash-bound delivery
evidence, contextual occurrence mappings, inherited AcroForm structural checks,
and explicit security and unsupported-input policies. Recent fixes address
contextual target verification and field appearance handling. Each behavior
remains subject to its documented gates and limitations.

The public payload contains only the portable skill source, licenses and reviewed
public documentation. It excludes private development history, corpus binaries,
fonts, benchmark downloads, dependency wheels and internal execution evidence.
MIT notices remain intact, with full AGPLv3 text and the combined-work scope
specified in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

The final stress rerun remains **1/13 available documents completed**, from
17 attempted sources and 415 available pages. It measures pseudo-localization
and mechanical pipeline behavior, not translation accuracy. Two documents
progressed to final verification after fixes but still failed other gates.
Five cases stopped at retypeset and seven at final verification. See the
[complete sanitized result table](docs/BENCHMARK.md).

The local runtime suite passed 296 tests at the recorded qualification point.
Fresh Windows version-50 Spanish and Arabic synthetic lifecycle checks passed.
These findings do not imply success on the 12 failed public-document cases.

Qualified bilingual review, macOS and individual PDF viewer qualification remain
pending. Initial agent-host PDF tasks timed out before final responses; the
version-50 positive and injection repeats completed and independently passed
artifact verification with zero QA issues. The earlier negative activation
case completed without tool use. The initial timeouts remain part of the evidence;
these bounded cases do not qualify the full evaluation matrix. See the
[support matrix](docs/SUPPORT.md).

Migration: use the full `pdf-translate/` directory. A clean job and final delivery
manifest are required; do not reuse stale build evidence or overwrite prior
deliveries. No private repository history or previous binary fixtures accompany
this preview.
