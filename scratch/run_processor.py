from app.core import invoice_processor
import os

pdf_path = "uploads/pdf_fatura.pdf"
if not os.path.exists(pdf_path):
    print("PDF not found!")
    exit(1)

invoices = invoice_processor.process_pdf_with_multiple_invoices(pdf_path)
print(f"Total invoices processed: {len(invoices)}")
for idx, inv in enumerate(invoices):
    print(f"\nInvoice {idx+1}:")
    print(f"  Cliente: {inv.get('cliente')}")
    print(f"  UC: {inv.get('uc')}")
    print(f"  Medidor: {inv.get('medidor')}")
    print(f"  Referência: {inv.get('conta_mes')}")
    print(f"  Total a Pagar: {inv.get('total_pagar')}")
