import pdfplumber
import os
from app.core import extractor

pdf_path = "uploads/pdf_fatura.pdf"
if not os.path.exists(pdf_path):
    print("PDF not found!")
    exit(1)

with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=3)
        print(f"\n--- Page {i+1} ---")
        if not text:
            print("[Empty text]")
            continue
            
        data = extractor.extract_fields(text)
        print(f"Extracted client: {data.get('cliente')}")
        print(f"Extracted UC: {data.get('uc')}")
        print(f"Extracted medidor: {data.get('medidor')}")
        print(f"Extracted conta_mes: {data.get('conta_mes')}")
        print(f"Extracted total_pagar: {data.get('total_pagar')}")
