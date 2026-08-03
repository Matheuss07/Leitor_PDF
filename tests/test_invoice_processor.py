from pathlib import Path

import pytest
from app.core import invoice_processor

# Mocking text representing individual invoices
INVOICE_1_TEXT = """
GRUPO DE TENSÃO: B SUBGRUPO: B3
CLASSIFICAÇÃO: PODER PÚBLICO MUNICIPAL
SUBCLASSE: MUNICIPAL SERVICOS PUBLICOS
TIPO DE FORNECIMENTO: MONOFÁSICO
MODALIDADE TARIFÁRIA: B3_OUTROS

MUNICIPIO DE FLEXEIRAS
CNPJ: **.***.721/000*-**
CASA DA MERENDA
R. CEL ALCANTARA , S/N ,
CEP: 57995-000 - CENTRO - FLEXEIRAS - AL

Leitura Anterior Leitura Atual Nº de Dias Próxima Leitura
06/05/2026 03/06/2026 28 03/07/2026

E2005221 Consumo ATIVO TOTAL 32.690 32.985 1,00 295 kWh

Nome do Cliente: C.C: Unidade de Leitura: Competência: Vencimento: Valor cobrado (R$):
MUNICIPIO DE FLEXEIRAS 7790228 FL01B004 06/2026 349,64

23/07/2026 R$ 349,64
669.008.008-24
06/2026

NOTA FISCAL Nº 071133140
DATA DE EMISSÃO: 03/06/2026
"""

INVOICE_2_TEXT = """
GRUPO DE TENSÃO: B SUBGRUPO: B3
CLASSIFICAÇÃO: PODER PÚBLICO MUNICIPAL
SUBCLASSE: MUNICIPAL SERVICOS PUBLICOS
TIPO DE FORNECIMENTO: MONOFÁSICO
MODALIDADE TARIFÁRIA: B3_OUTROS

MUNICIPIO DE MACEIO
CNPJ: **.***.123/000*-**
SECRETARIA DE SAUDE
AV. FERNANDES LIMA , 100 ,
CEP: 57000-000 - FAROL - MACEIO - AL

Leitura Anterior Leitura Atual Nº de Dias Próxima Leitura
10/05/2026 08/06/2026 29 08/07/2026

E9999999 Consumo ATIVO TOTAL 10.000 10.500 1,00 500 kWh

Nome do Cliente: C.C: Unidade de Leitura: Competência: Vencimento: Valor cobrado (R$):
MUNICIPIO DE MACEIO 1234567 FL01B004 06/2026 500,00

25/07/2026 R$ 500,00
111.222.333-44
06/2026

NOTA FISCAL Nº 071133141
DATA DE EMISSÃO: 08/06/2026
"""


def test_process_single_invoice():
    """Test that a list with pages of a single invoice yields exactly 1 invoice dictionary."""
    pages = [INVOICE_1_TEXT]
    invoices = invoice_processor.process_invoice_pages(pages)
    
    assert len(invoices) == 1
    assert invoices[0]["cliente"] == "MUNICIPIO DE FLEXEIRAS"
    assert invoices[0]["uc"] == "669.008.008-24"
    assert invoices[0]["medidor"] == "E2005221"
    assert invoices[0]["conta_mes"] == "06/2026"
    assert invoices[0]["total_pagar"] == 349.64


def test_process_multiple_invoices():
    """Test that a list with pages representing multiple invoices yields all of them."""
    pages = [INVOICE_1_TEXT, INVOICE_2_TEXT]
    invoices = invoice_processor.process_invoice_pages(pages)
    
    assert len(invoices) == 2
    
    # Verify first invoice
    assert invoices[0]["cliente"] == "MUNICIPIO DE FLEXEIRAS"
    assert invoices[0]["uc"] == "669.008.008-24"
    assert invoices[0]["medidor"] == "E2005221"
    assert invoices[0]["conta_mes"] == "06/2026"
    assert invoices[0]["total_pagar"] == 349.64
    
    # Verify second invoice
    assert invoices[1]["cliente"] == "MUNICIPIO DE MACEIO"
    assert invoices[1]["uc"] == "111.222.333-44"
    assert invoices[1]["medidor"] == "E9999999"
    assert invoices[1]["conta_mes"] == "06/2026"
    assert invoices[1]["total_pagar"] == 500.00


