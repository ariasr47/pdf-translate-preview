#!/usr/bin/env python3
"""Check every distributed source file; no third-party dependency required."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'SHA256SUMS.json').read_text(encoding='utf-8'))
    ignored_roots = {'.git', '.venv', 'jobs', 'local-evidence'}
    distributed = set()
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if relative.parts[0] in ignored_roots or '__pycache__' in relative.parts:
            continue
        if relative.as_posix() in {'SHA256SUMS.json', 'sample-input.pdf'}:
            continue
        if path.is_symlink():
            raise SystemExit('FAIL: unexpected symlink: '+relative.as_posix())
        if path.is_file():
            distributed.add(relative.as_posix())
    if distributed != set(manifest):
        raise SystemExit('FAIL: source inventory differs from the distributed manifest')
    for name, expected in manifest.items():
        path = root/name
        if not path.resolve().is_relative_to(root) or path.is_symlink() or not path.is_file():
            raise SystemExit('FAIL: missing or unsafe source path: '+name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit('FAIL: checksum mismatch: '+name)
    print(f'Verified {len(manifest)} distributed source files against the included manifest.')
    print('Git metadata, .venv, jobs, local-evidence and sample-input.pdf are local-only exclusions.')


if __name__ == '__main__':
    main()
