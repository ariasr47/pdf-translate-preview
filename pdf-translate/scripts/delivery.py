"""Finalize and independently verify the exact bytes named by a delivery.

The manifest is written last. Automated success never implies that a person
reviewed the translation or that a viewer/assistive-technology test occurred.
"""
import io
import json
import os
import platform
import shutil
import tempfile
from contextlib import redirect_stdout
from importlib.metadata import version
from pathlib import Path

from compare import compare
from field_fonts import field_fonts
from qa_check import qa_check
from verify import verify
from provenance import sha256, validate_build, disjoint_files
from input_policy import inventory, enforce

SCHEMA_VERSION = '1.0'
REVIEW_KINDS = ('visual', 'bilingual_human', 'monolingual_human',
                'model_bilingual', 'viewer', 'accessibility')


def read_review(path=None):
    value = {} if path is None else json.loads(Path(path).read_text(encoding='utf-8-sig'))
    return validate_review(value)


def validate_review(value):
    result = {kind: {'status': 'not_performed'} for kind in REVIEW_KINDS}
    if not isinstance(value, dict) or set(value) - set(REVIEW_KINDS):
        raise ValueError('review must contain only named review categories')
    for kind, entry in value.items():
        if not isinstance(entry, dict) or set(entry) - {'status', 'reviewer', 'scope', 'evidence', 'output_sha256'} or entry.get('status') not in (
                'not_performed', 'passed', 'failed', 'not_applicable'):
            raise ValueError(f'invalid review status for {kind}')
        if entry['status'] != 'not_performed' and not all(
                isinstance(entry.get(key), str) and entry[key].strip()
                for key in ('reviewer', 'scope', 'evidence')):
            raise ValueError(f'{kind} review requires reviewer, scope and evidence')
        result[kind] = entry
    return result


def _record(path, root):
    path = Path(path).resolve()
    return {'path': Path(os.path.relpath(path, root)).as_posix(), 'sha256': sha256(path)}


def review_state(review):
    if any(item['status'] == 'failed' for item in review.values()):
        return 'review_failed'
    if review['visual']['status'] == 'passed' and review['bilingual_human']['status'] == 'passed':
        return 'reviewed'
    return 'review_required'


def bind_review(review, output_hash):
    for kind, item in review.items():
        if item['status'] != 'not_performed' and item.get('output_sha256') != output_hash:
            raise ValueError(f'{kind} review must name the exact final PDF SHA-256')


def finalize(original, intermediate, font, final, html, *, translations=None,
             segments=None, review=None, allow=None, fill_text='Test value 123'):
    """Stage, verify, then publish local artifacts and their manifest. Return rc."""
    original, intermediate, font, final, html = map(
        lambda p: Path(p).resolve(), (original, intermediate, font, final, html))
    root = final.parent
    translations = Path(translations or intermediate.parent/'translations.json').resolve()
    segments = Path(segments or intermediate.parent/'segments.json').resolve()
    manifest_path = root/'delivery.json'
    inputs = (original, intermediate, font, translations, segments)
    scale_destination = root/'delivery-scale-report.json'
    destinations = (final, html, manifest_path, root/'verification.json', scale_destination)
    try:
        if any(not path.is_file() for path in inputs):
            raise ValueError('finish requires original, intermediate, full font, translations and segments files')
        if len(set(destinations)) != len(destinations) or not disjoint_files(inputs, destinations):
            raise ValueError('delivery outputs must be distinct from each other and every input')
        if any(path.exists() or path.is_symlink() for path in destinations):
            raise ValueError('delivery output already exists; use a new delivery directory or filenames')
        if html.parent != root:
            raise ValueError('comparison and final PDF must share the delivery directory')
        if final.suffix.lower() != '.pdf' or html.suffix.lower() not in ('.html', '.htm'):
            raise ValueError('final output must be .pdf and comparison must be .html or .htm')
        # A manifest stays portable and cannot authorize files outside its job.
        if not translations.is_relative_to(root) or not segments.is_relative_to(root):
            raise ValueError('translations and segments must be inside the delivery directory')
        review_status = read_review(review)
        config = json.loads(translations.read_text(encoding='utf-8-sig'))
        if not isinstance(config.get('lang'), str) or not config['lang'].strip():
            raise ValueError('finish requires the target language tag in translations.json')
        build = validate_build(intermediate, segments, translations)
        extracted = json.loads(segments.read_text(encoding='utf-8-sig'))
        if extracted.get('source_sha256') != sha256(original):
            raise ValueError('segments are not bound to the original PDF; extract and rebuild')
        source_inventory = inventory(original)
        intermediate_inventory = inventory(intermediate)
        preflight = build['input_policy']
        if preflight.get('source_sha256') != sha256(original):
            raise ValueError('build input policy belongs to a different source PDF')
        policy = preflight['policy']
        if preflight.get('keep_encryption') and source_inventory['encrypted'] and not intermediate_inventory['encrypted']:
            raise ValueError('requested encryption was lost before finalization')
        enforce(source_inventory, policy)
        findings = qa_check(str(translations), str(segments))
        if any(item.get('severity') == 'error' for item in findings):
            raise ValueError('translation QA has errors; run pipeline qa and resolve them')
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.delivery-', dir=root) as tmp:
            stage = Path(tmp)
            staged_pdf = stage/final.name
            rc = field_fonts(str(intermediate), str(font), str(staged_pdf))
            if rc:
                return rc
            output_inventory = inventory(staged_pdf)
            enforce(output_inventory, policy)
            if any(output_inventory[key] != intermediate_inventory[key]
                   for key in ('encrypted', 'permissions')):
                raise ValueError('finalization changed encryption or permission settings')
            bind_review(review_status, sha256(staged_pdf))
            shutil.copyfile(intermediate.parent/'scale_report.json', stage/'scale_report.json')
            log = io.StringIO()
            with redirect_stdout(log):
                rc = verify(str(original), str(staged_pdf), translations=str(translations),
                            segments=str(segments), source_words_from=str(segments),
                            allow=allow or [], fill_text=fill_text)
            print(log.getvalue(), end='')
            if rc:
                print('FAIL final delivery: verification rejected the finalized PDF')
                return rc
            staged_html = stage/html.name
            compare(str(original), str(staged_pdf), str(staged_html))
            records = {'output': _record(staged_pdf, stage),
                       'source': {'name': original.name, 'sha256': sha256(original)},
                       'translations': _record(translations, root),
                       'segments': _record(segments, root),
                       'field_font': {'name': font.name, 'sha256': sha256(font)},
                       'comparison': _record(staged_html, stage),
                       'scale_report': {'path': scale_destination.name,
                                        'sha256': sha256(stage/'scale_report.json')}}
            verification = {'schema_version': SCHEMA_VERSION, 'exit_code': rc,
                            'output_sha256': records['output']['sha256'],
                            'settings': {'allow': allow or [], 'fill_text': fill_text,
                                         'translations_sha256': records['translations']['sha256'],
                                         'segments_sha256': records['segments']['sha256']},
                            'log': log.getvalue(), 'qa': findings}
            status = review_state(review_status)
            manifest = {
                'schema_version': SCHEMA_VERSION, 'status': status,
                'output': final.name,
                'translations': Path(os.path.relpath(translations, root)).as_posix(),
                'segments': Path(os.path.relpath(segments, root)).as_posix(),
                'allow': allow or [], 'fill_text': fill_text,
                'artifacts': records, 'verification': verification,
                'build': {**build, 'fonts': {role: {'sha256': item['sha256'],
                    'name': Path(item['path']).name} for role, item in build['fonts'].items()}},
                'review': review_status, 'locale': config['lang'],
                'security': {'policy': policy, 'source': source_inventory,
                             'output': output_inventory,
                             'signature_validation': 'not_performed',
                             'certification': 'translated derivative; not certified'},
                'environment': {'python': platform.python_version(),
                    'platform': platform.platform(), 'dependencies': {
                        name: version(name) for name in ('PyMuPDF', 'pikepdf', 'fonttools')}},
            }
            (stage/'verification.json').write_text(json.dumps(
                verification, ensure_ascii=False, indent=2), encoding='utf-8')
            (stage/'delivery.json').write_text(json.dumps(
                manifest, ensure_ascii=False, indent=2), encoding='utf-8')
            # Manifest last: incomplete copies cannot masquerade as a delivery.
            for src, dst in ((staged_pdf, final), (staged_html, html),
                             (stage/'scale_report.json', scale_destination),
                             (stage/'verification.json', root/'verification.json'),
                             (stage/'delivery.json', manifest_path)):
                os.replace(src, dst)
            print(f'delivery: {status}; manifest {manifest_path}')
            return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'FAIL final delivery: {exc}')
        return 2


