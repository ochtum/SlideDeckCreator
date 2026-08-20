#!/usr/bin/env python3
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("ERROR: pypdf is required: python -m pip install pypdf")
    raise SystemExit(2)

EXPECTED_WIDTH_PT = 960.0
EXPECTED_HEIGHT_PT = 540.0
TOLERANCE_PT = 1.0


def main():
    if len(sys.argv) != 3:
        print("Usage: validate_pdf.py <index.pdf> <index.html>")
        return 2

    pdf_path = Path(sys.argv[1])
    html_path = Path(sys.argv[2])
    reader = PdfReader(str(pdf_path))
    html = html_path.read_text(encoding="utf-8")
    slide_count = len(
        re.findall(r"<section\b[^>]*class=[\"'][^\"']*\bslide\b", html, re.I)
    )
    errors = []

    if len(reader.pages) != slide_count:
        errors.append(
            f"PDF has {len(reader.pages)} pages but HTML has {slide_count} slides"
        )

    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if (
            abs(width - EXPECTED_WIDTH_PT) > TOLERANCE_PT
            or abs(height - EXPECTED_HEIGHT_PT) > TOLERANCE_PT
        ):
            errors.append(
                f"page {index} is {width:.2f}x{height:.2f}pt; "
                f"expected {EXPECTED_WIDTH_PT:.0f}x{EXPECTED_HEIGHT_PT:.0f}pt"
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"OK: {len(reader.pages)} PDF pages at "
        f"{EXPECTED_WIDTH_PT:.0f}x{EXPECTED_HEIGHT_PT:.0f}pt (16:9)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
