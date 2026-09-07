#!/usr/bin/env python3
"""Generate a tiny invented form locally; no PDFs or fonts are distributed."""
import argparse
from pathlib import Path
import pymupdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; choose a new file')
    with pymupdf.open() as doc:
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), 'Community workshop', fontsize=16)
        page.insert_text((72, 110), 'Please write your full name below.', fontsize=11)
        field = pymupdf.Widget()
        field.field_name = 'participant_name'
        field.field_label = 'Full name'
        field.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
        field.rect = pymupdf.Rect(72, 140, 340, 164)
        field.border_width = 1
        field.border_color = (0.3, 0.3, 0.3)
        field.fill_color = (0.96, 0.96, 0.96)
        field.text_font = 'Helv'
        field.text_fontsize = 11
        page.add_widget(field)
        doc.set_language('en-US')
        doc.save(args.output)
    print('Synthetic input created; no translation or review has been performed.')


if __name__ == '__main__':
    main()
