"""Run an authored Spanish translation of the generated sample, without a service."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', required=True, type=Path,
                        help='User-supplied regular TrueType font with embedding permission')
    parser.add_argument('--output', required=True, type=Path, help='New job directory')
    args = parser.parse_args()
    font = args.font.resolve(strict=True)
    from fontTools.ttLib import TTFont
    with TTFont(font) as face:
        if 'glyf' not in face:
            parser.error('The sample requires a TrueType glyf font.')
    job = args.output.resolve()
    job.mkdir(parents=True, exist_ok=False)
    public = Path(__file__).resolve().parents[1]
    root = public if (public / 'pdf-translate').is_dir() else public.parents[1]
    pipeline = root / 'pdf-translate/scripts/pipeline.py'

    def run(label, script, *arguments):
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(script),
                                 *map(str, arguments)], capture_output=True,
                                encoding='utf-8', errors='replace')
        (job / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'{label} failed ({result.returncode}); see {job / (label + ".log")}')

    source = job / 'source.pdf'
    run('01-generate', public / 'examples/make_example.py', '--output', source)
    widget = job / 'widget-authored.json'
    widget.write_text(json.dumps({'participant_name': {'tooltip': {
        'source': 'Full name', 'target': 'Nombre completo'}}}), encoding='utf-8')
    run('02-init', pipeline, 'init', source, '--work', job, '--widget-text', widget)
    run('03-scaffold', pipeline, 'from-cores', '--work', job)
    mapping_path = job / 'translations.json'
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    authored = {'Community workshop': 'Taller comunitario',
                'Please write your full name below.': 'Escriba su nombre completo abajo.'}
    if set(mapping['translations']) != set(authored):
        raise RuntimeError('Sample text changed; review and update the authored example.')
    mapping.update(lang='es-US', translations=authored,
                   fonts={role: str(font) for role in ('regular', 'bold', 'italic', 'bold_italic')})
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    run('04-qa', pipeline, 'qa', '--work', job)
    run('05-fonts', pipeline, 'audit-fonts', '--work', job, '--output', job / 'font-audit.json')
    intermediate = job / 'intermediate.pdf'
    run('06-rebuild', pipeline, 'rebuild', '--work', job, source, intermediate)
    run('07-finish', pipeline, 'finish', source, intermediate, font,
        job / 'final.pdf', job / 'comparison.html')
    delivery = json.loads((job / 'delivery.json').read_text(encoding='utf-8'))
    if delivery['status'] != 'review_required':
        raise RuntimeError('Unexpected review state; inspect delivery.json.')
    print(f'Created {job / "final.pdf"}. Automated checks passed; human review is still required.')


if __name__ == '__main__':
    main()
