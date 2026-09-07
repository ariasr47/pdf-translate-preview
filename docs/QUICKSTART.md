# Your first Spanish form

Complete [Python installation](INSTALL.md) first. Run these commands from the
extracted preview root containing `README.md` and `pdf-translate/`. An agent host
is optional for this deterministic example; [host setup](HOSTS.md) enables work
on your own documents.

Choose a regular TrueType font (`.ttf`, with a glyf table) that you have permission
to use and embed. Supply its absolute path. No font or translation service is
downloaded by the example. Python dependency installation does access the network.

Windows PowerShell, using `$PY` from installation:

```powershell
& $PY examples/first_translation.py --font 'C:/path/to/regular.ttf' --output jobs/first-spanish
```

macOS Terminal, using `$PY` from installation:

```bash
"$PY" examples/first_translation.py --font '/path/to/regular.ttf' --output jobs/first-spanish
```

For automated documentation checks, this is the same command expressed as argv
placeholders (`PY`, `FONT`, and `JOB` are replaced by the test):

```text
PY examples/first_translation.py --font FONT --output JOB
```

The script generates a synthetic English form, authors two Spanish page strings
and the field tooltip, checks fonts, rebuilds, and finalizes through the normal
pipeline gates. It preserves the field identifier `participant_name`. The sample
uses regular text only; assigning the same face to all font roles does not
demonstrate bold or italic support. This fixed mapping translates only this
sample. Your documents require translations authored by a translator or agent.

| Output inside the job | Purpose |
| --- | --- |
| `source.pdf` | Generated English input; retain for comparison |
| `translations.json`, `widget-authored.json` | Explicit sample translations |
| `font-audit.json`, numbered `.log` files | Diagnostics and stage results |
| `intermediate.pdf` | Build artifact; use the finalized PDF for review |
| `final.pdf` | Spanish candidate with a fillable name field |
| `comparison.html` | Source/target visual comparison |
| `delivery.json` | Exact output hashes and outstanding review status |

Success prints that automated checks passed and human review is required.
`delivery.json` must say `review_required`. Open the comparison and check text
placement; review Spanish meaning, and enter, save, close and reopen the name
field in the viewers you intend to support. Follow the [review packet](review/human.md)
to record reviews actually performed against the exact final bytes. Automated
success does not establish linguistic accuracy, accessibility or viewer compatibility.

The script refuses an existing job directory, including an empty one. Choose
`jobs/first-spanish-2` for another attempt. If a stage fails, it stops and retains
its log; see [recovery](../pdf-translate/references/recovery.md). Resolve the cause
and rerun into a new directory. Do not weaken gates to make the tutorial pass.

For a real document, use the [full workflow](../pdf-translate/references/workflow.md)
and [support matrix](SUPPORT.md). Keep jobs under `jobs/` so generated files do
not alter the public source inventory.