def validate_manifest(path):
    """Read a v1 delivery and reject stale or substituted output/evidence."""
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if data.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('unsupported delivery schema_version')
    root = path.parent
    for name in ('output', 'translations', 'segments', 'comparison', 'scale_report'):
        record = data['artifacts'][name]
        actual = (root/record['path']).resolve()
        if not actual.is_relative_to(root) or not actual.is_file():
            raise ValueError(f'invalid delivery artifact: {name}')
        if sha256(actual) != record['sha256']:
            raise ValueError(f'delivery artifact hash mismatch: {name}')
        if name in ('output', 'translations', 'segments') and (
                root/data[name]).resolve() != actual:
            raise ValueError(f'delivery selection mismatch: {name}')
    if data['verification']['exit_code'] != 0 or data['verification'][
            'output_sha256'] != data['artifacts']['output']['sha256']:
        raise ValueError('delivery verification is not bound to successful final output')
    settings = data['verification']['settings']
    if any(settings.get(key+'_sha256') != data['artifacts'][key]['sha256']
           for key in ('translations', 'segments')) or any(
               settings.get(key) != data.get(key) for key in ('allow', 'fill_text')):
        raise ValueError('delivery verification settings do not match the selected artifacts')
    if data['build']['scale_report_sha256'] != data['artifacts']['scale_report']['sha256']:
        raise ValueError('delivery scale report is not bound to the build')
    if any(data['build'].get(key+'_sha256') != data['artifacts'][key]['sha256']
           for key in ('translations', 'segments')):
        raise ValueError('delivery mapping/segments are not bound to the build')
    if set(data['review']) != set(REVIEW_KINDS):
        raise ValueError('delivery review must contain every review category')
    validate_review(data['review'])
    bind_review(data['review'], data['artifacts']['output']['sha256'])
    if data['status'] != review_state(data['review']):
        raise ValueError('delivery status does not match its review evidence')
    return data


def record_review(manifest, review):
    """Attach declared review of existing exact bytes; never edit the PDF."""
    path = Path(manifest).resolve()
    try:
        data = validate_manifest(path)
        changes = json.loads(Path(review).read_text(encoding='utf-8-sig'))
        validated = read_review(review)
        for kind in changes:
            data['review'][kind] = validated[kind]
        bind_review(data['review'], data['artifacts']['output']['sha256'])
        data['status'] = review_state(data['review'])
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=path.parent, prefix='.review-', suffix='.json', delete=False) as stream:
            tmp = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
        try:
            validate_manifest(path)
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
        print(f'review recorded: {data["status"]}')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL review: {exc}')
        return 2
