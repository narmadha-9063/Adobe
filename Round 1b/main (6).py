import fitz  # PyMuPDF
import os
import json
import re
from datetime import datetime
from collections import defaultdict

# === CONFIGURATION === #
PERSONA = "Travel Planner"
JOB_TO_BE_DONE = "Plan a trip of 4 days for a group of 10 college friends."
KEYWORDS = [
    "cities", "things to do", "restaurants", "hotels", "coastal", "adventure", "cuisine",
    "culture", "nightlife", "tips", "itinerary", "activities", "food", "packing", "places"
]

INPUT_FOLDER = "/input"
OUTPUT_FOLDER = "/output"

# === HELPER FUNCTIONS === #

def clean_text(text):
    return ' '.join(text.strip().split())

def is_relevant(text, keywords):
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)

def extract_pdf_info(pdf_path, keywords):
    doc = fitz.open(pdf_path)
    relevant_sections = []
    subsection_texts = []

    filename = os.path.basename(pdf_path)

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = ""
                font_sizes = []

                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                    font_sizes.append(span.get("size", 0))

                text = clean_text(line_text)
                if not text or len(text) < 4:
                    continue

                max_font = max(font_sizes or [0])

                if is_relevant(text, keywords):
                    section = {
                        "document": filename,
                        "section_title": text,
                        "page_number": page_num + 1,
                        "importance_score": len([kw for kw in keywords if kw in text.lower()]),
                        "refined_text": page.get_text()
                    }
                    relevant_sections.append(section)

    return relevant_sections

# === MAIN PROCESSOR === #

def main():
    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".pdf")]
    all_sections = []

    for file in files:
        pdf_path = os.path.join(INPUT_FOLDER, file)
        sections = extract_pdf_info(pdf_path, KEYWORDS)
        all_sections.extend(sections)

    # Sort by importance
    ranked_sections = sorted(all_sections, key=lambda x: -x["importance_score"])

    # Pick top 5
    top_sections = ranked_sections[:5]

    # Build final JSON
    metadata = {
        "input_documents": files,
        "persona": PERSONA,
        "job_to_be_done": JOB_TO_BE_DONE,
        "processing_timestamp": datetime.now().isoformat()
    }

    extracted_sections = [
        {
            "document": s["document"],
            "section_title": s["section_title"],
            "importance_rank": i + 1,
            "page_number": s["page_number"]
        }
        for i, s in enumerate(top_sections)
    ]

    subsection_analysis = [
        {
            "document": s["document"],
            "refined_text": s["refined_text"].strip(),
            "page_number": s["page_number"]
        }
        for s in top_sections
    ]

    result = {
        "metadata": metadata,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(os.path.join(OUTPUT_FOLDER, "final_output.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ Round 1B Output JSON generated successfully.")

# === RUN === #
if __name__ == "__main__":
    main()
