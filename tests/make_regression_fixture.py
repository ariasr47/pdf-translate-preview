#!/usr/bin/env python3
"""Generate the invented public regression form; distribute source only."""
import argparse
from pathlib import Path

import pymupdf


def _name_field(page, rect):
    field = pymupdf.Widget()
    field.field_name = "applicant_name"
    field.field_label = "Applicant full name"
    field.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    field.rect = rect
    field.field_value = "Sample Person"
    page.add_widget(field)


def build(output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    with pymupdf.open() as doc:
        first = doc.new_page(width=400, height=300)
        first.insert_text((40, 42), "Application", fontsize=16)
        first.insert_text((40, 82), "Applicant name:", fontsize=11)
        _name_field(first, pymupdf.Rect(40, 95, 260, 118))
        choice = pymupdf.Widget()
        choice.field_name = "contact_method"
        choice.field_label = "Preferred contact method"
        choice.field_type = pymupdf.PDF_WIDGET_TYPE_COMBOBOX
        choice.choice_values = ["Email", "Phone"]
        choice.field_value = "Email"
        choice.rect = pymupdf.Rect(40, 155, 180, 178)
        first.add_widget(choice)

        second = doc.new_page(width=400, height=300)
        second.insert_text((40, 52), "Applicant name:", fontsize=11)
        _name_field(second, pymupdf.Rect(40, 65, 260, 88))
        doc.set_metadata({"title": "Public regression form", "author": "Synthetic fixture"})
        doc.set_toc([[1, "Application", 1]])
        doc.set_language("en-US")
        doc.save(output, garbage=4, deflate=True, no_new_id=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)
    print("Generated synthetic PDF in the requested location; no fixture bytes are distributed.")


if __name__ == "__main__":
    main()
