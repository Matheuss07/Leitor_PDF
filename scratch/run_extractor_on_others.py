import pdfplumber
import os
from app.core import extractor, pdf_reader

files = ["uploads/Fatura.pdf", "uploads/Fatura_certa.pdf"]

for f in files:
    if not os.path.exists(f):
        print(f"{f} not found!")
        continue
    print(f"\n==================== File: {f} ====================")
    text = pdf_reader.extract_text_from_pdf(f)
    data = extractor.extract_fields(text)
    for k, v in data.items():
        print(f"{k}: {v}")
