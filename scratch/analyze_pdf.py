import pdfplumber
import re
import os

pdf_path = "uploads/pdf_fatura.pdf"
if not os.path.exists(pdf_path):
    print("PDF not found!")
    exit(1)

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    invoice_start_regex = re.compile(r"GRUPO\s*DE\s*TENS", re.IGNORECASE)
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=3)
        print(f"\n--- Page {i+1} ---")
        if not text:
            print("[Empty page text]")
            continue
            
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        print(f"Lines count: {len(lines)}")
        print("First 5 lines:")
        for line in lines[:5]:
            print(f"  {line}")
        print("Last 5 lines:")
        for line in lines[-5:]:
            print(f"  {line}")
            
        match = invoice_start_regex.search(text)
        print(f"Contains INVOICE_START: {bool(match)}")
