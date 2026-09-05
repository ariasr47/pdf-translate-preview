"""Small hash-bound receipts for reconstruction and delivery inputs."""
import hashlib
import json
import os
from pathlib import Path


def same_file(a, b):
    """Resolve path aliases and existing hardlinks before a destructive write."""
    if Path(a).resolve() == Path(b).resolve():
        return True
    try:
        return os.path.samefile(a, b)
    except (FileNotFoundError, OSError):
        return False


def disjoint_files(inputs, outputs):
    return not any(same_file(a, b) for a in inputs for b in outputs)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write_build(output, stripped, segments, translations, fonts, scale_report):
    output = Path(output).resolve()
    extracted = json.loads(Path(segments).read_text(encoding='utf-8-sig'))
    policy = extracted.get('input_policy')
    if policy is None and (Path(segments).parent/'preflight.json').is_file():
        policy = json.loads((Path(segments).parent/'preflight.json').read_text(encoding='utf-8-sig'))
    policy = policy or {'policy': 'preserve-report', 'keep_encryption': False,
                        'source_sha256': extracted.get('source_sha256')}
    if policy.get('source_sha256') != extracted.get('source_sha256'):
        raise ValueError('preflight belongs to a different source PDF')
    data = {'schema_version': '1.0', 'input_policy': policy, 'output_sha256': sha256(output),
            'stripped_sha256': sha256(stripped), 'segments_sha256': sha256(segments),
            'translations_sha256': sha256(translations),
            'scale_report_sha256': sha256(scale_report),
            'fonts': {role: {'path': str(Path(path).resolve()), 'sha256': sha256(path)}
                      for role, path in fonts.items() if path}}
    (output.parent/'build-evidence.json').write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def validate_build(output, segments, translations):
    output = Path(output).resolve()
    receipt = output.parent/'build-evidence.json'
    data = json.loads(receipt.read_text(encoding='utf-8-sig'))
    if data.get('schema_version') != '1.0':
        raise ValueError('unsupported build evidence schema')
    for label, path in (('output', output), ('segments', segments),
                        ('translations', translations),
                        ('scale_report', output.parent/'scale_report.json')):
        if data.get(label+'_sha256') != sha256(path):
            raise ValueError(f'stale build evidence: {label} hash mismatch; rebuild')
    return data
