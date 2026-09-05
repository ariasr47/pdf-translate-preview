# Qualified bilingual review packet

**Status: pending.** This is a blank protocol. No reviewer has signed it by
its inclusion in the preview. Complete it only for material the reviewer is
authorized to see and only after the finalized PDF bytes are stable.

## Prepare locally

Provide the original PDF, finalized PDF, side-by-side comparison, translation
mapping, field labels/options, QA findings and delivery manifest through an
approved private channel. Record both PDF SHA256 values, locale/register,
document purpose, preview version and reviewer qualifications. Do not place
these materials in a public issue by default.

The reviewer must be competent in both languages and the document domain.
Record consent before sharing their identity or assessment publicly. A model
may supply `model_bilingual` evidence but cannot fill a human category.

## Examine and decide

- Compare every source statement with its target: omissions, additions,
  negations, conditions, dates, amounts, units, identifiers and obligations.
- Check domain terms, consistent wording, locale/register and natural phrasing.
- Inspect every final page for clipping, overlapping text and unreadable size.
  Check legends, instructions, tooltips, choices and defaults as well as page text.
- Record each issue with page/field, severity, correction and disposition.
  Do not accept semantic loss to make text fit.
- After any PDF change, repeat affected checks and bind sign-off to the new hash.

## Record the actual outcome

Use a project-specific [MQM Core](https://www.themqm.org/mqm-pillars/the-mqm-core-typology/)
subset: accuracy, terminology, fluency, style, locale conventions and design.
For this trial, classify limited-impact issues as minor, substantial obstacles
to correct use as major, and errors that defeat the intended purpose as critical.
Record neutral preferences separately. These severity decisions depend on the
job brief; a spelling error is not automatically assigned one severity.
Resolve every critical or major issue before acceptance. Do not infer a pass
from a low average score that masks a serious instruction or numeric error.
The [MQM scoring guidance](https://www.themqm.org/mqm-pillars/the-mqm-scoring-models/)
allows project-specific scoring; this preview does not prescribe a universal
numeric quality threshold. Blank issue counts mean unreviewed, not zero errors.

Suggested issue record: stable occurrence/page/field; source and target span;
MQM category; severity and user impact; proposed correction; resolution;
reviewer; final output hash; and date. Assess every page for a small form.

Use `record-template.json` as the starting state. Change only categories actually
performed. A completed category requires `status`, `reviewer`, `scope`,
`evidence` and `output_sha256` naming the exact final PDF. Status can be `passed`,
`failed` or `not_applicable`; explain the evidence and scope for each declaration.
Leave unavailable categories `not_performed`.

Retain a signed/consented human report locally and record a safe evidence reference.
Use the runtime's `pipeline.py review DELIVERY.json REVIEW.json` to bind the
declaration. Do not edit `delivery.json` by hand to create a pass. The runtime
validates declared evidence binding; it cannot authenticate reviewer competence
or independently establish that the human work happened.

Public summary, if consented: locale/domain, synthetic document hashes, reviewer
role, checks performed, result and remaining limits. No confidential attachments.
