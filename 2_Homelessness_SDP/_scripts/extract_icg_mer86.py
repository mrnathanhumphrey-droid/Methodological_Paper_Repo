"""Extract text from ICG MER N°86 PDF + scan for Yemen Six Wars admin units."""
import pathlib, sys, io, re
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
from pypdf import PdfReader

PDF = pathlib.Path(r"D:/IDP/historical_polygons/_sources/icg_mer86_yemen_saada.pdf")
OUT_TXT = pathlib.Path(r"D:/IDP/historical_polygons/_sources/icg_mer86_yemen_saada.txt")

# Yemen governorate + district candidates implicated in Six Wars 2004-2010.
# (Pre-extraction candidate list — to be confirmed against PDF text.)
YEMEN_GOVERNORATES = [
    "Saada", "Sa'dah", "Sa'da", "Sadah", "Sa`da", "Sa'ada",
    "Amran", "'Amran", "Amraan",
    "Hajjah", "Hajja",
    "Al-Jawf", "Al Jawf", "Jawf",
    "Sana'a", "Sanaa", "Sana", "Sanaa Province",
    "Marib", "Ma'rib",
]


def extract():
    if not PDF.exists():
        print(f"ERROR: {PDF} not found")
        return
    print(f"=== Extracting {PDF.name} ===")
    reader = PdfReader(str(PDF))
    print(f"  pages: {len(reader.pages)}")
    pages_text = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception as e:
            print(f"  page {i+1}: extract fail {type(e).__name__}: {e}")
            txt = ""
        pages_text.append(txt)
    full = "\n\n--- PAGE BREAK ---\n\n".join(pages_text)
    OUT_TXT.write_text(full, encoding="utf-8")
    print(f"  -> {OUT_TXT}  ({len(full):,} chars)")

    # Scan for governorate mentions + provide counts
    print(f"\n=== Yemen Six Wars admin-unit candidates ===")
    full_lower = full.lower()
    for gov in YEMEN_GOVERNORATES:
        n = full_lower.count(gov.lower())
        if n > 0:
            print(f"  {gov:20s} {n:4d} mentions")

    # Extract context windows around 'Saada' (the primary war zone)
    print(f"\n=== Sample contexts around 'Saada' (first 5) ===")
    pattern = re.compile(r".{120}saada.{120}", re.IGNORECASE)
    matches = pattern.findall(full)[:5]
    for m in matches:
        cleaned = " ".join(m.split())
        print(f"  ... {cleaned} ...")


if __name__ == "__main__":
    extract()
