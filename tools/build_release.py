#!/usr/bin/env python3
"""Build an allowlisted, deterministic portable skill ZIP (never publishes).

python tools/build_release.py --output runs/release/pdf-translate.zip --smoke
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {'SKILL.md', 'README.md', 'LICENSE', 'requirements.txt', 'constraints-reference.txt',
              'THIRD_PARTY_NOTICES.md', 'COPYING.AGPL-3.0'}
DIRECTORIES = {'scripts': '.py', 'references': '.md', 'schemas': '.json'}
REQUIRED = {'SKILL.md', 'LICENSE', 'COPYING.AGPL-3.0', 'THIRD_PARTY_NOTICES.md', 'requirements.txt', 'scripts/pipeline.py',
            'scripts/verify.py', 'scripts/delivery.py', 'references/translations-format.md'}


def runtime_files(skill):
    skill = Path(skill).resolve()
    paths = [skill/name for name in ROOT_FILES if (skill/name).exists()]
    for directory, suffix in DIRECTORIES.items():
        parent = skill/directory
        if parent.is_symlink():
            raise ValueError(f'symlink runtime directory: {directory}')
        if parent.exists():
            paths.extend(p for p in parent.rglob('*') if p.suffix == suffix and '__pycache__' not in p.parts)
    for path in paths:
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(skill):
            raise ValueError(f'invalid runtime file: {path}')
        if any(p.is_symlink() for p in path.parents if p != skill and p.is_relative_to(skill)):
            raise ValueError(f'symlink runtime parent: {path}')
    return {p.relative_to(skill).as_posix(): p for p in sorted(paths)}


def validate(skill, checksums=False):
    skill = Path(skill).resolve()
    files = runtime_files(skill)
    missing = REQUIRED - files.keys()
    if missing:
        raise ValueError(f'missing required runtime files: {sorted(missing)}')
    text = files['SKILL.md'].read_text(encoding='utf-8')
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError('SKILL.md requires YAML frontmatter')
    metadata = text.split('---', 2)[1]
    if not re.search(r'^name:\s*pdf-translate\s*$', metadata, re.M):
        raise ValueError('skill name must be pdf-translate')
    if not re.search(r'^description:\s*\S', metadata, re.M):
        raise ValueError('skill description is required')
    for name, path in files.items():
        if path.suffix != '.md':
            continue
        content = path.read_text(encoding='utf-8')
        for reference in re.findall(r'(?:references/[^\s`\)\]<>"\x27]+\.md|schemas/[^\s`\)\]<>"\x27]+\.json)', content):
            if reference not in files:
                raise ValueError(f'missing runtime reference in {name}: {reference}')
    if checksums:
        manifest = json.loads((skill/'SHA256SUMS.json').read_text(encoding='utf-8'))
        actual = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
        all_files = {p.relative_to(skill).as_posix() for p in skill.rglob('*') if p.is_file()}
        if manifest != actual or all_files != set(actual) | {'SHA256SUMS.json'}:
            raise ValueError('runtime checksum or file inventory mismatch')
    return len(files)


def smoke(skill):
    """Import and exercise extracted runtime in an unrelated working directory."""
    skill = Path(skill).resolve()
    with tempfile.TemporaryDirectory(prefix='skill-smoke-') as tmp:
        env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        env.pop('PYTHONPATH', None)
        code = '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import pipeline, delivery, verify, pymupdf
with pymupdf.open() as doc:
    page = doc.new_page()
    page.insert_text((72, 72), "Portable skill smoke test")
    doc.save("source.pdf")
'''
        subprocess.run([sys.executable, '-c', code, str(skill/'scripts')],
                       cwd=tmp, env=env, check=True, capture_output=True, text=True)
        result = subprocess.run([sys.executable, str(skill/'scripts/extract_segments.py'),
                                 'source.pdf', '--outdir', 'extracted'], cwd=tmp, env=env,
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError(f'copied skill CLI smoke failed: {result.stderr}')
        segments = json.loads((Path(tmp)/'extracted/segments.json').read_text(encoding='utf-8'))
        if not segments['segments'] or not any(s['core'] == 'Portable skill smoke test' for s in segments['segments']):
            raise ValueError('copied skill extraction did not retain source text')


def build(skill, output):
    skill, output = Path(skill).resolve(), Path(output).resolve()
    if output.is_relative_to(skill):
        raise ValueError('release output must be outside the skill')
    validate(skill)
    files = runtime_files(skill)
    payloads = {name: path.read_bytes() for name, path in files.items()}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(payloads.items())}
    payloads['SHA256SUMS.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive mode preserves existing release/evidence files.
    with output.open('xb') as stream:
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
            for name, payload in sorted(payloads.items()):
                info = zipfile.ZipInfo('pdf-translate/'+name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payload)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path, default=ROOT/'pdf-translate')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    digest = build(args.skill, args.output)
    if args.smoke:
        with tempfile.TemporaryDirectory(prefix='release-install-') as tmp:
            with zipfile.ZipFile(args.output) as archive:
                archive.extractall(tmp)
            copied = Path(tmp)/'pdf-translate'
            validate(copied, checksums=True)
            smoke(copied)
    print(json.dumps({'archive': str(args.output), 'sha256': digest, 'copied_smoke': args.smoke}))


if __name__ == '__main__':
    main()
