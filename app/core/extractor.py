"""Field extraction rules for Equatorial electricity invoices."""

import logging
import re

from app.core import normalizer

logger = logging.getLogger(__name__)

DEFAULT_DATA = {
    "cliente": "N/A",
    "uc": "N/A",
    "medidor": "N/A",
    "local_unidade": "N/A",
    "conta_mes": "N/A",
    "vencimento": "N/A",
    "classificacao": "N/A",
    "subclasse": "N/A",
    "tipo_fornecimento": "N/A",
    "leitura_anterior": 0,
    "leitura_atual": 0,
    "consumo_kwh": 0.0,
    "total_pagar": 0.0,
}


def _clean_text(value: str) -> str:
    """Collapse layout spacing without changing meaningful punctuation."""
    value = re.sub(r"[ \t]+", " ", value).strip()
    value = re.sub(r"\s+([,.;:])", r"\1", value)
    value = re.sub(r"([,.;:])(?=\S)", r"\1 ", value)
    return re.sub(r",\s*,", ",", value)


def _first_group(patterns: list[str], text: str, flags: int = re.IGNORECASE) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return None


def _extract_measurement(text: str) -> tuple[str, int, int, float] | None:
    """Extract the consumption row, the authoritative source for meter/readings."""
    number = r"(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"
    pattern = re.compile(
        # Meters in the supplied public-lighting batch can be alphanumeric
        # (E3252034) or numeric (17020234040).  They are distinct from a UC
        # because they occur directly before the measurement row.
        rf"\b([A-Z][A-Z0-9-]{{4,}}|\d{{6,}})\s*Consumo\s*ATIVO\s*TOTAL\s+"
        rf"({number})\s+({number})\s+{number}\s+({number})\s*kWh\b",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None

    meter, previous, current, consumption = match.groups()
    return (
        meter.upper(),
        normalizer.normalize_number(previous),
        normalizer.normalize_number(current),
        normalizer.normalize_float(consumption),
    )


def _extract_address(text: str) -> str | None:
    """Read the installation-address block that follows the CNPJ/CPF block."""
    lines = [_clean_text(line) for line in text.splitlines() if line.strip()]
    start = next((i + 1 for i, line in enumerate(lines) if re.match(r"^(?:CNPJ|CPF)\s*:", line, re.I)), None)
    if start is None:
        return _first_group([
            r"(?:ENDERE[CÇ]O|LOCAL)\s*:\s*(.+?)(?=\s+CEP\s*:|\n|$)",
        ], text)

    address_lines = []
    stop_pattern = re.compile(
        r"^(?:Leitura Anterior|Nome do Cliente|NOTA FISCAL|GRUPO DE TENS[ÃA]O|"
        r"CONTA|VENCIMENTO|Valor cobrado)",
        re.IGNORECASE,
    )
    for line in lines[start:]:
        if stop_pattern.match(line):
            break
        if line.startswith("--- P"):
            continue
        address_lines.append(line)
        if line.upper().startswith("CEP:"):
            break

    if not address_lines:
        return None

    address = _clean_text(" ".join(address_lines))
    address = re.sub(r"NOTA\s*FISCAL[^\n]*", "", address, flags=re.I)
    address = re.sub(r"DATA\s*DE\s*EMISS.{0,4}O\s*:\s*\d{2}/\d{2}/\d{4}", "", address, flags=re.I)
    address = re.sub(r"Consulte\s+pela\s+Chave.*$", "", address, flags=re.I)
    cep_match = re.search(r"(.+?\bCEP\s*:\s*\d{5}-\d{3}\s*-\s*.+?\s*-\s*[A-Z]{2}\b)", address, re.I)
    if cep_match:
        address = cep_match.group(1)
    if not re.search(r"\b(?:R\.|RUA|AV\.|AVENIDA|ESTRADA|TRAVESSA)\s", address, re.I):
        street_match = re.search(r"((?:R\.|RUA|AV\.|AVENIDA|ESTRADA|TRAVESSA)\s*[^\n]+)", text, re.I)
        cep_line_match = re.search(r"(CEP\s*:\s*\d{5}-\d{3}\s*-\s*[^\n]+?\s*-\s*[A-Z]{2}\b)", text, re.I)
        if street_match and cep_line_match:
            street = re.sub(r"NOTA\s*FISCAL.*$", "", street_match.group(1), flags=re.I)
            street = re.sub(r"DATA\s*DE\s*EMISS.{0,4}O\s*:\s*\d{2}/\d{2}/\d{4}", "", street, flags=re.I)
            address = f"{address}, {_clean_text(street)}, {_clean_text(cep_line_match.group(1))}"
    address = re.sub(r"(?<=\w)\s+(?=(?:R\.|RUA\b|AV\.|AVENIDA\b|ESTRADA\b|TRAVESSA\b))", ", ", address, flags=re.I)
    return _clean_text(address)


def extract_fields(text: str) -> dict:
    """Extract exactly the invoice model consumed by API, UI, and Excel."""
    data = DEFAULT_DATA.copy()
    if not text or not text.strip():
        logger.warning("Invoice text is empty.")
        return data

    normalized = re.sub(r"[ \t]+", " ", text)

    # The customer row follows the 'Nome do Cliente' header in current invoices.
    cliente = _first_group([
        r"Nome\s*do\s*Cliente\s*:[^\n]*\n\s*([^\n]+?)\s+\d{5,}\b",
        r"Nome\s*do\s*Cliente\s*:\s*([A-ZÀ-Ú][A-ZÀ-Ú ]+?)(?=\s*(?:C\.?C\.?|\d{5,}))",
    ], text, re.IGNORECASE | re.DOTALL)
    if cliente:
        data["cliente"] = _clean_text(cliente).upper()

    uc = _first_group([
        r"\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b",
        r"(?:UNIDADE CONSUMIDORA|C[ÓO]DIGO DA UC|\bUC)\s*[:\-]?\s*([0-9][0-9.\-]{5,30})",
    ], normalized)
    if uc:
        data["uc"] = normalizer.normalize_uc(uc)

    measurement = _extract_measurement(normalized)
    if measurement:
        data["medidor"], data["leitura_anterior"], data["leitura_atual"], data["consumo_kwh"] = measurement
    else:
        meter = _first_group([
            r"(?:N[º°]\s*)?Medidor\s*[:\-]?\s*([A-Z0-9][A-Z0-9-]{3,})",
        ], normalized)
        if meter and meter.upper() not in {"CTE", "ATUAL", "ANTERIOR", "FP"}:
            data["medidor"] = meter.upper()

        previous = _first_group([r"Leit(?:ura|\.)?\s*Anterior\s*:\s*([\d.,]+)"], normalized)
        current = _first_group([r"Leit(?:ura|\.)?\s*Atual\s*:\s*([\d.,]+)"], normalized)
        consumption = _first_group([
            r"Consumo\s+Ativo\s*\(?(?:kWh)?\)?\s*([\d.,]+)",
            r"ATIVO\s*:\s*([\d.,]+)\s*kWh",
        ], normalized)
        if previous:
            data["leitura_anterior"] = normalizer.normalize_number(previous)
        if current:
            data["leitura_atual"] = normalizer.normalize_number(current)
        if consumption:
            data["consumo_kwh"] = normalizer.normalize_float(consumption)

    address = _extract_address(text)
    if address:
        data["local_unidade"] = address

    reference = _first_group([
        r"Nome\s*do\s*Cliente\s*:.*?\b(\d{1,2}/\d{4})\b(?=\s*(?:\d{1,3}(?:\.\d{3})*,\d{2}|AG\s*/))",
        r"Compet[êe]ncia:.*?\n[^\n]*?\b(\d{1,2}/\d{4})\b",
        r"(?:M[ÊE]S/ANO\s*REF\.?|M[ÊE]S\s*REF\.?|REFER[ÊE]NCIA|Ref\.)\s*[:\-]?\s*([A-Z0-9/]+)",
        r"\b(\d{1,2}/\d{4})\b",
    ], text, re.IGNORECASE | re.DOTALL)
    if reference:
        data["conta_mes"] = normalizer.normalize_reference_month(reference)

    due_date = _first_group([
        r"\b(\d{1,2}/\d{1,2}/\d{4})\s+R\$\s*[\d.,]+",
        r"Vencimento:.*?\n[^\n]*?\b(\d{1,2}/\d{1,2}/\d{2,4})\b",
        r"(?:VENCIMENTO|Vence em|Vecto\.?)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ], text, re.IGNORECASE | re.DOTALL)
    if due_date:
        data["vencimento"] = normalizer.normalize_date(due_date)

    compact_fields = {
        "classificacao": r"CLASSIFICA.{0,4}O\s*:\s*(.+?)(?=\s*(?:SUBCLASSE|TIPO\s*DE\s*FORNECIMENTO|MODALIDADE\s*TARIF.{0,5}RIA|\n|$))",
        "subclasse": r"SUBCLASSE\s*:\s*(.+?)(?=\s*(?:TIPO\s*DE\s*FORNECIMENTO|MODALIDADE\s*TARIF.{0,5}RIA|LEITURA\s*ANTERIOR|\n|$))",
        "tipo_fornecimento": r"TIPO\s*DE\s*FORNECIMENTO\s*:\s*(.+?)(?=\s*(?:MODALIDADE\s*TARIF.{0,5}RIA|LEITURA\s*ANTERIOR|\n|$))",
    }
    for key, pattern in compact_fields.items():
        value = _first_group([pattern], text)
        if value:
            data[key] = _clean_text(value).upper()

    for key, label in (
        ("classificacao", "CLASSIFICA[ÇC][ÃA]O"),
        ("subclasse", "SUBCLASSE"),
        ("tipo_fornecimento", "TIPO DE FORNECIMENTO"),
    ):
        value = _first_group([rf"{label}\s*:\s*([^\n]+)"], text)
        if value and data[key] == "N/A":
            data[key] = _clean_text(value).upper()

    # In Equatorial's current layout, this value is the last currency in the
    # customer summary row. Prefer it over billing-line totals elsewhere.
    summary = re.search(r"Nome\s*do\s*Cliente\s*:.*?(?=NOTA\s*FISCAL|\Z)", text, re.I | re.S)
    if summary:
        # Do not require a word boundary after cents: layout extraction can
        # concatenate the amount with the following footer text (e.g. 93,85DV).
        values = re.findall(r"(?<![\d.,])\d{1,3}(?:\.\d{3})*,\d{2}(?!\d)", summary.group(0))
        if values:
            data["total_pagar"] = normalizer.normalize_monetary(values[-1])
    if data["total_pagar"] == 0.0:
        total = _first_group([
            r"(?:VALOR TOTAL A PAGAR|TOTAL A PAGAR|Valor cobrado)\s*(?:R\$)?\s*([\d.,]+)",
            r"\b\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+R\$\s*([\d.,]+)",
        ], normalized)
        if total:
            data["total_pagar"] = normalizer.normalize_monetary(total)

    logger.info("Invoice extraction completed: %s", data)
    return data
