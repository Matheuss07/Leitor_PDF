import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


MONTHS_PT = {
    'JANEIRO': '01',
    'JAN': '01',
    'FEVEREIRO': '02',
    'FEV': '02',
    'MARÇO': '03',
    'MAR': '03',
    'ABRIL': '04',
    'ABR': '04',
    'MAIO': '05',
    'MAI': '05',
    'JUNHO': '06',
    'JUN': '06',
    'JULHO': '07',
    'JUL': '07',
    'AGOSTO': '08',
    'AGO': '08',
    'SETEMBRO': '09',
    'SET': '09',
    'OUTUBRO': '10',
    'OUT': '10',
    'NOVEMBRO': '11',
    'NOV': '11',
    'DEZEMBRO': '12',
    'DEZ': '12'
}


def clean_only_digits(value: str) -> str:
    """
    Remove tudo exceto dígitos numéricos.
    """

    if value is None:
        return ""

    return re.sub(r"\D", "", str(value))


def normalize_uc(uc_val: str) -> str:
    """
    Normaliza a Unidade Consumidora.

    Mantém a formatação original da UC quando possível.

    Exemplo:
        669.008.008-24
        permanece:
        669.008.008-24

    Caso a UC venha sem formatação, mantém os números.
    """

    if uc_val is None:
        logger.warning("UC recebida como None.")
        return "N/A"

    uc_val = str(uc_val).strip()

    if not uc_val:
        logger.warning("UC recebida vazia.")
        return "N/A"

    # Remove espaços extras
    labelled_value = re.search(
        r"(?:UC|UNIDADE\s+CONSUMIDORA)\s*:\s*([0-9][0-9.\-\s]+)",
        uc_val,
        re.IGNORECASE,
    )
    if labelled_value:
        uc_val = labelled_value.group(1)

    uc_val = re.sub(r"\s+", "", uc_val)

    # Verifica se contém pelo menos 6 dígitos
    digits = clean_only_digits(uc_val)

    if len(digits) < 6:
        logger.warning(
            f"UC encontrada, mas parece inválida: '{uc_val}'"
        )
        return "N/A"

    # Mantém a UC exatamente como encontrada
    logger.info(
        f"UC normalizada com sucesso: '{uc_val}'"
    )

    return uc_val


def normalize_cpf_cnpj(val: str) -> str:
    """
    Normaliza CPF ou CNPJ mantendo apenas números
    e preservando zeros à esquerda.
    """

    if not val:
        return "N/A"

    cleaned = clean_only_digits(val)

    if len(cleaned) in [11, 14]:
        return cleaned

    return cleaned if cleaned else "N/A"


