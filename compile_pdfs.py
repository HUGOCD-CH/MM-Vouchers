import fitz
import glob
import os

PDF_DIR = "/home/user/MM-Vouchers"
pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
pdfs = [p for p in pdfs if os.path.basename(p) not in ("all_vouchers.pdf", "barcode_summary.pdf")]

print(f"Processing {len(pdfs)} PDFs...")

# ── 1. Simple full merge ──────────────────────────────────────────────────────
merged = fitz.open()
for path in pdfs:
    doc = fitz.open(path)
    merged.insert_pdf(doc)
    doc.close()
merged_path = os.path.join(PDF_DIR, "all_vouchers.pdf")
merged.save(merged_path)
merged.close()
print(f"Full merge saved: {merged_path}")

# ── 2. Barcode-focused summary ────────────────────────────────────────────────
# Crop region: left third, bottom 22% of each A4 page (barcode lives here)
# A4 ≈ 596 × 842 pt  →  crop x=[0,220], y=[670,842]
CROP = fitz.Rect(0, 665, 235, 842)

# Layout: 2 columns × 4 rows = 8 crops per page, on A4
A4_W, A4_H = 595, 842
COLS, ROWS = 2, 4
MARGIN = 20
CELL_W = (A4_W - MARGIN * (COLS + 1)) / COLS
CELL_H = (A4_H - MARGIN * (ROWS + 1)) / ROWS

summary = fitz.open()
current_page = None
idx = 0

for pdf_path in pdfs:
    src = fitz.open(pdf_path)
    src_page = src[0]

    col = idx % COLS
    row = (idx // COLS) % ROWS

    if idx % (COLS * ROWS) == 0:
        current_page = summary.new_page(width=A4_W, height=A4_H)

    # Destination rectangle for this cell
    x0 = MARGIN + col * (CELL_W + MARGIN)
    y0 = MARGIN + row * (CELL_H + MARGIN)
    dest_rect = fitz.Rect(x0, y0, x0 + CELL_W, y0 + CELL_H)

    # Draw a light border around each cell
    current_page.draw_rect(dest_rect, color=(0.8, 0.8, 0.8), width=0.5)

    # Label: filename without extension
    label = os.path.splitext(os.path.basename(pdf_path))[0]
    current_page.insert_text(
        (x0 + 2, y0 + 9),
        label,
        fontsize=7,
        color=(0.4, 0.4, 0.4),
    )

    # Clip and render the barcode region into the cell
    clip_rect = fitz.Rect(x0, y0 + 11, x0 + CELL_W, y0 + CELL_H)
    current_page.show_pdf_page(clip_rect, src, 0, clip=CROP)

    src.close()
    idx += 1

summary_path = os.path.join(PDF_DIR, "barcode_summary.pdf")
summary.save(summary_path)
summary.close()
print(f"Barcode summary saved: {summary_path}")
print("Done.")
