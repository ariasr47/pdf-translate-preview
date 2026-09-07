# Install the skill in an agent host

First complete [Python setup](INSTALL.md) and the [sample translation](QUICKSTART.md).
Installing a skill makes instructions discoverable; it does not install Python,
dependencies or fonts. Keep the virtual environment and jobs outside the copied
skill folder. Give the agent the absolute path to that environment's Python.

Copy the **complete `pdf-translate/` folder**, including `SKILL.md`, `scripts/`,
`references/` and license files. Copying only `SKILL.md` leaves required tools missing.
Choose one host and one scope; avoid duplicate installations with the same name.

| Host | Personal installation | Project alternative |
| --- | --- | --- |
| Codex | `~/.agents/skills/pdf-translate/SKILL.md` | `.agents/skills/pdf-translate/SKILL.md` in your working project |
| Claude Code | `~/.claude/skills/pdf-translate/SKILL.md` | `.claude/skills/pdf-translate/SKILL.md` in your working project |

`~` means your home directory (`$HOME` in the shells below). The project alternative
belongs in your working project, rather than the extracted preview whose inventory
you verify. These instructions cover Codex and Claude Code; they do not establish
compatibility with Claude web uploads or other hosts.

## Copy a personal installation

Run from the extracted preview root. For **Codex**, use these commands. For
**Claude Code**, replace `.agents/skills` with `.claude/skills` in the target only.
The guard refuses an existing installation; do not merge releases in place.

Windows PowerShell:

```powershell
$skillTarget = Join-Path $HOME '.agents/skills/pdf-translate'
if (Test-Path -LiteralPath $skillTarget) { throw 'Skill already exists; review it before updating.' }
New-Item -ItemType Directory -Force -Path (Split-Path $skillTarget) | Out-Null
Copy-Item -LiteralPath './pdf-translate' -Destination $skillTarget -Recurse
Test-Path -LiteralPath (Join-Path $skillTarget 'SKILL.md')
```

macOS Terminal:

```bash
skill_target="$HOME/.agents/skills/pdf-translate"
if [ -e "$skill_target" ]; then
  printf '%s\n' 'Skill already exists; review it before updating.'
else
  mkdir -p "$(dirname "$skill_target")"
  cp -R ./pdf-translate "$skill_target"
  test -f "$skill_target/SKILL.md"
fi
```

Start a fresh host session after copying. In Codex, explicitly ask to use the
`pdf-translate` skill. In Claude Code, invoke `/pdf-translate`. Use this first prompt:

> Use pdf-translate. First report the absolute SKILL.md path you loaded and the
> Python interpreter you will use. Translate my synthetic sample into Spanish
> (es-US), preserve its form fields, and follow the full finalize-and-review
> workflow. Use the font path I supply. Report failed gates and unperformed reviews.

Supply absolute input, Python, font and fresh job paths with your request.
Confirm the reported skill path matches the installation you intended. A host
recognizing the skill is a discovery check, not an end-to-end qualification.

## Updating and troubleshooting

Verify a newly downloaded preview with `tools/verify_preview.py` before copying.
Preserve local edits separately, replace the old skill as a complete unit, and
rerun the sample with the intended environment. Do not copy `.venv` or job evidence
between machines. If discovery fails, check the folder nesting, `SKILL.md` filename,
duplicate scopes and any disabled-skill configuration, then restart the host.
If script execution fails, check the Python path and imports in [installation](INSTALL.md).

Host discovery paths and invocation are based on the official
[Codex skill documentation](https://learn.chatgpt.com/docs/build-skills) and
[Claude Code skill documentation](https://code.claude.com/docs/en/skills).
Host discovery and manual viewer qualification must still be recorded on the
actual host and operating system; see [support status](SUPPORT.md).
