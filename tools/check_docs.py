"""Check local inline Markdown link targets (not remote URLs or heading anchors)."""
import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def check(root):
    root = Path(root).resolve()
    errors = []
    for source in root.rglob('*.md'):
        if any(part in {'.git', '.venv', 'jobs', 'local-evidence', '__pycache__'}
               for part in source.relative_to(root).parts):
            continue
        text = re.sub(r'^```.*?^```[^\n]*', '', source.read_text(encoding='utf-8'),
                      flags=re.M | re.S)
        text = re.sub(r'`[^`\n]*`', '', text)
        for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', text):
            target = target.strip().split(' "', 1)[0].strip('<>')
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path:
                continue
            path = (source.parent / unquote(url.path)).resolve()
            if not path.is_relative_to(root) or not path.exists():
                errors.append(f'{source.relative_to(root)}: missing/outside target {target}')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    errors = check(parser.parse_args().root)
    print('\n'.join(errors) if errors else 'Local Markdown link targets passed.')
    raise SystemExit(bool(errors))
