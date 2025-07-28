import fitz  # PyMuPDF
import os
import json
from pathlib import Path
from collections import defaultdict

def extract_title_and_outline(pdf_path):
    doc = fitz.open(pdf_path)
    all_spans = []
    font_size_map = defaultdict(list)
    max_font_size = 0

    for page_number, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if not text or len(text) < 2:
                        continue
                    size = round(span["size"], 1)
                    font = span.get("font", "").lower()
                    bbox = span.get("bbox", [])
                    is_bold = "bold" in font or "bd" in font

                    font_size_map[size].append(text)
                    all_spans.append({
                        "text": text,
                        "size": size,
                        "page": page_number,
                        "bbox": bbox,
                        "is_bold": is_bold,
                        "font": font
                    })

                    if size > max_font_size:
                        max_font_size = size

    sizes = sorted(font_size_map.keys(), reverse=True)
    page_count = len(doc)

    # ---- Detect Document Type ---- #
    def detect_doc_type():
        big_spans = [s for s in all_spans if s["size"] >= sizes[0] - 0.5]
        fonts_used = set(s["font"] for s in all_spans)
        if page_count == 1:
            if len(big_spans) <= 2 and len(fonts_used) <= 3:
                return "form"
            elif len(big_spans) >= 3:
                return "poster"
            else:
                return "company_doc"
        elif page_count > 5:
            return "structured"
        else:
            return "unknown"

    doc_type = detect_doc_type()

    # ---- Extract Title ---- #
    title = ""
    title_spans = [
        s for s in all_spans
        if s["page"] == 0
        and 80 < s["bbox"][1] < 300
        and len(s["text"].split()) > 2
        and s["size"] >= max_font_size - 0.5
        and not any(x in s["text"].lower() for x in ["doi", "@", "author", "copyright", "received"])
    ]
    title_spans = sorted(title_spans, key=lambda s: s["bbox"][1])
    if title_spans:
        title = " ".join([s["text"] for s in title_spans]).strip()
    else:
        fallback = [
            s for s in all_spans
            if s["page"] == 0 and s["size"] >= sizes[0] - 0.5 and len(s["text"]) > 3
        ]
        if fallback:
            title = " ".join([s["text"] for s in sorted(fallback, key=lambda s: s["bbox"][1])]).strip()

    # ---- Outline Extraction ---- #
    outline = []
    used = set()

    banned_keywords = ["copyright", "doi", "page", "email", "received", "author", "published", "version"]
    banned_start = tuple(str(i) for i in range(1950, 2030))

    def is_heading_like(text):
        text = text.strip()
        lower = text.lower()
        if any(b in lower for b in banned_keywords):
            return False
        if text.startswith(banned_start):
            return False
        if len(text.split()) > 20:
            return False
        return (
            text.isupper() or
            len(text.split()) <= 7 or
            text[0].isdigit()
        )

    def get_level(size):
        if size >= sizes[0] - 0.1:
            return "H1"
        elif len(sizes) > 1 and size >= sizes[1] - 0.1:
            return "H2"
        elif len(sizes) > 2 and size >= sizes[2] - 0.1:
            return "H3"
        else:
            return "H4"

    if doc_type in ["structured", "company_doc"]:
        for s in all_spans:
            key = (s["text"], s["page"])
            if key in used:
                continue
            if not is_heading_like(s["text"]):
                continue
            if s["size"] < sizes[-1] or len(s["text"]) < 4:
                continue
            if s["bbox"][1] > 750:  # skip footers
                continue
            used.add(key)
            outline.append({
                "level": get_level(s["size"]),
                "text": s["text"],
                "page": s["page"]
            })
        if len(outline) < 2:
            outline = []

    elif doc_type == "poster":
        largest = max(all_spans, key=lambda s: s["size"], default=None)
        if largest and len(largest["text"].split()) <= 12:
            outline = [{
                "level": "H1",
                "text": largest["text"],
                "page": largest["page"]
            }]

    elif doc_type == "form":
        outline = []

    return {
        "title": title.strip(),
        "outline": outline
    }

def process_all_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("📂 No PDFs found in /app/input.")
        return

    for pdf_file in pdf_files:
        try:
            result = extract_title_and_outline(str(pdf_file))
            output_path = output_dir / f"{pdf_file.stem}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"[✓] Processed: {pdf_file.name}")
        except Exception as e:
            print(f"[✗] Failed: {pdf_file.name} – {e}")

if __name__ == "__main__":
    print("🚀 Running Final PDF Extractor...")
    process_all_pdfs()
    print("✅ All Done.")
