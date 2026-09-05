# Reporting and contributing

This source preview has a deliberately narrow, experimental scope. Start with
a reproducible failure on a synthetic document. Read [support limits](docs/SUPPORT.md)
and retain the unmodified original, exact version, dependency versions and the
gate that failed in your own local evidence.

Use the public issue templates for sanitized bug reports and qualification
results. Describe what happened and what you expected. Include the target
locale and whether the document has widgets, rotation, unusual scripts or
long text. Never attach confidential input/output, fonts without redistribution
permission, credentials or raw host traces. An unavailable case is not a pass.

Small focused patches should explain the concrete trigger, changed behavior
and checks actually run. Use synthetic source generators for reproductions;
do not add third-party PDFs or font binaries. Preserve license notices and the
combined-work licensing scope. Do not weaken verification thresholds to obtain
a favorable benchmark score.

This public preview does not contain the private development corpus or history.
Public contributions must be independently reproducible from permitted source
and assets. [Review protocols](docs/review/human.md) distinguish automated,
model, human and viewer evidence. A model must never sign as a human reviewer.
