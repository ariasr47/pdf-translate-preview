# Translation quality and review

Use a short project brief: source edition, locale, audience, purpose, register,
terminology sources, protected data, layout constraints, required reviewers and
acceptance criteria. A reusable schema is in `../schemas/job.schema.json`.
Language alone is insufficient context: Spanish for a US school form can use
different terminology from Spanish for an issuer in Spain.

Read whole sentences and document sections before translating extracted lines.
Extraction boundaries are layout boundaries, not necessarily translation units.
Use reviewed paragraph merges where appropriate and occurrence-specific targets
where the same source string has different meanings. Keep a project glossary
with source, preferred target, authority and context; do not treat a generic
domain dictionary as authoritative for every issuer.

Preserve quantities, signs, decimals, units, dates, form codes, URLs, negation,
conditions and obligations. Do not translate field identifiers, export tokens
or user-entered data by default. Automated checks can flag number/terminology
changes, omissions, untranslated text and unsafe markup; they cannot decide
legal meaning, tone, ambiguity or whether a shorter paraphrase lost a condition.

Review in distinct layers:

- Automated structural, placement, data and font checks on final bytes.
- Model bilingual review, explicitly labeled, comparing source and target.
- Qualified human bilingual revision for meaning and completeness when needed.
- Monolingual target review for natural usage and audience comprehension.
- Visual and viewer testing for clipping, scale, field entry and saved values.

Record issue category, severity, source/target location, correction, reviewer
and disposition. A critical mistranslated obligation or identifier blocks an
acceptable delivery even if aggregate metrics look good. A model cannot mark
`bilingual_human` or `monolingual_human` as performed on its own behalf.

The approach follows project specification and risk-based quality principles,
not a claim of certification to a standard. See [DGT translation quality](https://translation.ec.europa.eu/languages-and-translation-european-commission/translation-quality_en)
and the [MQM error typology](https://www.themqm.org/mqm-pillars/typology/).
[ITS 2.0](https://www.w3.org/TR/its20/) illustrates context/terminology metadata
for XML/HTML; applying those ideas to PDF sidecars does not make PDF an ITS format.
ISO 17100, 18587 and 5060 concern different processes/evaluation scopes. The
skill does not assert compliance based on automated tests or public summaries.
