import re
from app.core import extractor, normalizer

MOCK_FATURA_1 = """
EQUATORIAL ENERGIA MARANHÃO
UNIDADE CONSUMIDORA: 30198765
CONTA CONTRATO: 0030198765
CLIENTE: JOÃO DA SILVA CORREIA
CPF: 123.456.789-00
ENDEREÇO: RUA DAS PALMEIRAS, 100 - COHAB
CEP: 65000-000 - SÃO LUÍS - MA
NOTA FISCAL Nº 876543
MÊS/ANO REF. 05/2026
VENCIMENTO 15/05/2026
EMISSÃO 02/05/2026
VALOR TOTAL A PAGAR R$ 345,78
Consumo Ativo (kWh) 250
Leitura Anterior: 12300 em 01/04/2026
Leitura Atual: 12550 em 01/05/2026
PREV. PRÓX. LEITURA: 01/06/2026
Tarifa de energia: 0,85430
CIP - ILUM. PUBLICA: R$ 25,50
Multa por atraso: R$ 3,50
"""

# Let's run a manual check on the name extraction
titular_patterns = [
    r"(?:nome\s+do\s+cliente|cliente|titular|destinat[áa]rio)[:\s]+([A-ZÀ-Úa-zà-ú0-9\s\.]{10,60})",
    r"(?:nome\s+do\s+cliente|cliente|titular|destinat[áa]rio)\s+([A-ZÀ-Úa-zà-ú0-9\s\.]{10,60})"
]

print("--- Check Name patterns ---")
for p in titular_patterns:
    match = re.search(p, MOCK_FATURA_1, re.IGNORECASE)
    if match:
        print(f"Pattern {p} matched: {match.group(1)}")
    else:
        print(f"Pattern {p} did NOT match")

# Let's run a manual check on ref_patterns
ref_patterns = [
    r"(?:m[êe]s/ano\s+ref[erência]*|refer[êe]ncia|m[êe]s\s+ref\.*)[:\s]+([a-zA-Z0-9/]+)",
    r"(?:m[êe]s/ano\s+ref[erência]*|refer[êe]ncia|m[êe]s\s+ref\.*)\s+([a-zA-Z0-9/]+)",
    r"\b(0[1-9]|1[0-2])/(20\d{2}|\d{2})\b"
]

print("--- Check Ref patterns ---")
for idx, p in enumerate(ref_patterns):
    match = re.search(p, MOCK_FATURA_1, re.IGNORECASE)
    if match:
        print(f"Pattern {idx} matched: {match.groups()}")
    else:
        print(f"Pattern {idx} did NOT match")

data = extractor.extract_fields(MOCK_FATURA_1)
print("Extracted data:", data)
