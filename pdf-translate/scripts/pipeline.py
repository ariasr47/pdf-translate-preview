#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hot-path wrappers around the stage scripts.

The deterministic pipeline is a few seconds. Wall-clock is the translation
and visual loop. Use `rebuild` after the first extract instead of re-running
strip / extract / prepare_font / compare every round.

Usage:
  python3 pipeline.py init ORIGINAL.pdf --work DIR [--captions captions.json]
                                                  [--widget-text wt.json]
                                                  [--keep-encryption]
                                                  [--content-policy preserve-report|refuse-active]
                                                  [--pages 1-10]
      strip + extract into DIR (stripped.pdf, segments.json,
      to_translate.json, widget_text.json). Run it once bare to get the
      widget_text.json scaffold, author the targets, then run it again with
      --widget-text to apply tooltips, dropdown labels and defaults.

  python3 pipeline.py from-cores --work DIR [--force]
      scaffold DIR/translations.json from DIR/to_translate.json cores.
      Values are JSON null (retypeset still FAILs until you author them).
      Refuses to overwrite unless --force. No model, no auto-merge.

  python3 pipeline.py propose-merges --work DIR [--accept] [--min-lines 2]
      turn the extractor's wrapped-paragraph candidates into ready-to-edit
      "merges" entries with html: null. Writes DIR/merges_proposed.json;
      --accept also folds them into DIR/translations.json. Nothing merges
      without this command, and a null html still FAILs retypeset until
      you author the paragraph. Paragraph mode for manuals and brochures.

  python3 pipeline.py merge-mappings OUT.json IN.json [IN.json ...]
      combine mappings authored per page range into one. Conflicting
      values for the same core are reported and nothing is written unless
      --last-wins.

  python3 pipeline.py qa --work DIR [--glossary glossary.csv] [--strict]
      linguistic QA on DIR/translations.json before you build: numbers and
      dates that moved, untranslated lines, inconsistent variants, brackets,
      punctuation parity, spacing, expansion band. Advisory; --strict makes
      warnings fail too.

  python3 pipeline.py rebuild --work DIR ORIGINAL.pdf OUT.pdf [verify flags...]
      retypeset DIR/stripped.pdf + DIR/segments.json + DIR/translations.json
      then verify ORIGINAL.pdf OUT.pdf with any extra verify flags

  python3 pipeline.py render ORIGINAL.pdf TRANSLATED.pdf renders/ [--dpi 110]

  python3 pipeline.py finish ORIGINAL.pdf OUT.pdf FONT.ttf FINAL.pdf HTML
      stage field fonts, verify final bytes with mapping/segments, then publish
      final PDF + comparison + hash-bound delivery.json (existing outputs refused)
      [--translations FILE --segments FILE --review FILE --allow PHRASES]

  python3 pipeline.py review DELIVERY.json REVIEW.json
      attach declared review of exact final bytes; never edit the PDF

  python3 pipeline.py diagnose STAGE.log [--output NEW_REPORT.json]
      group explicit failures and suggest bounded repairs; does not change gates

  python3 pipeline.py audit-form SOURCE.pdf [--output NEW_REPORT.json]
      inventory form mechanics; does not establish accessibility conformance

  python3 pipeline.py bilingual ORIGINAL.pdf FINAL.pdf BOTH.pdf
      optional reading copy with source and target pages interleaved.
      Refuses a fillable input unless --reading-copy (duplicate field
      names fill together).