def normalize_monetary(val: str) -> float:
    """
    Normaliza valores monetários brasileiros.

    Exemplos:

        R$ 1.250,50 -> 1250.50
        1.250,50 -> 1250.50
        349.64 -> 349.64
        -15,30 -> -15.30
        4.25- -> -4.25
    """

    if val is None:
        return 0.0

    if not str(val).strip():
        return 0.0

    try:

        cleaned = str(val).strip()

        # Remove R$
        cleaned = re.sub(
            r"R\$",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = cleaned.strip()

        # Verifica negativo
        is_negative = False

        if cleaned.startswith("-"):
            is_negative = True
            cleaned = cleaned[1:].strip()

        elif cleaned.endswith("-"):
            is_negative = True
            cleaned = cleaned[:-1].strip()

        # Remove espaços
        cleaned = cleaned.replace(" ", "")

        # Formato brasileiro:
        # 1.250,50 -> 1250.50

        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif re.fullmatch(r"[-+]?\d{1,3}(?:\.\d{3})+", cleaned):
            cleaned = cleaned.replace(".", "")

        else:

            # Formato:
            # 349.64

            # Mantém o ponto decimal
            cleaned = cleaned

        result = float(cleaned)

        if is_negative:
            result = -result

        return result

    except Exception as e:

        logger.warning(
            f"Não foi possível normalizar "
            f"valor monetário '{val}': {e}"
        )

        return 0.0


def normalize_float(val: str) -> float:
    """
    Normaliza valores float brasileiros.

    Exemplos:

        250,5 -> 250.5
        1.250,00 -> 1250.0
        1.250,00 kWh -> 1250.0
    """

    if not val:
        return 0.0

    try:

        cleaned = str(val).strip()

        # Remove kWh
        cleaned = re.sub(
            r"(?i)\s*kwh",
            "",
            cleaned
        )

        # Formato brasileiro
        if "," in cleaned:

            cleaned = (
                cleaned
                .replace(".", "")
                .replace(",", ".")
            )
        elif re.fullmatch(r"[-+]?\d{1,3}(?:\.\d{3})+", cleaned):
            # A dot-only value in this layout is a thousands separator
            # (e.g. 1.448 kWh), not a decimal consumption value.
            cleaned = cleaned.replace(".", "")

        return float(cleaned)

    except Exception as e:

        logger.warning(
            f"Não foi possível normalizar "
            f"float '{val}': {e}"
        )

        return 0.0


def normalize_number(val: str) -> int:
    """
    Normaliza números inteiros.

    Exemplos:

        1.250 -> 1250
        235,00 -> 235
        32.690,00 -> 32690
        32.985,00 -> 32985
    """

    if val is None:
        return 0

    if not str(val).strip():
        return 0

    try:

        cleaned = str(val).strip()

        # Remove kWh
        cleaned = re.sub(
            r"(?i)\s*kwh",
            "",
            cleaned
        )

        # Se possui vírgula decimal,
        # remove a parte decimal
        if "," in cleaned:
            cleaned = cleaned.split(",", 1)[0].replace(".", "")
        elif re.fullmatch(r"[-+]?\d{1,3}(?:\.\d{3})+", cleaned):
            cleaned = cleaned.replace(".", "")

        return int(float(cleaned))

    except Exception as e:

        logger.warning(
            f"Não foi possível normalizar "
            f"número '{val}': {e}"
        )

        return 0


def normalize_date(date_str: str) -> str:
    """
    Normaliza datas brasileiras.

    Entrada:
        23/07/2026

    Saída:
        2026-07-23
    """

    if not date_str:
        return "N/A"

    cleaned = str(date_str).strip()

    # Já está em ISO
    if re.match(
        r"^\d{4}-\d{2}-\d{2}$",
        cleaned
    ):
        return cleaned

    # Aceita / ou -
    match = re.match(
        r"^(\d{1,2})[/-]"
        r"(\d{1,2})[/-]"
        r"(\d{2,4})$",
        cleaned
    )

    if match:

        day, month, year = match.groups()

        day = day.zfill(2)
        month = month.zfill(2)

        if len(year) == 2:
            year = "20" + year

        return (
            f"{year}-"
            f"{month}-"
            f"{day}"
        )

    logger.warning(
        f"Data no formato desconhecido: "
        f"'{date_str}'"
    )

    return "N/A"


def normalize_reference_month(ref_str: str) -> str:
    """
    Normaliza mês/ano de referência.

    Exemplos:

        05/2026 -> 05/2026
        MAIO/2026 -> 05/2026
        MAI/26 -> 05/2026
    """

    if not ref_str:
        return "N/A"

    cleaned = str(ref_str).strip().upper()

    # Formato numérico
    match_digits = re.match(
        r"^(\d{1,2})/"
        r"(\d{2,4})$",
        cleaned
    )

    if match_digits:

        month, year = match_digits.groups()

        month = month.zfill(2)

        if len(year) == 2:
            year = "20" + year

        return f"{month}/{year}"

    # Formato textual
    parts = re.split(
        r"[/\-\s]+",
        cleaned
    )

    if len(parts) == 2:

        month_part, year_part = parts

        month_num = MONTHS_PT.get(
            month_part
        )

        if not month_num:

            for key, value in MONTHS_PT.items():

                if (
                    key in month_part
                    or month_part in key
                ):

                    month_num = value
                    break

        if month_num:

            year = year_part

            if len(year) == 2:
                year = "20" + year

            return (
                f"{month_num}/{year}"
            )

    logger.warning(
        f"Mês de referência não reconhecido: "
        f"'{ref_str}'"
    )

    return "N/A"
