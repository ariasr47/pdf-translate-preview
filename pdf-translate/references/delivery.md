# Final artifact and review evidence

`finish` verifies the finalized field-font PDF, not an earlier reconstruction.
`delivery.json` schema 1.0 identifies the exact final PDF, mapping, segments,
comparison and scale report by SHA-256. It records build/font hashes, locale,
actual dependency versions, verification settings/log, security inventory and
separate review categories. Relative artifact paths stay inside the delivery
folder; source and full font are identified by name/hash without requiring
those original local paths on another machine.

`validate_manifest` in scripts/delivery.py checks bytes and cross-file settings.
Hashes detect accidental substitution or stale evidence. They are not digital
signatures or proof that a claimed reviewer performed a review. Keep provenance
records under the same access controls as the deliverable.

Review starts `not_performed`. After inspecting the exact final PDF, create
review.json containing only categories being updated, for example:

```json
{
  "visual": {
    "status": "passed",
    "reviewer": "Reviewer identity and tool",
    "scope": "All pages at normal and enlarged scale",
    "evidence": "Location of saved observations and page images",
    "output_sha256": "REPLACE_WITH_ACTUAL_FINAL_PDF_SHA256"
  }
}
```

Run `pipeline.py review JOB/delivery.json JOB/review.json`. Allowed categories:
visual, bilingual_human, monolingual_human, model_bilingual, viewer, accessibility.
Performed entries require reviewer, scope, evidence and the output hash. Do not
copy this example as a claim of actual review. A model identifies itself in
model_bilingual; human categories require a human's work.

Status is `review_failed` if any review failed, `reviewed` when visual and human
bilingual review passed, otherwise `review_required`. This coarse status is not
an all-purpose release approval: inspect the individual categories and the job
brief, which may additionally require particular viewers or accessibility.
Automation passing and review completion are independent facts.

Deliver the final PDF, comparison, manifest and supporting evidence with the
source identity, target locale, actual review scope and unresolved limitations.
An official-form translation is an unofficial derivative unless the relevant
authority separately recognizes it. See compliance.md before claiming filing
eligibility or imposing a notice that changes source content.

Do not modify sealed artifact bytes. Attach review before freezing a run. If an
external evaluation protocol prohibits edits after scoring, finish all review
updates before that scoring step and keep subsequent commentary outside the run.
