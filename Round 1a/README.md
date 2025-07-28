Adobe India Hackathon – Round 1A Submission


🔍 Challenge
Extract a structured outline (Title, H1, H2, H3) from a PDF and output as JSON.
The solution must run in a CPU-only Docker container, offline, within 10 seconds per 50-page PDF.


🛠 Tech Stack
Language: Python 3.10
Library: PyMuPDF (fitz)
Infra: Docker (CPU-only, AMD64)
Constraints: No Internet, No GPU, Model-Free (≤ 200MB total size)



🧠 Approach
Used PyMuPDF to extract fonts, sizes, bounding boxes, and layout.
Detected Title using highest font size, position constraints, and filters.
Detected headings (H1, H2, H3) using:
Font size thresholds (relative to top 3 sizes)
Bold/uppercase/length heuristics
Layout features (position on page, avoiding footers/headers)
Skipped low-confidence matches like copyright/DOI/email lines.



🐳 Docker Instructions

🔨 Build Docker Image
docker build --platform linux/amd64 -t pdf-extractor .

▶ Run Container
docker run --rm ^
 -v %cd%\input:/app/input ^
 -v %cd%\output:/app/output ^
 --network none pdf-extractor
📌 Use ^ in Windows CMD.
📌 For PowerShell, replace with `.



📂 I/O Format
Input:
PDFs in input/ folder (mounted to /app/input)

Output:
JSONs in output/ folder (mounted to /app/output)

Example:
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 }
  ]
}


✅ Constraints Handled
⏱ Executes in ≤10 seconds for 50-page PDFs
🧠 No large models used
🌐 Offline execution (no web calls)
🧊 Docker image platform: linux/amd64