"""
import json
import os
import sys
import time
import pikepdf

# Same directory as the stage scripts.
from extract_segments import main as extract_main
from field_fonts import field_fonts
from compare import compare
from render_pages import render_pages
from retypeset import retypeset
from strip_text import strip_text, WidgetTextError
from bilingual import main as bilingual_main
from qa_check import main as qa_main
from verify import verify, main as verify_main


def cmd_init(argv):
    src = argv[0]
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    from pathlib import Path
    from input_policy import inventory, enforce
    from provenance import sha256, disjoint_files
    outputs = ('stripped.pdf', 'segments.json', 'to_translate.json',
               'widget_text.json', 'preflight.json')
    generated = [Path(work)/name for name in outputs]
    protected = [src] + ([argv[argv.index('--captions')+1]] if '--captions' in argv else [])
    widget_input = [argv[argv.index('--widget-text')+1]] if '--widget-text' in argv else []
    if (not disjoint_files(protected, generated)
            or not disjoint_files(widget_input, [p for p in generated if p.name != 'widget_text.json'])
            or any(not disjoint_files([p], generated[i+1:]) for i,p in enumerate(generated))):
        print('FAIL init: source and generated job files must be distinct')
        return 2
    os.makedirs(work, exist_ok=True)
    policy = argv[argv.index('--content-policy')+1] if '--content-policy' in argv else 'preserve-report'
    try:
        capabilities = inventory(src)
        preflight = {'schema_version': '1.0', 'source_sha256': sha256(src),
                     'policy': policy, 'inventory': capabilities,
                     'keep_encryption': '--keep-encryption' in argv}
        with open(os.path.join(work, 'preflight.json'), 'w', encoding='utf-8') as stream:
            json.dump(preflight, stream, ensure_ascii=False, indent=2)
        print(f'preflight: {len(capabilities["actions"])} action(s), '
              f'{len(capabilities["attachments"])} attachment(s), '
              f'{len(capabilities["signatures"])} signature(s); policy={policy}')
        enforce(capabilities, policy)
    except (OSError, ValueError, pikepdf.PdfError) as exc:
        print(f'FAIL input policy: {exc}')
        return 2
    captions = None
    if '--captions' in argv:
        with open(argv[argv.index('--captions') + 1], encoding='utf-8') as f:
            captions = json.load(f)
    widget_text = None
    if '--widget-text' in argv:
        with open(argv[argv.index('--widget-text') + 1], encoding='utf-8') as f:
            widget_text = json.load(f)
    stripped = os.path.join(work, 'stripped.pdf')
    t0 = time.perf_counter()
    try:
        report = strip_text(src, stripped, captions=captions,
                            widget_text=widget_text,
                            keep_encryption='--keep-encryption' in argv)
    except WidgetTextError as exc:
        print(f'FAIL widget text: {exc}')
        return 2
    print(f'strip: xfa_removed={report.get("xfa_removed")} '
          f'dead_buttons={len(report.get("dead_buttons") or [])}')
    if report.get('perms_removed'):
        print(f'strip: deleted /Perms {report["perms_removed"]}')
    if report.get('certified'):
        print('WARNING: the source was CERTIFIED (/Perms /DocMDP); the '
              'translation is not. Say so when you deliver it.')
    if report.get('encryption', {}).get('encrypted') and not report.get('reencrypted'):
        print('NOTE: the source was encrypted; the output is not '
              '(--keep-encryption re-applies its permission bits).')
    leftover = report.get('leftover_text') or []
    if leftover:
        print(f'FAIL: page text survived strip on {len(leftover)} page(s); '
              f'{stripped} was not written:')
        for item in leftover:
            print(f"  p{item['page']}: {item['text']}")
        return 1
    extract_args = [src, '--outdir', work]
    if '--max-per-kind' in argv:
        extract_args += ['--max-per-kind', argv[argv.index('--max-per-kind') + 1]]
    if '--pages' in argv:
        extract_args += ['--pages', argv[argv.index('--pages') + 1]]
    rc = extract_main(extract_args)
    if rc == 0:
        segment_path = Path(work)/'segments.json'
        extracted = json.loads(segment_path.read_text(encoding='utf-8-sig'))
        extracted['input_policy'] = json.loads((Path(work)/'preflight.json').read_text(encoding='utf-8-sig'))
        if widget_text is not None:
            (Path(work)/'widget_text.json').write_text(json.dumps(widget_text, ensure_ascii=False, indent=2), encoding='utf-8')
        segment_path.write_text(json.dumps(extracted, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'elapsed {time.perf_counter()-t0:.2f}s -> {work}')
    return rc


def scaffold_from_cores(to_translate_path, out_path, force=False):
    """Write translations.json with a null for every core. Returns 0, or 2."""
    if not os.path.isfile(to_translate_path):
        print(f'from-cores: missing {to_translate_path}')
        return 2
    if os.path.isfile(out_path) and not force:
        print(f'from-cores: {out_path} exists (pass --force to overwrite)')
        return 2
    with open(to_translate_path, encoding='utf-8') as f:
        data = json.load(f)
    cores = data.get('cores') or []
    translations = {}
    for c in cores:
        text = (c.get('text') if isinstance(c, dict) else None) or ''
        if text:
            translations[text] = None
    conf = {
        'fonts': {'regular': 'font-sub.ttf', 'bold': 'font-sub.ttf',
                  'italic': 'font-sub.ttf', 'bold_italic': 'font-sub.ttf'},
        # BCP-47 tag of the TARGET language, e.g. "es-MX". retypeset writes
        # it to /Lang and to dc:language; verify REVIEWs a mapping without
        # one, because the output otherwise tells screen readers it is
        # still in the source language.
        'lang': None,
        'translations': translations,
        'segment_targets': {item['occurrence_id']: None
                            for item in data.get('occurrences', [])
                            if item.get('occurrence_id')},
        'merges': [],
        'overrides': [],
        'center': [],
        'right': [],
        'skip': [],
        'allow_scale': [],
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'from-cores: {len(translations)} cores -> {out_path} '
          f'(values are null — author them; do not ship)')
    return 0


def cmd_from_cores(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    force = '--force' in argv
    to_path = os.path.join(work, 'to_translate.json')
    out_path = os.path.join(work, 'translations.json')
    return scaffold_from_cores(to_path, out_path, force=force)


def propose_merges(work, accept=False, min_lines=2):
    """Shape the extractor's merge candidates as editable merges entries.

    A wrapped paragraph must be translated as one unit and re-flowed;
    translating each visual line on its own is how a brochure turns to
    fragments. Geometry can propose those groups but must never apply
    them — sibling list items share a column and read exactly like a
    wrapped paragraph. So: propose in bulk, accept in bulk, author each
    html. A proposal with html null still fails retypeset.
    """
    seg_path = os.path.join(work, 'segments.json')
    if not os.path.isfile(seg_path):
        print(f'propose-merges: missing {seg_path}')
        return 2
    with open(seg_path, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {s['id']: s for s in data.get('segments') or []}
    proposals = []
    for w in data.get('warnings') or []:
        ids = w.get('ids') or []
        # Candidates carry kind "merge-candidate" since row 22; a
        # segments.json from an earlier extractor has none. Both propose:
        # a stale work directory must not lose its paragraphs.
        if w.get('kind') not in (None, 'merge-candidate', 'narrow-column'):
            continue
        if len(ids) < min_lines:
            continue
        segs = [by_id[i] for i in ids if i in by_id]
        if len(segs) < min_lines:
            continue
        proposals.append({
            'page': w.get('page', segs[0]['page']),
            'lines': [s['text'].strip() for s in segs],
            'html': None,
            'align': 'left',
            # Null means "re-flow into the union of these lines". A rect
            # here is the author's decision and nothing else's: look at the
            # page first (row 26).
            'box': None,
            'why': w.get('why', ''),
        })
    out_path = os.path.join(work, 'merges_proposed.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'merges': proposals}, f, ensure_ascii=False, indent=1)
    print(f'propose-merges: {len(proposals)} candidate(s) -> {out_path} '
          f'(html is null — author each, or delete the entry; box is null '
          f'— set one only if you looked at the page)')
    if not accept:
        print('propose-merges: nothing changed. Re-run with --accept to fold '
              'these into translations.json.')
        return 0

    tr_path = os.path.join(work, 'translations.json')
    if not os.path.isfile(tr_path):
        print(f'propose-merges: missing {tr_path} (run from-cores first)')
        return 2
    with open(tr_path, encoding='utf-8') as f:
        conf = json.load(f)
    existing = {tuple(m.get('lines') or []) for m in conf.get('merges') or []}
    merges = list(conf.get('merges') or [])
    added = 0
    for p in proposals:
        key = tuple(p['lines'])
        if key in existing:
            continue
        merges.append({k: p[k] for k in ('page', 'lines', 'html', 'align')})
        existing.add(key)
        added += 1
    conf['merges'] = merges
    with open(tr_path, 'w', encoding='utf-8') as f:
        json.dump(conf, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'propose-merges: added {added} merge(s) to {tr_path}; author every '
          f'html (null still FAILs retypeset)')
    return 0


def cmd_propose_merges(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    min_lines = int(argv[argv.index('--min-lines') + 1]
                    if '--min-lines' in argv else 2)
    return propose_merges(work, accept='--accept' in argv,
                          min_lines=min_lines)


def merge_mappings(out_path, paths, last_wins=False):
    """Combine per-page-range mappings into one. Conflicts stop the write."""
    merged = None
    conflicts = []
    for path in paths:
        with open(path, encoding='utf-8') as f:
            conf = json.load(f)
        if merged is None:
            merged = json.loads(json.dumps(conf))
            continue
        for channel in ('translations', 'segment_targets'):
            merged.setdefault(channel, {})
            for core, target in (conf.get(channel) or {}).items():
                have = merged[channel].get(core, KeyError)
                if have is not KeyError and have != target and target is not None:
                    if have is None or last_wins:
                        merged[channel][core] = target
                    else:
                        conflicts.append((channel+':'+core, have, target, path))
                elif have is KeyError:
                    merged[channel][core] = target
        for key in ('merges', 'overrides'):
            merged.setdefault(key, [])
            merged[key].extend(conf.get(key) or [])
        for key in ('center', 'right', 'skip', 'allow_scale',
                    'allow_translate'):
            if conf.get(key):
                merged[key] = sorted(set(merged.get(key) or [])
                                     | set(conf[key]))
    if merged is None:
        print('merge-mappings: no inputs')
        return 2
    if conflicts:
        print(f'merge-mappings: {len(conflicts)} conflicting core(s); '
              f'nothing written (pass --last-wins to take the later file):')
        for core, a, b, path in conflicts[:20]:
            print(f'  {core[:50]!r}: {a!r} vs {b!r} (from {path})')
        return 1
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=1)
        f.write('\n')
    total = len(merged.get('translations') or {})
    print(f'merge-mappings: {total} cores -> {out_path}')
    return 0


def cmd_merge_mappings(argv):
    rest = [a for a in argv if a != '--last-wins']
    if len(rest) < 2:
        print('merge-mappings: OUT.json IN.json [IN.json ...]')
        return 2
    return merge_mappings(rest[0], rest[1:], last_wins='--last-wins' in argv)


def cmd_qa(argv):
    work = argv[argv.index('--work') + 1] if '--work' in argv else '.'
    rest = [a for a in argv if a not in ('--work', work)]
    tr = os.path.join(work, 'translations.json')
    segs = os.path.join(work, 'segments.json')
    if not os.path.isfile(tr):
        print(f'qa: missing {tr}')
        return 2
    args = [tr]
    if os.path.isfile(segs):
        args += ['--segments', segs]
    return qa_main(args + rest)


def cmd_rebuild(argv):
    if '--work' not in argv:
        print('rebuild requires --work DIR')
        return 2
    wi = argv.index('--work')
    work = argv[wi + 1]
    rest = argv[:wi] + argv[wi + 2:]
    if len(rest) < 2:
        print('rebuild: ORIGINAL.pdf OUT.pdf [verify flags...]')
        return 2
    orig, out, extra = rest[0], rest[1], rest[2:]
    orig = os.path.abspath(orig)
    out = os.path.abspath(out)
    work = os.path.abspath(work)
    stripped = os.path.join(work, 'stripped.pdf')
    segs = os.path.join(work, 'segments.json')
    tr = os.path.join(work, 'translations.json')
    t0 = time.perf_counter()
    from provenance import disjoint_files
    generated = [out] + [os.path.join(os.path.dirname(out), name)
                         for name in ('scale_report.json', 'build-evidence.json')]
    if not disjoint_files((orig, stripped, segs, tr), generated):
        print('FAIL rebuild: output or sidecar aliases an original/input file')
        return 2
    rc = retypeset(stripped, segs, tr, out)
    if rc != 0:
        print(f'elapsed {time.perf_counter()-t0:.2f}s (retypeset failed)')
        return rc
    # Retypeset resolves font paths beside the mapping. Leave the caller's
    # directory intact so all command-line verification paths keep meaning.
    defaults = []
    for flag, value in (('--translations', tr), ('--segments', segs),
                        ('--source-words-from', segs)):
        if flag not in extra:
            defaults += [flag, value]
    rc = verify_main([orig, out] + defaults + extra)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return rc


def cmd_render(argv):
    dpi = int(argv[argv.index('--dpi') + 1]) if '--dpi' in argv else 110
    orig, trans, outdir = argv[0], argv[1], argv[2]
    t0 = time.perf_counter()
    render_pages(orig, trans, outdir, dpi=dpi)
    print(f'elapsed {time.perf_counter()-t0:.2f}s')
    return 0


def cmd_finish(argv):
    import argparse
    from delivery import finalize
    parser = argparse.ArgumentParser(prog='pipeline finish')
    for name in ('original', 'intermediate', 'font', 'final', 'html'):
        parser.add_argument(name)
    parser.add_argument('--translations')
    parser.add_argument('--segments')
    parser.add_argument('--review')
    parser.add_argument('--allow', default='')
    parser.add_argument('--fill-text', default='Test value 123')
    args = parser.parse_args(argv)
    return finalize(args.original, args.intermediate, args.font, args.final,
                    args.html, translations=args.translations,
                    segments=args.segments, review=args.review,
                    allow=[s.strip() for s in args.allow.split(',') if s.strip()],
                    fill_text=args.fill_text)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd in ('diagnose', 'audit-form'):
        from diagnostics import main as diagnostics_main
        return diagnostics_main([cmd, *rest])
    if cmd == 'init':
        return cmd_init(rest)
    if cmd == 'from-cores':
        return cmd_from_cores(rest)
    if cmd == 'propose-merges':
        return cmd_propose_merges(rest)
    if cmd == 'merge-mappings':
        return cmd_merge_mappings(rest)
    if cmd == 'qa':
        return cmd_qa(rest)
    if cmd == 'rebuild':
        return cmd_rebuild(rest)
    if cmd == 'render':
        return cmd_render(rest)
    if cmd == 'finish':
        return cmd_finish(rest)
    if cmd == 'review':
        from delivery import record_review
        if len(rest) != 2:
            print('review: DELIVERY.json REVIEW.json')
            return 2
        return record_review(*rest)
    if cmd == 'bilingual':
        return bilingual_main(rest)
    print('unknown command', cmd)
    print(__doc__)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
