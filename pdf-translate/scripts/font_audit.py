"""Optional codepoint coverage inventory; never a layout or delivery gate."""
import argparse
import json
from pathlib import Path

import pymupdf

from diagnostics import write_report
from retypeset import missing_glyphs
from text_model import effective_texts


def _validate_inputs(conf, data):
    if not isinstance(conf, dict):
        raise ValueError('translations.json must contain an object')
    segments = data.get('segments') if isinstance(data, dict) else data
    if not isinstance(segments, list):
        raise ValueError('segments.json must contain a segment array or an object with a segments array')
    for row in segments:
        if (not isinstance(row, dict)
                or not isinstance(row.get('id'), (int, str))
                or not isinstance(row.get('page'), int)
                or not isinstance(row.get('core'), str)
                or not isinstance(row.get('text'), str)
                or ('occurrence_id' in row and not isinstance(row['occurrence_id'], str))):
            raise ValueError('Each segment must be an object with id, integer page, string core and text')
    for key in ('translations', 'segment_targets'):
        if conf.get(key) is not None and not isinstance(conf[key], dict):
            raise ValueError(f'{key} must be an object')
    if conf.get('skip') is not None and (not isinstance(conf['skip'], list)
            or any(not isinstance(item, str) for item in conf['skip'])):
        raise ValueError('skip must be an array of strings')
    for key in ('merges', 'overrides', 'notices'):
        values = conf.get(key)
        if values is None:
            continue
        if not isinstance(values, list) or any(not isinstance(item, dict) for item in values):
            raise ValueError(f'{key} must be an array of objects')
        for item in values:
            if key == 'merges':
                lines = item.get('lines') or []
                if not isinstance(lines, list) or any(not isinstance(line, str) for line in lines):
                    raise ValueError('merge lines must be an array of strings')
            if key == 'overrides':
                parts = item.get('parts') or []
                if (not isinstance(item.get('contains'), str)
                        or not isinstance(item.get('page'), int)
                        or not isinstance(parts, list)
                        or any(not isinstance(part, dict) or not isinstance(part.get('text'), str)
                               for part in parts)):
                    raise ValueError('overrides require string contains, integer page and an array of text parts')
    return segments


def audit(work):
    work = Path(work)
    mapping = work / 'translations.json'
    segments_path = work / 'segments.json'
    conf = json.loads(mapping.read_text(encoding='utf-8-sig'))
    data = json.loads(segments_path.read_text(encoding='utf-8-sig'))
    segments = _validate_inputs(conf, data)
    rows = [row for row in effective_texts(conf, segments) if row['channel'] != 'widget']
    configured = conf.get('fonts')
    if not isinstance(configured, dict) or not configured.get('regular'):
        raise ValueError('fonts.regular must name a configured font file')
    paths = {}
    notes = []
    for role, value in configured.items():
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = mapping.parent / path
            if not path.is_file() and Path(value).is_file():
                path = Path(value).absolute()
                notes.append(f'{role}: legacy caller-relative path; prefer mapping-relative fonts')
        paths[role] = path
    paths['bold_italic'] = paths.get('bold_italic', paths.get('bold', paths.get('italic', paths['regular'])))
    paths['bold'] = paths.get('bold', paths['regular'])
    paths['italic'] = paths.get('italic', paths['regular'])
    faces = []
    for role, path in paths.items():
        try:
            font = pymupdf.Font(fontfile=str(path))
        except (RuntimeError, OSError, ValueError, pymupdf.mupdf.FzErrorBase) as exc:
            raise ValueError(f'Cannot load font role {role}: {path}: {exc}') from exc
        missing = []
        for row in rows:
            chars = missing_glyphs(font, row['target'])
            if chars:
                missing.append({**{k: row[k] for k in ('channel', 'segment_id', 'page') if k in row},
                                'codepoints': [f'U+{ord(ch):04X}' for ch in chars]})
        faces.append({'role': role, 'font': str(path), 'missing': missing,
                      'scope': 'All effective authored text checked against this face; actual role usage is not inferred.'})
    report = {'schema_version': '1.0', 'advisory': True,
              'status': 'coverage_gaps' if any(f['missing'] for f in faces) else 'codepoints_covered',
              'delivery_decision': 'unchanged', 'faces': faces, 'notes': notes,
              'limits': ['Coverage does not establish shaping, geometry, fallback behavior or all-style layout.',
                         'A gap in an unused role may not affect rendering; this is not an automatic rebuild gate.',
                         'Excluded: source markers, tails, passthrough text, widgets and future field input.',
                         'Final glyph, layout, verification and delivery gates remain authoritative.']}
    return report, [mapping, segments_path, *paths.values()]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        report, inputs = audit(args.work)
        if args.output:
            write_report(args.output, report, inputs)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['status'] == 'coverage_gaps' else 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'FAIL advisory font audit: {exc}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
