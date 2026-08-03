from pathlib import Path

import pytest

from app.core import extractor, normalizer


REFERENCE_TEXT = """
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


EXPECTED = {
    "cliente": "MUNICIPIO DE FLEXEIRAS",
    "uc": "669.008.008-24",
    "medidor": "E2005221",
    "local_unidade": "CASA DA MERENDA, R. CEL ALCANTARA, S/N, CEP: 57995-000 - CENTRO - FLEXEIRAS - AL",
    "conta_mes": "06/2026",
    "vencimento": "2026-07-23",
    "classificacao": "PODER PÚBLICO MUNICIPAL",
    "subclasse": "MUNICIPAL SERVICOS PUBLICOS",
    "tipo_fornecimento": "MONOFÁSICO",
    "leitura_anterior": 32690,
    "leitura_atual": 32985,
    "consumo_kwh": 295.0,
    "total_pagar": 349.64,
}


def test_extracts_all_fields_from_equatorial_reference_layout():
    result = extractor.extract_fields(REFERENCE_TEXT)

    assert result == EXPECTED
    assert set(result) == set(EXPECTED)


def test_measurement_row_never_uses_cte_as_meter():
    result = extractor.extract_fields(REFERENCE_TEXT)

    assert result["medidor"] == "E2005221"
    assert result["medidor"] != "Cte"
    assert result["leitura_anterior"] == 32690
    assert result["leitura_atual"] == 32985
    assert result["consumo_kwh"] == 295.0


def test_extracts_numeric_meter_and_thousands_separated_consumption():
    public_lighting_text = REFERENCE_TEXT.replace(
        "E2005221 Consumo ATIVO TOTAL 32.690 32.985 1,00 295 kWh",
        "17020234040 Consumo ATIVO TOTAL 7.279 7.435 1,00 1.448 kWh",
    )

    result = extractor.extract_fields(public_lighting_text)

    assert result["medidor"] == "17020234040"
    assert result["leitura_anterior"] == 7279
    assert result["leitura_atual"] == 7435
    assert result["consumo_kwh"] == 1448.0


def test_uses_billed_value_instead_of_other_invoice_totals():
    result = extractor.extract_fields(REFERENCE_TEXT + "\nTOTAL A PAGAR R$ 346,22\n")

    assert result["total_pagar"] == 349.64


def test_extracts_billed_value_when_footer_is_attached_to_amount():
    text = REFERENCE_TEXT.replace("349,64", "93,85DV")

    result = extractor.extract_fields(text)

    assert result["total_pagar"] == 93.85


def test_extracts_fields_when_adjacent_pdf_columns_join_a_line():
    compact = REFERENCE_TEXT.replace(
        "TIPO DE FORNECIMENTO: MONOFÁSICO\nMODALIDADE",
        "TIPODEFORNECIMENTO:MONOFÁSICO MODALIDADE",
    ).replace(
        "CLASSIFICAÇÃO: PODER PÚBLICO MUNICIPAL\nSUBCLASSE",
        "CLASSIFICAÇÃO: PODER PÚBLICO MUNICIPAL SUBCLASSE",
    )

    result = extractor.extract_fields(compact)

    assert result["classificacao"] == "PODER PÚBLICO MUNICIPAL"
    assert result["subclasse"] == "MUNICIPAL SERVICOS PUBLICOS"
    assert result["tipo_fornecimento"] == "MONOFÁSICO"
    assert result["medidor"] == "E2005221"
    assert result["leitura_anterior"] == 32690
    assert result["leitura_atual"] == 32985
    assert result["consumo_kwh"] == 295.0
    assert result["total_pagar"] == 349.64


def test_defaults_are_returned_for_empty_or_unmatched_text():
    assert extractor.extract_fields("") == extractor.DEFAULT_DATA
    assert extractor.extract_fields("Texto sem campos da fatura") == extractor.DEFAULT_DATA


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("32.690,00", 32690),
        ("32.985,00", 32985),
        ("32.690", 32690),
        ("32.985", 32985),
    ],
)
def test_normalize_number(raw, expected):
    assert normalizer.normalize_number(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("295,00", 295.0), ("503,72", 503.72), ("349,64", 349.64)],
)
def test_brazilian_decimals(raw, expected):
    assert normalizer.normalize_float(raw) == expected
    assert normalizer.normalize_monetary(raw) == expected


def test_normalizer_identifiers_and_dates():
    assert normalizer.normalize_uc("UC: 669.008.008-24") == "669.008.008-24"
    assert normalizer.normalize_reference_month("6/26") == "06/2026"
    assert normalizer.normalize_date("23/07/2026") == "2026-07-23"


def test_real_pdf_when_it_is_available():
    pdf_path = Path.home() / "Downloads" / "Fatura_certa.pdf"
    if not pdf_path.exists():
        pytest.skip("Reference PDF is not present in Downloads.")

    pytest.importorskip("pdfplumber")
    from app.core import pdf_reader

    result = extractor.extract_fields(pdf_reader.extract_text_from_pdf(str(pdf_path)))
    assert result == EXPECTED
