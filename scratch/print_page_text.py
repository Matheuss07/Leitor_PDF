import pdfplumber
import os

pdf_path = "uploads/pdf_fatura.pdf"
if not os.path.exists(pdf_path):
    print("PDF not found!")
    exit(1)

with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text(layout=True, x_tolerance=2, y_tolerance=3)
    print("--- Page 1 Text ---")
    print(text)
