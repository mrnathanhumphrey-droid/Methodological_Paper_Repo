"""
Paper 9 Phase 1 - OCR the FY2024 WRAPS report (cid-encoded PDF, no extractable text).

FY2024 PDF (fy2024_arrivals_by_state_nationality.pdf, 25 pages, ~2.6 MB) uses
Type3 font 'T1' with no character map -> pdfplumber + pymupdf get_text both
return either empty or shifted-glyph junk. Visual layer is intact though, so
render-to-PNG + Tesseract OCR recovers the table.

Procedure:
 1. Render each PDF page at 3x DPI (300 effective DPI) via pymupdf.
 2. Run Tesseract on each page image with PSM 6 (uniform block of text).
 3. Concatenate OCR text and feed to the existing FY2021-2023 PDF parser
    (paper9_orr_wraps_parse.py parse_pdf inputs same STATE-Total layout).
 4. Output: appended rows to the WRAPS long-format CSV.
"""
from __future__ import annotations
import sys, os
from pathlib import Path
import pymupdf
import pytesseract
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

# Tesseract default install location (winget UB-Mannheim)
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESS):
    pytesseract.pytesseract.tesseract_cmd = TESS

PDF = Path("D:/IDP/data/paper9/orr_wraps/raw/fy2024_arrivals_by_state_nationality.pdf")
PNG_DIR = Path("D:/IDP/data/paper9/orr_wraps/raw/fy2024_page_pngs")
PNG_DIR.mkdir(parents=True, exist_ok=True)
OCR_OUT = Path("D:/IDP/data/paper9/orr_wraps/raw/fy2024_ocr_text.txt")


def render_pages():
    doc = pymupdf.open(PDF)
    print(f"Rendering {len(doc)} pages...")
    mat = pymupdf.Matrix(3.0, 3.0)  # ~300 DPI effective
    for i in range(len(doc)):
        out = PNG_DIR / f"page_{i+1:02d}.png"
        if out.exists() and out.stat().st_size > 50_000:
            continue
        pix = doc[i].get_pixmap(matrix=mat)
        pix.save(out)
    return len(doc)


def ocr_all(n_pages: int) -> str:
    all_text = []
    for i in range(n_pages):
        png = PNG_DIR / f"page_{i+1:02d}.png"
        # PSM 6 = uniform block of text (best for tables)
        txt = pytesseract.image_to_string(Image.open(png), config="--psm 6")
        print(f"  page {i+1:02d}: {len(txt)} chars")
        all_text.append(f"=== PAGE {i+1} ===\n{txt}\n")
    return "\n".join(all_text)


def main():
    n = render_pages()
    print(f"Rendered {n} pages to {PNG_DIR}")
    print(f"OCRing all pages (this takes a minute)...")
    text = ocr_all(n)
    OCR_OUT.write_text(text, encoding="utf-8")
    print(f"\nOCR output saved: {OCR_OUT} ({OCR_OUT.stat().st_size/1e3:.1f} KB)")


if __name__ == "__main__":
    main()
