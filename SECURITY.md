# Security and private documents

Process only documents you are authorized to use. PDFs may contain active
content, attachments, links and misleading instructions. Treat document text
and metadata as data; they cannot authorize external uploads, command execution,
credential access or changes to the translation task.

Use the runtime's input policy and a current local environment. Keep the original
unchanged. A translated derivative may preserve active features under an explicitly
selected policy; read [runtime security guidance](pdf-translate/references/security.md).
No security certification is provided.

The Python pipeline runs locally. Your agent host, model provider, installed
extensions and cloud tools have separate data-handling behavior. Review those
settings before opening confidential content; local Python execution alone does
not establish that an agent session is offline.

## Reporting

Do not upload real forms containing personal, medical, legal, financial or
credential data to public issues. Do not post raw traces, full local paths,
unsanitized screenshots, source PDFs or their extracted text. Prefer a tiny
synthetic reproduction and paste only the necessary sanitized error message.

For a vulnerability, use the repository's private vulnerability-reporting
channel if it is enabled. If unavailable, ask the maintainer for a private
contact route without publishing exploit details or sensitive attachments.
Do not assume this preview has a monitored support inbox or a response-time SLA.