def test_ignores_non_invoice_pages_before_extracting_fields(monkeypatch):
    """Grouped summaries and invoice backs never reach the field extractor."""
    grouped_summary = "CLIENTE: MUNICIPIO DE FLEXEIRAS\nVALOR: 349,64"
    invoice_back = "UNIDADE CONSUMIDORA 669.008.008-24\nVENCIMENTO 23/07/2026"
    extracted_texts = []

    def record_extraction(text):
        extracted_texts.append(text)
        return {"source": text}

    monkeypatch.setattr(invoice_processor.extractor, "extract_fields", record_extraction)
    invoices = invoice_processor.process_invoice_pages([
        grouped_summary, INVOICE_1_TEXT, invoice_back, INVOICE_2_TEXT, "",
    ])

    assert len(invoices) == 2
    assert extracted_texts == [INVOICE_1_TEXT, INVOICE_2_TEXT]
    assert invoice_processor.split_invoice_pages([
        grouped_summary, INVOICE_1_TEXT, invoice_back, INVOICE_2_TEXT,
    ]) == [INVOICE_1_TEXT, INVOICE_2_TEXT]


def test_no_data_leakage():
    """Verify that data from one invoice does not leak into another."""
    pages = [INVOICE_1_TEXT, INVOICE_2_TEXT]
    invoices = invoice_processor.process_invoice_pages(pages)
    
    assert len(invoices) == 2
    
    # Cross checks
    assert invoices[0]["uc"] != invoices[1]["uc"]
    assert invoices[0]["cliente"] != invoices[1]["cliente"]
    assert invoices[0]["medidor"] != invoices[1]["medidor"]
    assert invoices[0]["total_pagar"] != invoices[1]["total_pagar"]


def test_last_invoice_is_processed():
    """Verify that the last invoice in the pages is fully processed."""
    pages = [INVOICE_1_TEXT, INVOICE_2_TEXT]
    blocks = invoice_processor.split_invoice_pages(pages)
    
    assert len(blocks) == 2
    assert "MUNICIPIO DE MACEIO" in blocks[1]
    
    invoices = invoice_processor.process_invoice_pages(pages)
    assert len(invoices) == 2
    assert invoices[1]["cliente"] == "MUNICIPIO DE MACEIO"


def test_invoices_with_same_uc_and_reference_are_preserved():
    """Grouped PDFs keep one result for every invoice even when IDs repeat."""
    # Same UC/reference, but still two distinct source invoices.
    invoice_1_dup = INVOICE_1_TEXT.replace("MUNICIPIO DE FLEXEIRAS", "MUNICIPIO DE FLEXEIRAS UPDATED")
    
    pages = [INVOICE_1_TEXT, invoice_1_dup]
    invoices = invoice_processor.process_invoice_pages(pages)
    
    assert len(invoices) == 2
    assert invoices[0]["cliente"] == "MUNICIPIO DE FLEXEIRAS"
    assert invoices[1]["cliente"] == "MUNICIPIO DE FLEXEIRAS UPDATED"


def test_real_grouped_pdf_generates_one_record_per_invoice():
    """The supplied grouped PDF has 15 one-page invoices."""
    pdf_path = Path(__file__).parents[1] / "uploads" / "pdf_fatura.pdf"

    invoices = invoice_processor.process_pdf_with_multiple_invoices(str(pdf_path))

    assert len(invoices) == 15
    required_fields = {
        "cliente", "uc", "medidor", "local_unidade", "conta_mes",
        "vencimento", "classificacao", "subclasse", "tipo_fornecimento",
        "leitura_anterior", "leitura_atual", "consumo_kwh", "total_pagar",
    }
    assert all(required_fields <= invoice.keys() for invoice in invoices)
    assert len({(invoice["medidor"], invoice["total_pagar"]) for invoice in invoices}) > 1

    invoice_11 = invoices[10]
    assert invoice_11["uc"] == "281.609.008-09"
    assert invoice_11["medidor"] == "E3252034"
    assert invoice_11["tipo_fornecimento"] == "TRIFÁSICO"
    assert invoice_11["leitura_anterior"] == 8982
    assert invoice_11["leitura_atual"] == 9288
    assert invoice_11["consumo_kwh"] == 306.0
